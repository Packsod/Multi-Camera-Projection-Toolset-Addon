import bpy

class RenderSelectedCamPOperator(bpy.types.Operator):
    bl_idname = "scene.render_selected_camp"
    bl_label = "Render Selected CamP"
    bl_options = {'REGISTER'}

    render_CamP: bpy.props.IntProperty(name="Select CamP ind(1~24)", description="Specify a CamP_sub to render controlnet images", default=1, min=1, max=24)
    render_video: bpy.props.BoolProperty(name="Render Video", description="Enable video rendering mode", default=False)
    frame_start: bpy.props.IntProperty(name="Frame Start", description="Start frame of the video", default=1, min=1)
    frame_count: bpy.props.IntProperty(name="Frame Count", description="Total number of frames to render", default=121, min=1)

    def invoke(self, context, event):
        wm = context.window_manager
        self.frame_start = context.scene.frame_start
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "render_CamP")
        layout.prop(self, "render_video")
        if self.render_video:
            layout.prop(self, "frame_start")
            layout.prop(self, "frame_count")

    def execute(self, context):
        import os
        import re

        # Save the current frame, image settings, use_nodes setting, and timeline frame range
        current_frame = bpy.context.scene.frame_current
        current_file_format = bpy.context.scene.render.image_settings.file_format
        current_use_overwrite = bpy.context.scene.render.use_overwrite
        current_use_nodes = bpy.context.scene.use_nodes
        original_camera = bpy.context.scene.camera
        original_render_filepath = bpy.context.scene.render.filepath
        original_frame_start = bpy.context.scene.frame_start
        original_frame_end = bpy.context.scene.frame_end

        # Set the image settings to PNG format and enable overwrite
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.use_overwrite = True
        bpy.context.scene.use_nodes = True

        # Calculate the selected frame
        current_frame_new = -self.render_CamP

        # Get the name of the camera to use for rendering
        camera_name = "CamP_sub%02d" % self.render_CamP

        # Check if the camera exists
        if camera_name not in bpy.data.objects:
            self.report({'ERROR'}, f'Camera {camera_name} does not exist')
            return {'CANCELLED'}

        # Set the camera to use for rendering
        bpy.context.scene.camera = bpy.data.objects[camera_name]

        # Directory where the PNG files are located
        blend_file_dir = os.path.dirname(bpy.data.filepath)
        node_tree = bpy.data.scenes[bpy.context.scene.name].node_tree

        # Check if the "Output_path_MP" node exists
        output_path_node = node_tree.nodes.get("Output_path_MP")
        if not output_path_node or not hasattr(output_path_node, "base_path"):
            self.report({'ERROR'}, 'Node "Output_path_MP" not found or missing base_path attribute')
            return {'CANCELLED'}

        # Save the original base_path
        original_base_path = output_path_node.base_path

        # append camera name to base_path
        if not output_path_node.base_path.endswith('/'):
            output_path_node.base_path += '/'
        output_path_node.base_path += camera_name

        """
        Note that // means a network path in Windows,
        so need to remove the slashes in the string that you inputed in Output_path_MP,
        then append it with os.listdir(),
        otherwise bpy will report that the network path cannot be found.
        This is really annoying.
        """
        
        relative_output_directory = output_path_node.base_path.lstrip('/') + '/'
        output_directory = os.path.join(blend_file_dir, relative_output_directory)

        # Create the output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)

        # Delete existing files based on the render mode
        def delete_files_by_extension(directory, extension):
            try:
                for filename in os.listdir(directory):
                    if filename.endswith(extension):
                        file_path = os.path.join(directory, filename)
                        os.remove(file_path)
            except FileNotFoundError:
                pass

        if self.render_video:
            delete_files_by_extension(output_directory, ".mp4")
        else:
            delete_files_by_extension(output_directory, ".png")

        # Set the render filepath to the output directory
        bpy.context.scene.render.filepath = os.path.join(output_directory, camera_name)

        if self.render_video:
            # Record all current camera markers and their positions
            original_markers = [(marker.name, marker.frame, marker.camera) for marker in bpy.context.scene.timeline_markers if marker.camera]

            # Remove all camera markers
            for marker in bpy.context.scene.timeline_markers:
                if marker.camera:
                    bpy.context.scene.timeline_markers.remove(marker)

            # Set render settings for video
            bpy.context.scene.frame_start = self.frame_start
            bpy.context.scene.frame_end = self.frame_start + self.frame_count - 1

            # Set render settings for video
            bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
            bpy.context.scene.render.ffmpeg.format = 'MPEG4'
            bpy.context.scene.render.resolution_percentage = 100

            # Render the animation
            bpy.ops.render.opengl(animation=True, view_context=True)

            # Restore the original camera markers to their original positions
            for name, frame, camera in original_markers:
                if camera and camera.name in bpy.data.objects:
                    marker = bpy.context.scene.timeline_markers.new(name=name, frame=frame)
                    marker.camera = bpy.data.objects[camera.name]

        else:
            # Jump to the selected frame and render
            bpy.context.scene.frame_set(current_frame_new)

            # Render the selected frame
            bpy.ops.render.render(write_still=True)

            # Iterate through all PNG files in the directory and rename them if necessary
            for filename in os.listdir(output_directory):
                if filename.endswith(".png"):
                    match = re.search(r'-(?P<frame_number>\d{4})\.png$', filename)
                    if match:
                        new_filename = filename.replace(match.group(0), "").replace("{camera}", camera_name) + ".png"
                        os.rename(os.path.join(output_directory, filename), os.path.join(output_directory, new_filename))

            # Delete CamP_sub##.png
            CamP_sub_file = os.path.join(output_directory, camera_name + ".png")
            if os.path.exists(CamP_sub_file):
                os.remove(CamP_sub_file)

        # Jump back to the original frame and restore the original settings
        bpy.context.scene.frame_set(current_frame)
        bpy.context.scene.render.image_settings.file_format = current_file_format
        bpy.context.scene.render.use_overwrite = current_use_overwrite
        bpy.context.scene.use_nodes = current_use_nodes
        bpy.context.scene.camera = original_camera
        bpy.context.scene.render.filepath = original_render_filepath
        bpy.context.scene.frame_start = original_frame_start
        bpy.context.scene.frame_end = original_frame_end

        # Restore the original base_path
        output_path_node.base_path = original_base_path

        # Show a pop-up message
        camera_name = bpy.context.scene.camera.name
        self.report({'INFO'}, f'{camera_name} rendered successfully')
        return {'FINISHED'}

# Register the operator
bpy.utils.register_class(RenderSelectedCamPOperator)

# Invoke the operator
bpy.ops.scene.render_selected_camp('INVOKE_DEFAULT')
