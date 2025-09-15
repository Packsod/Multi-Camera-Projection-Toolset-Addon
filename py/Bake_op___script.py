import bpy
from mathutils import Vector

class BakeVcol:
    @staticmethod
    def bake_selected_meshes(bake_settings, colname='GI', use_world_override=True):
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
            current_world = bpy.context.scene.world  # Record the current world
            current_render_engine = bpy.context.scene.render.engine  # Record the current render engine

            # ---------- SET OVERRIDE CLAY MAT ----------
            override_clay_mat = bpy.data.materials.get('override_clay_GI')
            if override_clay_mat is None:
                # create material and assign
                override_clay_mat = bpy.data.materials.new(name="override_clay_GI")
                override_clay_mat.use_nodes = True
                override_clay_nodes = override_clay_mat.node_tree.nodes
                bsdf_diffuse_node = override_clay_nodes.new(type="ShaderNodeBsdfDiffuse")
                bsdf_diffuse_node.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
                bsdf_diffuse_node.location = Vector((-200.0, 0.0))
                override_clay_mat.node_tree.links.new(
                    bsdf_diffuse_node.outputs['BSDF'],
                    override_clay_mat.node_tree.nodes.get("Material Output").inputs['Surface']
                )

            # Switch to Cycles render engine
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.data.scenes[current_scene_name].view_layers[current_viewlayer_name].material_override = override_clay_mat

            # ---------- SET LAMPS SHOW/HIDE ----------
            lights = [o for o in bpy.context.scene.objects if o.type == 'LIGHT']
            exceptions = []
            must_include = []

            for light in lights:
                if light.name in exceptions:
                    light.hide_render = True
                    light.hide_viewport = True
                if light.name in must_include:
                    light.hide_render = False
                    light.hide_viewport = False

            # ---------- SET WORLD ----------
            if use_world_override:
                found_world = None
                # Find a world different from current and not named "World_GI"
                for world in bpy.data.worlds:
                    if world != current_world and world.name != "World_GI":
                        found_world = world
                        break
                if found_world is None:
                    new_world = bpy.data.worlds.new("World_GI")
                    found_world = new_world
                bpy.context.scene.world = found_world
            else:
                found_world = current_world  # Keep current world if no override

            # Record the active vertex color attribute for each selected mesh
            active_vertex_colors = {}
            for mesh in selected_meshes:
                try:
                    active_vertex_colors[mesh] = mesh.data.attributes.active_color.name
                except AttributeError:
                    pass

            for mesh in selected_meshes:
                if not mesh.data.attributes.get(colname):
                    mesh.data.attributes.new(name=colname, domain='CORNER', type='BYTE_COLOR')

            for o in selected_meshes:
                o.select_set(True)
                bpy.context.view_layer.objects.active = o
                named_color_attributes = bpy.context.object.data.color_attributes
                bpy.context.object.data.attributes.active_color = named_color_attributes.get(colname)

                # Set bake settings
                bpy.context.scene.cycles.bake_type = 'DIFFUSE'
                bpy.context.scene.cycles.view_from = 'ABOVE_SURFACE'
                bpy.context.scene.render.bake.use_selected_to_active = False
                bpy.context.scene.render.bake.use_pass_direct = bake_settings.get("use_pass_direct", True)
                bpy.context.scene.render.bake.use_pass_indirect = bake_settings.get("use_pass_indirect", True)
                bpy.context.scene.render.bake.use_pass_diffuse = bake_settings.get("use_pass_diffuse", True)
                bpy.context.scene.render.bake.use_pass_glossy = bake_settings.get("use_pass_glossy", False)
                bpy.context.scene.render.bake.use_pass_transmission = bake_settings.get("use_pass_transmission", True)
                bpy.context.scene.render.bake.use_pass_emit = bake_settings.get("use_pass_emit", True)
                bpy.context.scene.render.bake.target = "VERTEX_COLORS"

                bpy.ops.object.bake()

            # Recover settings
            bpy.context.scene.render.engine = current_render_engine
            bpy.context.view_layer.material_override = None
            bpy.context.scene.world = current_world

            for light in lights:
                if light.name in exceptions:
                    light.hide_render = False
                    light.hide_viewport = False
                if light.name in must_include:
                    light.hide_render = True
                    light.hide_viewport = True

            # Restore the active vertex color attribute for each selected mesh
            for mesh, active_color_name in active_vertex_colors.items():
                try:
                    mesh.data.attributes.active_color = mesh.data.attributes.get(active_color_name)
                except AttributeError:
                    pass

        bpy.ops.ed.undo_push(message="End of script operation")

    @staticmethod
    def bake_GI_full():
        bake_settings = {
            "use_pass_direct": True,
            "use_pass_indirect": True,
            "use_pass_diffuse": True,
            "use_pass_glossy": False,
            "use_pass_transmission": True,
            "use_pass_emit": True,
        }
        BakeVcol.bake_selected_meshes(bake_settings)

    @staticmethod
    def bake_GI_indirect():
        bake_settings = {
            "use_pass_direct": False,
            "use_pass_indirect": True,
            "use_pass_diffuse": True,
            "use_pass_glossy": False,
            "use_pass_transmission": True,
            "use_pass_emit": True,
        }
        BakeVcol.bake_selected_meshes(bake_settings)

    @staticmethod
    def bake_shadow():
        bake_settings = {
            "use_pass_direct": True,
            "use_pass_indirect": False,
            "use_pass_diffuse": True,
            "use_pass_glossy": False,
            "use_pass_transmission": True,
            "use_pass_emit": True,
        }
        # Call bake_selected_meshes with colname 'shadow' and no world override
        BakeVcol.bake_selected_meshes(bake_settings, colname='shadow', use_world_override=False)

    @staticmethod
    def bake_ambient_occlusion():
        """Function to execute the AO baking process."""
        # Save the current render engine
        current_render_engine = bpy.context.scene.render.engine
        # Switch to Cycles render engine
        bpy.context.scene.render.engine = 'CYCLES'

        # Get selected mesh objects
        selected_objects = bpy.context.selected_objects
        mesh_objects = [obj for obj in selected_objects if obj.type == 'MESH']

        # Record the active vertex color attribute for each selected mesh
        active_vertex_colors = {}
        for obj in mesh_objects:
            try:
                active_vertex_colors[obj] = obj.data.attributes.active_color.name
            except AttributeError:
                pass

        for obj in mesh_objects:
            # Create or get the "AO" vertex color attribute
            ao_layer = obj.data.attributes.get("AO")
            if ao_layer is None:
                ao_layer = obj.data.attributes.new(name="AO", domain='CORNER', type='BYTE_COLOR')
            # Set "AO" as the active attribute for vertex colors
            obj.data.attributes.active_color = ao_layer

        # Bake AO to vertex colors for each object
        for obj in mesh_objects:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            bpy.context.scene.render.bake.use_selected_to_active = False
            bpy.context.scene.cycles.bake_type = 'AO'
            bpy.context.scene.render.bake.target = 'VERTEX_COLORS'

            bpy.ops.object.bake(type='AO')

        # Restore original render engine
        bpy.context.scene.render.engine = current_render_engine

        # Restore the active vertex color attribute for each selected mesh
        for obj, active_color_name in active_vertex_colors.items():
            try:
                obj.data.attributes.active_color = obj.data.attributes.get(active_color_name)
            except AttributeError:
                pass

    @staticmethod
    def bake_vcolcombine():
        # Start the undo block
        bpy.ops.ed.undo_push(message="Start of script operation")

        current_render_engine = bpy.context.scene.render.engine

        # Check if there are any selected mesh objects
        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']
        if not selected_meshes:
            bpy.context.window_manager.popup_menu(
                lambda self, context: self.layout.label(text="You need to select at least one mesh to bake."),
                title="Error",
                icon='ERROR'
            )

        colname = 'Vcolcombine'
        original_active_colors = {}  # Dictionary to store original active colors

        for mesh in selected_meshes:
            try:
                # Record the original active color
                original_active_colors[mesh.name] = mesh.data.attributes.active_color
            except AttributeError:
                pass

            # Add a new vertex color for Vcolcombine
            if not mesh.data.attributes.get(colname):  # check if col already exists
                # Create Vertex Color for each selected mesh
                mesh.data.attributes.new(name=colname, domain='CORNER', type='BYTE_COLOR')

            mesh.select_set(True)  # Select the object
            # Set the object shade to smooth angle 90°
            # bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=1.570796)

            # Set each object as the active object
            bpy.context.view_layer.objects.active = mesh

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

        bpy.context.scene.render.engine = current_render_engine  # Restore the original render engine

        # Restore original active colors
        for mesh in selected_meshes:
            try:
                mesh.data.attributes.active_color = original_active_colors[mesh.name]
            except AttributeError:
                pass

        # End the undo block
        bpy.ops.ed.undo_push(message="End of script operation")

# Uncomment the following lines to test the functions
# BakeVcol.bake_GI_full()
# BakeVcol.bake_ambient_occlusion()
# BakeVcol.bake_vcolcombine()
