#!/usr/bin/env python3
"""Offline procedural 3D animation renderer. All visuals are generated locally in Blender."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile, re
from pathlib import Path

def split_script(text):
    parts = [x.strip() for x in re.split(r'(?<=[.!?])\s+', text) if x.strip()]
    if not parts:
        parts = [text.strip()]
    return [{"text": p, "visual": "cinematic_character", "mood": "determined"} for p in parts]

BLENDER_SOURCE = r'''
import bpy, sys, json, math, os
from mathutils import Vector
args = sys.argv[sys.argv.index("--")+1:]
plan_path, output, fps, seconds = args[0], args[1], int(args[2]), float(args[3])
plan=json.load(open(plan_path,encoding="utf-8"))
scenes=plan.get("scenes") or [{"text":plan.get("title","A cinematic moment")}]
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene
# Blender renamed/removed Eevee engine identifiers across major versions.
engine_ids = {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
if "BLENDER_EEVEE_NEXT" in engine_ids:
    s.render.engine = "BLENDER_EEVEE_NEXT"
elif "BLENDER_EEVEE" in engine_ids:
    s.render.engine = "BLENDER_EEVEE"
else:
    raise RuntimeError("No Eevee render engine is available in this Blender build. Available engines: " + ", ".join(sorted(engine_ids)))
s.render.resolution_x=1280; s.render.resolution_y=720; s.render.resolution_percentage=100
s.render.fps=fps
s.render.image_settings.file_format="FFMPEG"
s.render.ffmpeg.format="MPEG4"; s.render.ffmpeg.codec="H264"; s.render.ffmpeg.constant_rate_factor="MEDIUM"
s.render.filepath=output
s.world.color=(0.025,0.025,0.025)
s.view_settings.view_transform="AgX"
def mat(name,color,metal=0,rough=.55):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get("Principled BSDF"); p.inputs["Base Color"].default_value=(*color,1); p.inputs["Metallic"].default_value=metal; p.inputs["Roughness"].default_value=rough
 return m
skin=mat("warm natural skin",(0.56,.31,.19)); shirt=mat("deep teal fabric",(.025,.20,.23)); pants=mat("charcoal trousers",(.055,.075,.095)); hair=mat("dark hair",(.035,.022,.018)); white=mat("eye whites",(.82,.82,.76)); iris=mat("dark irises",(.06,.035,.02)); gold=mat("warm practical light",(.8,.39,.09),.2)
def uv(name,loc,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(material); bpy.ops.object.shade_smooth(); return o
def cyl(name,a,b,r,material):
 mid=(Vector(a)+Vector(b))/2; d=Vector(b)-Vector(a)
 bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=d.length, location=mid)
 o=bpy.context.object; o.name=name; o.rotation_mode="QUATERNION"; o.rotation_quaternion=d.to_track_quat("Z","Y"); o.data.materials.append(material); bpy.ops.object.shade_smooth(); bevel=o.modifiers.new("soft edges","BEVEL"); bevel.width=.06; bevel.segments=3; o.modifiers.new("weighted normals","WEIGHTED_NORMAL"); return o
# Ground and layered atmospheric backdrop
floor_mat=mat("matte stage",(.035,.055,.07))
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.08)); bpy.context.object.data.materials.append(floor_mat)
for x in (-5,-3,3,5):
 bpy.ops.mesh.primitive_cube_add(size=1, location=(x,2,1.1)); o=bpy.context.object; o.scale=(1.1,.6,1.2+(abs(x)%2)*.5); o.data.materials.append(mat("architectural shadow "+str(x),(.045+.01*abs(x),.07,.09)))
# Character assembled as separate expressive parts; keyframes animate posture, gaze and gestures.
root=bpy.data.objects.new("CHARACTER_ROOT",None); s.collection.objects.link(root)
def part(o):
 o.parent=root; return o
torso=part(uv("torso",(0,0,1.22),(.39,.24,.57),shirt))
neck=part(uv("neck",(0,0,1.83),(.13,.13,.18),skin))
head=part(uv("face",(0,0,2.16),(.34,.29,.43),skin))
part(uv("hair cap",(0,.015,2.48),(.35,.30,.20),hair))
# ears
for x in (-.34,.34): part(uv("ear",(x,0,2.17),(.075,.09,.12),skin))
# Eyes, eyelids and brows face camera at y=-1
for x in (-.13,.13):
 part(uv("eye white",(x,-.265,2.22),(.075,.035,.052),white))
 part(uv("iris",(x,-.299,2.22),(.027,.016,.032),iris))
 brow=part(cyl("expressive brow",(x-.07,-.275,2.32),(x+.07,-.275,2.34),.025,hair))
# Nose and mouth; mouth shape is changed per shot by scale/keyframes
part(uv("nose",(0,-.30,2.13),(.055,.07,.10),skin))
mouth=part(uv("mouth",(0,-.277,2.00),(.105,.025,.025),hair))
# arms and legs as segmented articulated-looking forms
limbs=[]
for side in (-1,1):
 shoulder=part(uv("shoulder",(side*.40,0,1.55),(.18,.19,.20),shirt))
 upper=part(cyl("upper arm",(side*.42,0,1.48),(side*.53,0,1.05),.105,shirt))
 fore=part(cyl("forearm",(side*.53,0,1.05),(side*.48,-.04,.70),.085,skin))
 hand=part(uv("hand",(side*.48,-.04,.67),(.09,.075,.11),skin))
 thigh=part(cyl("thigh",(side*.16,0,.82),(side*.18,0,.42),.13,pants))
 shin=part(cyl("shin",(side*.18,0,.42),(side*.18,-.03,.08),.095,pants))
 foot=part(uv("shoe",(side*.18,-.12,.06),(.14,.25,.08),hair))
 limbs += [upper,fore,thigh,shin]
# Stage props, key light and cinematic camera
def area(name,loc,power,color,size,target):
 bpy.ops.object.light_add(type="AREA", location=loc); l=bpy.context.object; l.name=name; l.data.energy=power; l.data.color=color; l.data.shape="DISK"; l.data.size=size; l.rotation_euler=(Vector(target)-l.location).to_track_quat("-Z","Y").to_euler()
area("warm key",(-3,-4,6),950,(1,.72,.48),5,(0,0,1.4))
area("cool fill",(4,-2,3),600,(.35,.58,1),4,(0,0,1.4))
area("rim",(0,3,4),1100,(1,.35,.12),3,(0,0,1.5))
bpy.ops.object.camera_add(location=(3.2,-7.8,2.9)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,1.35))-cam.location).to_track_quat("-Z","Y").to_euler(); cam.data.lens=48; s.camera=cam
# A restrained title-card-free scene: no external textures, images, fonts or footage.
caption_curve=bpy.data.curves.new("scene caption","FONT"); caption_curve.body=""; caption_curve.size=.25
caption=bpy.data.objects.new("caption",caption_curve); s.collection.objects.link(caption); caption.location=(-2.3,-.2,.15); caption.rotation_euler=(math.radians(90),0,0); caption.data.materials.append(mat("caption ivory",(.9,.78,.54)))
# Animate all scenes in one continuous film; character acts are varied by semantic cues.
frame=1
for idx,scn in enumerate(scenes):
 text=str(scn.get("text","")); low=text.lower()
 start=frame; end=frame+max(1,int(seconds*fps))-1
 caption.data.body=text[:105]
 # Character moves through a simple motivated action: approach, turn, react, then settle.
 root.location=(0,0,0); root.rotation_euler=(0,0,0)
 root.keyframe_insert("location",frame=start); root.keyframe_insert("rotation_euler",frame=start)
 root.location=(.20 if idx%2==0 else -.20,0,0); root.rotation_euler[2]=math.radians(-8 if any(w in low for w in ("fear","afraid","attack","danger")) else 8)
 root.keyframe_insert("location",frame=end); root.keyframe_insert("rotation_euler",frame=end)
 # Natural arm gesture and readable emotional change.
 for j,obj in enumerate(limbs[:2]):
  obj.keyframe_insert("rotation_euler",frame=start)
  obj.rotation_euler[1]=math.radians((-18 if j==0 else 18) if any(w in low for w in ("said","speak","speech","ordered","believe","promise")) else (8 if j==0 else -8))
  obj.keyframe_insert("rotation_euler",frame=start+int((end-start)*.45))
  obj.rotation_euler[1]=0; obj.keyframe_insert("rotation_euler",frame=end)
 # Mouth opens subtly for speech; brows/eyes are intentionally understated.
 mouth.scale=(.105,.025,.045 if any(w in low for w in ("said","speak","speech","shout")) else .018); mouth.keyframe_insert("scale",frame=start); mouth.keyframe_insert("scale",frame=end)
 cam.location=(3.2 if idx%3==0 else 2.7,-7.8,2.9 if idx%2==0 else 2.65)
 cam.rotation_euler=(Vector((0,0,1.35))-cam.location).to_track_quat("-Z","Y").to_euler(); cam.keyframe_insert("location",frame=start); cam.keyframe_insert("rotation_euler",frame=start)
 frame=end+1
s.frame_start=1; s.frame_end=frame-1; s.render.filepath=output
s.render.image_settings.color_mode="RGB"
bpy.ops.wm.save_as_mainfile(filepath=output+".blend")
bpy.ops.render.render(animation=True)
'''

def main():
    p=argparse.ArgumentParser(description="Fully local procedural 3D animation renderer (no image websites or online assets).")
    p.add_argument("script"); p.add_argument("out"); p.add_argument("--plan"); p.add_argument("--blender")
    p.add_argument("--fps",type=int,default=24); p.add_argument("--seconds",type=float,default=6.0); p.add_argument("--silent",action="store_true")
    a=p.parse_args()
    source=Path(a.script).read_text(encoding="utf-8")
    if a.plan:
        plan=json.loads(Path(a.plan).read_text(encoding="utf-8"))
        if not isinstance(plan.get("scenes"),list) or not plan["scenes"]: raise ValueError("Plan must contain a non-empty scenes array.")
    else:
        plan={"title":Path(a.script).stem,"scenes":split_script(source)}
    if not plan["scenes"]: raise ValueError("No scenes found in script.")
    blender=a.blender or os.environ.get("BLENDER_EXE") or shutil.which("blender")
    if not blender: raise RuntimeError("Blender was not found. Install the free Blender desktop application and add blender.exe to PATH, or set BLENDER_EXE.")
    out=Path(a.out).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ai_cinema_animation_") as td:
        plan_path=Path(td)/"plan.json"; py_path=Path(td)/"render_scene.py"
        plan_path.write_text(json.dumps(plan,ensure_ascii=False),encoding="utf-8"); py_path.write_text(BLENDER_SOURCE,encoding="utf-8")
        cmd=[blender,"-b","-t","4","--python",str(py_path),"--",str(plan_path),str(out),str(max(12,min(60,a.fps))),str(max(2.0,min(20.0,a.seconds)))]
        print("[animation] Backend: local Blender procedural 3D",flush=True)
        print("[animation] Visual source: generated geometry/materials/lighting only; no external image or footage requests.",flush=True)
        print(f"[animation] Scenes: {len(plan['scenes'])}; target: {out}",flush=True)
        result=subprocess.run(cmd)
        if result.returncode: return result.returncode
    if not out.is_file(): raise RuntimeError("Blender finished without creating the requested MP4.")
    print(f"[animation] Render complete: {out}",flush=True)
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"[animation] ERROR: {exc}",file=sys.stderr); raise SystemExit(2)
