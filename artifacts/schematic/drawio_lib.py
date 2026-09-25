"""Native, editable mxGraph primitives. No raster or SVG intermediates."""
from pathlib import Path
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
INK = '#243447'
DATA = '#edf4fa'
STORE = '#e8f2ef'
CTRL = '#f3f0e8'
MUTED = '#566576'
FONT = 'Noto Sans CJK SC'

def style(**kw):
    return ';'.join(f'{k}={v}' for k,v in kw.items())+';'

class Page:
    def __init__(self, number, name, title, subtitle, source, width=1600, height=1000):
        self.name, self.width, self.height = name, width, height
        self.model = ET.Element('mxGraphModel', dx=str(width),dy=str(height),grid='1',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',pageWidth=str(width),pageHeight=str(height),math='0',shadow='0',background='#ffffff')
        self.root = ET.SubElement(self.model,'root')
        ET.SubElement(self.root,'mxCell',id='0')
        ET.SubElement(self.root,'mxCell',id='1',parent='0',value='Schematic')
        self.n=1; self.bounds={}; self.parents={}; self.muxes={}
        # A native page frame fixes identical PDF/PNG extents.
        self.box('',0,0,width,height,fill='#ffffff',stroke='none',extra={'locked':1})
        self.text(f'{number:02d}  {title}',42,25,width-84,44,size=29,bold=True)
        self.text(subtitle,44,76,width-88,31,size=17,color=MUTED)
        self.line([(42,119),(width-42,119)],arrow=False,color='#a7b4bf',width=1)
        self.line([(42,height-63),(width-42,height-63)],arrow=False,color='#a7b4bf',width=1)
        self.text('RTL: '+source,44,height-49,width-260,29,size=13,color=MUTED)
        self.text(f'AES-128  /  {number:02d}–06',width-225,height-49,180,29,size=14,color=MUTED,align='right')

    def vertex(self,value,x,y,w,h,st,parent='1'):
        self.n+=1; i=f'v{self.n}'
        c=ET.SubElement(self.root,'mxCell',id=i,value=value,style=style(**st),vertex='1',parent=parent)
        ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
        px,py=(self.bounds[parent][:2] if parent in self.bounds else (0,0))
        self.bounds[i]=(x+px,y+py,w,h);self.parents[i]=parent
        return i

    def box(self,value,x,y,w,h,fill=DATA,stroke=INK,size=18,bold=False,parent='1',extra=None):
        st=dict(shape='rectangle',rounded=0,html=0,whiteSpace='wrap',overflow='hidden',align='center',verticalAlign='middle',fontFamily=FONT,fontSize=size,fontStyle=1 if bold else 0,fontColor=INK,fillColor=fill,strokeColor=stroke,strokeWidth=1.8,spacing=6,container=1,collapsible=0,recursiveResize=0)
        st.update(extra or {})
        return self.vertex(value,x,y,w,h,st,parent)

    def text(self,value,x,y,w,h,size=17,bold=False,color=INK,align='left',parent='1'):
        return self.vertex(value,x,y,w,h,dict(shape='text',html=0,whiteSpace='wrap',overflow='hidden',align=align,verticalAlign='middle',fontFamily=FONT,fontSize=size,fontStyle=1 if bold else 0,fontColor=color,fillColor='none',strokeColor='none',spacing=0),parent)

    def reg(self,name,bits,x,y,w=205,h=90,parent='1'):
        i=self.box(name+'\n'+str(bits)+' bit',x,y,w,h,fill=STORE,bold=True,parent=parent)
        self.vertex('',5,h-22,12,14,dict(shape='triangle',direction='east',fillColor='#ffffff',strokeColor=INK,strokeWidth=1.2),i)
        self.text('clk',22,h-23,35,17,size=11,parent=i)
        return i

    def mux(self,label,x,y,w=64,h=126,parent='1',down=False):
        # Native grouped strokes give unambiguous orientation and fixed ports.
        i=self.box(label,x,y,w,h,fill='#ffffff',stroke='none',size=16,parent=parent)
        pts=([(0,0),(w,0),(.86*w,h),(.14*w,h),(0,0)] if down else
             [(0,0),(w,.14*h),(w,.86*h),(0,h),(0,0)])
        self.line(pts,arrow=False,parent=i,width=1.8)
        self.muxes[i]=down
        return i

    def xor(self,x,y,d=42,parent='1'):
        i=self.box('',x,y,d,d,fill='#ffffff',parent=parent,extra={'shape':'ellipse'})
        # Native child strokes form the XOR cross, avoiding font-glyph ambiguity.
        self.line([(2,d/2),(d-2,d/2)],arrow=False,parent=i,width=1.6)
        self.line([(d/2,2),(d/2,d-2)],arrow=False,parent=i,width=1.6)
        return i

    def tag(self,value,x,y,w=170,h=30,parent='1',control=False):
        return self.box(value,x,y,w,h,fill=CTRL if control else '#ffffff',size=14,parent=parent,extra={'shape':'hexagon','size':0.06,'strokeWidth':1.2})

    def dot(self,x,y,parent='1',visible=True):
        return self.box('',x-3,y-3,6,6,fill=INK if visible else 'none',stroke=INK if visible else 'none',parent=parent,extra={'shape':'ellipse'})

    def line(self,points,arrow=True,color=INK,width=1.8,dashed=False,parent='1'):
        self.n+=1;i=f'e{self.n}'
        c=ET.SubElement(self.root,'mxCell',id=i,value='',edge='1',parent=parent,style=style(edgeStyle='none',noEdgeStyle=1,rounded=0,html=0,strokeColor=color,strokeWidth=width,endArrow='block' if arrow else 'none',endSize=7,endFill=1,startArrow='none',dashed=1 if dashed else 0,jumpStyle='arc' if parent=='1' else 'none',jumpSize=7))
        g=ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
        ET.SubElement(g,'mxPoint',x=str(points[0][0]),y=str(points[0][1]),**{'as':'sourcePoint'})
        ET.SubElement(g,'mxPoint',x=str(points[-1][0]),y=str(points[-1][1]),**{'as':'targetPoint'})
        if len(points)>2:
            a=ET.SubElement(g,'Array',**{'as':'points'})
            for x,y in points[1:-1]:ET.SubElement(a,'mxPoint',x=str(x),y=str(y))
        return i

    def edge(self,source,target,sp=(1,.5),tp=(0,.5),via=(),label='',labelpos=None,arrow=True,dashed=False,width=1.8):
        def mux_port(i,p):
            if i not in self.muxes:return p
            x,y=p
            if self.muxes[i]:
                if x==0:x=.14*y
                elif x==1:x=1-.14*y
            else:
                if y==0:y=.14*x
                elif y==1:y=1-.14*x
            return x,y
        sp,tp=mux_port(source,sp),mux_port(target,tp)
        def pos(i,p):
            x,y,w,h=self.bounds[i];return x+w*p[0],y+h*p[1]
        points=[pos(source,sp),*via,pos(target,tp)]
        i=self.line(points,arrow=arrow,dashed=dashed,width=width)
        cell=self.root[-1];cell.set('source',source);cell.set('target',target)
        cell.set('style',cell.get('style')+style(exitX=sp[0],exitY=sp[1],exitDx=0,exitDy=0,exitPerimeter=0,entryX=tp[0],entryY=tp[1],entryDx=0,entryDy=0,entryPerimeter=0))
        if label:
            if labelpos is None:
                a,b=points[0],points[-1];labelpos=((a[0]+b[0])/2-45,(a[1]+b[1])/2-25,90,23)
            self.text(label,*labelpos,size=14,align='center')
        return i

    def note(self,text,x,y,w,h=65):
        return self.text(text,x,y,w,h,size=17,color=MUTED)

    def rom(self,x,y,w=280,h=185,reference=False):
        group=self.box('',x,y,w,h,fill='#ffffff',extra={'dashed':1 if reference else 0})
        self.text('S-box / sbox_rom',12,8,w-24,28,size=19,bold=True,parent=group)
        self.box('256 × 8\nsynchronous ROM',50,48,w-72,95,fill=STORE,size=17,parent=group)
        for yy in [58,70,82,94]:self.line([(56,yy),(74,yy)],arrow=False,parent=group,width=.8,color='#879f95')
        self.text('A[7:0]',5,66,48,24,size=11,parent=group)
        self.text('Q[7:0]',w-53,108,50,24,size=11,parent=group)
        self.text('▷ CLK   CEB = ~enable',12,h-32,w-24,24,size=13,parent=group)
        return group

def save(pages,path=None):
    doc=ET.Element('mxfile',host='Electron',agent='AES RTL schematic generator',version='31.3.2',type='device',compressed='false')
    for n,p in enumerate(pages,1):
        d=ET.SubElement(doc,'diagram',id=f'aes128-page-{n}',name=p.name);d.append(p.model)
    ET.indent(doc,space='  ')
    target=path or OUT/'aes128_schematic.drawio'
    ET.ElementTree(doc).write(target,encoding='utf-8',xml_declaration=True)
    return target
