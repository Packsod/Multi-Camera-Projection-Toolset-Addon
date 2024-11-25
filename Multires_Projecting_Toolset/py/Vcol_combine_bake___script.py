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

ob = bpy.context.active_object
colname = 'Vcolcombine'

for mesh in selected_meshes:
    # Add a new vertex color for Vcolcombine
    # Mesh.vertex_colors is deprecated, and the new sculpt paint tool uses mesh.attributes instead
    if not mesh.data.attributes.get(colname):  # check if col already exists
        # Create Vertex Color for each selected mesh
        mesh.data.attributes.new(name=colname, domain='CORNER', type='FLOAT_COLOR')

    mesh.select_set(True)  # Select the object
    # Set the object shade to smooth angle 90°
    # bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=1.570796)

    # Set each object as the active object
    bpy.context.view_layer.objects.active = mesh

    # set vertex color for render (not necessary)
    bpy.ops.geometry.color_attribute_render_set(name=colname)

    # active color attribute
    named_color_attributes = bpy.context.object.data.color_attributes
    bpy.context.object.data.attributes.active_color = named_color_attributes.get(colname)

    # Switch to the Cycles render engine
    bpy.context.scene.render.engine = 'CYCLES'

    # Set the bake settings
    bpy.context.scene.cycles.bake_type = 'DIFFUSE'
    bpy.context.scene.cycles.view_from = 'ABOVE_SURFACE'
    bpy.context.scene.render.bake.use_selected_to_active = False

    # Enable specific bake contributions
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.use_pass_diffuse = False
    bpy.context.scene.render.bake.use_pass_glossy = False
    bpy.context.scene.render.bake.use_pass_transmission = False
    bpy.context.scene.render.bake.use_pass_emit = True
    bpy.context.scene.render.bake.target = "VERTEX_COLORS"

    # Perform the bake
    bpy.ops.object.bake()

    # Get material
    basecol_mat = bpy.data.materials.get('Basecol')

    if not mesh.material_slots:
        bpy.ops.object.material_slot_add()

    if basecol_mat is None:
        # create material and assign
        bpy.ops.object.material_slot_remove()
        basecol_mat = bpy.data.materials.new(name="Basecol")
        basecol_mat.use_nodes = True
        mesh.data.materials.append(basecol_mat)
        bpy.ops.object.material_slot_remove_unused()

        # ---------- MANAGE NODES OF SHADER EDITOR ----------

        # Get node tree from the material
        basecol_nodes = basecol_mat.node_tree.nodes

        # Get Vertex Color Node, create it if it does not exist in the current node tree
        if not "VERTEX_COLOR" in [node.type for node in basecol_nodes]:
            vertex_color_node = basecol_nodes.new(type="ShaderNodeVertexColor")
        else:
            vertex_color_node = basecol_nodes.get("Color Attribute")

        from mathutils import Vector
        vertex_color_node.location = Vector((-200.0, 0.0))

        # Set the vertex_color layer we created at the beginning as input
        vertex_color_node.layer_name = "Vcolcombine"

        if not "EMISSION" in [node.type for node in basecol_nodes]:
            emission_node = basecol_nodes.new(type="ShaderNodeEmission")
        else:
            emission_node = basecol_nodes.get("Emission")

        # Set the vertex_color layer we created at the beginning as input
        vertex_color_node.layer_name = "Vcolcombine"

        # Link Vertex Color output to shader output
        link = basecol_mat.node_tree.links.new(vertex_color_node.outputs[0], basecol_mat.node_tree.nodes.get("Emission").inputs[0])
        link = basecol_mat.node_tree.links.new(emission_node.outputs[0], basecol_mat.node_tree.nodes.get("Material Output").inputs[0])

        basecol_nodes.remove(basecol_nodes['Principled BSDF'])

    else:
        # delete material in object, Assign material
        mesh.material_slots[0].material = bpy.data.materials['Basecol']
        bpy.ops.object.material_slot_remove_unused()

bpy.context.scene.render.engine = 'BLENDER_EEVEE'

# End the undo block
bpy.ops.ed.undo_push(message="End of script operation")