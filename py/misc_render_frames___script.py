import bpy
import os

class RenderAnimationOperator(bpy.types.Operator):
    bl_idname = "scene.render_animation"
    bl_label = "Render Animation"
    bl_options = {'REGISTER'}

    def execute(self, context):
        import re
        # Save the original settings
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

        # Set the frame range from the scene settings
        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end

        # jump to frame 1 at first, useful for "per_camera_resolution" add-on
        bpy.context.scene.frame_set(1)

        # Try to get the output path from the node in the current scene's node tree
        try:
            # Get the current scene's node tree
            node_tree = bpy.data.scenes[bpy.context.scene.name].node_tree

            # Check if the "Output_path_MP" node exists
            output_path_node = node_tree.nodes.get("Output_path_MP")
            if not output_path_node or not hasattr(output_path_node, "base_path"):
                raise ValueError('Node "Output_path_MP" not found or missing base_path attribute')

            # Get the current base_path
            original_base_path = output_path_node.base_path

            # Replace backslashes with forward slashes
            base_path = original_base_path.replace('\\', '/')

            # Use regular expressions to capture the first-level directory
            match = re.match(r'^(/*[^/]+)', base_path)
            if match:
                first_level_directory = match.group(1)
            else:
                first_level_directory = base_path

            # Ensure the directory ends with a slash
            if not first_level_directory.endswith('/'):
                first_level_directory += '/'

            # Append "output_render/" and the name of the current camera
            camera_name = bpy.context.scene.camera.name
            new_output_directory = first_level_directory + "output_render/" + camera_name + "/"

            # Get relative output directory
            relative_output_directory = new_output_directory.lstrip('/') + '/'

            # Get the directory of the blend file
            blend_file_dir = os.path.dirname(bpy.data.filepath)

            # Construct the output directory
            output_directory = os.path.join(blend_file_dir, relative_output_directory)

            # Construct the img path
            img_path = os.path.join(output_directory, f"{camera_name}")

            # Set the new base_path in the node
            output_path_node.base_path = new_output_directory

            # Set the img path
            bpy.context.scene.render.filepath = img_path

            # Function to delete all PNG files in a directory (including subdirectories)
            def delete_png_files(directory):
                for root, dirs, files in os.walk(directory, topdown=False):  # Use topdown=False to delete directories after their contents
                    for file in files:
                        if file.endswith('.png'):
                            file_path = os.path.join(root, file)
                            os.remove(file_path)
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        os.rmdir(dir_path)

            # Delete existing PNG files
            delete_png_files(output_directory)

            bpy.context.scene.render.resolution_percentage = 100

            # Render each frame using API loop
            for frame in range(frame_start, frame_end + 1):
                bpy.context.scene.frame_set(frame)
                bpy.ops.render.render(write_still=True)

            # Iterate through all PNG files in the directory and rename them if necessary
            for filename in os.listdir(output_directory):
                if filename.endswith(".png"):
                    new_filename = filename.replace("{camera}", camera_name)
                    os.rename(os.path.join(output_directory, filename), os.path.join(output_directory, new_filename))

            # Delete useless one png
            CamP_sub_file = os.path.join(output_directory, camera_name + ".png")
            if os.path.exists(CamP_sub_file):
                os.remove(CamP_sub_file)

            # Move files to subdirectories based on category (The last underscore is used as a separator)
            for filename in os.listdir(output_directory):
                if filename.endswith(".png"):
                    match = re.match(r'^.+_(\w+)(\d{4})\.png$', filename)
                    if match:
                        category = match.group(1)
                        new_path = os.path.join(output_directory, category, filename)
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        os.rename(os.path.join(output_directory, filename), new_path)

        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        # Restore the original settings
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
        self.report({'INFO'}, f'Animation rendered successfully to {img_path}')
        return {'FINISHED'}

# Register the operator
bpy.utils.register_class(RenderAnimationOperator)

# Invoke the operator
bpy.ops.scene.render_animation('INVOKE_DEFAULT')
