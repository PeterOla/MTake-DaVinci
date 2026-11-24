"""Original transparent ink effects and dry sound components. See references/components.md."""
import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from media import RATE, wav


def steam(size, origin, radius, phase, seed=14):
    """Workshop steam backlit by a lamp. Radius in pixels, phase in [0,1]."""
    layer=Image.new("RGBA",size)
    if not 0 < phase < 1 or radius<=0:
        return layer
    rng=np.random.default_rng(seed)
    d=ImageDraw.Draw(layer)
    x0,y0=origin
    for depth in range(3):
        # Rear glow lasts longer; foreground lobes occlude parts of it.
        for i in range(13-depth):
            direction=rng.uniform(-math.pi*.96,-math.pi*.04)
            distance=radius*rng.uniform(.20,.98)*(phase**.58)
            x=x0+math.cos(direction)*distance+radius*.26*phase
            y=y0+math.sin(direction)*distance-radius*(.26+depth*.09)*phase
            r=radius*rng.uniform(.12,.29)*math.sin(math.pi*phase)**.52
            alpha=round(240*min(1,(1-phase)*3))
            palette=((187,119,72),(119,81,62),(52,46,44))
            d.ellipse((x-r,y-r,x+r,y+r),fill=(*palette[depth],alpha),
                      outline=(33,29,29,alpha),width=max(1,round(radius*.012)))
            if depth==0 and i%3==0:
                h=r*.36
                d.ellipse((x-h,y-h,x+h,y+h),fill=(245,198,133,alpha))
    return layer


def motion_marks(size, above, below, angle_deg, frame, length, weight=2):
    """Anchor to two silhouette points in output coordinates. Angle is screen direction."""
    layer=Image.new("RGBA",size)
    d=ImageDraw.Draw(layer)
    dx,dy=math.cos(math.radians(angle_deg)),math.sin(math.radians(angle_deg))
    for side,anchor in enumerate((above,below)):
        phase=((frame+side*4)%8)/8
        if phase>=.62:
            continue
        for i in range(2):
            near=length*(.06+.46*phase+i*.64)
            far=near+length*(.48 if i==0 else .23)
            x,y=anchor
            d.line([(x-dx*near,y-dy*near),(x-dx*far,y-dy*far)],
                   fill=(222,209,184,round(190*(1-phase))),width=weight)
    return layer


def felt_note(hz, seconds, level=.25, decay=.34):
    t=np.arange(round(seconds*RATE))/RATE
    envelope=np.minimum(1,t/.004)*np.exp(-t/decay)*np.minimum(1,(seconds-t)/.018)
    return level*envelope*(np.sin(2*np.pi*hz*t)+.28*np.sin(4*np.pi*hz*t)+.12*np.sin(6*np.pi*hz*t))


def air_rise(seconds=1.7, seed=4):
    rng=np.random.default_rng(seed)
    t=np.arange(round(seconds*RATE))/RATE
    u=t/seconds
    noise=rng.normal(0,.4,len(t))
    low=np.convolve(noise,np.ones(38)/38,"same")
    air=.26*(low*(1-u)+noise*u*.65)*u**1.4
    air+=.055*np.sin(2*np.pi*(65*t+64*t*t/seconds))*u
    return air*np.minimum(1,(seconds-t)/.035)


def samples(folder):
    folder.mkdir(parents=True,exist_ok=False)
    for name,sound in (("felt-note",felt_note(174.61,2)),("air-rise",air_rise())):
        wav(folder/(name+".wav"),np.column_stack((sound,sound)))
    for idx,phase in enumerate((.20,.45,.72)):
        steam((360,360),(172,259),128,phase).save(folder/f"steam-{idx}.png")
    for frame in (0,4):
        motion_marks((360,160),(210,55),(221,110),-12,frame,100).save(folder/f"marks-{frame}.png")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path)
    samples(parser.parse_args().folder)
