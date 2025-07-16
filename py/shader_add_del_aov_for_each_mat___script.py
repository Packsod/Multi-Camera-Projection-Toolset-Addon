import bpy

class AOV_Manager:
    def __init__(self):
        self.node_group_name = ".AOV"
        self.script_state = bpy.context.window_manager.get('script_state', False)

    def find_node_group(self):
        return bpy.data.node_groups.get(self.node_group_name)

    def execute_script_on(self):
        node_group = self.find_node_group()

        if node_group is None:
            self.display_error("AOV nodegroup does not exist, run set scene to get it.")
        else:
            for material in bpy.data.materials:
                if material.name == "NPR_Shader_Library":
                    continue
                if material.node_tree and any(node.node_tree.name == self.node_group_name for node in material.node_tree.nodes if hasattr(node, 'node_tree')):
                    continue
                if material.node_tree:
                    new_node = material.node_tree.nodes.new('ShaderNodeGroup')
                    new_node.node_tree = node_group

    def execute_script_off(self):
        for material in bpy.data.materials:
            if not material.node_tree or not material.use_nodes:
                continue
            if material.name == "NPR_Shader_Library":
                continue
            nodes_to_remove = [node for node in material.node_tree.nodes if getattr(node, 'node_tree', None) and node.node_tree.name == self.node_group_name]
            for node in nodes_to_remove:
                material.node_tree.nodes.remove(node)

    def toggle_script(self):
        if self.script_state:
            print("Running execute_script_off")
            self.execute_script_off()
            bpy.context.window_manager['script_state'] = False
        else:
            print("Running execute_script_on")
            self.execute_script_on()
            bpy.context.window_manager['script_state'] = True

    def display_error(self, message):
        bpy.context.window_manager.popup_menu(
            lambda self, context: self.layout.label(text=message),
            title="Error",
            icon='ERROR'
        )

AOVManager = AOV_Manager()
AOVManager.toggle_script()
