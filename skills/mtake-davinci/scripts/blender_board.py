"""Run inside Blender: blender -b -P blender_board.py -- source.obj fresh-directory"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def build(source, dest):
    if source.suffix.lower() not in (".obj", ".glb", ".gltf"):
        raise ValueError("Supply an OBJ, GLB or glTF mesh.")
    dest.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if source.suffix.lower() == ".obj":
        bpy.ops.wm.obj_import(filepath=str(source), forward_axis="Y", up_axis="Z")
    else:
        bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type=="MESH"]
    if not meshes:
        raise ValueError("The source did not import any mesh geometry.")
    scene=bpy.context.scene
    corners=[obj.matrix_world @ Vector(pt) for obj in meshes for pt in obj.bound_box]
    centre=sum(corners, Vector((0,0,0)))/len(corners)
    camera=bpy.data.objects.new("Review camera",bpy.data.cameras.new("Orthographic"))
    scene.collection.objects.link(camera)
    direction=Vector((-4,-6,3.5)).normalized()
    radius=max((pt-centre).length for pt in corners)
    camera.location=centre+direction*max(4*radius,1)
    camera.rotation_euler=(-direction).to_track_quat("-Z","Y").to_euler()
    camera.data.type="ORTHO"
    scene.camera=camera
    scene.render.resolution_x,scene.render.resolution_y=540,960
    scene.render.resolution_percentage=100
    bpy.context.view_layer.update()
    inverse=camera.matrix_world.inverted()
    projected=[inverse @ pt for pt in corners]
    # In portrait Blender's orthographic scale covers the longer (vertical) dimension.
    camera.data.ortho_scale=max(max(abs(p.y) for p in projected)*2,
                                max(abs(p.x) for p in projected)*2*960/540)*1.18
    camera.data.clip_start=max(radius/10000,0.0001)
    camera.data.clip_end=max(12*radius,10)
    scene.render.engine="BLENDER_WORKBENCH"
    scene.display.render_aa="8"
    shade=scene.display.shading
    shade.light="STUDIO"
    shade.background_type="WORLD"
    world=bpy.data.worlds.new("Charcoal background")
    scene.world=world
    world.color=(.012,.014,.016)
    scene.view_settings.view_transform="Standard"
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    def write(name):
        scene.render.filepath=str(dest / (name+".png"))
        bpy.ops.render.render(write_still=True)
    shade.color_type="SINGLE"
    shade.single_color=(.48,.48,.48)
    write("neutral")
    shade.color_type="MATERIAL"
    values={m.name:tuple(m.diffuse_color) for m in bpy.data.materials}
    base=bpy.data.materials.new("Base charcoal")
    base.diffuse_color=(.079,.070,.063,1)
    for m in bpy.data.materials:
        if m==base:
            continue
        rgb=values[m.name][:3]
        luma=sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722)))
        v=.034+.25*max(0.,min(1.,luma))**1.65
        m.diffuse_color=(v,v*.87,v*.73,1)
    for obj in meshes:
        if not obj.data.materials:
            obj.data.materials.append(base)
    shade.show_object_outline=True
    shade.object_outline_color=(.56,.48,.38)
    shade.show_cavity=True
    shade.cavity_type="BOTH"
    shade.curvature_ridge_factor=1.35
    shade.curvature_valley_factor=1.15
    write("on")
    for obj in meshes:
        obj.hide_render=True
    write("off")
    for obj in meshes:
        obj.hide_render=False
    scene.render.filepath="//on.png"
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/"subject.blend"))


if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:
        raise SystemExit("Expected: -- input-mesh new-output-folder")
    build(Path(args[0]).resolve(),Path(args[1]).resolve())
