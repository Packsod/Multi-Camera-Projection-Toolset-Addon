#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import os

# ----------------------------------------------------
# 1) Start undo block
bpy.ops.ed.undo_push(message="Start of script operation")

# 2) Get the active object
obj = bpy.context.view_layer.objects.active

# ----------------------------------------------------
# Helper: show a popup message
def display_popup(message):
    def draw(self, context):
        layout = context.layout
        layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title="Error", icon='ERROR')

# ----------------------------------------------------
# 3) Check if active object is a mesh with a material node tree
if obj and obj.type == 'MESH' and obj.active_material and obj.active_material.use_nodes and obj.data.uv_layers:
    # Get node tree of active material
    node_tree = obj.active_material.node_tree

    # ----------------------------------------------------
    # 4) Find the reference image node
    acceptable_names = ["overpaint", "ov", "op", "project", "projecting", "billboard", "BR"]
    ref_img_node = None
    for node in node_tree.nodes:
        if hasattr(node, 'image') and node.image is not None:
            if isinstance(node, bpy.types.ShaderNodeTexImage):
                for name in acceptable_names:
                    if name.lower() in node.label.lower() or name.lower() in node.image.name.lower():
                        ref_img_node = node
                        break
            if ref_img_node:
                break

    if not ref_img_node:
        display_popup("No reference image node found.")
        exit()

    # ----------------------------------------------------
    # 5) Determine the UVMap used by the reference image node
    uv_node = None
    for link in ref_img_node.inputs['Vector'].links:
        if isinstance(link.from_node, bpy.types.ShaderNodeUVMap):
            uv_node = link.from_node
            break
    uv_map_name = uv_node.uv_map if uv_node else "UVMap"

    # ----------------------------------------------------
    # 6) Set the object's active UV layer to this UVMap
    uv_layer = obj.data.uv_layers.get(uv_map_name)
    if uv_layer is not None:
        obj.data.uv_layers.active = uv_layer
    else:
        uv_layer = obj.data.uv_layers[0]
        uv_layer.name = uv_map_name
        obj.data.uv_layers.active = uv_layer

    # ----------------------------------------------------
    # 7) Create a new UVMap node in the node tree using the same name
    uv_map_node = node_tree.nodes.new(type='ShaderNodeUVMap')
    uv_map_node.uv_map = uv_map_name

    # ----------------------------------------------------
    # 8) Ensure all Material Output nodes target 'ALL'
    for n in node_tree.nodes:
        if isinstance(n, bpy.types.ShaderNodeOutputMaterial):
            n.target = 'ALL'

    # ----------------------------------------------------
    # 9) Create a new image node (empty image)
    ref_img = ref_img_node.image
    ref_img_name = ref_img.name
    ref_img.name = "legacy_" + ref_img.name
    ref_width, ref_height = ref_img.size[0], ref_img.size[1]

    # **Store original file path**
    ref_img_path = ref_img.filepath

    img_new = node_tree.nodes.new(type='ShaderNodeTexImage')
    img_new.label = "billboard"
    img_new.image = bpy.data.images.new(name=ref_img_name,
                                        width=ref_width,
                                        height=ref_height,
                                        alpha=True)

    # Link UV node to image node
    node_tree.links.new(img_new.inputs['Vector'], uv_map_node.outputs['UV'])
    node_tree.nodes.active = img_new

    # ----------------------------------------------------
    # 10) Record current render engine & bake settings
    current_engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'CYCLES'

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

    # ----------------------------------------------------
    # 11) Set bake settings
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

    # ----------------------------------------------------
    # 12) Bake the new image
    bpy.ops.object.bake(type='COMBINED')

    # ----------------------------------------------------
    # 13) Set output image format
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGBA"
    bpy.context.scene.render.image_settings.color_depth = "8"
    bpy.context.scene.render.image_settings.compression = 15

    # ----------------------------------------------------
    # 14) Save the baked image to the original file path
    img_new.image.filepath_raw = ref_img_path
    img_new.image.file_format = 'PNG'
    img_new.image.save()

    # ----------------------------------------------------
    # 15) Restore render engine & bake settings
    bpy.context.scene.render.engine = current_engine
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

    # ----------------------------------------------------
    # 16) Create a new material that uses the baked image
    ref_mat = obj.active_material
    ref_mat_name = ref_mat.name
    ref_mat.name = "legacy_" + ref_mat_name

    new_mat = bpy.data.materials.new(name=ref_mat_name)
    new_mat.use_nodes = True

    obj.data.materials.clear()
    obj.data.materials.append(new_mat)

    nodes = new_mat.node_tree.nodes
    links = new_mat.node_tree.links
    output = nodes['Material Output']

    img_node = nodes.new(type="ShaderNodeTexImage")
    img_node.label = "Billboard"
    img_node.image = img_new.image

    uv_node_new = nodes.new(type="ShaderNodeUVMap")
    uv_node_new.uv_map = uv_map_name

    emit_node = nodes.new(type='ShaderNodeEmission')
    mix_node = nodes.new(type='ShaderNodeMixShader')
    transparent_node = nodes.new(type='ShaderNodeBsdfTransparent')
    mix_node_2 = nodes.new(type='ShaderNodeMixShader')
    lightpath_node = nodes.new(type="ShaderNodeLightPath")

    links.new(uv_node_new.outputs['UV'], img_node.inputs['Vector'])
    links.new(img_node.outputs['Alpha'], mix_node.inputs['Fac'])
    links.new(img_node.outputs['Color'], emit_node.inputs['Color'])
    links.new(transparent_node.outputs['BSDF'], mix_node.inputs[1])
    links.new(emit_node.outputs['Emission'], mix_node.inputs[2])
    links.new(mix_node.outputs['Shader'], mix_node_2.inputs[2])
    links.new(transparent_node.outputs['BSDF'], mix_node_2.inputs[1])
    links.new(lightpath_node.outputs['Is Camera Ray'], mix_node_2.inputs['Fac'])
    links.new(mix_node_2.outputs['Shader'], output.inputs['Surface'])

    img_node.location = (-400, 300)
    uv_node_new.location = (-575, 140)
    emit_node.location = (-100, 175)
    mix_node.location = (-100, 275)
    transparent_node.location = (-100, 40)
    mix_node_2.location = (100, 275)
    lightpath_node.location = (-100, 550)

    bsdf_node = nodes.get('Principled BSDF')
    if bsdf_node:
        nodes.remove(bsdf_node)

    bpy.data.materials.remove(ref_mat)
    bpy.data.images.remove(ref_img)

else:
    display_popup("No mesh object with a material node tree is selected.")

# ----------------------------------------------------
# 17) End undo block
bpy.ops.ed.undo_push(message="End of script operation")
