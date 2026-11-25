"""High-detail, low-cost procedural environment kits for Blender scenes.

The kits are generated locally, use deterministic geometry/materials, and are
switched per scene by the renderer. They deliberately avoid expensive simulations.
"""

ENVIRONMENT_BUILD = r'''
# CINEMATIC ENVIRONMENTS — layered, reusable, low-poly art direction.
# The terrain material uses procedural noise so the ground is not a flat colour.
ground_mat = mat("earth | layered soil", (.105,.078,.048), 0, .92)
ground_nodes = ground_mat.node_tree
ground_bsdf = ground_nodes.nodes.get("Principled BSDF")
noise = ground_nodes.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 3.8
noise.inputs["Detail"].default_value = 4.0
ramp = ground_nodes.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = .22
ramp.color_ramp.elements[0].color = (.025,.035,.022,1)
ramp.color_ramp.elements[1].position = .78
ramp.color_ramp.elements[1].color = (.24,.17,.09,1)
bump = ground_nodes.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = .22
bump.inputs["Distance"].default_value = .08
ground_nodes.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
ground_nodes.links.new(ramp.outputs["Color"], ground_bsdf.inputs["Base Color"])
ground_nodes.links.new(noise.outputs["Fac"], bump.inputs["Height"])
ground_nodes.links.new(bump.outputs["Normal"], ground_bsdf.inputs["Normal"])
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.10))
terrain = bpy.context.object
terrain.name = "continuous terrain"
terrain.data.materials.append(ground_mat)

wood = mat("aged timber", (.16,.075,.032), 0, .84)
bark = mat("tree bark", (.105,.047,.021), 0, .9)
leaf_dark = mat("deep foliage", (.025,.105,.043), 0, .94)
leaf_mid = mat("foliage", (.055,.19,.065), 0, .9)
leaf_light = mat("sunlit leaves", (.16,.28,.075), 0, .86)
plaster = mat("sun baked plaster", (.48,.32,.18), 0, .9)
thatch = mat("weathered thatch", (.20,.105,.045), 0, .96)
stone = mat("rough stone", (.20,.22,.21), 0, .95)
charcoal = mat("burnt timber", (.035,.028,.024), 0, .95)
water_mat = mat("deep river water", (.018,.095,.14), .12, .2)
metal = mat("aged iron", (.075,.085,.08), .65, .42)
interior_wall = mat("interior lime plaster", (.30,.24,.17), 0, .95)
interior_wood = mat("interior dark timber", (.075,.035,.018), 0, .88)

environment_objects = {
    "landscape": [], "forest": [], "village": [], "battlefield": [],
    "interior": [], "water": [], "mountain": [], "smoke": []
}

def env_add(group, obj):
    environment_objects[group].append(obj)
    return obj

def env_cube(group, name, loc, scale, material, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("worn softened edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new("weighted corner normals", "WEIGHTED_NORMAL")
    return env_add(group, obj)

def env_tree(x, y, scale=1.0, seed=0):
    trunk = cyl("tree trunk", (x,y,0), (x,y,2.0*scale), .17*scale, bark)
    env_add("forest", trunk)
    for branch in (-1,1):
        b = cyl("tree branch", (x,y,1.05*scale),
                (x+branch*.48*scale,y,1.72*scale), .075*scale, bark)
        env_add("forest", b)
    for j, (dx,dy,dz,r) in enumerate(((0,0,2.15,.85),(-.48,0,1.95,.58),(.48,.02,2.0,.62),(0,.38,2.45,.55))):
        crown = uv("layered tree crown", (x+dx*scale,y+dy*scale,dz*scale),
                   (r*scale,r*.78*scale,r*1.08*scale),
                   (leaf_dark,leaf_mid,leaf_light)[(j+seed)%3])
        env_add("forest", crown)

# Landscape: distant rolling ridges, scrub, and a winding dirt track.
for i, x in enumerate((-8,-5,-2,2,5,8)):
    bpy.ops.mesh.primitive_cone_add(vertices=9, radius1=3.1, radius2=.05,
                                    depth=2.8+(i%3)*.7, location=(x,7,1.0))
    ridge = bpy.context.object
    ridge.name = "distant rolling ridge"
    ridge.data.materials.append(mat("ridge earth "+str(i),(.055+.008*i,.075+.006*i,.065),0,1))
    env_add("landscape", ridge)
for x in (-6,-3,3,6):
    bush = uv("distant scrub", (x,3,.42), (1.1,.55,.55), leaf_dark)
    env_add("landscape", bush)

# Forest: varied tree scale, undergrowth, exposed roots and a readable path.
for i, (x,y,sc) in enumerate(((-4.8,2.6,1.2),(-3.5,4,.85),(-2.6,2.9,1.05),(2.8,3.2,1.0),(4.3,4.2,1.2),(5.1,2.7,.9))):
    env_tree(x,y,sc,i)
for x in (-4.2,-3.0,3.1,4.4):
    for j in range(3):
        fern = uv("forest undergrowth", (x+(j-1)*.24,1.0+j*.35,.18),
                  (.34,.22,.22), leaf_mid)
        env_add("forest", fern)
path_mat = mat("forest earth path",(.19,.13,.075),0,.98)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0,-.2,-.035))
path = bpy.context.object
path.name = "worn forest path"
path.dimensions = (2.8,18,1)
path.rotation_euler[2] = math.radians(8)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
path.data.materials.append(path_mat)
env_add("forest", path)

# Village: individual huts with timber framing, doors, windows, roofs and fences.
for i, x in enumerate((-4.1,0,4.1)):
    env_cube("village","mud plaster hut",(x,3,.92),(2.25,1.65,1.8),plaster,.06)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.55, radius2=.02,
        depth=1.18, location=(x,3,2.34), rotation=(0,0,math.radians(45)))
    roof_obj=bpy.context.object
    roof_obj.name="thatch roof"
    roof_obj.data.materials.append(thatch)
    env_add("village",roof_obj)
    env_cube("village","wooden doorway",(x,2.10,.70),(.48,.09,1.25),wood,.025)
    env_cube("village","door crossbar",(x,2.045,.78),(.40,.035,.07),metal,.01)
    for side in (-1,1):
        env_cube("village","window recess",(x+side*.67,2.10,1.16),(.36,.08,.42),wood,.02)
        env_cube("village","window shutter",(x+side*.67,2.045,1.16),(.26,.035,.34),thatch,.015)
    for side in (-1,1):
        beam=cyl("hut timber post",(x+side*.98,2.12,.08),(x+side*.98,2.12,1.78),.055,wood)
        env_add("village",beam)
# Fence rails and posts create foreground depth.
for x in (-5.2,-4.3,-3.4,3.4,4.3,5.2):
    post=cyl("village fence post",(x,.3,.02),(x,.3,.92),.065,wood)
    env_add("village",post)
for z in (.35,.68):
    rail=cyl("village fence rail",(-5.3,.3,z),( -3.3,.3,z),.045,wood)
    env_add("village",rail)
    rail=cyl("village fence rail",(3.3,.3,z),(5.3,.3,z),.045,wood)
    env_add("village",rail)

# Battlefield: broken stakes, irregular rubble, crater lips and charred beams.
for i, (x,y,sz) in enumerate(((-4,2,.55),(-2.5,3,.8),(2.4,2.5,.62),(4.1,3.4,.9),(0,4,.48))):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=sz, location=(x,y,sz*.55))
    rock=bpy.context.object
    rock.name="battlefield rubble"
    rock.scale=(1.4,.8,.72)
    rock.data.materials.append(stone)
    env_add("battlefield",rock)
for x in (-3.7,-1.8,2.0,3.8):
    stake=cyl("broken battlefield stake",(x,1.7,.05),(x+.35,1.85,1.15),.075,charcoal)
    env_add("battlefield",stake)
for x in (-2.7,2.8):
    beam=cyl("burnt fallen beam",(x-1,1.4,.18),(x+1,2.0,.32),.12,charcoal)
    env_add("battlefield",beam)

# Interior: enclosed room, timber beams, doorway, window, table and practical lamp.
env_cube("interior","interior floor",(0,1,-.01),(9,8,.18),wood,.02)
env_cube("interior","back wall",(0,4,2.1),(9,.22,4.2),interior_wall,.02)
env_cube("interior","left wall",(-4.5,1,2.1),(.22,6,4.2),interior_wall,.02)
env_cube("interior","right wall",(4.5,1,2.1),(.22,6,4.2),interior_wall,.02)
for x in (-3.8,-1.3,1.3,3.8):
    beam=cyl("interior ceiling beam",(x,-2,3.85),(x,4,3.85),.09,interior_wood)
    env_add("interior",beam)
env_cube("interior","interior table",(0,.8,1.0),(2.2,1.1,.16),wood,.04)
for x in (-.9,.9):
    env_cube("interior","table leg",(x,.8,.5),(.13,.13,.95),interior_wood,.02)
env_cube("interior","window opening",(2.7,3.86,2.2),(1.15,.06,1.35),interior_wood,.02)
env_cube("interior","window light",(2.7,3.81,2.2),(.85,.025,1.05),mat("cool window light",(.19,.31,.39),0,.5),.01)
bpy.ops.object.light_add(type="POINT", location=(-1,1.3,2.3))
lamp=bpy.context.object
lamp.name="interior practical lamp"
lamp.data.energy=95
lamp.data.color=(1.0,.48,.19)
lamp.data.shadow_soft_size=.65
env_add("interior",lamp)

# Water: reflective channel, irregular bank stones and reeds.
bpy.ops.mesh.primitive_plane_add(size=1, location=(0,3,-.025))
river=bpy.context.object
river.name="river channel"
river.dimensions=(16,9,1)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
river.data.materials.append(water_mat)
env_add("water",river)
for x in (-6,-4,-2,2,4,6):
    rock=uv("river bank stone",(x,-1.25,.12),(.48,.34,.22),stone)
    env_add("water",rock)
    reed=cyl("river reed",(x+.35,-.7,.05),(x+.48,-.72,.95),.025,leaf_mid)
    env_add("water",reed)

# Mountains: layered angular peaks with snow caps and foreground scree.
snow=mat("mountain snow",(.68,.72,.70),0,.8)
for i,x in enumerate((-5,-1.8,1.8,5)):
    height=4.8+(i%2)*1.5
    bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=2.8,radius2=.05,depth=height,
                                    location=(x,5,height*.5-.05))
    peak=bpy.context.object
    peak.name="mountain peak"
    peak.data.materials.append(stone)
    env_add("mountain",peak)
    bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=.95,radius2=.02,depth=1.2,
                                    location=(x,5,height*.84))
    cap=bpy.context.object
    cap.name="mountain snow cap"
    cap.data.materials.append(snow)
    env_add("mountain",cap)
for x in (-3,-1,1,3):
    scree=uv("mountain scree",(x,-.1,.18),(.65,.5,.24),stone)
    env_add("mountain",scree)

# Smoke bank is made of overlapping soft forms; animation is applied per scene.
smoke_mat = mat("smoke volume tint",(.20,.22,.23),0,1)
for i in range(7):
    puff=uv("smoke plume",(2.5+i*.11,2.0,1.0+i*.42),
            (.42+i*.045,.38+i*.045,.48+i*.07),smoke_mat)
    env_add("smoke",puff)

# Atmospheric world fill plus a broad sun key: useful even in wide establishing shots.
if s.world is None:
    s.world = bpy.data.worlds.new("cinematic atmosphere")
s.world.use_nodes = True
world_bg = s.world.node_tree.nodes.get("Background")
if world_bg:
    world_bg.inputs["Color"].default_value = (.075,.105,.15,1)
    world_bg.inputs["Strength"].default_value = .32
bpy.ops.object.light_add(type="SUN", location=(0,0,8))
sun = bpy.context.object
sun.name = "cinematic sun"
sun.data.energy = 1.35
sun.data.angle = math.radians(18)
sun.rotation_euler = (math.radians(24), math.radians(-18), math.radians(-28))

# Default to the landscape kit, not an empty black stage.
for group, objects in environment_objects.items():
    for obj in objects:
        obj.hide_render = (group != "landscape")
'''

def upgrade_environment_source(source: str) -> str:
    """Replace the empty stage and sparse props with complete environment kits."""
    start = source.find("# Ground and layered atmospheric backdrop")
    end = source.find("# Character assembled as separate expressive parts")
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("Cannot locate environment section; refusing partial environment replacement.")
    return source[:start] + ENVIRONMENT_BUILD + "\n" + source[end:]
