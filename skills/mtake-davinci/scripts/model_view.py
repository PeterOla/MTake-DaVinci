"""Render the original library's vertex-coloured GLBs in dark or light architectural ink."""
import argparse
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image


def records(path):
    raw=path.read_bytes()
    if raw[:4]!=b"glTF":
        raise ValueError("Expected a binary glTF file.")
    length=struct.unpack_from("<I",raw,12)[0]
    doc=json.loads(raw[20:20+length])
    binary=memoryview(raw)[28+length:]
    def attribute(index):
        a=doc["accessors"][index]
        size={"VEC3":3,"SCALAR":1}[a["type"]]
        if a["componentType"]!=5126:
            raise ValueError("Use Blender for other GLB encodings.")
        v=doc["bufferViews"][a["bufferView"]]
        address=v.get("byteOffset",0)+a.get("byteOffset",0)
        return np.frombuffer(binary,"<f4",count=a["count"]*size,offset=address).reshape(-1,size)
    rows=[]
    for m in doc["meshes"]:
        for prim in m["primitives"]:
            if prim["mode"] not in (1,4) or "indices" in prim:
                raise ValueError("This reader supports the MTake unindexed triangle and line library. Use Blender for other GLBs.")
            attr=prim["attributes"]
            xyz=attribute(attr["POSITION"])
            rgb=attribute(attr["COLOR_0"])
            size=3 if prim["mode"]==4 else 2
            widths=attribute(attr["_STROKE_WIDTH"])[::size,0] if "_STROKE_WIDTH" in attr else None
            rows.append((size,xyz.reshape(-1,size,3),rgb.reshape(-1,size,3).mean(axis=1),widths))
    return rows


def render(path, theme="dark", azimuth=-34, elevation=23, width=640, height=460):
    rows=records(path)
    az,el=map(math.radians,(azimuth,elevation))
    eye=np.array([math.cos(el)*math.sin(az),math.sin(el),math.cos(el)*math.cos(az)])
    right=np.cross((0,1,0),eye); right/=np.linalg.norm(right)
    up=np.cross(eye,right)
    basis=np.column_stack((right,-up,eye))
    points=np.vstack([row[1].reshape(-1,3) for row in rows])@basis
    lo,hi=points.min(axis=0),points.max(axis=0)
    centre=(hi+lo)/2
    # Render at two times final size so phone-size edges keep their hierarchy.
    w,h=width*2,height*2
    scale=min(w*.86/max(hi[0]-lo[0],1e-5),h*.78/max(hi[1]-lo[1],1e-5))
    move=np.array((w/2,h/2,0))-centre*scale
    dark=theme=="dark"
    canvas=np.full((h,w,3),(22,22,23) if dark else (236,230,215),dtype=np.uint8)
    depth=np.full((h,w),-np.inf,dtype=np.float32)

    for size,positions,colours,widths in sorted(rows,key=lambda r:-r[0]):
        faces=positions@basis*scale+move
        for i,(pts,color) in enumerate(zip(faces,colours)):
            if size==3:
                (x0,y0,z0),(x1,y1,z1),(x2,y2,z2)=pts
                denominator=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
                if abs(denominator)<1e-5:
                    continue
                x_min,y_min=np.maximum(0,np.floor(pts[:,:2].min(axis=0)).astype(int))
                x_max,y_max=np.minimum([w-1,h-1],np.ceil(pts[:,:2].max(axis=0)).astype(int))
                if x_max<x_min or y_max<y_min: continue
                yy,xx=np.ogrid[y_min:y_max+1,x_min:x_max+1]
                a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/denominator
                b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/denominator
                c=1-a-b
                dz=a*z0+b*z1+c*z2
                zbuf=depth[y_min:y_max+1,x_min:x_max+1]
                visible=(a>=-.0001)&(b>=-.0001)&(c>=-.0001)&(dz>=zbuf)
                n=np.cross(positions[i,1]-positions[i,0],positions[i,2]-positions[i,0])
                n=n/max(1e-8,np.linalg.norm(n))
                light=.80+.36*np.dot(n,(-.35,.80,.47))
                tone=(20+73*color)*light if dark else (121+112*color)*(.91+.12*light)
                canvas[y_min:y_max+1,x_min:x_max+1][visible]=np.clip(tone,0,255)
                zbuf[visible]=dz[visible]
            else:
                a,b=pts
                steps=int(np.max(np.abs(b[:2]-a[:2])))+2
                step=np.linspace(a,b,steps)
                xs,ys=np.round(step[:,:2]).astype(int).T
                tone=(36+179*color) if dark else (83-51*color)
                radius=int(np.clip(round(widths[i]*.9 if widths is not None else 1),1,3))
                for dx,dy in ((0,0),(1,0),(0,1),(-1,0),(0,-1)):
                    if radius<2 and (dx<0 or dy<0): continue
                    x=np.clip(xs+dx,0,w-1); y=np.clip(ys+dy,0,h-1)
                    visible=step[:,2]>=depth[y,x]-1.75
                    canvas[y[visible],x[visible]]=np.clip(tone,0,255)
    return Image.fromarray(canvas).resize((width,height),Image.Resampling.LANCZOS)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--theme",choices=("dark","light"),default="dark")
    parser.add_argument("--azimuth",type=float,default=-34)
    parser.add_argument("--elevation",type=float,default=23)
    args=parser.parse_args()
    if args.output.exists(): parser.error("Choose a fresh output filename.")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    render(args.model,args.theme,args.azimuth,args.elevation).save(args.output)
