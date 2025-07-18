import bpy


current_scene_name = bpy.context.scene.name
current_viewlayer_name = bpy.context.window.view_layer.name
current_world_name = bpy.context.scene.world.name
current_engine = bpy.context.scene.render.engine

           # ---------- SET OVERRIDE CLAY MAT ----------
override_clay_mat = bpy.data.materials.get('override_clay_NPR')

if override_clay_mat is None:
    # create material and assign
    override_clay_mat =  bpy.data.materials.new(name="override_clay_NPR")
    override_clay_mat.use_nodes = True         
           # ---------- MANAGE NODES OF SHADER EDITOR ----------
    # Get node tree from the material
    override_clay_nodes = override_clay_mat.node_tree.nodes

    # Get Vertex Color Node, create it if it does not exist in the current node tree
    bsdf_diffuse_node = override_clay_nodes.new(type = "ShaderNodeBsdfDiffuse")
    bsdf_diffuse_node.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
            
    from mathutils import Vector
    bsdf_diffuse_node.location = Vector((-200.0, 0.0))

    # Link bsdf output to shader output        
    link = override_clay_mat.node_tree.links.new(bsdf_diffuse_node.outputs[0], override_clay_mat.node_tree.nodes.get("Material Output").inputs[0])        
    override_clay_nodes.remove( override_clay_nodes['Principled BSDF'] )
else: 
    pass
# Switch to the Cycles render engine to apply the material override
bpy.context.scene.render.engine = 'CYCLES'
bpy.data.scenes[current_scene_name].view_layers[current_viewlayer_name].material_override = bpy.data.materials['override_clay_NPR']


           # ---------- CHANGE TO CURRENT ENGINE ----------

bpy.context.scene.render.engine = current_engine

           # ---------- SET LAMPS SHOW/HIDE ----------


#バーチャルライトはベーキングに役立たないが、結果に影響を与えないから手放していい。
# Virtual lights is needless for baking light,but left it for convenience
must_include = [
'Key Light (Background) ',
'Key Light (Character) ',
'Key Light (Extra) ',
'Virtual Point Light',
'Virtual Spot Light',
'Virtual Sun Light',
]


lights = [o for o in bpy.context.scene.objects if o.type == 'LIGHT']

for light in lights:
    
    if light.name in must_include :
        light.hide_render = False
        light.hide_viewport = False
    else:
        light.hide_render = True
        light.hide_viewport = True
           
           
           
           # ---------- SET WORLD ----------
if 'World_NPR' in bpy.data.worlds:
    bpy.context.scene.world = bpy.data.worlds['World_NPR']

else:
    # create a new world
    world_NPR = bpy.data.worlds.new("World_NPR")
    bpy.context.scene.world = world_NPR
    
bpy.context.scene.world.use_fake_user = True

           # ---------- 次はベーキングに関するマニュアル設定が必要から、ここで止めていい ----------