#!/usr/bin/env python3
"""Export the editable source with the installed official draw.io application.

Run from any directory: python3 artifacts/schematic/export_drawio.py
The application performs all rendering; this script only invokes its CLI and
records provenance. Linux requires xvfb-run unless --no-xvfb is supplied.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def default_application() -> str:
    # Use the installed application directly: the snap launcher may require
    # access to /run/user even when Electron itself can run under Xvfb.
    installed = Path('/snap/drawio/current/app/drawio')
    if installed.is_file():
        return str(installed)
    return shutil.which('drawio') or 'drawio'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path,
                        default=Path(__file__).resolve().parent / 'aes128_schematic.drawio')
    parser.add_argument('--application', default=default_application())
    parser.add_argument('--scale', type=float, default=3.125,
                        help='PNG scale; 3.125 corresponds to 300 dpi at a 96 dpi base')
    parser.add_argument('--border', type=int, default=20)
    parser.add_argument('--timeout', type=int, default=180,
                        help='Maximum seconds per official application invocation')
    parser.add_argument('--no-xvfb', action='store_true',
                        help='Use an existing display instead of xvfb-run')
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    if args.scale <= 0 or args.border < 0:
        parser.error('--scale must be positive and --border must be nonnegative')

    root = ET.parse(source).getroot()
    pages = root.findall('diagram')
    if root.tag != 'mxfile' or not pages:
        raise ValueError('Expected a multi-page draw.io mxfile with diagram elements')

    source_hash = sha256(source)
    command_base = ([] if args.no_xvfb else ['xvfb-run', '-a']) + [
        args.application, '--no-sandbox', '--disable-gpu', '--disable-update',
    ]
    manifest = {
        'exporter': 'official draw.io desktop CLI',
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'source': source.name,
        'source_sha256': source_hash,
        'application': args.application,
        'page_count': len(pages),
        'png_scale': args.scale,
        'border': args.border,
        'commands': [],
        'outputs': [],
        'complete': False,
    }
    manifest_path = source.parent / 'export_manifest.json'

    def save_manifest() -> None:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n',
                                 encoding='utf-8')

    def invoke(options: list[str]) -> subprocess.CompletedProcess[str]:
        command = command_base + options
        print(subprocess.list2cmdline(command), flush=True)
        result = subprocess.run(command, text=True, capture_output=True,
                                timeout=args.timeout, check=False)
        manifest['commands'].append({
            'argv': command,
            'returncode': result.returncode,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
        })
        save_manifest()
        if result.returncode:
            raise RuntimeError(f'draw.io failed ({result.returncode}): {result.stderr or result.stdout}')
        if result.stdout:
            print(result.stdout.strip(), flush=True)
        return result

    def export(output: Path, options: list[str], page_name: str | None = None) -> None:
        invoke(['--export', '--theme', 'light', '--border', str(args.border)] + options +
               ['--output', str(output), str(source)])
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f'draw.io did not create a nonempty output: {output}')
        item = {'file': output.name, 'bytes': output.stat().st_size, 'sha256': sha256(output)}
        if page_name is not None:
            item['page_name'] = page_name
        manifest['outputs'].append(item)
        save_manifest()

    try:
        manifest['application_version'] = invoke(['--version']).stdout.strip()
        export(source.with_suffix('.pdf'), ['--format', 'pdf', '--all-pages', '--crop'])
        used_names: set[str] = set()
        for index, page in enumerate(pages, start=1):
            name = page.get('name', f'page_{index}')
            slug = re.sub(r'[^a-z0-9_-]+', '_', name.lower()).strip('_')
            slug = re.sub(r'^\d+[_-]*', '', slug) or 'page'
            filename = f'{index:02d}_{slug}.png'
            if filename in used_names:
                raise ValueError(f'Duplicate output page filename: {filename}')
            used_names.add(filename)
            export(source.parent / filename,
                   ['--format', 'png', '--page-index', str(index), '--scale', str(args.scale)],
                   page_name=name)
        if sha256(source) != source_hash:
            raise RuntimeError('Source changed during export; run again after saving the final draw.io file')
        manifest['complete'] = True
        manifest['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
        save_manifest()
    except Exception as exc:
        manifest['error'] = str(exc)
        save_manifest()
        raise


if __name__ == '__main__':
    main()
