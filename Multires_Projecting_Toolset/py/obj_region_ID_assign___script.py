import bpy
from bpy.types import Operator


class ColorConversion:
    def srgb_to_linearrgb(self, c):
        if c < 0:
            return 0
        elif c < 0.04045:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4

    def hex_to_rgba(self, hex_value):
        hex_color = hex_value[1:]
        r = int(hex_color[:2], base=16)
        sr = r / 255.0
        lr = self.srgb_to_linearrgb(sr)
        g = int(hex_color[2:4], base=16)
        sg = g / 255.0
        lg = self.srgb_to_linearrgb(sg)
        b = int(hex_color[4:6], base=16)
        sb = b / 255.0
        lb = self.srgb_to_linearrgb(sb)
        return (lr, lg, lb, 1.0)

    def generate_colors(self, index):
        import colorsys
        pcyc = -1
        cval = 0
        st = 0
        for i in range(st, index):
            ccyc = 0
            while 2 ** ccyc <= i:
                ccyc += 1
            if ccyc == 0:
                cval = 0
            elif pcyc != ccyc:
                dlt = 1 / (2 ** ccyc)
                cval = dlt
            else:
                cval += 2 * dlt
            pcyc = ccyc
        return colorsys.hsv_to_rgb(cval, 0.5, 0.5)

class CheckColorIDAndSelect(bpy.types.Operator, ColorConversion):
    bl_idname = "object.check_color_id_and_select"
    bl_label = "Check region color ID and Select"
    color_id_map = {}
    TOLERANCE = 0.0001

    def execute(self, context):
        import math
        selected_objs = bpy.context.selected_objects
        if selected_objs:
            id_set = set()
            non_matching_objs = []
            for obj in selected_objs:
                color = obj.color
                found_match = False
                for index in range(0, 360):
                    rgb_color = self.generate_colors(index)
                    hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb_color[0]*256), int(rgb_color[1]*256), int(rgb_color[2]*256))
                    rgba_color = self.hex_to_rgba(hex_color)
                    if all(math.isclose(a, b, rel_tol=1e-5) for a, b in zip(color[:3], rgba_color[:3])):
                        id_set.add(index if index != 0 else 1)
                        self.color_id_map[tuple(color)] = index if index != 0 else 1
                        found_match = True
                        break
                if not found_match:
                    non_matching_objs.append(obj.name)
            id_list = sorted(list(id_set))
            message = "Selected objects region color ID:\n"
            if id_list:
                message += ', '.join(map(str, id_list))
            if non_matching_objs:
                message += "\nNone in:\n"
                message += ', '.join(non_matching_objs)
            context.scene['color_id_result'] = message
            self.select_matched_objs(context)
        else:
            context.scene['color_id_result'] = "No objects selected"
        return {'FINISHED'}

    def select_matched_objs(self, context):
        selected_objects = bpy.context.selected_objects
        if selected_objects:
            not_in_view_layer = []
            for current_obj in selected_objects:
                current_color = current_obj.color
                current_color_id = self.color_id_map.get(tuple(current_color))
                if current_color_id is not None:
                    for obj in bpy.data.objects:
                        if self.color_id_map.get(tuple(obj.color)) == current_color_id:
                            if obj.name in context.view_layer.objects:
                                obj.select_set(True)
                            else:
                                not_in_view_layer.append(obj.name)
            if not_in_view_layer:
                message = "objects not in the current view layer:\n" + ', '.join(not_in_view_layer) + "\n\nYou might need to ungroup them or check your scene setup."
                self.report({'WARNING'}, message)
        else:
            context.scene['color_id_result'] = "No objects selected"
        return {'FINISHED'}

class SelectObjsByAssignedID(bpy.types.Operator, ColorConversion):
    bl_idname = "object.select_objs_by_assigned_id"
    bl_label = "Select Objs by Assigned ID"
    bl_description = "Select objects based on the region color ID entered in the 'region color ID' input box"
    TOLERANCE = 0.0001
    index: bpy.props.IntProperty()

    def execute(self, context):
        import math
        # Deselect all objects first
        bpy.ops.object.select_all(action='DESELECT')
        rgb_color = self.generate_colors(self.index)
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb_color[0]*256), int(rgb_color[1]*256), int(rgb_color[2]*256))
        rgba_color = self.hex_to_rgba(hex_color)
        not_in_view_layer = []
        for obj in bpy.data.objects:
            if all(math.isclose(a, b, abs_tol=self.TOLERANCE) for a, b in zip(obj.color, rgba_color)):
                if obj.name in context.view_layer.objects:
                    obj.select_set(True)
                else:
                    not_in_view_layer.append(obj.name)
        if not_in_view_layer:
            message = "These objects are not in the current view layer:\n" + ', '.join(not_in_view_layer) + "\n\nYou might need to ungroup them or check your scene setup."
            self.report({'WARNING'}, message)
        return {'FINISHED'}

class RegionIDMaker(bpy.types.Operator, ColorConversion):
    bl_idname = "object.show_dialog"
    bl_label = "Assgin a region color ID (1-256) for selected objects"
    index: bpy.props.IntProperty(name="region color ID", min=-1, max=256, default=1, update=lambda self, context: self.update_index(context))
    color_id_result: bpy.props.StringProperty(name="region color ID Result", default="")

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        import random
        selected_objects = bpy.context.selected_objects
        if selected_objects:
            if self.index == -1:
                # Pre-generate a list of unique indices
                indices = list(range(1, 257))
                random.shuffle(indices)
                for obj in selected_objects:
                    try:
                        index = indices.pop(0)
                    except IndexError:
                        # If the list is exhausted, start from the beginning
                        indices = list(range(1, 257))
                        random.shuffle(indices)
                        index = indices.pop(0)
                    rgb_color = self.generate_colors(index)
                    hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb_color[0]*256), int(rgb_color[1]*256), int(rgb_color[2]*256))
                    rgba_color = self.hex_to_rgba(hex_color)
                    obj.color = list(rgba_color)
            elif self.index == 0:
                rgba_color = (1.0, 1.0, 1.0, 1.0)
                for obj in selected_objects:
                    obj.color = list(rgba_color)
            elif self.index <= 256:
                rgb_color = self.generate_colors(self.index)
                hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb_color[0]*256), int(rgb_color[1]*256), int(rgb_color[2]*256))
                rgba_color = self.hex_to_rgba(hex_color)
                for obj in selected_objects:
                    obj.color = list(rgba_color)
        context.scene['region_id_maker_index'] = self.index
        return {'FINISHED'}

    def invoke(self, context, event):
        if 'region_id_maker_index' in bpy.context.scene:
            self.index = bpy.context.scene['region_id_maker_index']
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("object.check_color_id_and_select", text="", icon='RESTRICT_SELECT_ON')
        row.prop(self, "index")
        row.operator("object.select_objs_by_assigned_id", text="", icon='RESTRICT_SELECT_OFF').index = self.index
        layout.label(text=context.scene.get('color_id_result', ""))

    def update_index(self, context):
        context.scene['region_id_maker_index'] = self.index

bpy.utils.register_class(CheckColorIDAndSelect)
bpy.utils.register_class(SelectObjsByAssignedID)
bpy.utils.register_class(RegionIDMaker)
bpy.ops.object.show_dialog('INVOKE_DEFAULT')
