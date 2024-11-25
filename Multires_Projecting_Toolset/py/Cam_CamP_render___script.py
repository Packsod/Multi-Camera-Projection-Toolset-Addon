import bpy

class RenderSelectedFrameOperator(bpy.types.Operator):
    bl_idname = "scene.render_selected_frame"
    bl_label = "export by specified CamP_sub"
    bl_options = {'REGISTER'}

    selected_frame: bpy.props.IntProperty(name="CamP ind(1~24)", description="Specific a CamP_sub to export", default=1, min=1, max=24)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        import os
        import re
        # Save the current frame and image settings
        current_frame = bpy.context.scene.frame_current
        current_file_format = bpy.context.scene.render.image_settings.file_format
        current_use_overwrite = bpy.context.scene.render.use_overwrite

        # Set the image settings to PNG format and enable overwrite
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.use_overwrite = True

        # Calculate the selected frame
        selected_frame = -self.selected_frame
        # Jump to the selected frame and render
        bpy.context.scene.frame_set(selected_frame)

        # Directory where the PNG files are located
        blend_file_dir = os.path.dirname(bpy.data.filepath)
        # Note that // means a network path in Windows,
        # so you need to remove the slashes in the string that you inputed in Output_path_MP,
        # then append it with os.listdir(),
        # otherwise bpy will report that the network path cannot be found.
        # This is really annoying.
        relative_output_directory = bpy.data.scenes[bpy.context.scene.name].node_tree.nodes["Output_path_MP"].base_path.replace("{camera}", bpy.context.scene.camera.name).lstrip('/') + '/'
        output_directory = os.path.join(blend_file_dir, relative_output_directory)

        # Delete any existing PNG files in the output directory
        try:
            for filename in os.listdir(output_directory):
                if filename.endswith(".png"):
                    file_path = os.path.join(output_directory, filename)
                    os.remove(file_path)
        except FileNotFoundError:
            pass

        # Render the selected frame
        bpy.ops.render.render(write_still=True)

        # Iterate through all PNG files in the directory and rename them if necessary
        for filename in os.listdir(output_directory):
            if filename.endswith(".png"):
                match = re.search(r'-(?P<frame_number>\d{4})\.png$', filename)
                if match:
                    new_filename = filename.replace(match.group(0), "") + ".png"
                    os.rename(os.path.join(output_directory, filename), os.path.join(output_directory, new_filename))

        # Jump back to the original frame and restore the original image settings
        bpy.context.scene.frame_set(current_frame)
        bpy.context.scene.render.image_settings.file_format = current_file_format
        bpy.context.scene.render.use_overwrite = current_use_overwrite
        # Show a pop-up message
        selected_frame_formatted = "%02d" % abs(selected_frame)
        camera_name = bpy.context.scene.camera.name
        self.report({'INFO'}, f'CamP_sub{selected_frame_formatted} rendered successfully')
        return {'FINISHED'}


# Register the operator
bpy.utils.register_class(RenderSelectedFrameOperator)

# Invoke the operator
bpy.ops.scene.render_selected_frame('INVOKE_DEFAULT')
