"""Build the original bevelled domino mesh as Wavefront OBJ. Axes are X depth, Y width, Z up."""
import math
from pathlib import Path

HEIGHT, WIDTH, THICKNESS = 1.80, 0.90, 0.28


def make():
    vertices, surfaces = [], []

    def loop(x, margin):
        w, length = WIDTH / 2 - margin, HEIGHT / 2 - margin
        rad = .075 - margin / 2
        pts = []
        for cy, cz, start in ((w-rad,length-rad,0),(-w+rad,length-rad,90),
                              (-w+rad,-length+rad,180),(w-rad,-length+rad,270)):
            for i in range(5):
                angle = math.radians(start + i*22.5)
                pts.append((x, cy+rad*math.cos(angle), HEIGHT/2+cz+rad*math.sin(angle)))
        ids = list(range(len(vertices)+1, len(vertices)+1+len(pts)))
        vertices.extend(pts)
        return ids

    rings = [loop(-THICKNESS,.026), loop(-THICKNESS+.026,0), loop(-.026,0), loop(0,.026)]
    surfaces.extend([("marked", list(reversed(rings[0]))), ("back", rings[-1])])
    for a,b,group in zip(rings, rings[1:], ("bevel","side","bevel")):
        for j in range(len(a)):
            k=(j+1)%len(a)
            surfaces.append((group,[a[j],a[k],b[k],b[j]]))
    def detail(yz, group):
        start=len(vertices)+1
        vertices.extend([(-THICKNESS-.001,y,z) for y,z in yz])
        surfaces.append((group,list(reversed(range(start, start+len(yz))))))
    for y,z in ((-.212,1.53),(0,1.33),(.212,1.13),(0,.45)):
        detail([(y+.071*math.cos(i*math.tau/24),z+.071*math.sin(i*math.tau/24))
                for i in range(24)],"pip")
    detail([(-.365,.89),(.365,.89),(.365,.91),(-.365,.91)],"rule")
    lines=["# Original MTake DaVinci teaching mesh; upright; pivot on the lower forward edge.",
           "mtllib domino.mtl", "o Domino_Three_One"]
    lines.extend("v {:.6f} {:.6f} {:.6f}".format(*v) for v in vertices)
    current=None
    for group,face in surfaces:
        if group != current:
            lines.append("g "+group)
            lines.append("usemtl "+group)
            current=group
        lines.append("f "+" ".join(map(str,face)))
    return "\n".join(lines)+"\n"


if __name__ == "__main__":
    Path(__file__).with_name("domino.obj").write_text(make(),encoding="ascii")
