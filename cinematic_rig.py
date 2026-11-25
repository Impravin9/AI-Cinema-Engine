"""Replace the prototype's center-rotated cylinders with a joint-pivot character rig.

This module runs in the host Python process and patches the embedded Blender script
before Blender starts. The generated rig uses lightweight meshes and explicit joint
pivots, so it remains usable on integrated graphics.
"""
from __future__ import annotations

CHARACTER_BUILD = r'''
# Cinematic character: overlapping smooth forms plus real joint pivots.
# All geometry is parented to joint empties; limbs rotate around shoulders, elbows,
# hips and knees instead of spinning around their own centers.
root = bpy.data.objects.new("HERO_ROOT", None)
s.collection.objects.link(root)
root.empty_display_type = "PLAIN_AXES"
root.empty_display_size = 0.25

def attach(obj, parent, local_location=None):
    obj.parent = parent
    if local_location is not None:
        obj.location = local_location
    return obj

def joint(name, parent, location):
    obj = bpy.data.objects.new(name, None)
    s.collection.objects.link(obj)
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = 0.08
    obj.parent = parent
    obj.location = location
    return obj

def body_ellipsoid(name, parent, location, scale, material):
    obj = uv(name, (0,0,0), scale, material)
    return attach(obj, parent, location)

def limb_segment(name, parent, length, radius, material):
    obj = uv(name, (0,0,0), (radius, radius, length * 0.62), material)
    return attach(obj, parent, (0,0,-length * 0.5))

# Torso has a tapered silhouette, layered tunic, collar and belt.
body_ellipsoid("torso core", root, (0,0,1.27), (.36,.23,.53), shirt)
body_ellipsoid("upper chest", root, (0,-.006,1.52), (.39,.235,.30), shirt)
body_ellipsoid("waist tunic", root, (0,0,.98), (.31,.22,.31), shirt)
body_ellipsoid("leather belt", root, (0,-.004,.96), (.325,.232,.065), wood)
body_ellipsoid("belt clasp", root, (0,-.237,.96), (.055,.025,.055), gold)
body_ellipsoid("neck", root, (0,0,1.82), (.125,.13,.18), skin)
head_joint = joint("head_turn", root, (0,0,1.82))
body_ellipsoid("head", head_joint, (0,-.012,.31), (.315,.275,.405), skin)
body_ellipsoid("hair crown", head_joint, (0,.012,.61), (.325,.285,.19), hair)
body_ellipsoid("rear hair", head_joint, (0,.17,.40), (.29,.15,.29), hair)
for side in (-1,1):
    body_ellipsoid("ear", head_joint, (side*.305,-.005,.32), (.075,.085,.105), skin)
    body_ellipsoid("eye socket", head_joint, (side*.115,-.260,.37), (.083,.033,.062), hair)
    body_ellipsoid("eye white", head_joint, (side*.115,-.287,.375), (.057,.019,.039), white)
    body_ellipsoid("iris", head_joint, (side*.115,-.304,.375), (.022,.012,.027), iris)
    brow = cyl("eyebrow", (side*.055,-.286,2.275), (side*.18,-.278,2.29), .022, hair)
    attach(brow, head_joint, (side*.117,-.282,.462))
body_ellipsoid("nose bridge", head_joint, (0,-.285,.30), (.043,.065,.09), skin)
body_ellipsoid("nose tip", head_joint, (0,-.337,.265), (.052,.045,.042), skin)
mouth = body_ellipsoid("mouth", head_joint, (0,-.281,.165), (.072,.018,.018), hair)

# Shoulder/arm pivots. Upper and lower arms are separate articulated segments.
arm_rigs = []
for side, label in ((-1,"L"),(1,"R")):
    shoulder = joint("shoulder_"+label, root, (side*.39,0,1.57))
    body_ellipsoid("shoulder pad_"+label, shoulder, (0,0,0), (.17,.18,.19), shirt)
    upper = limb_segment("upper_arm_"+label, shoulder, .43, .105, shirt)
    elbow = joint("elbow_"+label, shoulder, (0,0,-.43))
    forearm = limb_segment("forearm_"+label, elbow, .37, .078, skin)
    hand = body_ellipsoid("hand_"+label, elbow, (0,-.012,-.39), (.085,.075,.105), skin)
    arm_rigs.append((shoulder, elbow, side))

# Leg pivots with separate knees, shins and shoes. These produce an actual gait.
leg_rigs = []
for side, label in ((-1,"L"),(1,"R")):
    hip = joint("hip_"+label, root, (side*.17,0,.91))
    thigh = limb_segment("thigh_"+label, hip, .43, .125, pants)
    knee = joint("knee_"+label, hip, (0,0,-.43))
    shin = limb_segment("shin_"+label, knee, .39, .087, pants)
    ankle = joint("ankle_"+label, knee, (0,0,-.39))
    body_ellipsoid("boot_"+label, ankle, (0,-.105,-.02), (.12,.22,.095), hair)
    leg_rigs.append((hip,knee,ankle,side))

# A small shoulder strap and satchel give the silhouette material character.
strap = cyl("diagonal leather strap", (-.27,-.195,1.69), (.22,-.205,1.05), .035, wood)
attach(strap, root)
body_ellipsoid("small satchel", root, (.30,.13,1.02), (.16,.13,.20), wood)

def key_linear(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return
    action = obj.animation_data.action
    try:
        curves = action.fcurves
    except (AttributeError, RuntimeError):
        # Blender 5.x may expose layered actions rather than legacy fcurves.
        # Default Bezier interpolation is still valid; do not fail the render.
        return
    for fc in curves:
        for key in fc.keyframe_points:
            key.interpolation = "LINEAR"

all_rig_objects = [root] + arm_rigs[0][:2] + arm_rigs[1][:2] + leg_rigs[0][:2] + leg_rigs[1][:2]
'''

ANIMATION_LOOP = r'''
# Directed film timeline: joint-based gait, body weight shift, acting and camera beats.
frame = 1
for idx, scn in enumerate(scenes):
    text = str(scn.get("text", ""))
    low = text.lower()
    start = frame
    duration = max(1, int(seconds * fps))
    end = start + duration - 1
    env = str(scn.get("environment", "landscape"))
    for env_name, env_objects in environment_objects.items():
        for env_obj in env_objects:
            visible = (env_name == env) if env_name != "smoke" else any(
                w in low for w in ("smoke", "fire", "burning", "burns", "flames")
            )
            env_obj.hide_render = not visible
            env_obj.keyframe_insert(data_path="hide_render", frame=start)
            env_obj.keyframe_insert(data_path="hide_render", frame=end)

    caption.data.body = text[:105]
    action = str(scn.get("action", "observe"))
    mood = str(scn.get("mood", "determined"))
    shot = str(scn.get("shot_type", "medium"))
    travel = {"walk": .95, "run": 1.65, "fall": .12}.get(action, .18)
    direction = -1 if idx % 2 else 1
    root.rotation_euler = (0, 0, math.radians(90 * direction) if action in ("walk", "run") else 0)
    head_joint.rotation_euler = (0, 0, 0)
    head_joint.keyframe_insert("rotation_euler", frame=start)
    root.location = (-travel * .5 * direction, 0, 0)
    root.keyframe_insert("location", frame=start)
    root.keyframe_insert("rotation_euler", frame=start)

    # Four gait phases per shot. Hip and shoulder swing oppose one another;
    # knees flex during the recovery phase and the torso absorbs the impact.
    moving = action in ("walk", "run")
    stride = 27 if action == "run" else 17
    cycles = 2 if action == "run" else 1
    if moving:
        sample_count = max(4, min(duration, max(12, duration // 2)))
        for step in range(sample_count + 1):
            t = step / sample_count
            f = start + int((end - start) * t)
            phase = t * cycles * 2 * math.pi
            for hip, knee, ankle, side in leg_rigs:
                swing = math.sin(phase + (math.pi if side < 0 else 0))
                recovery = max(0, math.cos(phase + (math.pi if side < 0 else 0)))
                hip.rotation_euler[1] = math.radians(stride) * swing
                knee.rotation_euler[1] = math.radians(22 if action == "run" else 10) * recovery
                ankle.rotation_euler[1] = math.radians(-stride * .24) * swing
                hip.keyframe_insert("rotation_euler", frame=f)
                knee.keyframe_insert("rotation_euler", frame=f)
                ankle.keyframe_insert("rotation_euler", frame=f)
            for shoulder, elbow, side in arm_rigs:
                swing = math.sin(phase + (0 if side < 0 else math.pi))
                shoulder.rotation_euler[1] = math.radians(stride * .72) * swing
                elbow.rotation_euler[1] = math.radians(-18 if action == "run" else -8)
                shoulder.keyframe_insert("rotation_euler", frame=f)
                elbow.keyframe_insert("rotation_euler", frame=f)
            root.location = (-travel*.5*direction + travel*t*direction, 0,
                             (.045 if action == "run" else .018) * abs(math.sin(phase*2)))
            root.rotation_euler[1] = math.radians(-7 if action == "run" else -3)
            root.rotation_euler[2] = math.radians(90 * direction)
            root.keyframe_insert("location", frame=f)
            root.keyframe_insert("rotation_euler", frame=f)
    else:
        # Acting beats: anticipation, reaction, and a held emotional pose.
        head_joint.rotation_euler[2] = math.radians(22 * direction if action == "react" else 0)
        head_joint.rotation_euler[1] = math.radians(7 if mood == "sadness" else -5 if mood == "curiosity" else 0)
        head_joint.keyframe_insert("rotation_euler", frame=start)
        head_joint.rotation_euler[2] *= .35
        head_joint.keyframe_insert("rotation_euler", frame=start + max(1, duration//3))
        head_joint.keyframe_insert("rotation_euler", frame=end)
        lean = {"fear": 9, "sadness": 7, "anger": -8, "curiosity": -4}.get(mood, 0)
        root.rotation_euler[1] = math.radians(lean)
        root.keyframe_insert("rotation_euler", frame=start)
        root.rotation_euler[1] = math.radians(-lean * .35)
        root.keyframe_insert("rotation_euler", frame=start + max(1, duration//3))
        root.rotation_euler[1] = math.radians(lean * .25)
        root.keyframe_insert("rotation_euler", frame=end)
        for shoulder, elbow, side in arm_rigs:
            if action == "speak":
                shoulder.rotation_euler[1] = math.radians(-24 if side < 0 else -12)
                elbow.rotation_euler[1] = math.radians(-32)
            elif mood == "fear":
                shoulder.rotation_euler[1] = math.radians(-28)
                elbow.rotation_euler[1] = math.radians(-42)
            elif mood == "anger":
                shoulder.rotation_euler[1] = math.radians(14)
                elbow.rotation_euler[1] = math.radians(-12)
            shoulder.keyframe_insert("rotation_euler", frame=start)
            elbow.keyframe_insert("rotation_euler", frame=start)
            shoulder.keyframe_insert("rotation_euler", frame=end)
            elbow.keyframe_insert("rotation_euler", frame=end)

    # Mouth movement is a restrained speech beat rather than a scaling sphere gag.
    speaking = action == "speak" or any(w in low for w in ("says", "said", "speaks", "shouts"))
    mouth.scale = (.072,.018,.045 if speaking else .018)
    mouth.keyframe_insert("scale", frame=start)
    mouth.keyframe_insert("scale", frame=end)

    profiles = {
        "wide": ((3.8,-9.5,3.1),35,(0,0,1.2)),
        "medium_wide": ((3.0,-8.0,2.8),40,(0,0,1.35)),
        "medium": ((2.5,-6.8,2.65),50,(0,0,1.4)),
        "medium_close": ((1.2,-5.2,2.45),65,(0,0,1.85)),
        "close_up": ((.6,-4.2,2.35),75,(0,0,2.1)),
    }
    base, lens, target = profiles.get(shot, profiles["medium"])
    cam.data.lens = lens
    base_v = Vector(base)
    target_v = Vector(target)
    move = str(scn.get("camera_move", "slow_pan"))
    if move == "push_in":
        cam.location = base_v + (base_v-target_v)*.10
    elif move == "tracking":
        cam.location = base_v + Vector((-.45*direction,0,0))
    else:
        cam.location = base_v + Vector((.12 if idx%2 else -.12,0,0))
    cam.rotation_euler = (target_v-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.keyframe_insert("location", frame=start)
    cam.keyframe_insert("rotation_euler", frame=start)
    if move == "push_in":
        cam.location = base_v
    elif move == "pull_back":
        cam.location = base_v + (base_v-target_v)*.12
    elif move == "tracking":
        cam.location = base_v + Vector((.45*direction,0,0))
    else:
        cam.location = base_v + Vector((-.12 if idx%2 else .12,0,0))
    cam.rotation_euler = (target_v-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.keyframe_insert("location", frame=end)
    cam.keyframe_insert("rotation_euler", frame=end)
    frame = end + 1

for obj in bpy.data.objects:
    key_linear(obj)
'''

def upgrade_blender_source(source: str) -> str:
    """Patch known renderer sections; fail loudly if the upstream template changed."""
    start = source.find("# Character assembled as separate expressive parts")
    end = source.find("# Stage props, key light and cinematic camera")
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("Cannot locate the character section in Blender source; refusing a partial rig upgrade.")
    source = source[:start] + CHARACTER_BUILD + "\n" + source[end:]
    start = source.find("# Animate all scenes in one continuous film")
    end = source.find("s.frame_start=1; s.frame_end=frame-1;")
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("Cannot locate the animation timeline in Blender source; refusing a partial rig upgrade.")
    source = source[:start] + ANIMATION_LOOP + "\n" + source[end:]
    return source
