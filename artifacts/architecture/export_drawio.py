"""Export the inspected figures as native, uncompressed draw.io XML.

All rectangles, text, XOR symbols, junctions and signal routes are editable
mxGraph cells. Module labels are children of their module boxes. Connectors
whose endpoints touch a module are attached using fixed connection points.
No SVG images or bitmap images are embedded in the draw.io documents.
"""
from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET
import cairo
from figure_lib import ROOT
from build_detailed import build_top,build_round,build_key
from build_overviews import build_controller,build_transforms


def num(v):
    return f'{float(v):.3f}'.rstrip('0').rstrip('.')


def style(**kw):
    return ';'.join(f'{k}={v}' for k,v in kw.items())+';'


def convert(svg):
    xml=ET.parse(svg).getroot()
    w,h=float(xml.get('width')),float(xml.get('height'))
    elements=list(xml)
    records=[]
    surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,1,1)
    ctx=cairo.Context(surface)
    # Preserve the original object ordering and turn arrowhead polygons into
    # native edge arrowheads instead of disconnected decorative triangles.
    for el in elements:
        kind=el.tag.rsplit('}',1)[-1];a=el.attrib
        if kind=='polygon':
            assert records[-1]['kind']=='polyline'
            records[-1]['arrow']=True
            continue
        rec={'el':el,'kind':kind,'id':f'c{len(records)+2}','parent':'1'}
        if kind=='rect':
            box=tuple(float(a[k]) for k in ['x','y','width','height'])
            # The background is the page background, not an editable white box.
            if box==(0.,0.,w,h):continue
            rec['box']=box
        elif kind=='circle':
            x,y,r=[float(a[k]) for k in ['cx','cy','r']]
            rec['box']=(x-r,y-r,2*r,2*r)
        elif kind=='text':
            s=el.text or '';fs=float(a['font-size'])
            ctx.select_font_face('DejaVu Sans',cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_BOLD if a.get('font-weight')=='700' else cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(fs)
            tw=ctx.text_extents(s).x_advance+10
            x,y=float(a['x']),float(a['y'])
            anchor=a.get('text-anchor','start')
            left=x-tw/2 if anchor=='middle' else x-tw+5 if anchor=='end' else x-5
            rec['box']=(left,y-fs,tw,fs*1.25)
        elif kind=='polyline':
            rec['points']=[tuple(map(float,p.split(','))) for p in a['points'].split()]
            rec['arrow']=False
        else:
            raise ValueError(kind)
        records.append(rec)

    # Only meaningful module boxes act as grouping parents; panels, table grid
    # cells and white label masks remain independent graphical elements.
    modules=[r for r in records if r['kind']=='rect'
        and r['el'].get('stroke') not in ('none','#CCD2D9')
        and r['box'][2]>100 and 50<r['box'][3]<500]
    def contains(a,b):
        return b[0]>=a[0]-.01 and b[1]>=a[1]-.01 and b[0]+b[2]<=a[0]+a[2]+.01 and b[1]+b[3]<=a[1]+a[3]+.01
    byid={r['id']:r for r in records}
    for rec in records:
        if rec['kind'] not in ('rect','text'):continue
        parents=[m for m in modules if m is not rec and contains(m['box'],rec['box'])
                 and m['box'][2]*m['box'][3]>rec['box'][2]*rec['box'][3]+1]
        if parents:rec['parent']=min(parents,key=lambda r:r['box'][2]*r['box'][3])['id']

    model=ET.Element('mxGraphModel',dx=num(w),dy=num(h),grid='1',gridSize='10',guides='1',
        tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',
        pageWidth=num(w),pageHeight=num(h),math='0',shadow='0',background='#FFFFFF')
    root=ET.SubElement(model,'root')
    ET.SubElement(root,'mxCell',id='0')
    ET.SubElement(root,'mxCell',id='1',parent='0')
    terminals=modules+[r for r in records if r['kind']=='circle' and r['box'][2]>10]
    def terminal(p):
        candidates=[]
        for r in terminals:
            x,y,rw,rh=r['box'];px,py=p
            if px<x-.1 or px>x+rw+.1 or py<y-.1 or py>y+rh+.1:continue
            boundary=min(abs(px-x),abs(px-x-rw),abs(py-y),abs(py-y-rh))
            if boundary<.1:candidates.append(r)
        return min(candidates,key=lambda r:r['box'][2]*r['box'][3]) if candidates else None

    for rec in records:
        a=rec['el'].attrib;k=rec['kind']
        attrs={'id':rec['id'],'parent':rec['parent']}
        st={}
        if k=='polyline':
            attrs.update(edge='1',value='')
            st.update(noEdgeStyle=1,edgeStyle='none',rounded=0,html=0,
                strokeColor=a['stroke'],strokeWidth=a.get('stroke-width','2'),
                startArrow='none',endArrow='block' if rec['arrow'] else 'none',
                endFill=1,endSize=8)
            if 'stroke-dasharray' in a:st.update(dashed=1,dashPattern='4 3')
            pts=rec['points']
            for side,p,prefix in [('source',pts[0],'exit'),('target',pts[-1],'entry')]:
                term=terminal(p)
                if term:
                    attrs[side]=term['id'];tx,ty,tw,th=term['box']
                    st.update({prefix+'X':num((p[0]-tx)/tw),prefix+'Y':num((p[1]-ty)/th),
                        prefix+'Dx':0,prefix+'Dy':0,prefix+'Perimeter':0})
            attrs['style']=style(**st)
            cell=ET.SubElement(root,'mxCell',**attrs)
            geo=ET.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
            for label,p in [('sourcePoint',pts[0]),('targetPoint',pts[-1])]:
                ET.SubElement(geo,'mxPoint',x=num(p[0]),y=num(p[1]),**{'as':label})
            if len(pts)>2:
                arr=ET.SubElement(geo,'Array',**{'as':'points'})
                for p in pts[1:-1]:ET.SubElement(arr,'mxPoint',x=num(p[0]),y=num(p[1]))
            continue
        attrs['vertex']='1'
        if k=='text':
            attrs['value']=rec['el'].text or ''
            st.update(shape='text',html=0,whiteSpace='nowrap',overflow='visible',
                align='center',verticalAlign='middle',spacing=0,
                fontFamily='DejaVu Sans',fontSize=a['font-size'],
                fontStyle=1 if a.get('font-weight')=='700' else 0,
                fontColor=a['fill'],strokeColor='none',fillColor='none',
                resizable=1,rotatable=0)
        else:
            attrs['value']=''
            st.update(shape='ellipse' if k=='circle' else 'rectangle',
                fillColor=a.get('fill','none'),strokeColor=a.get('stroke','none'),
                strokeWidth=a.get('stroke-width','1'),rounded=0,html=0,
                container=1 if rec in modules else 0,collapsible=0,recursiveResize=0)
            if 'stroke-dasharray' in a:st.update(dashed=1,dashPattern='4 3')
        attrs['style']=style(**st)
        cell=ET.SubElement(root,'mxCell',**attrs)
        x,y,rw,rh=rec['box']
        if rec['parent']!='1':
            px,py,_,_=byid[rec['parent']]['box'];x-=px;y-=py
        ET.SubElement(cell,'mxGeometry',x=num(x),y=num(y),width=num(rw),height=num(rh),**{'as':'geometry'})
    return model


def save(path,pages):
    doc=ET.Element('mxfile',host='app.diagrams.net',agent='RTL architecture exporter',
        version='26.0.0',type='device',compressed='false')
    for i,(title,model) in enumerate(pages,1):
        diagram=ET.SubElement(doc,'diagram',id=f'aes128-{i}',name=title)
        diagram.append(deepcopy(model))
    ET.indent(doc,space='  ')
    ET.ElementTree(doc).write(path,encoding='utf-8',xml_declaration=True)


if __name__=='__main__':
    pages=[]
    for fn in [build_top,build_round,build_key,build_controller,build_transforms]:
        svg=fn();model=convert(svg)
        title=next(t.text for t in ET.parse(svg).getroot() if t.tag.endswith('text'))
        pages.append((title,model))
        out=svg.with_suffix('.drawio');save(out,[(title,model)]);print(out)
    combined=ROOT/'aes128_rtl_architecture.drawio';save(combined,pages);print(combined)
