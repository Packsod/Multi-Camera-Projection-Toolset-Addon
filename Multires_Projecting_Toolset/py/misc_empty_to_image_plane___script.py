import bpy

# Start the undo block
bpy.ops.ed.undo_push(message="Start of script operation")

# Nested function
def image_plane_at_image_emtpy(empty, prefix="Image Plane"):
    """Add image plane at given empty"""
    if not empty.data or not empty.data.filepath:
        return

    def get_image_by_filepath(filepath):
        """Find image by filepath"""
        for img in bpy.data.images.values():
            if img.filepath == filepath:
                return img

    img = get_image_by_filepath(empty.data.filepath)
    cursor = bpy.context.scene.cursor
    cursor.location = (0, 0, 0)

    bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, location=(0, 0, 0))
    plane = bpy.context.object

    x = img.size[0] / 2000
    y = img.size[1] / 2000

    if x <= y:
        plane.scale.x = x / y
    else:
        plane.scale.y = y / x

    lx = plane.location.x
    ly = plane.location.y
    sx = plane.scale.x
    sy = plane.scale.y
    e_offx = empty.empty_image_offset[0]
    e_offy = empty.empty_image_offset[1]

    cursor.location.x = lx - sx / 2 - sx * e_offx
    cursor.location.y = ly - sy / 2 - sy * e_offy

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    plane.location = empty.location
    plane.rotation_euler = (1.5708, 0, empty.rotation_euler[2]) # x=90 degrees, y=0 degrees
    plane.scale.x = empty.empty_display_size * empty.scale.x
    plane.scale.y = empty.empty_display_size * empty.scale.y

    mat = bpy.data.materials.new(img.name)
    mat.use_nodes = True
    mat.blend_method = 'CLIP'
    mat.shadow_method = 'NONE'
    plane.data.materials.append(mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes['Material Output']

    img_node = nodes.new(type="ShaderNodeTexImage")
    img_node.label = "Billboard"
    uv_node = nodes.new(type="ShaderNodeUVMap")
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

    img_node.image = img
    img_node.location = (-400, 300)
    uv_node.location = (-575, 140)
    emit_node.location = (-100, 175)
    mix_node.location = (-100, 275)
    transparent_node.location = (-100, 40)
    mix_node_2.location = (100, 275)
    lightpath_node.location = (-100, 550)

    plane.name = prefix + img.name
    bpy.data.objects.remove(empty, do_unlink=True)
    bsdf_node = nodes.get('Principled BSDF')
    if bsdf_node:
        nodes.remove(bsdf_node)
    return True

# Example usage
selected_objects = bpy.context.selected_objects
for obj in selected_objects:
    if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
        image_plane_at_image_emtpy(obj, prefix="Image Plane ")

# End the undo block
bpy.ops.ed.undo_push(message="End of script operation")
