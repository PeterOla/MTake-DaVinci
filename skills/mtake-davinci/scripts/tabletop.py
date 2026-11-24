"""Project the editable OBJ instances through one orthographic camera."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SIZE = (540, 960)
FPS, FRAMES = 30, 270
POSITIONS = (0., 1.1, 2.2, 3.3, 5.85)
START = (9, 23, 32, 41)
CONTACTS = (23, 32, 41, 58)
HEIGHT, THICKNESS = 1.80, .28


def smooth(x):
    x = max(0., min(1., x))
    return x*x*(3-2*x)


def load_mesh(path):
    points, faces, group = [], [], None
    for line in path.read_text(encoding="ascii").splitlines():
        tok = line.split()
        if tok[:1] == ["v"]:
            points.append(tuple(map(float, tok[1:4])))
        elif tok[:1] == ["g"]:
            group = tok[1]
        elif tok[:1] == ["f"]:
            faces.append((group, np.array([int(a)-1 for a in tok[1:]], dtype=int)))
    return np.array(points), faces


def angle(index, frame):
    if index == 4 or frame <= START[index]:
        return 0.
    # The right-hand top corner reaches the next tile's back plane at this angle.
    hit = math.asin((1.1 - THICKNESS) / HEIGHT)
    if index < 3:
        contact = CONTACTS[index]
        if frame <= contact:
            return hit*((frame - START[index])/(contact - START[index]))**1.65
        end = 58 + index * 2
        resting = math.radians((75, 75, 77)[index])
        return hit + (resting-hit)*smooth((frame-contact)/(end-contact))
    u = min(1., (frame-START[index])/(CONTACTS[index]-START[index]))
    return (math.pi/2)*u**1.5


def unit(v):
    return v / np.linalg.norm(v)


class View:
    def __init__(self, frame):
        pull = smooth((frame-5)/65)
        approach = smooth((frame-106)/91)
        self.centre = np.array([1.14+2.00*pull+.98*approach, 0., .78-.29*approach])
        self.eye = unit(np.array([-5.+1.6*pull, -9., 4.5+2.9*pull]))
        self.right = unit(np.cross((0.,0.,1.), self.eye))
        self.up = np.cross(self.eye, self.right)
        self.scale = 125.-39.*pull+31.*approach

    def project(self, points):
        delta = np.asarray(points)-self.centre
        x = SIZE[0]*.50 + (delta @ self.right)*self.scale
        y = SIZE[1]*.475 - (delta @ self.up)*self.scale
        return list(zip(x.tolist(),y.tolist()))

    def depth(self, points):
        return np.asarray(points) @ self.eye


def desk(draw, view):
    def poly(pts, fill, edge=None):
        draw.polygon(view.project(pts), fill=fill)
        if edge:
            draw.line(view.project(pts+[pts[0]]),fill=edge,width=2)
    x0,x1=-5.3,10.4
    y0,y1=-2.20,2.6
    poly([(x0,y0,0),(x1,y0,0),(x1,y0,-.34),(x0,y0,-.34)],(37,32,30),(87,72,62))
    poly([(x0,y0,0),(x0,y1,0),(x0,y1,-.34),(x0,y0,-.34)],(32,29,28))
    poly([(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)],(46,40,36),(108,89,73))
    for y in (-1.55,-.65,.40,1.58):
        draw.line(view.project([(x0,y,0),(x1,y,0)]),fill=(59,50,43),width=1)
    for i in range(64):
        x=x0+i*.25
        length = .14 if i%4==0 else .065
        draw.line(view.project([(x,y0+.025,.001),(x,y0+length,.001)]),fill=(103,82,63),width=1)
    rng=np.random.default_rng(927)
    for _ in range(90):
        x=rng.uniform(x0,x1); y=rng.uniform(y0,y1); span=rng.uniform(.07,.58)
        draw.line(view.project([(x,y,0),(x+span*.44,y+.009,0),(x+span,y,0)]),fill=(51,44,39),width=1)


def tile_points(mesh, idx, frame):
    pts = mesh[0]
    a = angle(idx,frame)
    c, s = math.cos(a), math.sin(a)
    rot=np.array([[c,0,s],[0,1,0],[-s,0,c]])
    return pts @ rot.T + (POSITIONS[idx],0.,.006)


def render(frame, mesh, fontfile, subtitles, mode="ink", omit=None):
    w,h=SIZE
    background=np.zeros((h,1,3),np.uint8)
    for y in range(h):
        u=math.exp(-((y/h-.51)/.34)**2)
        background[y,0]=(round(15+11*u),round(17+9*u),round(19+6*u))
    im=Image.fromarray(np.repeat(background,w,axis=1))
    d=ImageDraw.Draw(im)
    view=View(frame)
    desk(d,view)
    ids=[i for i in range(5) if i != omit]
    for idx in ids:
        x=POSITIONS[idx]
        hproj=.25*math.cos(angle(idx,frame))
        shadow=[(x-.29,-.47,.003),(x+.09,-.47,.003),(x+hproj+.9*math.sin(angle(idx,frame)),.43,.003),
                (x+hproj-.28,.56,.003)]
        d.polygon(view.project(shadow),fill=(31,29,28))
    light=unit(np.array([-3.,-3.,6.]))
    # The fronts, bevels, sides and pips are faces of the imported mesh.
    for idx in sorted(ids,key=lambda i:view.depth([POSITIONS[i],0,0])):
        pts=tile_points(mesh,idx,frame)
        projected=view.project(pts)
        def face_depth(item):
            g,face=item
            return (g in ("pip","rule"),float(np.mean(view.depth(pts[face]))))
        for group,face in sorted(mesh[1],key=face_depth):
            vertices=pts[face]
            # Accumulate all edges; a rounded face's first few vertices can be nearly collinear.
            n=unit(np.cross(vertices[1]-vertices[0], vertices[-1]-vertices[0]))
            if np.dot(n,view.eye)<.001:
                continue
            xy=[projected[i] for i in face]
            lit=max(0.,np.dot(n,light))
            if mode=="neutral":
                val=int(70+134*lit); color=(val,val,val)
                if group in ("pip","rule"): color=(57,57,57)
            elif group in ("pip","rule"):
                color=(210,185,143) if group=="pip" else (132,116,94)
            elif group=="marked":
                color=(64,59,55)
            elif group=="bevel":
                color=tuple(round(a+b*lit) for a,b in ((58,103),(53,88),(48,71)))
            else:
                color=tuple(round(a+b*lit) for a,b in ((34,47),(33,41),(34,33)))
            d.polygon(xy,fill=color)
            if group in ("marked","back") and mode!="neutral":
                d.line(xy+[xy[0]],fill=(182,158,124),width=2,joint="curve")
    if mode=="ink" and omit is None and frame>=148:
        amount=smooth((frame-148)/30)
        start=POSITIONS[3]+HEIGHT
        finish=POSITIONS[4]-THICKNESS
        extent=start+(finish-start)*amount
        for pts in ([(start,-.63,.008),(extent,-.63,.008)],
                    [(start,-.53,.008),(start,-.72,.008)],
                    [(extent,-.53,.008),(extent,-.72,.008)]):
            d.line(view.project(pts),fill=(218,141,101),width=2)
    if mode=="ink":
        for start,end,phrase in subtitles:
            if start <= frame < end:
                font=ImageFont.truetype(str(fontfile),37)
                d.text((w*.5,h*.72),phrase,font=font,anchor="mm",fill=(247,236,214),
                       stroke_width=1,stroke_fill=(21,19,20))
    return im
