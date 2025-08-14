import bpy
import os

bl_info = {
    "name": "Multires Projecting Toolset",
    "author": "Packsod",
    "version": (0, 9),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar > Multires Projecting",
    "description": "texture projection tool with support for multiple cameras",
    "warning": "",
    "doc_url": "https://github.com/Packsod/Multi-Camera-Projection-Toolset-Addon/tree/main",
    "category": "3D View",
}

categories = {
    "mp_vcol_bake": {"prop_name": "mp_vcol_bake_expanded", "operators": []},
    "mp_Combo_op": {"prop_name": "mp_Combo_op_expanded", "operators": []},
    "mp_cam_and_tex": {"prop_name": "mp_cam_and_tex_expanded", "operators": []},
    "mp_misc": {"prop_name": "mp_misc_expanded", "operators": []},
    "mp_shader": {"prop_name": "mp_shader_expanded", "operators": []},
    "mp_nodegroups": {"prop_name": "mp_nodegroups_expanded", "operators": []}, 
    # New category
}

class ScriptOperator(bpy.types.Operator):
    bl_label = ""
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        script_path = get_script_path(self.filepath)
        with open(script_path, 'r') as f:
            exec(f.read())
        return {'FINISHED'}

def create_operator_1(name, label, icon, script_name=None, def_name=None):
    operator_class = type(f"{name}_ot_operator", (ScriptOperator,), {
        "bl_idname": f"mp.{name.lower().replace(' ', '_')}_ot_operator",
        "bl_label": label,
        "icon": icon
    })
    if script_name and def_name:
        operator_class.filepath = script_name
        operator_class.execute = create_execute_method(def_name, script_name)
    else:
        operator_class.filepath = f"{name}___script.py"
    return operator_class

def create_operator_big(def_name, label, icon, script_name):
    op_name = def_name.replace('.', '_')
    operator_class = type(f"{op_name}_ot_operator", (ScriptOperator,), {
        "bl_idname": f"mp.{op_name.lower().replace(' ', '_')}",
        "bl_label": label,
        "icon": icon,
        "filepath": script_name,
        "execute": create_execute_method(def_name, script_name)
    })
    return operator_class

def create_operator_2(def_name, label, icon):
    return create_operator_big(def_name, label, icon, "Combo_op___script.py")

def create_operator_3(def_name, label, icon):
    return create_operator_big(def_name, label, icon, "Cam_op___script.py")

def create_operator_4(def_name, label, icon):
    return create_operator_big(def_name, label, icon, "misc_op___script.py")

def create_operator_5(def_name, label, icon):
    return create_operator_big(def_name, label, icon, "shader_op___script.py")

def create_operator_6(def_name, label):
    return create_operator_big(def_name, label, 'NONE', "shader_nodegroups___script.py")



def create_execute_method(def_name, script_name):
    def execute(self, context):
        script_path = get_script_path(self.filepath)
        with open(script_path, 'r') as f:
            script_code = f.read()
        script_globals = {}
        exec(compile(script_code, script_path, 'exec'), script_globals)
        eval(f"{def_name}()", script_globals)
        return {'FINISHED'}
    return execute

def get_script_path(script_name):
    try:
        blend_file_dir = os.path.dirname(bpy.data.filepath)
        script_path = os.path.join(blend_file_dir, 'py', script_name)

        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"The script file '{script_name}' was not found.")

    except (NameError, FileNotFoundError):
        current_file_path = os.path.abspath(__file__)
        current_file_dir = os.path.dirname(current_file_path)
        script_path = os.path.join(current_file_dir, 'py', script_name)

    return os.path.abspath(script_path)

class MP_NODEGROUPS_MT_Menu(bpy.types.Menu):
    bl_label = "mp_nodegroups"
    bl_idname = "MP_NODEGROUPS_MT_menu"

    def draw(self, context):
        layout = self.layout
        separator_positions = categories["mp_nodegroups"]["layout.separator"]
        for i, operator in enumerate(categories["mp_nodegroups"]["operators"]):
            layout.operator(operator.bl_idname, text=operator.bl_label).filepath = operator.filepath
            if i in separator_positions:
                layout.separator()



class MultiresProjectingPanel(bpy.types.Panel):
    bl_label = "Multires Projecting Toolset v0.5"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multires Projecting"

    def draw(self, context):
        layout = self.layout
        space_type = context.space_data.type

        # Draw operators for 3D Viewport
        if space_type == 'VIEW_3D':
            self.draw_panel(layout, context, ["mp_vcol_bake", "mp_Combo_op", "mp_cam_and_tex", "mp_misc"])

        # Draw operators for Node Editor and Shader Editor
        elif space_type in {'NODE_EDITOR', 'SHADER_EDITOR'}:
            self.draw_panel(layout, context, ["mp_shader"])

    def draw_panel(self, layout, context, category_names):
        for category_name in category_names:
            category = categories[category_name]
            box = layout.box()
            row = box.row()
            row.alignment = 'EXPAND'
            row.prop(context.scene, category["prop_name"], icon="TRIA_DOWN" if getattr(context.scene, category["prop_name"]) else "TRIA_RIGHT", emboss=False, text=category_name)
            if getattr(context.scene, category["prop_name"]):
                col = box.column(align=True)
                i = 0
                for title, size in category.get("row_data", []):
                    if size == 0:
                        # Add an empty column as a placeholder with increased gap
                        col.separator(factor=1.5)
                    else:
                        operator_row = category["operators"][i:i + size]
                        if title:
                            col.label(text=title)
                        row = col.row(align=True)
                        for operator in operator_row:
                            row.operator(operator.bl_idname, text=operator.bl_label, icon=operator.icon).filepath = operator.filepath
                        i += size # Move the index update here to avoid double printing



categories["mp_vcol_bake"]["operators"] = [
    create_operator_1("Vcol_GI_bake", "GI bake ", "EXPERIMENTAL"),
    create_operator_1("Vcol_AO_bake", "AO bake", "MATSHADERBALL"),
    create_operator_1("Vcol_combine_bake", "combine bake", "NODE_MATERIAL"),
    create_operator_1("misc_prepare_for_NPR_light_bake", "prepare for NPR light bake", "SETTINGS"),
]

categories["mp_vcol_bake"]["row_data"] = [
    ("", 1),
    ("", 1),
    ("", 1),
    ("", 1),
]


categories["mp_shader"]["operators"] = [
    create_operator_1("shader_auto_projection_helper", "auto projection helper", "BLENDER"),
    create_operator_1("shader_apply_tex_adijust", "apply tex adijust for billboard", "TEXTURE_DATA"),
    
    
    create_operator_5("shader_NPR_bake_helper_toggle", "NPR bake helper toggle", "SCRIPT"),
    create_operator_5("shader_alphaSet.Mesh_Pass_Index_Switch", "mesh_index_mask_Switch", "OUTLINER_OB_POINTCLOUD"),
    create_operator_5("shader_add_del_aov_for_each_mat", "aov all toggle add/del", "NODE_COMPOSITING"),  
    create_operator_5("shader_NPR_clay_debug_on_off", "npr_clay_debug toggle", "NODE_COMPOSITING"),  
    create_operator_5("shader_camera_tex_link_toggle", "camera tex link toggle", "LINKED"),
    
    
    create_operator_2("shader_mask.CamP_set__1", "", "STRIP_COLOR_01"),
    create_operator_2("shader_mask.CamP_set__2", "", "STRIP_COLOR_02"),
    create_operator_2("shader_mask.CamP_set__3", "", "STRIP_COLOR_03"),
    create_operator_2("shader_mask.CamP_set__4", "", "STRIP_COLOR_04"),
    create_operator_2("shader_mask.CamP_set__5", "", "STRIP_COLOR_05"),
    create_operator_2("shader_mask.CamP_set__6", "", "STRIP_COLOR_06"),
    create_operator_2("shader_mask.CamP_set__7", "", "STRIP_COLOR_07"),
    create_operator_2("shader_mask.CamP_set__8", "", "STRIP_COLOR_08"),
    create_operator_2("shader_mask.CamP_set__unlink", "", "UNLINKED"),
    
    create_operator_2("shader_mask.CamP_opacity__100", "", "DOT"),
    create_operator_2("shader_mask.CamP_opacity__90", "", "DOT"),
    create_operator_2("shader_mask.CamP_opacity__80", "", "DOT"),
    create_operator_2("shader_mask.CamP_opacity__70", "", "DOT"),
    create_operator_2("shader_mask.CamP_opacity__60", "", "DOT"),
    create_operator_2("shader_mask.CamP_opacity__50", "", "DOT"),
    create_operator_2("shader_mask.CamP_opacity__40", "", "DOT"),
    create_operator_2("shader_mask.CamP_opacity__30", "", "DOT"),
    create_operator_2("shader_mask.CamP_opacity__20", "", "DOT"),
    
    create_operator_2("adij_mask.ADIJ_set__1", "", "STRIP_COLOR_01"),
    create_operator_2("adij_mask.ADIJ_set__2", "", "STRIP_COLOR_02"),
    create_operator_2("adij_mask.ADIJ_set__3", "", "STRIP_COLOR_03"),
    create_operator_2("adij_mask.ADIJ_set__4", "", "STRIP_COLOR_04"),
    create_operator_2("adij_mask.ADIJ_set__5", "", "STRIP_COLOR_05"),
    create_operator_2("adij_mask.ADIJ_set__6", "", "STRIP_COLOR_06"),
    create_operator_2("adij_mask.ADIJ_set__7", "", "STRIP_COLOR_07"),
    create_operator_2("adij_mask.ADIJ_set__8", "", "STRIP_COLOR_08"),
    create_operator_2("adij_mask.ADIJ_set__unlink", "", "UNLINKED"),
    
    create_operator_5("shader_reset_CURVE_RGB_curves", "reset RGB curve node", "IPO_LINEAR"),
    
    create_operator_2("Shader_VisibilityKey.update", "", "FILE_REFRESH"),
    create_operator_2("Shader_VisibilityKey.hide1by1", "hide", "HIDE_ON"),
    create_operator_2("Shader_VisibilityKey.show1by1", "show", "HIDE_OFF"),   
]

categories["mp_shader"]["row_data"] = [
    ("main", 1),
    ("", 1),
    ("", 0),
    ("toggle", 1),
    ("", 1),
    ("", 1),
    ("", 1),
    ("", 1),
    ("", 0),
    ("CamID mask set", 9),
    ("CamID opacity set", 9),
    ("adijust mask set", 9),
    ("", 0),
    ("op for selected nodes", 1),
    ("insert CamP_ID_visibility key", 3),
]


categories["mp_misc"]["operators"] = [
    create_operator_1("misc_render_test_anim", "render test anim", "RENDER_ANIMATION"),
    create_operator_1("misc_render_frames", "render frames", "RENDER_ANIMATION"),
    
    create_operator_1("misc_empty_to_image_plane", "ref img to mesh", "IMAGE_RGB"),
    create_operator_4("misc.clear_custom_props", "clear custom props", "TRASH"),
    create_operator_1("misc_invisible_vertex_checker", "check invisible vertex", "NORMALS_FACE"),

    create_operator_4("misc.UV_sets_all", "UV set all", "UV"),
    create_operator_1("misc_set_scene", "scene set", "SCENE_DATA"),
]

categories["mp_misc"]["row_data"] = [
    ("", 1),
    ("", 1),
    ("", 0),
    ("Object-oriented", 1),
    ("", 1),
    ("", 1),
    ("", 0),
    ("", 1),
    ("", 1),
]


categories["mp_cam_and_tex"]["operators"] = [
    create_operator_1("tex_projecting_overpaint", "project to obj(img)", "RENDER_RESULT"),
    create_operator_1("tex_quick_reload_overpaint", "", "RECOVER_LAST"),
    create_operator_1("tex_quick_save_overpaint", "", "FILE_TICK"),
    
    create_operator_1("tex_projecting_vid_overpaint", "project to obj(vid)", "RENDER_RESULT"),
    create_operator_3("Placeholder.nothing", "", "BLANK1"),
    create_operator_3("Placeholder.nothing", "", "BLANK1"),
  
    create_operator_3("Cam_Visibility.hide_current_object", "1by1", "HIDE_ON"),
    create_operator_3("Cam_Visibility.hide_all_objects", "all", "HIDE_ON"),
    create_operator_3("Cam_Visibility.show_all_objects", "all","HIDE_OFF"),
    
    create_operator_1("Cam_CamP_render", "CN img export", "EXPORT"),
    create_operator_3("Cam_Switch.CamP_fit_to_active", "active → CamP", "OUTLINER_OB_CAMERA"),
    
    create_operator_1("Cam_CamP_save", "backup CamP", "FILE_TEXT"),
    create_operator_1("Cam_CamP_restore", "restore CamP", "FILE_TEXT"),
    
    create_operator_3("Cam_Main.MainCam_Switch", "Switch", "OUTLINER_OB_CAMERA"),
    create_operator_3("Cam_Main.MainCam_Action_Bake", "Action Bake", "OUTLINER_OB_CAMERA"),
    
    create_operator_3("Cam_Mist.set_distance", "set mist keyframes", "KEY_HLT"),
    
    create_operator_3("Cam_Switch.QShot_combine", "QShot combine", "OUTLINER_OB_CAMERA"),
]

categories["mp_cam_and_tex"]["row_data"] = [
    ("overpaint", 3),
    ("", 3),
    ("obj visibility -frames", 3),
    ("", 0),
    ("CamP operations", 1),
    ("", 1),   
    ("", 2),
    ("", 0),
    ("Main Cam operations", 2),
    ("", 0),
    ("z-depth picker insert keys", 1),
    ("others", 1),
]


categories["mp_Combo_op"]["operators"] = [
    create_operator_2("vcol_mask.CamP_ID_1", " ", "STRIP_COLOR_01"),
    create_operator_2("vcol_mask.CamP_ID_2", " ", "STRIP_COLOR_02"),
    create_operator_2("vcol_mask.CamP_ID_3", " ", "STRIP_COLOR_03"),
    create_operator_2("vcol_mask.CamP_ID_4", " ", "STRIP_COLOR_04"),
    create_operator_2("vcol_mask.CamP_ID_5", " ", "STRIP_COLOR_05"),
    create_operator_2("vcol_mask.CamP_ID_6", " ", "STRIP_COLOR_06"),
    create_operator_2("vcol_mask.CamP_ID_7", " ", "STRIP_COLOR_07"),
    create_operator_2("vcol_mask.CamP_ID_8", " ", "STRIP_COLOR_08"),
    create_operator_2("vcol_mask.CamP_ID_toggle", " ", "HIDE_OFF"),
    create_operator_2("vcol_mask.CamP_ID_delete", " ", "TRASH"),

    create_operator_2("vcol_mask.col_adijust_1", " ", "STRIP_COLOR_01"),
    create_operator_2("vcol_mask.col_adijust_2", " ", "STRIP_COLOR_02"),
    create_operator_2("vcol_mask.col_adijust_3", " ", "STRIP_COLOR_03"),
    create_operator_2("vcol_mask.col_adijust_4", " ", "STRIP_COLOR_04"),
    create_operator_2("vcol_mask.col_adijust_5", " ", "STRIP_COLOR_05"),
    create_operator_2("vcol_mask.col_adijust_6", " ", "STRIP_COLOR_06"),
    create_operator_2("vcol_mask.col_adijust_7", " ", "STRIP_COLOR_07"),
    create_operator_2("vcol_mask.col_adijust_8", " ", "STRIP_COLOR_08"),
    create_operator_2("vcol_mask.col_adijust_toggle", " ", "HIDE_OFF"),    
    create_operator_2("vcol_mask.col_adijust_delete", " ", "TRASH"),

    create_operator_2("vcol_mix.lighten", "Lighten", "PROP_ON"),
    create_operator_2("vcol_mix.softlight", "Softlight", "PROP_CON"),
    create_operator_2("vcol_mix.darken", "Darken", "LAYER_USED"),

    create_operator_2("vcol_mix.remove_lighten", "X", "PROP_ON"),
    create_operator_2("vcol_mix.remove_softlight", "X", "PROP_CON"),
    create_operator_2("vcol_mix.remove_darken", "X", "LAYER_USED"),

    create_operator_2("vcol_mix.cel_highlight", "hgl", "NODE_SOCKET_COLLECTION"),
    create_operator_2("vcol_mix.cel_littone", "lit", "NODE_SOCKET_COLLECTION"),
    create_operator_2("vcol_mix.cel_midtone", "mid", "NODE_SOCKET_FLOAT"),
    create_operator_2("vcol_mix.cel_darktone", "dim", "NODE_SOCKET_MENU"),
    create_operator_2("vcol_mix.cel_ambient", "amb", "NODE_SOCKET_COLLECTION"),

    create_operator_2("vcol_mix.remove_highlight", "X", "NODE_SOCKET_COLLECTION"),
    create_operator_2("vcol_mix.remove_littone", "X", "NODE_SOCKET_COLLECTION"),
    create_operator_2("vcol_mix.remove_midtone", "X", "NODE_SOCKET_FLOAT"),
    create_operator_2("vcol_mix.remove_darktone", "X", "NODE_SOCKET_MENU"),
    create_operator_2("vcol_mix.remove_ambient", "X", "NODE_SOCKET_COLLECTION"),
    
    create_operator_1("obj_region_ID_assign", "assign to obj", "COPY_ID"),
    create_operator_2("vcol_mask.region_ID_toggle", "", "HIDE_OFF"),
]

categories["mp_Combo_op"]["row_data"] = [
    ("CamP ID mask", 10),
    ("color adijust mask", 10),
    ("", 0),
    ("paint mix layer active", 3),
    ("paint mix layer remove", 3),
    ("", 0),
    ("cel colors active", 5),
    ("cel colors remove", 5),
    ("", 0),
    ("region color ID", 2),
]


categories["mp_nodegroups"]["operators"] = [   
    create_operator_5("shader_add_gradient_mask", "gradient mask add", "MOD_MASK"), 
    create_operator_6("ShaderAdder.npr_Key_Light", ".npr_Key Light"),
    create_operator_6("ShaderAdder.npr_Specular", ".npr_Specular"),
    create_operator_6("ShaderAdder.npr_Virtual_Point_Light", ".npr_Virtual Point Light"),
    create_operator_6("ShaderAdder.npr_Virtual_Spot_Light", ".npr_Virtual Spot Light"),
    create_operator_6("ShaderAdder.npr_Virtual_Sun_Light", ".npr_Virtual Sun Light"),
#4
    create_operator_6("ShaderAdder.npr_layer_mix_shader", ".(09) npr_layer_mix_shader"),
    create_operator_6("ShaderAdder.npr_Color", ".npr_Color"),
    create_operator_6("ShaderAdder.npr_Layer_Adjustment", ".npr_Layer Adjustment"),
    create_operator_6("ShaderAdder.npr_Global_Color", ".npr_Global Color"),
#8        
    create_operator_6("ShaderAdder.npr_Linear_Gradient", ".npr_Linear Gradient"),
    create_operator_6("ShaderAdder.npr_Spherical_Gradient", ".npr_Spherical Gradient"),
    create_operator_6("ShaderAdder.npr_Local_Gradient", ".npr_Local Gradient"),
    create_operator_6("ShaderAdder.npr_Z_Depth", ".npr_Z Depth"),
#12
    create_operator_6("ShaderAdder.npr_2D_Outline", ".npr_2D Outline"),
    create_operator_6("ShaderAdder.npr_2D_Rim_Light", ".npr_2D Rim Light",),
    create_operator_6("ShaderAdder.npr_2D_Specular", ".npr_2D Specular"),
    create_operator_6("ShaderAdder.npr_Matcap", ".npr_Matcap"),
#16
    create_operator_6("ShaderAdder.npr_Ambient_Occlusion_Baked", ".npr_Ambient Occlusion (Baked)"),
    create_operator_6("ShaderAdder.npr_Ambient_Occlusion_SS", ".npr_Ambient Occlusion (SS)"),
#18
    create_operator_6("ShaderAdder_add_Halftone_Style", ".Halftone Style"),
    create_operator_6("ShaderAdder_add_Hatch_Style", ".Hatch Style"),
    create_operator_6("ShaderAdder_add_Painterly_Style", ".Painterly Style"),
    create_operator_6("ShaderAdder_add_Anisotropic_Style", ".Anisotropic Style"),
]

categories["mp_nodegroups"]["layout.separator"] =[4, 8, 12, 16, 18]

for category in categories.values():
    setattr(bpy.types.Scene, category["prop_name"], bpy.props.BoolProperty(name="", default=True))

mp = type("mp_PT_panel", (MultiresProjectingPanel,), {"bl_idname": "mp_PT_panel", "bl_label": "Multires Projecting Toolset v0.5"})
mp_shader = type("mp_SHADER_PT_panel", (MultiresProjectingPanel,), {"bl_idname": "mp_SHADER_PT_panel", "bl_label": "Multires Projecting Shader", "bl_space_type": 'NODE_EDITOR'})


_registered_classes = []

def register():
    global _registered_classes
    try:
        unregister()
    except Exception:
        pass
    cls = []
    for category in categories.values():
        for operator in category["operators"]:
            bpy.utils.register_class(operator)
            cls.append(operator)
    bpy.utils.register_class(mp)
    cls.append(mp)
    bpy.utils.register_class(mp_shader)
    cls.append(mp_shader)
    bpy.utils.register_class(MP_NODEGROUPS_MT_Menu)
    cls.append(MP_NODEGROUPS_MT_Menu)
    if not any(draw_mp_nodegroups_menu.__name__ == f.__name__ for f in bpy.types.NODE_MT_add._dyn_ui_initialize()):
        bpy.types.NODE_MT_add.append(draw_mp_nodegroups_menu)
    _registered_classes = cls

def unregister():
    global _registered_classes
    if hasattr(bpy.types.NODE_MT_add, "_dyn_ui_initialize"):
        for f in bpy.types.NODE_MT_add._dyn_ui_initialize():
            if f.__name__ == draw_mp_nodegroups_menu.__name__:
                bpy.types.NODE_MT_add.remove(f)
    for c in reversed(_registered_classes):
        try:
            bpy.utils.unregister_class(c)
        except Exception:
            pass
    _registered_classes.clear()

def draw_mp_nodegroups_menu(self, context):
    self.layout.separator()
    self.layout.menu(MP_NODEGROUPS_MT_Menu.bl_idname)

if __name__ == "__main__":
    register()
