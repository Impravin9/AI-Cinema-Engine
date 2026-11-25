"""Replace the prototype's center-rotated cylinders with a joint-pivot character rig.

This module runs in the host Python process and patches the embedded Blender script
before Blender starts. The generated rig uses lightweight meshes and explicit joint
pivots, so it remains usable on integrated graphics.
"""
from __future__ import annotations

CHARACTER_BUILD = r'''
# Stylized feature-animation hero: deliberately designed proportions, clean silhouette,
# expressive face, layered costume and light geometry for fast Eevee rendering.
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
    obj.empty_display_size = 0.07
    obj.parent = parent
    obj.location = location
    return obj

def body_ellipsoid(name, parent, location, scale, material):
    obj = uv(name, (0,0,0), scale, material)
    obj.data.name = name + "_mesh"
    return attach(obj, parent, location)

def limb_segment(name, parent, length, radius, material):
    obj = uv(name, (0,0,0), (radius, radius, length * .66), material)
    return attach(obj, parent, (0,0,-length * .5))

# Head-to-body ratio and compact limbs establish a friendly feature-cartoon silhouette.
body_ellipsoid("rounded tunic", root, (0,0,1.16), (.37,.245,.48), shirt)
body_ellipsoid("chest panel", root, (0,-.018,1.39), (.365,.245,.255), shirt)
body_ellipsoid("waist panel", root, (0,0,.91), (.31,.225,.29), shirt)
body_ellipsoid("collar", root, (0,-.012,1.58), (.20,.235,.105), white)
body_ellipsoid("scarf knot", root, (0,-.245,1.49), (.095,.055,.105), gold)
body_ellipsoid("scarf tail", root, (.10,-.225,1.31), (.065,.035,.20), gold)
body_ellipsoid("belt", root, (0,-.008,.88), (.32,.237,.065), wood)
body_ellipsoid("belt buckle", root, (0,-.247,.88), (.075,.025,.065), gold)
for z in (1.24,1.08):
    body_ellipsoid("costume button", root, (0,-.251,z), (.027,.018,.027), gold)

body_ellipsoid("neck", root, (0,0,1.58), (.13,.13,.18), skin)
head_joint = joint("head_turn", root, (0,0,1.65))
# Oversized rounded head with cheeks and a soft jaw; all features face camera at Y=-.
body_ellipsoid("large cartoon face", head_joint, (0,-.015,.34), (.425,.345,.49), skin)
body_ellipsoid("hair cap", head_joint, (0,.025,.69), (.43,.345,.235), hair)
body_ellipsoid("back hair", head_joint, (0,.205,.40), (.36,.19,.34), hair)
# Sculpted fringe and side locks break the sphere silhouette.
for x,z,ang in ((-.25,.66,-18),(-.10,.72,-8),(.08,.73,8),(.25,.66,18)):
    lock=body_ellipsoid("sculpted fringe", head_joint, (x,-.245,z), (.15,.105,.19), hair)
    lock.rotation_euler[1]=math.radians(ang)
for side in (-1,1):
    body_ellipsoid("ear", head_joint, (side*.405,-.015,.32), (.095,.105,.14), skin)
    body_ellipsoid("ear inner", head_joint, (side*.448,-.105,.32), (.035,.018,.075), gold)
    # Eye whites, irises, pupils and catchlights form a readable expression at a distance.
    eye=body_ellipsoid("eye white", head_joint, (side*.155,-.322,.405), (.112,.045,.132), white)
    pupil=body_ellipsoid("iris", head_joint, (side*.145,-.362,.397), (.061,.028,.080), iris)
    body_ellipsoid("pupil", head_joint, (side*.145,-.386,.397), (.034,.016,.052), hair)
    body_ellipsoid("eye sparkle", head_joint, (side*.125,-.402,.435), (.018,.010,.023), white)
    brow=body_ellipsoid("expressive eyebrow", head_joint, (side*.155,-.327,.565), (.115,.035,.035), hair)
    brow.rotation_euler[1]=math.radians(-8*side)
    if side < 0:
        brow_rigs=[]
    brow_rigs.append(brow)
# Eye rig list is explicit for subtle blinks and gaze acting.
eye_rigs=[]
for side in (-1,1):
    eye_rigs.append(next(o for o in head_joint.children if o.name == "eye white" and o.location.x*side > 0))
# Soft nose, cheek blush and a shaped mouth rather than a floating black dot.
body_ellipsoid("nose", head_joint, (0,-.375,.285), (.075,.075,.095), skin)
for side in (-1,1):
    blush=body_ellipsoid("cheek blush", head_joint, (side*.265,-.304,.235), (.085,.022,.045), gold)
mouth=body_ellipsoid("mouth", head_joint, (0,-.345,.155), (.105,.028,.055), hair)
mouth_open=body_ellipsoid("mouth inner", head_joint, (0,-.372,.153), (.073,.012,.030), hair)
# Teeth add a clean readable smile when speaking.
body_ellipsoid("upper teeth", head_joint, (0,-.388,.173), (.060,.009,.012), white)

# Short rounded arms with shoulder, elbow and wrist pivots; mitten hands and fingers.
arm_rigs=[]
for side,label in ((-1,"L"),(1,"R")):
    shoulder=joint("shoulder_"+label, root, (side*.36,0,1.43))
    body_ellipsoid("rounded sleeve_"+label, shoulder, (0,0,-.06), (.17,.19,.23), shirt)
    upper=limb_segment("upper_arm_"+label, shoulder, .36, .115, shirt)
    elbow=joint("elbow_"+label, shoulder, (0,0,-.36))
    body_ellipsoid("cuff_"+label, elbow, (0,0,-.025), (.105,.11,.075), gold)
    forearm=limb_segment("forearm_"+label, elbow, .31, .09, skin)
    hand=body_ellipsoid("mitten hand_"+label, elbow, (0,-.018,-.34), (.115,.095,.12), skin)
    for finger in range(3):
        body_ellipsoid("finger_"+label, elbow, ((finger-1)*.052,-.075,-.405), (.035,.035,.075), skin)
    arm_rigs.append((shoulder,elbow,side))

# Rounded trousers, articulated knees, cuffed boots and visible toes.
leg_rigs=[]
for side,label in ((-1,"L"),(1,"R")):
    hip=joint("hip_"+label, root, (side*.16,0,.78))
    body_ellipsoid("shorts_"+label, hip, (0,0,-.09), (.17,.19,.23), pants)
    thigh=limb_segment("thigh_"+label, hip, .34, .115, pants)
    knee=joint("knee_"+label, hip, (0,0,-.34))
    shin=limb_segment("shin_"+label, knee, .31, .085, pants)
    ankle=joint("ankle_"+label, knee, (0,0,-.31))
    body_ellipsoid("boot cuff_"+label, ankle, (0,-.015,-.015), (.12,.13,.075), gold)
    body_ellipsoid("rounded boot_"+label, ankle, (0,-.12,-.055), (.145,.235,.105), hair)
    leg_rigs.append((hip,knee,ankle,side))

# Distinctive small backpack and strap complete the character silhouette.
body_ellipsoid("backpack", root, (0,.235,1.18), (.23,.16,.31), wood)
strap=cyl("cross-body strap",(-.28,-.205,1.52),(.25,-.205,.96),.035,wood)
attach(strap,root)

def key_linear(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return
    try:
        for fc in obj.animation_data.action.fcurves:
            for key in fc.keyframe_points:
                key.interpolation="BEZIER"
                key.handle_left_type="AUTO_CLAMPED"
                key.handle_right_type="AUTO_CLAMPED"
    except (AttributeError,RuntimeError):
        pass

all_rig_objects=([root,head_joint,mouth,mouth_open]
                 +[obj for arm in arm_rigs for obj in arm[:2]]
                 +[obj for leg in leg_rigs for obj in leg[:3]]
                 +brow_rigs+eye_rigs)
'''ANIMATION_LOOP = r'''
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
            if env_name == "smoke" and visible:
                base_location = Vector(env_obj["base_location"])
                base_scale = Vector(env_obj["base_scale"])
                env_obj.location = base_location
                env_obj.scale = base_scale
                env_obj.keyframe_insert(data_path="location", frame=start)
                env_obj.keyframe_insert(data_path="scale", frame=start)
                env_obj.location = base_location + Vector((.12, 0, .72 + idx*.025))
                env_obj.scale = base_scale * 1.35
                env_obj.keyframe_insert(data_path="location", frame=end)
                env_obj.keyframe_insert(data_path="scale", frame=end)

    caption.data.body = text[:105]
    action = str(scn.get("action", "observe"))
    mood = str(scn.get("mood", "determined"))
    shot = str(scn.get("shot_type", "medium"))
    travel = {"walk": .95, "run": 1.65, "fall": .12}.get(action, .18)
    direction = -1 if idx % 2 else 1
    root.rotation_euler = (0, 0, math.radians(90 * direction) if action in ("walk", "run") else 0)
    # Reset every articulated joint at each scene boundary to prevent pose leakage.
    for shoulder, elbow, side in arm_rigs:
        shoulder.rotation_euler = (0,0,0)
        elbow.rotation_euler = (0,0,0)
    for hip, knee, ankle, side in leg_rigs:
        hip.rotation_euler = (0,0,0)
        knee.rotation_euler = (0,0,0)
        ankle.rotation_euler = (0,0,0)
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
        if action == "fall":
            root.rotation_euler[0] = 0
            root.keyframe_insert("rotation_euler", frame=start)
            root.rotation_euler[0] = math.radians(76)
            root.keyframe_insert("rotation_euler", frame=end)
        else:
            root.rotation_euler[1] = math.radians(-lean * .35)
            root.keyframe_insert("rotation_euler", frame=start + max(1, duration//3))
            root.rotation_euler[1] = math.radians(lean * .25)
            root.keyframe_insert("rotation_euler", frame=end)
        # Distinct playable poses: combat has alternating strikes, pointing has a held
        # reach, and kneeling/sitting use articulated leg joints instead of a fake fall.
        if action == "kneel":
            root.location.z = -.28
            root.keyframe_insert("location", frame=start)
            for hip, knee, ankle, side in leg_rigs:
                hip.rotation_euler[1] = math.radians(-12)
                knee.rotation_euler[1] = math.radians(88)
                ankle.rotation_euler[1] = math.radians(-18)
                for obj in (hip, knee, ankle):
                    obj.keyframe_insert("rotation_euler", frame=start)
                    obj.keyframe_insert("rotation_euler", frame=end)
        elif action == "sit":
            root.location.z = -.34
            root.keyframe_insert("location", frame=start)
            for hip, knee, ankle, side in leg_rigs:
                hip.rotation_euler[1] = math.radians(78)
                knee.rotation_euler[1] = math.radians(82)
                ankle.rotation_euler[1] = math.radians(-12)
                for obj in (hip, knee, ankle):
                    obj.keyframe_insert("rotation_euler", frame=start)
                    obj.keyframe_insert("rotation_euler", frame=end)
        elif action == "fight":
            for shoulder, elbow, side in arm_rigs:
                shoulder.rotation_euler[1] = math.radians(-18)
                elbow.rotation_euler[1] = math.radians(-48)
                shoulder.keyframe_insert("rotation_euler", frame=start)
                elbow.keyframe_insert("rotation_euler", frame=start)
                shoulder.rotation_euler[1] = math.radians(48 if side < 0 else -18)
                elbow.rotation_euler[1] = math.radians(-12)
                shoulder.keyframe_insert("rotation_euler", frame=start + max(1, duration//3))
                elbow.keyframe_insert("rotation_euler", frame=start + max(1, duration//3))
                shoulder.rotation_euler[1] = math.radians(-18 if side < 0 else 48)
                elbow.rotation_euler[1] = math.radians(-12)
                shoulder.keyframe_insert("rotation_euler", frame=start + max(2, 2*duration//3))
                elbow.keyframe_insert("rotation_euler", frame=start + max(2, 2*duration//3))
                shoulder.keyframe_insert("rotation_euler", frame=end)
                elbow.keyframe_insert("rotation_euler", frame=end)
            root.rotation_euler[1] = math.radians(-12)
            root.keyframe_insert("rotation_euler", frame=start)
            root.rotation_euler[1] = math.radians(12)
            root.keyframe_insert("rotation_euler", frame=start + max(1, duration//2))
            root.rotation_euler[1] = 0
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
            elif action == "point":
                shoulder.rotation_euler[1] = math.radians(-62 if side > 0 else 8)
                elbow.rotation_euler[1] = math.radians(-8 if side > 0 else -20)
            elif action == "fall":
                shoulder.rotation_euler[1] = math.radians(-38 if side < 0 else 38)
                elbow.rotation_euler[1] = math.radians(-24)
            shoulder.keyframe_insert("rotation_euler", frame=start)
            elbow.keyframe_insert("rotation_euler", frame=start)
            shoulder.keyframe_insert("rotation_euler", frame=end)
            elbow.keyframe_insert("rotation_euler", frame=end)

    # Facial performance: brows, mouth shape and eye openness track the emotional beat.
    brow_tilt = {"anger": -18, "fear": 14, "sadness": 12, "curiosity": -10, "joy": 7}.get(mood, 0)
    for brow in brow_rigs:
        brow.rotation_euler[1] = math.radians(brow_tilt if brow.location.x > 0 else -brow_tilt)
        brow.keyframe_insert("rotation_euler", frame=start)
        brow.keyframe_insert("rotation_euler", frame=end)
    for eye in eye_rigs:
        eye.scale.z = .095 if mood == "anger" else (.15 if mood == "fear" else .132)
        eye.keyframe_insert("scale", frame=start)
        eye.keyframe_insert("scale", frame=end)
    mouth.scale = (.105,.028,.068 if mood == "joy" else .045 if action == "speak" else .028)
    mouth.keyframe_insert("scale", frame=start)
    mouth.keyframe_insert("scale", frame=end)
    mouth_open.scale = (.073,.012,.045 if action == "speak" else .018)
    mouth_open.keyframe_insert("scale", frame=start)
    mouth_open.keyframe_insert("scale", frame=end)

    # Jaw opening is a separate shape, preserving the designed smile silhouette.
    speaking = action == "speak" or any(w in low for w in ("says", "said", "speaks", "shouts"))
    mouth_open.scale = (.073,.012,.045 if speaking else .018)
    mouth_open.keyframe_insert("scale", frame=start)
    mouth_open.keyframe_insert("scale", frame=end)

    profiles = {
        "wide": ((3.8,-9.5,3.1),35,(0,0,1.2)),
        "medium_wide": ((3.0,-8.0,2.8),40,(0,0,1.35)),
        "medium": ((2.5,-6.8,2.65),50,(0,0,1.4)),
        "medium_close": ((1.2,-5.2,2.45),65,(0,0,1.85)),
        "close_up": ((.6,-4.2,2.35),75,(0,0,2.1)),
    }
    base, lens, target = profiles.get(shot, profiles["medium"])
    cam.data.lens = lens
    cam.data.keyframe_insert(data_path="lens", frame=start)
    cam.data.keyframe_insert(data_path="lens", frame=end)
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
