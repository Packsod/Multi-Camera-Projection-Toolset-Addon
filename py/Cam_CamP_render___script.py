import bpy
import os
import re

class RenderSelectedCamPOperator(bpy.types.Operator):
    bl_idname = "scene.render_selected_camp"
    bl_label = "Render Selected CamP"
    bl_options = {'REGISTER'}

    render_CamP: bpy.props.IntProperty(name="Select CamP ind(1~24)", description="Specify a CamP_sub to render controlnet images", default=1, min=1, max=24)
    render_video: bpy.props.BoolProperty(name="Render Video", description="Enable video rendering mode", default=False)
    frame_start: bpy.props.IntProperty(name="Frame Start", description="Start frame of the video", default=1, min=1)
    frame_count: bpy.props.IntProperty(name="Frame Count", description="Total number of frames to render", default=121, min=1)
    sockets_to_keep: bpy.props.BoolVectorProperty(
        name="Sockets to Keep",
        size=32,
        default=tuple([True]*32),
        options={'ANIMATABLE'}
    )

    def invoke(self, context, event):
        wm = context.window_manager
        self.frame_start = context.scene.frame_start
        node_tree = context.scene.node_tree
        output_path_node = node_tree.nodes.get("Output_path_MP")
        if output_path_node:
            total_sockets = len(output_path_node.file_slots)
            self.sockets_to_keep = [True] * total_sockets + [False] * (32 - total_sockets)
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "render_CamP")
        layout.prop(self, "render_video")
        if self.render_video:
            layout.prop(self, "frame_start")
            layout.prop(self, "frame_count")
            node_tree = context.scene.node_tree
            output_path_node = node_tree.nodes.get("Output_path_MP")
            if output_path_node:
                for i, slot in enumerate(output_path_node.file_slots):
                    layout.prop(self, "sockets_to_keep", index=i, text=slot.path)

    # Helper function: Save current settings
    def save_settings(self, context):
        current_frame = context.scene.frame_current
        current_file_format = context.scene.render.image_settings.file_format
        current_use_overwrite = context.scene.render.use_overwrite
        current_use_nodes = context.scene.use_nodes
        current_camera = context.scene.camera
        current_render_filepath = context.scene.render.filepath
        current_frame_start = context.scene.frame_start
        current_frame_end = context.scene.frame_end
        current_compositor = context.space_data.shading.use_compositor
        current_overlay = context.space_data.overlay.show_overlays
        current_resolution_percentage = context.scene.render.resolution_percentage

        region_data = []
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        region_data.append({
                            'view_matrix': space.region_3d.view_matrix.copy(),
                            'shading_type': space.shading.type,
                            'view_perspective': space.region_3d.view_perspective
                        })

        return {
            'current_frame': current_frame,
            'current_file_format': current_file_format,
            'current_use_overwrite': current_use_overwrite,
            'current_use_nodes': current_use_nodes,
            'current_camera': current_camera,
            'current_render_filepath': current_render_filepath,
            'current_frame_start': current_frame_start,
            'current_frame_end': current_frame_end,
            'current_compositor': current_compositor,
            'current_overlay': current_overlay,
            'current_resolution_percentage': current_resolution_percentage,
            'region_data': region_data
        }

    # Helper function: Restore settings
    def restore_settings(self, context, settings):
        context.scene.render.image_settings.file_format = settings['current_file_format']
        context.scene.render.resolution_percentage = settings['current_resolution_percentage']
        context.space_data.overlay.show_overlays = settings['current_overlay']
        for i, area in enumerate(bpy.context.screen.areas):
            if area.type == 'VIEW_3D':
                for j, space in enumerate(area.spaces):
                    if space.type == 'VIEW_3D':
                        rd = settings['region_data'][min(i, len(settings['region_data'])-1)]  # Prevent mismatched count
                        space.region_3d.view_matrix = rd['view_matrix']
                        space.shading.type = rd['shading_type']
                        space.region_3d.view_perspective = rd['view_perspective']
        context.scene.frame_set(settings['current_frame'])
        context.scene.camera = settings['current_camera']

    # Helper function: Delete files by extension
    def delete_files_by_extension(self, directory, extension):
        import os
        try:
            for filename in os.listdir(directory):
                if filename.endswith(extension):
                    file_path = os.path.join(directory, filename)
                    os.remove(file_path)
        except FileNotFoundError:
            pass

    # Helper function: Remove all Viewer nodes
    def remove_existing_viewer_nodes(self, node_tree):
        viewer_nodes = [node for node in node_tree.nodes if node.type == 'VIEWER']
        for viewer_node in viewer_nodes:
            node_tree.nodes.remove(viewer_node)

    # Helper function: Rename MP4 files
    def rename_mp4_files(self, output_directory, camera_name):
        import os
        import re
        for filename in os.listdir(output_directory):
            if filename.endswith(".mp4"):
                match = re.search(r'(?P<frame_number>\d{4})-(?P<end>\d{4})\.mp4$', filename)
                if match:
                    new_filename = filename.replace(match.group(0), "").replace("{camera}", camera_name) + f"{match.group('end')}.mp4"
                    os.rename(os.path.join(output_directory, filename), os.path.join(output_directory, new_filename))

    # Helper function: Rename PNG files
    def rename_png_files(self, output_directory, camera_name):
        import os
        import re
        for filename in os.listdir(output_directory):
            if filename.endswith(".png"):
                match = re.search(r'-(?P<frame_number>\d{4})\.png$', filename)
                if match:
                    new_filename = filename.replace(match.group(0), "").replace("{camera}", camera_name) + ".png"
                    os.rename(os.path.join(output_directory, filename), os.path.join(output_directory, new_filename))

    # Main execution logic
    def execute(self, context):
        import os
        import re
        settings = self.save_settings(context)
        current_camera = bpy.context.scene.camera
        camera_name = f"CamP_sub{self.render_CamP:02d}"

        if camera_name not in bpy.data.objects:
            self.report({'ERROR'}, f'Camera {camera_name} does not exist')
            return {'CANCELLED'}

        node_tree = context.scene.node_tree
        output_path_node = node_tree.nodes.get("Output_path_MP")
        if not output_path_node or not hasattr(output_path_node, "base_path"):
            self.report({'ERROR'}, 'Node "Output_path_MP" not found or missing base_path attribute')
            return {'CANCELLED'}

        original_base_path = output_path_node.base_path
        output_path_node.base_path = os.path.join(output_path_node.base_path, camera_name)
        relative_output_directory = output_path_node.base_path.lstrip('/') + '/'
        output_directory = os.path.join(os.path.dirname(bpy.data.filepath), relative_output_directory)
        os.makedirs(output_directory, exist_ok=True)

        if self.render_video:
            self.delete_files_by_extension(output_directory, ".mp4")
        else:
            self.delete_files_by_extension(output_directory, ".png")

        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.use_overwrite = True
        bpy.context.scene.use_nodes = True
        bpy.context.scene.camera = bpy.data.objects[camera_name]

        if self.render_video:
            original_markers = [(marker.name, marker.frame, marker.camera) for marker in context.scene.timeline_markers if marker.camera]
            for marker in reversed(context.scene.timeline_markers):
                if marker.camera:
                    context.scene.timeline_markers.remove(marker)

            # Force switch to camera view
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            if space.region_3d.view_perspective != 'CAMERA':
                                space.region_3d.view_perspective = 'CAMERA'

            context.space_data.shading.type = 'RENDERED'
            context.space_data.shading.use_compositor = 'ALWAYS'
            context.space_data.overlay.show_overlays = False

            context.scene.frame_start = self.frame_start
            context.scene.frame_end = self.frame_start + self.frame_count - 1
            context.scene.render.image_settings.file_format = 'FFMPEG'
            context.scene.render.ffmpeg.format = 'MPEG4'
            context.scene.render.resolution_percentage = 100

            self.remove_existing_viewer_nodes(node_tree)
            viewer_node = node_tree.nodes.new("CompositorNodeViewer")

            keep_indices = [i for i, v in enumerate(self.sockets_to_keep[:len(output_path_node.file_slots)]) if v]

            for i in keep_indices:
                input_socket = output_path_node.inputs[i]
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    node_tree.links.new(from_socket, viewer_node.inputs[0])
                    bpy.context.scene.render.filepath = os.path.join(output_directory, f"{input_socket.name}")
                    bpy.ops.render.opengl(animation=True, view_context=True)
                    node_tree.links.remove(viewer_node.inputs[0].links[0])
                else:
                    self.report({'WARNING'}, f'Slot {i+1} has no connection')

            node_tree.nodes.remove(viewer_node)
            self.rename_mp4_files(output_directory, camera_name)

            for name, frame, camera in original_markers:
                if camera and camera.name in bpy.data.objects:
                    marker = context.scene.timeline_markers.new(name=name, frame=frame)
                    marker.camera = bpy.data.objects[camera.name]

        else:
            bpy.context.scene.frame_set(-self.render_CamP)
            bpy.ops.render.render(write_still=True)
            self.rename_png_files(output_directory, camera_name)

        self.restore_settings(context, settings)
        output_path_node.base_path = original_base_path
        self.report({'INFO'}, f'{camera_name} rendered successfully')
        return {'FINISHED'}

# Register operator
bpy.utils.register_class(RenderSelectedCamPOperator)

# Call operator
bpy.ops.scene.render_selected_camp('INVOKE_DEFAULT')
