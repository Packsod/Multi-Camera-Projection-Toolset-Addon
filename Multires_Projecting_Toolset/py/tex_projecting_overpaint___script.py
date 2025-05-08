import bpy
import os

def popup_message_error(message):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title="Error", icon='ERROR')

# By defining a new function that encapsulates the any function call, I avoid the node variable scoping problem.
def check_node_name(node, acceptable_names):
    return any(name.lower() in node.image.name.lower() or name.lower() in node.label.lower() for name in acceptable_names)

active_obj = bpy.context.active_object
if not active_obj:
    popup_message_error("No object selected.")
elif active_obj.type != 'MESH':
    popup_message_error("Selected object is not a mesh.")
elif not active_obj.active_material:
    popup_message_error("The active object does not have an active material.")
else:
    active_mat = active_obj.active_material
    nodes = active_mat.node_tree.nodes
    node_found = False
    image_node = None
    for node in nodes:
        acceptable_names = ["overpaint", "ov", "op", "project", "projecting", "billboard", "BR"]
        if node.bl_idname == 'ShaderNodeTexImage' and node.image and check_node_name(node, acceptable_names):
            image_node = node
            node_found = True
            break
        if node.bl_idname == 'ShaderNodeGroup':
            group_nodes = node.node_tree.nodes
            for group_node in group_nodes:
                if group_node.bl_idname == 'ShaderNodeTexImage' and group_node.image and check_node_name(group_node, acceptable_names):
                    image_node = group_node
                    node_found = True
                    break
        if node_found:
            break
    if not node_found:
        popup_message_error("The active material does not use a image containing 'overpaint', 'ov', 'op', 'project', 'projecting', 'billboard', 'BR' in the name or label.")
    elif image_node.image:
        if image_node.image.filepath.lower().endswith('.psd'):
            popup_message_error("The image is a PSD file. Saving it may destroy the layered information.")
        else:
            image_node.image.save()
            self.report({'INFO'}, 'Image saved successfully.')
    else:
        popup_message_error("Error: No image found in the node.")
