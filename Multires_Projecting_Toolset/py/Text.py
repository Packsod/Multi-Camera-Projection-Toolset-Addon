import bpy

class RenderSelectedFrameOperator(bpy.types.Operator):
    bl_idname = "scene.render_selected_frame"
    bl_label = "Render Selected Frame"
    bl_options = {'REGISTER'}

    selected_frame: bpy.props.IntProperty(name="Select Frame", description="Select a frame to render", default=1, min=1, max=24)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
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
        bpy.ops.render.render(write_still=True)
        # Jump back to the original frame
        bpy.context.scene.frame_set(current_frame)
        # Restore the original image settings
        bpy.context.scene.render.image_settings.file_format = current_file_format
        bpy.context.scene.render.use_overwrite = current_use_overwrite
        # Show a pop-up message
        self.report({'INFO'}, f'Frame {selected_frame} rendered successfully')
        return {'FINISHED'}

def register():
    bpy.utils.register_class(RenderSelectedFrameOperator)
    bpy.types.Scene.selected_frame = bpy.props.IntProperty(min=1, max=24)

def unregister():
    bpy.utils.unregister_class(RenderSelectedFrameOperator)
    del bpy.types.Scene.selected_frame

if __name__ == "__main__":
    register()
    bpy.ops.scene.render_selected_frame('INVOKE_DEFAULT')