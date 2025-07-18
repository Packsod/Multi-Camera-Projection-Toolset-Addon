import bpy
import os

# Start the undo block
bpy.ops.ed.undo_push(message="Start of script operation")

# Get the active object
obj = bpy.context.view_layer.objects.active

# Function to display popup menu notifications
def display_popup(message):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title="Error", icon='ERROR')

# Check if the active object is a mesh with a material node tree
if obj and obj.type == 'MESH' and obj.active_material and obj.active_material.use_nodes and obj.data.uv_layers:
    # Get the node tree of the active object
    node_tree = obj.active_material.node_tree

    # Define acceptable names for the reference image node
    acceptable_names = ["overpaint", "ov", "op", "project", "projecting", "billboard", "BR"]  # Add or modify as needed
    # Find the reference image node
    ref_img_node = None
    for node in node_tree.nodes:
        if hasattr(node, 'image') and node.image is not None:
            if node.image.name is not None:
                if isinstance(node, bpy.types.ShaderNodeTexImage):
                    for name in acceptable_names:
                        if name.lower() in node.label.lower() or name.lower() in node.image.name.lower():
                            ref_img_node = node
                            break
                    if ref_img_node:# not strictly necessary
                        break# but easy to understand, stop the loop when get ref img node. 
                          
    if not ref_img_node:
        display_popup("No reference image node found.")
    else:
        ref_img = ref_img_node.image

    # If no reference image node is found, display a popup menu to notify the user
    if not ref_img_node:
        display_popup("No reference image node found.")
    else:
        # Get the reference image
        ref_img = ref_img_node.image
        if ref_img is not None:
            ref_img_name = ref_img.name
            ref_img.name = "legacy_" + ref_img.name
            
            ref_img_path = ref_img.filepath
            ref_width = ref_img.size[0]
            ref_height = ref_img.size[1]

            # Create a new image node
            img_new = node_tree.nodes.new(type='ShaderNodeTexImage')
            img_new.label = "billboard"
            img_new.image = bpy.data.images.new(name=ref_img_name, width=ref_width, height=ref_height, alpha=True)
            uv_map_node = node_tree.nodes.new(type='ShaderNodeUVMap')
            uv_map_node.uv_map = "UVMap"
            node_tree.links.new(img_new.inputs['Vector'], uv_map_node.outputs['UV'])

            # Make the new image node active
            node_tree.nodes.active = img_new

            # Record the current render engine
            current_engine = bpy.context.scene.render.engine
            bpy.context.scene.render.engine = 'CYCLES'

            # Record the current bake settings
            current_bake_samples = bpy.context.scene.cycles.samples
            current_bake_type = bpy.context.scene.cycles.bake_type
            current_use_pass_direct = bpy.context.scene.render.bake.use_pass_direct
            current_use_pass_indirect = bpy.context.scene.render.bake.use_pass_indirect
            current_use_pass_color = bpy.context.scene.render.bake.use_pass_color
            current_use_pass_emit = bpy.context.scene.render.bake.use_pass_emit
            current_use_pass_diffuse = bpy.context.scene.render.bake.use_pass_diffuse
            current_use_pass_glossy = bpy.context.scene.render.bake.use_pass_glossy
            current_use_pass_transmission = bpy.context.scene.render.bake.use_pass_transmission
            current_use_selected_to_active = bpy.context.scene.render.bake.use_selected_to_active
            current_target = bpy.context.scene.cycles.bake_type
            current_margin = bpy.context.scene.render.bake.margin

            # Set the bake settings
            bpy.context.scene.cycles.samples = 16
            bpy.context.scene.cycles.bake_type = 'COMBINED'
            bpy.context.scene.cycles.view_from = 'ABOVE_SURFACE'
            bpy.context.scene.render.bake.use_pass_direct = True
            bpy.context.scene.render.bake.use_pass_indirect = True
            bpy.context.scene.render.bake.use_pass_diffuse = True
            bpy.context.scene.render.bake.use_pass_glossy = False
            bpy.context.scene.render.bake.use_pass_transmission = True
            bpy.context.scene.render.bake.use_pass_emit = True
            bpy.context.scene.render.bake.use_selected_to_active = False
            bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'
            bpy.context.scene.render.bake.use_clear = True
            bpy.context.scene.render.bake.margin_type = 'ADJACENT_FACES'
            bpy.context.scene.render.bake.margin = 8

            # Bake the new image
            bpy.ops.object.bake(type='COMBINED')

            # Set the output image format
            bpy.context.scene.render.image_settings.file_format = "PNG"
            bpy.context.scene.render.image_settings.color_mode = "RGBA"
            bpy.context.scene.render.image_settings.color_depth = "8"
            bpy.context.scene.render.image_settings.compression = 15

            # Save the new image to the reference image file path with the same file name and a .png extension
            img_new.image.filepath_raw = ref_img_path
            img_new.image.file_format = 'PNG'
            img_new.image.save()

            # Restore the render engine
            bpy.context.scene.render.engine = current_engine

            # Restore the bake settings
            bpy.context.scene.cycles.samples = current_bake_samples
            bpy.context.scene.cycles.bake_type = current_bake_type
            bpy.context.scene.render.bake.use_pass_direct = current_use_pass_direct
            bpy.context.scene.render.bake.use_pass_indirect = current_use_pass_indirect
            bpy.context.scene.render.bake.use_pass_color = current_use_pass_color
            bpy.context.scene.render.bake.use_pass_emit = current_use_pass_emit
            bpy.context.scene.render.bake.use_pass_diffuse = current_use_pass_diffuse
            bpy.context.scene.render.bake.use_pass_glossy = current_use_pass_glossy
            bpy.context.scene.render.bake.use_pass_transmission = current_use_pass_transmission
            bpy.context.scene.render.bake.use_selected_to_active = current_use_selected_to_active
            bpy.context.scene.cycles.bake_type = current_target
            bpy.context.scene.render.bake.margin = current_margin

            # Get the active material of the active object
            ref_mat = obj.active_material
            ref_mat_name = ref_mat.name

            # Change the name of the active material
            ref_mat.name = "legacy_" + ref_mat_name

            # Create a new material
            new_mat = bpy.data.materials.new(name=ref_mat_name)
            new_mat.use_nodes = True
            new_mat.blend_method = 'CLIP'
            new_mat.shadow_method = 'NONE'

            # Assign the new material to the active object
            obj.data.materials.clear()
            obj.data.materials.append(new_mat)

            # Set up the node tree for the new material
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links
            output = nodes['Material Output']

            img_node = nodes.new(type="ShaderNodeTexImage")
            img_node.label = "Billboard"
            img_node.image = img_new.image

            uv_node = nodes.new(type="ShaderNodeUVMap")
            # Check if the UV map with index 0 exists and has the name "UVMap"
            if obj.data.uv_layers and obj.data.uv_layers[0].name != "UVMap":
                obj.data.uv_layers[0].name = "UVMap"
            uv_node.uv_map = "UVMap"
            emit_node = nodes.new(type='ShaderNodeEmission')
            mix_node = nodes.new(type='ShaderNodeMixShader')
            transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
            mix_node_2 = nodes.new(type='ShaderNodeMixShader')
            lightpath_node = nodes.new(type="ShaderNodeLightPath")

            links.new(uv_node.outputs['UV'], img_node.inputs['Vector'])
            links.new(img_node.outputs['Alpha'], mix_node.inputs['Fac'])
            links.new(img_node.outputs['Color'], emit_node.inputs['Color'])
            links.new(transparent_node.outputs['BSDF'], mix_node.inputs[1])
            links.new(emit_node.outputs['Emission'], mix_node.inputs[2])
            links.new(mix_node.outputs['Shader'], mix_node_2.inputs[2])
            links.new(transparent_node.outputs['BSDF'], mix_node_2.inputs[1])
            links.new(lightpath_node.outputs['Is Camera Ray'], mix_node_2.inputs['Fac'])
            links.new(mix_node_2.outputs['Shader'], output.inputs['Surface'])

            # Set the locations of the nodes for better organization in the node editor
            img_node.location = (-400, 300)
            uv_node.location = (-575, 140)
            emit_node.location = (-100, 175)
            mix_node.location = (-100, 275)
            transparent_node.location = (-100, 40)
            mix_node_2.location = (100, 275)
            lightpath_node.location = (-100, 550)

            # Remove the "Principled BSDF" node from the new material's node tree
            bsdf_node = nodes.get('Principled BSDF')
            if bsdf_node:
                nodes.remove(bsdf_node)

            # Remove the old material from data
            bpy.data.materials.remove(ref_mat)
            bpy.data.images.remove(ref_img)
        else:
            display_popup("Reference image is None.")
else:
    display_popup("No mesh object with a material node tree is selected.")


# End the undo block
bpy.ops.ed.undo_push(message="End of script operation")