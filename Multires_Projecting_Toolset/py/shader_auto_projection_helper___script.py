"""run this script in shader editor, not in text editor, or it can't find nodegroups"""

import bpy
import os
os.chdir(os.path.dirname(bpy.data.filepath))

def manage_material_and_node_group():
    def get_shader_editor():
        return next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)

    def check_node_exists(nodes, node_name):
        return node_name in nodes

    def popup_message(message, title="Error", icon='ERROR'):
        bpy.context.window_manager.popup_menu(
            lambda self, context: self.layout.label(text=message),
            title=title,
            icon=icon
        )

    def update_material(node_tree, index):
        if node_tree is None:
            popup_message("No node tree is currently active.")
            return

        nodes = node_tree.nodes
        psd_image = f"CamP_sub{index:02d}_render.psd"
        tex_image_node = f"CamP_sub{index:02d}_render"
        img_conv_node = f"projection_layer{index:02d}"
        layer_mixer = '(24) layer_mixer'
        socket_in = f'――――――  {index:02}'
        socket_in_a = f'――――――  {index:02}_a'
        out_c = 'Color_output'
        out_a = 'Alpha_output'

        try:
            base_path = bpy.data.scenes[bpy.context.scene.name].node_tree.nodes["Output_path_MP"].base_path
            base_path = base_path.format(camera=f"CamP_sub{index:02d}")
            psd_path = os.path.join(os.path.dirname(bpy.data.filepath), base_path, psd_image)
        except Exception:
            psd_path = os.path.join(os.path.dirname(bpy.data.filepath), f"multires_projecting/CamP_sub{index:02d}/{psd_image}")

        if not all([check_node_exists(nodes, node) for node in [tex_image_node, img_conv_node, layer_mixer]]):
            popup_message("One or more nodes do not exist in the current node tree.")
            return

        if os.path.exists(bpy.path.abspath(psd_path)):
            if psd_image not in bpy.data.images:
                bpy.data.images.load(bpy.path.abspath(psd_path))
            image = bpy.data.images[psd_image]
            if 'autoreload_modification_time' not in image or str(os.path.getmtime(bpy.path.abspath(psd_path))) != image['autoreload_modification_time']:
                image.reload()
                image['autoreload_modification_time'] = str(os.path.getmtime(bpy.path.abspath(psd_path)))

        if not nodes[tex_image_node].mute:
            if os.path.exists(bpy.path.abspath(psd_path)):
                if psd_image not in bpy.data.images:
                    bpy.data.images.load(bpy.path.abspath(psd_path))
                nodes[tex_image_node].image = bpy.data.images[psd_image]
                node_tree.links.new(nodes[img_conv_node].outputs[out_c], nodes[layer_mixer].inputs[socket_in])
                node_tree.links.new(nodes[img_conv_node].outputs[out_a], nodes[layer_mixer].inputs[socket_in_a])
            else:
                nodes[tex_image_node].image = None
                nodes[tex_image_node].mute = True
                try:
                    node_tree.links.remove(nodes[layer_mixer].inputs[socket_in].links[0])
                    node_tree.links.remove(nodes[layer_mixer].inputs[socket_in_a].links[0])
                except:
                    pass
        else:
            nodes[tex_image_node].image = None
            try:
                node_tree.links.remove(nodes[layer_mixer].inputs[socket_in].links[0])
                node_tree.links.remove(nodes[layer_mixer].inputs[socket_in_a].links[0])
            except:
                pass

    def update_node_group(index):
        node_group = bpy.data.node_groups['.cam_projection_all']
        if node_group is None:
            popup_message("No node group '.cam_projection_all' is currently available.")
            return

        psd_image = f"CamP_sub{index:02d}_render.psd"
        cam_projection = f'cam_projection_{str(index).zfill(2)}'
        cam_object = f'CamP_sub{index:02d}'

        if not check_node_exists(node_group.nodes, cam_projection):
            popup_message("The cam_projection node does not exist in the node group.")
            return

        if psd_image in bpy.data.images:
            width = bpy.data.images[psd_image].size[0]
            height = bpy.data.images[psd_image].size[1]
        else:
            width = 100
            height = 100

        node_group.nodes[cam_projection].inputs['Width'].default_value = width
        node_group.nodes[cam_projection].inputs['Height'].default_value = height
        node_group.nodes[cam_projection].inputs['camera_angle'].default_value = bpy.data.cameras[cam_object].angle
        node_group.nodes[cam_projection].inputs['sensor_width'].default_value = bpy.data.cameras[cam_object].sensor_width
        node_group.nodes[cam_projection].inputs['shift_x'].default_value = bpy.data.cameras[cam_object].shift_x
        node_group.nodes[cam_projection].inputs['shift_y'].default_value = bpy.data.cameras[cam_object].shift_y
        node_group.nodes[cam_projection].inputs['loc_x'].default_value = bpy.data.objects[cam_object].location[0]
        node_group.nodes[cam_projection].inputs['loc_y'].default_value = bpy.data.objects[cam_object].location[1]
        node_group.nodes[cam_projection].inputs['loc_z'].default_value = bpy.data.objects[cam_object].location[2]
        node_group.nodes[cam_projection].inputs['rot_x'].default_value = bpy.data.objects[cam_object].rotation_euler[0]
        node_group.nodes[cam_projection].inputs['rot_y'].default_value = bpy.data.objects[cam_object].rotation_euler[1]
        node_group.nodes[cam_projection].inputs['rot_z'].default_value = bpy.data.objects[cam_object].rotation_euler[2]

    shader_editor = get_shader_editor()
    if shader_editor is None or shader_editor.edit_tree is None:
        popup_message("No Shader Editor is currently open or no node tree is currently active.")
    else:
        for i in range(1, 25):
            update_material(shader_editor.edit_tree, i)
            update_node_group(i)

    for image in bpy.data.images:
        if image.users == 0:
            bpy.data.images.remove(image)
            

    def check_rgb_curves():
        shader_editor = get_shader_editor()
        if shader_editor is None:
            popup_message("No Shader Editor is currently open or no node tree is currently active.")
        else:
            rgb_curve_nodes = [node for node in shader_editor.node_tree.nodes if node.type == 'CURVE_RGB' and node.name.startswith('RGB Curves') and node.name[-2:].isdigit() and 1 <= int(node.name[-2:]) <= 24]
            if not rgb_curve_nodes:
                popup_message("No RGB Curves nodes (RGB Curves01 to RGB Curves24) found!")
            else:
                for node in rgb_curve_nodes:
                    curves_meet_condition = False
                    for curve in [node.mapping.curves[0], node.mapping.curves[1], node.mapping.curves[2], node.mapping.curves[3]]:
                        if len(curve.points) == 2 and \
                            abs(curve.points[0].location.x - 0.0) < 0.0001 and \
                            abs(curve.points[0].location.y - 0.0) < 0.0001 and \
                            abs(curve.points[1].location.x - 1.0) < 0.0001 and \
                            abs(curve.points[1].location.y - 1.0) < 0.0001:
                            curves_meet_condition = True
                        else:
                            curves_meet_condition = False
                            break
                    if curves_meet_condition:
                        node.use_custom_color = False
                    else:
                        node.use_custom_color = True
                        node.color = (0.474512, 0.274513, 0.113727)

    check_rgb_curves()

manage_material_and_node_group()
