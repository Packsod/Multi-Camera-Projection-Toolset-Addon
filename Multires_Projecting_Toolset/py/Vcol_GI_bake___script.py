import bpy

# Start the undo block
bpy.ops.ed.undo_push(message="Start of script operation")

# Check if there are any selected mesh objects
selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']

if not selected_meshes:
    bpy.context.window_manager.popup_menu(
        lambda self, context: self.layout.label(text="You need to select at least one mesh to bake."),
        title="Error",
        icon='ERROR'
    )
else:
    current_scene_name = bpy.context.scene.name
    current_viewlayer_name = bpy.context.window.view_layer.name
    current_world_name = bpy.context.scene.world.name

    # ---------- SET OVERRIDE CLAY MAT ----------
    override_clay_mat = bpy.data.materials.get('override_clay_GI')

    if override_clay_mat is None:
        # create material and assign
        override_clay_mat =  bpy.data.materials.new(name="override_clay_GI")
        override_clay_mat.use_nodes = True         
        # ---------- MANAGE NODES OF SHADER EDITOR ----------
        # Get node tree from the material
        override_clay_nodes = override_clay_mat.node_tree.nodes

        # Get Vertex Color Node, create it if it does not exist in the current node tree
        bsdf_diffuse_node = override_clay_nodes.new(type = "ShaderNodeBsdfDiffuse")
        bsdf_diffuse_node.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)

            
        from mathutils import Vector
        bsdf_diffuse_node.location = Vector((-200.0, 0.0))

        # Link bsdf output to shader output 
        link = override_clay_mat.node_tree.links.new(bsdf_diffuse_node.outputs['BSDF'], override_clay_mat.node_tree.nodes.get("Material Output").inputs['Surface'])

    else: 
        pass
    # Switch to the Cycles render engine
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.data.scenes[current_scene_name].view_layers[current_viewlayer_name].material_override = bpy.data.materials['override_clay_GI']




    # ---------- SET LAMPS SHOW/HIDE ----------
    render_engine = bpy.context.scene.render.engine
    #exceptions is an optional list where you may put the names of the lightobjects that you want to remain unchanged 
    #is not that useful if you consider that you may always remove the suffix (CY or EV) by the object's name instead
    exceptions = [
    'Key Light (Background) ',
    'Key Light (Character) ',
    'Key Light (Extra) ',
    'Virtual Point Light',
    'Virtual Spot Light',
    'Virtual Sun Light',
    ]

    must_include = [
    'Starlight Sun',
    ]

    lights = [o for o in bpy.context.scene.objects if o.type == 'LIGHT']

    for light in lights:
        if light.name in exceptions :
            light.hide_render = True
            light.hide_viewport = True
        if light.name in must_include :
            light.hide_render = False
            light.hide_viewport = False
           
           
           
    # ---------- SET WORLD ----------
    if 'World_PSA' in bpy.data.worlds:
        # create a new world
        bpy.context.scene.world = bpy.data.worlds['World_PSA']

    else:
        world_PSA = bpy.data.worlds.new("World_PSA")
        bpy.context.scene.world = world_PSA
    
    bpy.context.scene.world.use_fake_user = True




    colname = 'GI'
    for mesh in selected_meshes:
        # Add a new vertex color for lightmap
        if not mesh.data.attributes.get(colname):  # check if lightmap col already exist
            # Create Vertex Color for each selected meshes
            # just a note here useless: mesh.data.color_attributes.new(name=colname, data_type='FLOAT', domain="CORNER")
            mesh.data.attributes.new(name=colname, domain='CORNER', type='FLOAT_COLOR')
    for o in selected_meshes:
        o.select_set(True)  # Select the object
        # Set the object shade to smooth angle 90°
        # bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=1.570796)
        # Set each object as the active object
        bpy.context.view_layer.objects.active = o
        # set vertex color for render (not necessary)
        bpy.ops.geometry.color_attribute_render_set(name=colname)
        # active color atribute
        named_color_attributes = bpy.context.object.data.color_attributes
        bpy.context.object.data.attributes.active_color = named_color_attributes.get(colname)


        # Switch to the Cycles render engine
        #bpy.context.scene.render.engine = 'CYCLES'

        # Set the bake settings
        bpy.context.scene.cycles.bake_type = 'DIFFUSE'
        bpy.context.scene.cycles.view_from = 'ABOVE_SURFACE'
        bpy.context.scene.render.bake.use_selected_to_active = False

        # Enable specific bake contributions
        bpy.context.scene.render.bake.use_pass_direct = True
        bpy.context.scene.render.bake.use_pass_indirect = True
        bpy.context.scene.render.bake.use_pass_diffuse = True
        bpy.context.scene.render.bake.use_pass_glossy = False
        bpy.context.scene.render.bake.use_pass_transmission = True
        bpy.context.scene.render.bake.use_pass_emit = True
        bpy.context.scene.render.bake.target = "VERTEX_COLORS"

        # Perform the bake
        bpy.ops.object.bake()
    
    #recaover settings
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.view_layer.material_override = None
    bpy.context.scene.world = bpy.data.worlds[current_world_name]

    #recaover lights hide/show
    for light in lights:
        if light.name in exceptions :
            light.hide_render = False
            light.hide_viewport = False
        if light.name in must_include :
            light.hide_render = True
            light.hide_viewport = True
            
            
# End the undo block
bpy.ops.ed.undo_push(message="End of script operation")