import bpy


class ShowDialogOperator(bpy.types.Operator):
    bl_idname = "object.show_dialog"
    bl_label = "apply random color ID for all gp_coll"

    index: bpy.props.IntProperty(name="color ID", min=1, max=360, default=1)
    random_seed: bpy.props.IntProperty(name="Random seed", default=0)

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

    def shuffle_colors(self, colors, seed):
        shuffled_colors = colors.copy()
        for i in range(len(shuffled_colors)):
            j = (seed + i) % len(shuffled_colors)
            shuffled_colors[i], shuffled_colors[j] = shuffled_colors[j], shuffled_colors[i]
        return shuffled_colors

    def generate_colors(self, n):
        import colorsys
        pcyc = -1
        cval = 0
        st = 0
        lhsv = []

        for i in range(st, n):
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
            lhsv.append((cval, 0.5, 0.5))

        return [colorsys.hsv_to_rgb(*hsv) for hsv in lhsv]

    def execute(self, context):
        colors = self.generate_colors(360)
        hex_colors = ['#{:02x}{:02x}{:02x}'.format(int(rgb[0]*256), int(rgb[1]*256), int(rgb[2]*256)) for rgb in colors]

        num_empty_objects = len([obj for obj in bpy.data.objects if obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION'])
        if self.index > num_empty_objects:
            self.index = num_empty_objects
        hex_colors = hex_colors[:self.index]  # Limit the number of colors to the number of empty objects

        empty_objects = [obj for obj in bpy.data.objects if obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION']
        shuffled_colors = self.shuffle_colors(hex_colors, self.random_seed)

        for i, obj in enumerate(empty_objects):
            hex_color = shuffled_colors[i % len(shuffled_colors)]
            rgba_color = self.hex_to_rgba(hex_color)
            obj.color = rgba_color


        # Save the input values to the Blender data
        bpy.context.scene['show_dialog_operator_index'] = self.index
        bpy.context.scene['show_dialog_operator_random_seed'] = self.random_seed
        return {'FINISHED'}

    def invoke(self, context, event):
        # Load the input values from the Blender data if they exist
        if 'show_dialog_operator_index' in bpy.context.scene:
            self.index = bpy.context.scene['show_dialog_operator_index']
        if 'show_dialog_operator_random_seed' in bpy.context.scene:
            self.random_seed = bpy.context.scene['show_dialog_operator_random_seed']

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

bpy.utils.register_class(ShowDialogOperator)
bpy.ops.object.show_dialog('INVOKE_DEFAULT')