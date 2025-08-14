import bpy

class ColorPreset:
    @staticmethod
    def hex_to_rgb(hex_value):
        hex_color = hex_value[1:]
        r = int(hex_color[:2], base=16) / 255.0
        g = int(hex_color[2:4], base=16) / 255.0
        b = int(hex_color[4:6], base=16) / 255.0
        return tuple([r, g, b])

    Col_0 = hex_to_rgb("#000000")
    Col_1 = hex_to_rgb("#e1605b")
    Col_2 = hex_to_rgb("#f0a255")
    Col_3 = hex_to_rgb("#f0db55")
    Col_4 = hex_to_rgb("#7acb7a")
    Col_5 = hex_to_rgb("#5db5e9")
    Col_6 = hex_to_rgb("#8c59d9")
    Col_7 = hex_to_rgb("#c572b7")
    Col_8 = hex_to_rgb("#795441")

# vcol_mask module
class vcol_mask:
    @staticmethod
    def get_shading_settings():
        return (bpy.context.space_data.shading.type,
                bpy.context.space_data.shading.light,
                bpy.context.space_data.shading.color_type)

    @staticmethod
    def toggle_script(colname=None):
        if colname is None:
            colname = "REGION_ID"# special value "REGION_ID" is a placeholder value not an actual value.
        if ('script_state' in bpy.context.window_manager and
                bpy.context.window_manager['script_state'] and
                'colname' in bpy.context.window_manager and
                bpy.context.window_manager['colname'] == colname):
            # The script is already active with the same colname, so we need to reset the viewport settings.
            if 'settings_before_toggle' in bpy.context.window_manager:
                settings = bpy.context.window_manager['settings_before_toggle']
                bpy.context.space_data.shading.type, bpy.context.space_data.shading.light, bpy.context.space_data.shading.color_type = settings
                del bpy.context.window_manager['settings_before_toggle']
            if 'colname' in bpy.context.window_manager:
                del bpy.context.window_manager['colname']
            bpy.context.window_manager['script_state'] = False
            return
        # The script is not currently active, or it's active with a different colname, so we need to apply the new settings.
        settings = vcol_mask.get_shading_settings()
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.light = 'FLAT'
        if colname != "REGION_ID":
            bpy.context.space_data.shading.color_type = 'VERTEX'
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and colname in obj.data.vertex_colors:
                    obj.data.vertex_colors.active = obj.data.vertex_colors[colname]
        else:
            bpy.context.space_data.shading.color_type = 'OBJECT'
        if 'settings_before_toggle' not in bpy.context.window_manager:
            bpy.context.window_manager['settings_before_toggle'] = settings
        bpy.context.window_manager['colname'] = colname
        bpy.context.window_manager['script_state'] = True

    @staticmethod
    def region_ID_toggle():
        vcol_mask.toggle_script()

    @staticmethod
    def CamP_ID_toggle():
        vcol_mask.toggle_script("mask_CamP_ID")

    @staticmethod
    def col_adijust_toggle():
        vcol_mask.toggle_script("mask_col_adijust")

    def CamP_ID_1():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_CamP_ID', ColorPreset.Col_1)

    def CamP_ID_2():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_CamP_ID', ColorPreset.Col_2)

    def CamP_ID_3():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_CamP_ID', ColorPreset.Col_3)

    def CamP_ID_4():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_CamP_ID', ColorPreset.Col_4)

    def CamP_ID_5():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_CamP_ID', ColorPreset.Col_5)

    def CamP_ID_6():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_CamP_ID', ColorPreset.Col_6)

    def CamP_ID_7():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_CamP_ID', ColorPreset.Col_7)

    def CamP_ID_8():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_CamP_ID', ColorPreset.Col_8)

    def CamP_ID_delete():
        bpy.ops.ed.undo_push()
        vcol_mask.delete_mask('mask_CamP_ID')

    def col_adijust_1():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_col_adijust', ColorPreset.Col_1)

    def col_adijust_2():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_col_adijust', ColorPreset.Col_2)

    def col_adijust_3():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_col_adijust', ColorPreset.Col_3)

    def col_adijust_4():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_col_adijust', ColorPreset.Col_4)

    def col_adijust_5():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_col_adijust', ColorPreset.Col_5)

    def col_adijust_6():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_col_adijust', ColorPreset.Col_6)

    def col_adijust_7():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_col_adijust', ColorPreset.Col_7)

    def col_adijust_8():
        bpy.ops.ed.undo_push()
        vcol_mask.set_mask('mask_col_adijust', ColorPreset.Col_8)
        
    def col_adijust_delete():
        bpy.ops.ed.undo_push()
        vcol_mask.delete_mask('mask_col_adijust')

    @staticmethod
    def set_mask(colname, set_col):
        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']
        current_mode = bpy.context.mode
        active_object = bpy.context.view_layer.objects.active
        if current_mode == 'EDIT_MESH':
            for obj in selected_meshes:
                bpy.context.view_layer.objects.active = obj
                mesh = obj.data
                if colname not in mesh.vertex_colors:
                    mesh.vertex_colors.new(name=colname)
                # activate vertex color attribute
                bpy.context.object.data.vertex_colors.active = mesh.vertex_colors[colname]
                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                bpy.context.scene.tool_settings.unified_paint_settings.color = set_col
                bpy.context.scene.tool_settings.vertex_paint.brush.color = set_col
                bpy.context.active_object.data.use_paint_mask = True
                bpy.ops.paint.vertex_color_set(use_alpha=False)
                bpy.context.active_object.data.use_paint_mask = False
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.view_layer.objects.active = active_object
        else:
            for obj in selected_meshes:
                bpy.context.view_layer.objects.active = obj
                mesh = obj.data
                if colname not in mesh.vertex_colors:
                    mesh.vertex_colors.new(name=colname)
                    # set alpha to 0 when creating new attribute
                    for loop_index in range(len(mesh.loops)):
                        mesh.vertex_colors[colname].data[loop_index].color = set_col + (0,)
                else:
                    # activate vertex color attribute
                    bpy.context.object.data.vertex_colors.active = mesh.vertex_colors[colname]
                    for loop_index in range(len(mesh.loops)):
                        color = list(mesh.vertex_colors[colname].data[loop_index].color)
                        color[:3] = set_col
                        mesh.vertex_colors[colname].data[loop_index].color = color

    @staticmethod
    def delete_mask(colname):
        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']
        current_mode = bpy.context.mode
        active_object = bpy.context.view_layer.objects.active
        if current_mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
        for obj in selected_meshes:
            bpy.context.view_layer.objects.active = obj
            mesh = obj.data
            if colname in mesh.vertex_colors:
                # activate vertex color attribute
                bpy.context.object.data.vertex_colors.active = mesh.vertex_colors[colname]
                if current_mode == 'EDIT_MESH':
                    bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                    bpy.context.scene.tool_settings.unified_paint_settings.color = (1, 1, 1)
                    bpy.context.scene.tool_settings.vertex_paint.brush.color = (1, 1, 1)
                    bpy.context.active_object.data.use_paint_mask = True
                    bpy.ops.paint.vertex_color_set(use_alpha=False)
                    bpy.context.active_object.data.use_paint_mask = False
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.context.view_layer.objects.active = active_object
                else:
                    mesh.vertex_colors.remove(mesh.vertex_colors[colname])
                    


# vcol_mix module
class vcol_mix:
    def lighten():
        colname = 'mix_lighten'
        set_col = (0.0, 0.0, 0.0, 0.0)
        vcol_mix.process_color_attribute(colname, set_col)

    def softlight():
        colname = 'mix_softlight'
        set_col = (0.5, 0.5, 0.5, 0.0)
        vcol_mix.process_color_attribute(colname, set_col)

    def darken():
        colname = 'mix_darken'
        set_col = (1.0, 1.0, 1.0, 0.0)
        vcol_mix.process_color_attribute(colname, set_col)

    def remove_lighten():
        colname = 'mix_lighten'
        vcol_mix.remove_color_attribute(colname)

    def remove_softlight():
        colname = 'mix_softlight'
        vcol_mix.remove_color_attribute(colname)

    def remove_darken():
        colname = 'mix_darken'
        vcol_mix.remove_color_attribute(colname)


    @staticmethod
    def ensure_object_mode():
        """Switch to Object mode and return the previous mode name."""
        prev_mode = bpy.context.object.mode
        if prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        return prev_mode

    @staticmethod
    def back_to_mode(prev_mode):
        """Return to the previous mode (if not OBJECT)."""
        if prev_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode=prev_mode)
            except Exception as e:
                print(f"Failed to switch back to mode: {prev_mode}, Error: {e}")

    @staticmethod
    def cel_highlight():
        colname = 'cel_hgl'

        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']

        for o in selected_meshes:
            bpy.context.view_layer.objects.active = o
            mesh = o.data

            # Ensure Blender is in Object mode before attempting operations
            prev_mode = vcol_mask.ensure_object_mode()

            if colname not in mesh.color_attributes:
                if 'cel_lit' in mesh.color_attributes:
                    mesh.color_attributes.active_color = mesh.color_attributes['cel_lit']
                    bpy.ops.geometry.color_attribute_duplicate()
                    mesh.color_attributes[-1].name = colname
                else:
                    ca = mesh.color_attributes.new(
                        name=colname,
                        domain='CORNER',
                        type='BYTE_COLOR'
                    )
                    for elem in ca.data:
                        elem.color = (1.0, 1.0, 1.0, 1.0)  # Default highlight color

            mesh.color_attributes.active_color = mesh.color_attributes[colname]

            # Return to the previous mode if needed
            vcol_mask.back_to_mode(prev_mode)

    @staticmethod
    def cel_littone():
        colname = 'cel_lit'
        default_color = (1.0, 1.0, 1.0, 1.0)  # 0~1

        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']

        for o in selected_meshes:
            bpy.context.view_layer.objects.active = o
            mesh = o.data

            # Ensure Blender is in Object mode before attempting operations
            prev_mode = vcol_mix.ensure_object_mode()

            if colname not in mesh.color_attributes:
                if 'cel_mid' in mesh.color_attributes:
                    mesh.color_attributes.active_color = mesh.color_attributes['cel_mid']
                    bpy.ops.geometry.color_attribute_duplicate()
                    mesh.color_attributes[-1].name = colname
                else:
                    ca = mesh.color_attributes.new(
                        name=colname,
                        domain='CORNER',
                        type='BYTE_COLOR'
                    )
                    for elem in ca.data:
                        elem.color = default_color

            mesh.color_attributes.active_color = mesh.color_attributes[colname]

            # Return to the previous mode if needed
            vcol_mix.back_to_mode(prev_mode)

    @staticmethod
    def cel_midtone():
        colname = 'cel_mid'
        default_color = (0.5, 0.5, 0.5, 1.0)

        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']

        for o in selected_meshes:
            bpy.context.view_layer.objects.active = o
            mesh = o.data

            # Ensure Blender is in Object mode before attempting operations
            prev_mode = vcol_mix.ensure_object_mode()

            if 'cel_mid' not in mesh.color_attributes:
                ca = mesh.color_attributes.new(
                    name=colname,
                    domain='CORNER',
                    type='BYTE_COLOR'
                )
                for elem in ca.data:
                    elem.color = default_color

            mesh.color_attributes.active_color = mesh.color_attributes['cel_mid']

            # Return to the previous mode if needed
            vcol_mix.back_to_mode(prev_mode)

    @staticmethod
    def cel_darktone():
        colname = 'cel_dim'
        default_color = (0.1, 0.1, 0.1, 1.0)

        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']

        for o in selected_meshes:
            bpy.context.view_layer.objects.active = o
            mesh = o.data

            # Ensure Blender is in Object mode before attempting operations
            prev_mode = vcol_mix.ensure_object_mode()

            if colname not in mesh.color_attributes:
                if 'cel_mid' in mesh.color_attributes:
                    mesh.color_attributes.active_color = mesh.color_attributes['cel_mid']
                    bpy.ops.geometry.color_attribute_duplicate()
                    mesh.color_attributes[-1].name = colname
                else:
                    ca = mesh.color_attributes.new(
                        name=colname,
                        domain='CORNER',
                        type='BYTE_COLOR'
                    )
                    for elem in ca.data:
                        elem.color = default_color

            mesh.color_attributes.active_color = mesh.color_attributes[colname]

            # Return to the previous mode if needed
            vcol_mix.back_to_mode(prev_mode)

    @staticmethod
    def cel_ambient():
        colname = 'cel_amb'
        default_color = (0.2, 0.2, 0.2, 1.0)  # Default ambient color

        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']

        for o in selected_meshes:
            bpy.context.view_layer.objects.active = o
            mesh = o.data

            # Ensure Blender is in Object mode before attempting operations
            prev_mode = vcol_mask.ensure_object_mode()

            if colname not in mesh.color_attributes:
                if 'cel_dim' in mesh.color_attributes:
                    mesh.color_attributes.active_color = mesh.color_attributes['cel_dim']
                    bpy.ops.geometry.color_attribute_duplicate()
                    mesh.color_attributes[-1].name = colname
                else:
                    ca = mesh.color_attributes.new(
                        name=colname,
                        domain='CORNER',
                        type='BYTE_COLOR'
                    )
                    for elem in ca.data:
                        elem.color = default_color

            mesh.color_attributes.active_color = mesh.color_attributes[colname]

            # Return to the previous mode if needed
            vcol_mask.back_to_mode(prev_mode)

    def remove_highlight():
        colname = 'cel_hgl'
        vcol_mix.remove_color_attribute(colname)

    def remove_littone():
        colname = 'cel_lit'
        vcol_mix.remove_color_attribute(colname)

    def remove_midtone():
        colname = 'cel_mid'
        vcol_mix.remove_color_attribute(colname)

    def remove_darktone():
        colname = 'cel_dim'
        vcol_mix.remove_color_attribute(colname)

    def remove_ambient():
        colname = 'cel_amb'
        vcol_mix.remove_color_attribute(colname)

    def process_color_attribute(colname, set_col):
        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']

        for o in selected_meshes:
            if not o.data.color_attributes.get(colname):
                bpy.context.view_layer.objects.active = o
                o.data.color_attributes.new(name=colname, type='FLOAT_COLOR', domain='CORNER')
                color_attribute = o.data.color_attributes[colname]
                data = color_attribute.data
                for i in range(len(data)):
                    data[i].color = set_col
                o.data.update()

            bpy.context.view_layer.objects.active = o
            o.data.color_attributes.active_color = o.data.color_attributes[colname]

    # Helper function to remove a single color attribute
    def remove_color_attribute(colname):
        selected_meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']

        for o in selected_meshes:
            if o.data.color_attributes.get(colname):
                bpy.context.view_layer.objects.active = o
                o.data.color_attributes.remove(o.data.color_attributes[colname])



class shader_mask:
    def __init__():
        shader_editor = next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)
        if shader_editor is None or shader_editor.node_tree is None:
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="No valid shader editor or material found"), title="Error", icon='ERROR')
            return
        nodes = shader_editor.node_tree.nodes
        links = shader_editor.node_tree.links
        return nodes, links

    def set_mask(custom_color, mask_id_output):
        result = shader_mask.__init__()
        if result is None:
            return
        nodes, links = result
        if not bpy.context.selected_nodes:
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="No nodes selected"), title="Error", icon='ERROR')
            return
        for node in bpy.context.selected_nodes:
            if node.name.startswith("projection_layer"):
                print(node.name)
                opacity_value = node.inputs['opacity'].default_value / 100
                brightness = shader_mask.calculate_brightness(custom_color)
                adjusted_color = shader_mask.adjust_brightness(custom_color, brightness * opacity_value)
                node.use_custom_color = True
                node.color = adjusted_color
                links.new(nodes['CamP_ID_mask'].outputs[mask_id_output], node.inputs['CamP_ID_mask_input'])
        return



    def CamP_set__1():
        custom_color = ColorPreset.Col_1
        mask_id_output = 'ID_mask_1'
        shader_mask.set_mask(custom_color, mask_id_output)

    def CamP_set__2():
        custom_color = ColorPreset.Col_2
        mask_id_output = 'ID_mask_2'
        shader_mask.set_mask(custom_color, mask_id_output)

    def CamP_set__3():
        custom_color = ColorPreset.Col_3
        mask_id_output = 'ID_mask_3'
        shader_mask.set_mask(custom_color, mask_id_output)

    def CamP_set__4():
        custom_color = ColorPreset.Col_4
        mask_id_output = 'ID_mask_4'
        shader_mask.set_mask(custom_color, mask_id_output)

    def CamP_set__5():
        custom_color = ColorPreset.Col_5
        mask_id_output = 'ID_mask_5'
        shader_mask.set_mask(custom_color, mask_id_output)

    def CamP_set__6():
        custom_color = ColorPreset.Col_6
        mask_id_output = 'ID_mask_6'
        shader_mask.set_mask(custom_color, mask_id_output)

    def CamP_set__7():
        custom_color = ColorPreset.Col_7
        mask_id_output = 'ID_mask_7'
        shader_mask.set_mask(custom_color, mask_id_output)

    def CamP_set__8():
        custom_color = ColorPreset.Col_8
        mask_id_output = 'ID_mask_8'
        shader_mask.set_mask(custom_color, mask_id_output)

    def CamP_set__unlink():
        Mask_ID_color = ColorPreset.Col_0
        result = shader_mask.__init__()
        if result is None:
            return
        nodes, links = result
        if not bpy.context.selected_nodes:
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="No nodes selected"), title="Error", icon='ERROR')
            return
        for node in bpy.context.selected_nodes:
            if node.name.startswith("projection_layer"):
                print(node.name)
                node.use_custom_color = True
                node.color = Mask_ID_color
                for link in node.inputs['CamP_ID_mask_input'].links:
                    links.remove(link)
        return

    def CamP_opacity__100():
        opacity_value = 1.0
        shader_mask.set_opacity_and_color(opacity_value)

    def CamP_opacity__90():
        opacity_value = 0.9
        shader_mask.set_opacity_and_color(opacity_value)

    def CamP_opacity__80():
        opacity_value = 0.8
        shader_mask.set_opacity_and_color(opacity_value)

    def CamP_opacity__70():
        opacity_value = 0.7
        shader_mask.set_opacity_and_color(opacity_value)

    def CamP_opacity__60():
        opacity_value = 0.6
        shader_mask.set_opacity_and_color(opacity_value)

    def CamP_opacity__50():
        opacity_value = 0.5
        shader_mask.set_opacity_and_color(opacity_value)

    def CamP_opacity__40():
        opacity_value = 0.4
        shader_mask.set_opacity_and_color(opacity_value)

    def CamP_opacity__30():
        opacity_value = 0.3
        shader_mask.set_opacity_and_color(opacity_value)

    def CamP_opacity__20():
        opacity_value = 0.2
        shader_mask.set_opacity_and_color(opacity_value)

    def set_opacity_and_color(opacity_value):
        result = shader_mask.__init__()
        if result is None:
            return
        nodes = result

        if not bpy.context.selected_nodes:
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="No nodes selected"), title="Error", icon='ERROR')
            return

        for node in bpy.context.selected_nodes:
            if node.name.startswith("projection_layer"):
                print(node.name)
                if 'opacity' in node.inputs:
                    import colorsys
                    hue = node.color.hsv[0]
                    r, g, b = shader_mask.hue_match_rgb(hue)
                    h, s, v = colorsys.rgb_to_hsv(r, g, b)
                    v *= opacity_value
                    r, g, b = colorsys.hsv_to_rgb(h, s, v)
                    node.color = (r, g, b)
                    node.inputs['opacity'].default_value = int(opacity_value * 100)
        return

    def rgb_to_hue(rgb_color):
        import colorsys
        r, g, b = rgb_color
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return h

    def hue_match_rgb(hue):
        hue_color_map = {
            shader_mask.rgb_to_hue(ColorPreset.Col_0): ColorPreset.Col_0,
            shader_mask.rgb_to_hue(ColorPreset.Col_1): ColorPreset.Col_1,
            shader_mask.rgb_to_hue(ColorPreset.Col_2): ColorPreset.Col_2,
            shader_mask.rgb_to_hue(ColorPreset.Col_3): ColorPreset.Col_3,
            shader_mask.rgb_to_hue(ColorPreset.Col_4): ColorPreset.Col_4,
            shader_mask.rgb_to_hue(ColorPreset.Col_5): ColorPreset.Col_5,
            shader_mask.rgb_to_hue(ColorPreset.Col_6): ColorPreset.Col_6,
            shader_mask.rgb_to_hue(ColorPreset.Col_7): ColorPreset.Col_7,
            shader_mask.rgb_to_hue(ColorPreset.Col_8): ColorPreset.Col_8
        }
        closest_hue = min(hue_color_map.keys(), key=lambda x: abs(x - hue))
        return hue_color_map[closest_hue]


    def calculate_brightness(color):
        r, g, b = color
        return max(r, g, b)

    def adjust_brightness(color, brightness):
        r, g, b = color
        factor = brightness / max(r, g, b)
        r *= factor
        g *= factor
        b *= factor
        return r, g, b


class adij_mask:
    @staticmethod
    def init():
        adij_mask_node_group = bpy.data.node_groups.get(".col_adij_mask")
        if not adij_mask_node_group:
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="'.col_adij_mask' node group not found. Please run 'set scene' first."), title="Error", icon='ERROR')
            return None
        shader_editor = next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)
        if shader_editor is None or shader_editor.node_tree is None:
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="No valid shader editor or material found"), title="Error", icon='ERROR')
            return None
        nodes = shader_editor.node_tree.nodes
        links = shader_editor.node_tree.links
        return nodes, links, adij_mask_node_group

    @staticmethod
    def is_factor_input(node):
        return any(input.name in ["Factor", "Fac"] for input in node.inputs)

    @staticmethod
    def set_mask(mask_id_output, custom_color):
        result = adij_mask.init()
        if result is None:
            return
        nodes, links, adij_mask_node_group = result
        selected_nodes = bpy.context.selected_nodes
        if not selected_nodes:
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="No nodes selected"), title="Error", icon='ERROR')
            return
        # Check if ".col_adij_mask" node group already exists in the nodes
        col_adij_mask_node = next((node for node in nodes if node.type == 'GROUP' and node.node_tree.name == ".col_adij_mask"), None)
        if not col_adij_mask_node:
            # If not, create a new one
            col_adij_mask_node = nodes.new('ShaderNodeGroup')
            col_adij_mask_node.node_tree = adij_mask_node_group
            col_adij_mask_node.location = bpy.context.region.view2d.region_to_view(bpy.context.region.width/2, bpy.context.region.height/2)
        bpy.ops.node.select_all(action='DESELECT')
        for node in selected_nodes:
            if adij_mask.is_factor_input(node):
                node.select = True
                node.use_custom_color = True
                node.color = custom_color
                input_socket = next(input for input in node.inputs if input.name in ["Factor", "Fac"])
                links.new(
                    col_adij_mask_node.outputs[mask_id_output],
                    input_socket
                )
            else:
                print(f"No input socket with name 'Factor' or 'Fac' found in node '{node.name}'")


    @staticmethod
    def ADIJ_set__1():
        custom_color = ColorPreset.Col_1
        mask_id_output = 0
        adij_mask.set_mask(mask_id_output, custom_color)

    @staticmethod
    def ADIJ_set__2():
        custom_color = ColorPreset.Col_2
        mask_id_output = 1
        adij_mask.set_mask(mask_id_output, custom_color)

    @staticmethod
    def ADIJ_set__3():
        custom_color = ColorPreset.Col_3
        mask_id_output = 2
        adij_mask.set_mask(mask_id_output, custom_color)

    @staticmethod
    def ADIJ_set__4():
        custom_color = ColorPreset.Col_4
        mask_id_output = 3
        adij_mask.set_mask(mask_id_output, custom_color)

    @staticmethod
    def ADIJ_set__5():
        custom_color = ColorPreset.Col_5
        mask_id_output = 4
        adij_mask.set_mask(mask_id_output, custom_color)

    @staticmethod
    def ADIJ_set__6():
        custom_color = ColorPreset.Col_6
        mask_id_output = 5
        adij_mask.set_mask(mask_id_output, custom_color)

    @staticmethod
    def ADIJ_set__7():
        custom_color = ColorPreset.Col_7
        mask_id_output = 6
        adij_mask.set_mask(mask_id_output, custom_color)

    @staticmethod
    def ADIJ_set__8():
        custom_color = ColorPreset.Col_8
        mask_id_output = 7
        adij_mask.set_mask(mask_id_output, custom_color)

    @staticmethod
    def ADIJ_set__unlink():
        Mask_ID_color = ColorPreset.Col_0
        result = adij_mask.init()
        if result is None:
            return
        nodes, links, adij_mask_node_group = result
        selected_nodes = bpy.context.selected_nodes
        if not selected_nodes:
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="No nodes selected"), title="Error", icon='ERROR')
            return
        bpy.ops.node.select_all(action='DESELECT')
        for node in selected_nodes:
            if adij_mask.is_factor_input(node):
                node.select = True
                node.use_custom_color = True
                node.color = Mask_ID_color
                for input in node.inputs:
                    if input.name in ["Factor", "Fac"]:
                        for link in input.links:
                            links.remove(link)
                        break


class Shader_VisibilityKey:
    frame_range = (-24, 1)

    @staticmethod
    def show_popup(message="", title="Message", icon='INFO'):
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

    @staticmethod
    def insert_keyframe_on_node(node, value, frame_range, scene, current_frame):
        if node:
            if frame_range[0] <= current_frame <= frame_range[1]:
                node.inputs["show/hide 0/1"].default_value = value
                node.inputs["show/hide 0/1"].keyframe_insert(data_path="default_value")
                scene.frame_set(current_frame + 1)
                current_frame += 1
            else:
                Shader_VisibilityKey.show_popup(message=f"Current frame {current_frame} is outside the defined range.", title="Warning", icon='ERROR')
        else:
            Shader_VisibilityKey.show_popup(message="Please select the .CamP_ID_visibility node group.", title="Error", icon='ERROR')
        return current_frame

    @staticmethod
    def update():
        scene = bpy.context.scene
        original_frame = scene.frame_current
        shader_editor = next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)
        node_group = bpy.data.node_groups.get(".CamP_ID_visibility")
        node = None
        if shader_editor and node_group:
            if shader_editor.edit_tree.nodes.active and shader_editor.edit_tree.nodes.active.type == "GROUP" and shader_editor.edit_tree.nodes.active.node_tree == node_group:
                node = shader_editor.edit_tree.nodes.active
            else:
                Shader_VisibilityKey.show_popup(message="Please select the .CamP_ID_visibility node group.", title="Error", icon='ERROR')
        elif not shader_editor:
            Shader_VisibilityKey.show_popup(message="Could not find shader editor.", title="Error", icon='ERROR')
        elif not node_group:
            Shader_VisibilityKey.show_popup(message="Could not find .CamP_ID_visibility node group in shader editor.", title="Error", icon='ERROR')
        if node:
            for i in range(Shader_VisibilityKey.frame_range[0], Shader_VisibilityKey.frame_range[1]):
                scene.frame_set(i)
                if i in [marker.frame for marker in scene.timeline_markers] or i in {-24, -1}:
                    node.inputs["show/hide 0/1"].keyframe_insert(data_path="default_value")
        scene.frame_set(original_frame)

    @staticmethod
    def hide1by1():
        scene = bpy.context.scene
        current_frame = scene.frame_current
        shader_editor = next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)
        node_group = bpy.data.node_groups.get(".CamP_ID_visibility")
        node = None
        if shader_editor and node_group:
            if shader_editor.edit_tree.nodes.active and shader_editor.edit_tree.nodes.active.type == "GROUP" and shader_editor.edit_tree.nodes.active.node_tree == node_group:
                node = shader_editor.edit_tree.nodes.active
            else:
                Shader_VisibilityKey.show_popup(message="Please select the .CamP_ID_visibility node group.", title="Error", icon='ERROR')
        elif not shader_editor:
            Shader_VisibilityKey.show_popup(message="Could not find shader editor.", title="Error", icon='ERROR')
        elif not node_group:
            Shader_VisibilityKey.show_popup(message="Could not find .CamP_ID_visibility node group in shader editor.", title="Error", icon='ERROR')
        current_frame = Shader_VisibilityKey.insert_keyframe_on_node(node, value=1, frame_range=Shader_VisibilityKey.frame_range, scene=scene, current_frame=current_frame)
        return current_frame

    @staticmethod
    def show1by1():
        scene = bpy.context.scene
        current_frame = scene.frame_current
        shader_editor = next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)
        node_group = bpy.data.node_groups.get(".CamP_ID_visibility")
        node = None
        if shader_editor and node_group:
            if shader_editor.edit_tree.nodes.active and shader_editor.edit_tree.nodes.active.type == "GROUP" and shader_editor.edit_tree.nodes.active.node_tree == node_group:
                node = shader_editor.edit_tree.nodes.active
            else:
                Shader_VisibilityKey.show_popup(message="Please select the .CamP_ID_visibility node group.", title="Error", icon='ERROR')
        elif not shader_editor:
            Shader_VisibilityKey.show_popup(message="Could not find shader editor.", title="Error", icon='ERROR')
        elif not node_group:
            Shader_VisibilityKey.show_popup(message="Could not find .CamP_ID_visibility node group in shader editor.", title="Error", icon='ERROR')
        current_frame = Shader_VisibilityKey.insert_keyframe_on_node(node, value=0, frame_range=Shader_VisibilityKey.frame_range, scene=scene, current_frame=current_frame)
        return current_frame



# Placeholder class and def
class Placeholder:
    def nothing():
        # This method is a placeholder and does not perform any actions
        pass
