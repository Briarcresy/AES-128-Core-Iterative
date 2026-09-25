"""Small, deterministic SVG primitives for the RTL architecture figures."""
from pathlib import Path
from html import escape
import math
import cairo

ROOT = Path(__file__).resolve().parent
DATA = '#215D88'
KEY = '#96551B'
CTRL = '#636879'
INK = '#202733'
MUTED = '#626B78'
BLUE = '#F1F6FA'
GOLD = '#FBF5ED'
GRAY = '#F5F6F8'
LINE = '#CCD2D9'

class Figure:
    def __init__(self, width, height, title, subtitle, number):
        self.w, self.h, self.items = width, height, []
        self.rect(0, 0, width, height, fill='white', stroke='none')
        self.text(45, 49, title, 30, bold=True)
        self.text(45, 79, subtitle, 16, color=MUTED)
        self.text(width-45, 48, f'FIG. {number:02}', 17, color=MUTED, anchor='end')
        self.path([(45,96),(width-45,96)], LINE, arrow=False, width=1)

    def rect(self,x,y,w,h,fill='white',stroke=INK,width=1.6,dash=False,r=0):
        ds=' stroke-dasharray="7 5"' if dash else ''
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{ds}/>')

    def text(self,x,y,s,size=18,color=INK,anchor='start',bold=False):
        weight='700' if bold else '400'
        for i,line in enumerate(str(s).split('\n')):
            self.items.append(f'<text x="{x}" y="{y+i*size*1.35}" font-family="DejaVu Sans, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{escape(line)}</text>')

    def label(self,x,y,s,size=17,color=INK,anchor='middle'):
        surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,1,1)
        ctx=cairo.Context(surface);ctx.select_font_face('DejaVu Sans');ctx.set_font_size(size)
        lines=str(s).split('\n');w=max(ctx.text_extents(t).width for t in lines)+12
        left=x-w/2 if anchor=='middle' else x-6 if anchor=='start' else x-w+6
        self.rect(left,y-size,w,(len(lines)-1)*size*1.35+size+4,fill='white',stroke='none')
        self.text(x,y,s,size,color,anchor)

    def block(self,x,y,w,h,title,detail='',color=INK,fill='white',size=21):
        self.rect(x,y,w,h,fill,color)
        n=len(str(detail).split('\n')) if detail else 0
        ty=y+h/2-(n*21)/2+size*0.32
        self.text(x+w/2,ty,title,size,color,anchor='middle',bold=True)
        if detail:self.text(x+w/2,ty+28,detail,16,color,anchor='middle')

    def panel(self,x,y,w,h,title,color=INK,fill='white'):
        self.rect(x,y,w,h,fill,LINE,width=1)
        self.text(x+18,y+29,title,18,color,bold=True)

    def path(self,pts,color=DATA,width=2.5,dash=False,arrow=True):
        ds=' stroke-dasharray="8 6"' if dash else ''
        coords=' '.join(f'{x},{y}' for x,y in pts)
        self.items.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{ds}/>')
        if arrow and len(pts)>1:
            x,y=pts[-1];x0,y0=pts[-2];a=math.atan2(y-y0,x-x0)
            length=10 if width<3 else 12
            p=[(x,y),(x-length*math.cos(a)+4.5*math.sin(a),y-length*math.sin(a)-4.5*math.cos(a)),(x-length*math.cos(a)-4.5*math.sin(a),y-length*math.sin(a)+4.5*math.cos(a))]
            self.items.append(f'<polygon points="'+ ' '.join(f'{u},{v}' for u,v in p)+f'" fill="{color}"/>')

    def dot(self,x,y,color=DATA):
        self.items.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')

    def xor(self,x,y,r=22,color=KEY):
        self.items.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" stroke="{color}" stroke-width="2"/>')
        self.path([(x-r*.6,y),(x+r*.6,y)],color,width=1.8,arrow=False)
        self.path([(x,y-r*.6),(x,y+r*.6)],color,width=1.8,arrow=False)

    def footer(self,source):
        self.path([(45,self.h-49),(self.w-45,self.h-49)],LINE,width=1,arrow=False)
        self.text(45,self.h-24,source,14,color=MUTED)
        self.text(self.w-45,self.h-24,'RTL-derived | Verilog-2005',14,color=MUTED,anchor='end')

    def save(self,name):
        p=ROOT/(name+'.svg')
        p.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">\n'+ '\n'.join(self.items)+'\n</svg>\n')
        return p
