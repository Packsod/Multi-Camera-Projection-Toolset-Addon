import bpy
import mathutils

class ShaderAdder:
    @staticmethod
    def add_node_group(name):
        if name not in bpy.data.node_groups:
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text=f"The node group '{name}' does not exist."))
            return
        # Get the active node tree in the shader editor
        node_tree = bpy.context.space_data.edit_tree
        for node in node_tree.nodes:
            node.select = False
        node_group = node_tree.nodes.new('ShaderNodeGroup')
        node_group.node_tree = bpy.data.node_groups[name]
        node_group.location = bpy.context.space_data.cursor_location.copy()
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(False, False, False))
        bpy.types.SpaceView3D.draw_handler_add(ShaderAdder.handle_mouse_move, (node_group, ), 'WINDOW', 'POST_PIXEL')

    @staticmethod
    def handle_mouse_move(node_group, context, event):
        node_group.location = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
        return {'FINISHED'}

    @classmethod
    def npr_Key_Light(cls):
        cls.add_node_group(".npr_Key Light")

    @classmethod
    def npr_Specular(cls):
        cls.add_node_group(".npr_Specular")

    @classmethod
    def npr_Virtual_Point_Light(cls):
        cls.add_node_group(".npr_Virtual Point Light")

    @classmethod
    def npr_Virtual_Spot_Light(cls):
        cls.add_node_group(".npr_Virtual Spot Light")

    @classmethod
    def npr_Virtual_Sun_Light(cls):
        cls.add_node_group(".npr_Virtual Sun Light")

    @classmethod
    def npr_Color(cls):
        cls.add_node_group(".npr_Color")

    @classmethod
    def npr_layer_mix_shader(cls):
        cls.add_node_group(".(09) npr_layer_mix_shader")

    @classmethod
    def npr_Layer_Adjustment(cls):
        cls.add_node_group(".npr_Layer Adjustment")

    @classmethod
    def npr_Global_Color(cls):
        cls.add_node_group(".npr_Global Color")

    @classmethod
    def npr_Linear_Gradient(cls):
        cls.add_node_group(".npr_Linear Gradient")

    @classmethod
    def npr_Spherical_Gradient(cls):
        cls.add_node_group(".npr_Spherical Gradient")

    @classmethod
    def npr_Local_Gradient(cls):
        cls.add_node_group(".npr_Local Gradient")

    @classmethod
    def npr_Z_Depth(cls):
        cls.add_node_group(".npr_Z Depth")

    @classmethod
    def npr_2D_Outline(cls):
        cls.add_node_group(".npr_2D Outline")

    @classmethod
    def npr_2D_Rim_Light(cls):
        cls.add_node_group(".npr_2D Rim Light")

    @classmethod
    def npr_2D_Specular(cls):
        cls.add_node_group(".npr_2D Specular")

    @classmethod
    def npr_Matcap(cls):
        cls.add_node_group(".npr_Matcap")

    @classmethod
    def npr_Ambient_Occlusion_Baked(cls):
        cls.add_node_group(".npr_Ambient Occlusion (Baked)")

    @classmethod
    def npr_Ambient_Occlusion_SS(cls):
        cls.add_node_group(".npr_Ambient Occlusion (SS)")

    @classmethod
    def add_Halftone_Style(cls):
        cls.add_node_group(".Halftone Style")

    @classmethod
    def add_Hatch_Style(cls):
        cls.add_node_group(".Hatch Style")

    @classmethod
    def add_Painterly_Style(cls):
        cls.add_node_group(".Painterly Style")

    @classmethod
    def add_Anisotropic_Style(cls):
        cls.add_node_group(".Anisotropic Style")

