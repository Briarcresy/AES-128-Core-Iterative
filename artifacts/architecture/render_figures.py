"""Export editable SVG sources to vector PDF and high-resolution PNG."""
from pathlib import Path
import subprocess
import cairo
import gi
gi.require_version('Rsvg','2.0')
from gi.repository import Rsvg
import xml.etree.ElementTree as ET
from figure_lib import ROOT
from build_detailed import build_top,build_round,build_key


def render(svg):
    root=ET.parse(svg).getroot()
    w,h=[float(root.attrib[a]) for a in ['width','height']]
    pdf=ROOT.parent/'pdf'/(svg.stem+'.pdf')
    pdf.parent.mkdir(parents=True,exist_ok=True)
    handle=Rsvg.Handle.new_from_file(str(svg))
    viewport=Rsvg.Rectangle();viewport.x=0;viewport.y=0;viewport.width=w;viewport.height=h
    surface=cairo.PDFSurface(str(pdf),w*.6,h*.6)
    ctx=cairo.Context(surface);ctx.scale(.6,.6)
    handle.render_document(ctx,viewport)
    surface.finish()
    return pdf


if __name__=='__main__':
    paths=[build_top(),build_round(),build_key()]
    try:
        from build_overviews import build_controller,build_transforms
        paths.extend([build_controller(),build_transforms()])
    except ImportError:
        pass
    pdfs=[]
    for p in paths:
        pdf=render(Path(p));pdfs.append(pdf)
        # PDF-rendered inspection images are also the delivered high-res previews.
        subprocess.run(['pdftoppm','-scale-to','2400','-png','-singlefile',str(pdf),str(ROOT/Path(p).stem)],check=True)
        print(pdf)
    if len(pdfs)==5:
        combined=ROOT.parent/'pdf'/'aes128_rtl_architecture.pdf'
        subprocess.run(['pdfunite',*[str(p) for p in pdfs],str(combined)],check=True)
        print(combined)
