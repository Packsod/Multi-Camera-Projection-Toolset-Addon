import bpy
import os

"""Run this script in 3D Viewport, not in Text Editor"""

# Start the undo block
bpy.ops.ed.undo_push(message="Start of script operation")

# Store the names of selected objects and objects hidden in viewport
selected_objects = [obj.name for obj in bpy.context.selected_objects]
hidden_objects = [obj.name for obj in bpy.data.objects if obj.hide_get() and not obj.hide_viewport]

# Unhide all objects in viewport & Set hide_viewport to False for all objects
for obj in bpy.data.objects:
    obj.hide_set(False)

# Function to set render settings
def set_settings(shading_type, show_overlays, filepath, format, percentage):
    scn = bpy.context.scene
    scn.render.filepath = filepath
    scn.render.image_settings.file_format = 'FFMPEG'
    scn.render.ffmpeg.format = format
    scn.render.resolution_percentage = percentage
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = shading_type
                    space.overlay.show_overlays = show_overlays
                    break

# Function to restore original settings
def restore_settings(original_view_matrix, original_space_shading_type, original_video_path, format, percentage):
    scn = bpy.context.scene
    scn.render.filepath = original_video_path
    scn.render.image_settings.file_format = format
    scn.render.resolution_percentage = percentage
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.region_3d.view_matrix = original_view_matrix
                    space.shading.type = original_space_shading_type
                    break

# Store original viewport state
original_view_matrix = None
original_space_shading_type = None
camera_to_view_called = False
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                original_view_matrix = space.region_3d.view_matrix.copy()
                original_space_shading_type = space.shading.type
                if space.region_3d.view_perspective == 'CAMERA':
                    camera_to_view_called = True
                break

# Store camera state and frame
current_frame = bpy.context.scene.frame_current
original_camera = bpy.context.scene.camera
current_camera_view = None
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                current_camera_view = space.region_3d.view_perspective
                break

# Switch camera to another one without changing any camera parameters
cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
for cam in cameras:
    if cam != original_camera:
        bpy.context.scene.camera = cam
        break

# Store original render file path and resolution percentage
original_video_path, old_percentage = bpy.context.scene.render.filepath, bpy.context.scene.render.resolution_percentage

# Try to get the output path from the node in the current scene's node tree
try:
    # Get the current scene's node tree
    node_tree = bpy.data.scenes[bpy.context.scene.name].node_tree

    # Check if the "Output_path_MP" node exists
    output_path_node = node_tree.nodes.get("Output_path_MP")
    if not output_path_node or not hasattr(output_path_node, "base_path"):
        raise ValueError('Node "Output_path_MP" not found or missing base_path attribute')

    # Get the current base_path
    base_path = output_path_node.base_path

    # Replace backslashes with forward slashes
    base_path = base_path.replace('\\', '/')

    # Use regular expressions to capture the first-level directory
    import re
    match = re.match(r'^(/*[^/]+)', base_path)
    if match:
        first_level_directory = match.group(1)
    else:
        first_level_directory = base_path

    # Ensure the directory ends with a slash
    if not first_level_directory.endswith('/'):
        first_level_directory += '/'

    # Append "render_output/"
    new_output_directory = first_level_directory + "output_test_anim/"

    # Get relative output directory
    relative_output_directory = new_output_directory.lstrip('/') + '/'

    # Get the directory of the blend file
    blend_file_dir = os.path.dirname(bpy.data.filepath)

    # Construct the output directory
    output_directory = os.path.join(blend_file_dir, relative_output_directory)

    # Construct the video path
    video_path = os.path.join(output_directory, os.path.splitext(os.path.basename(bpy.data.filepath))[0] + '.mp4')
except Exception as e:
    # If failed, use default path
    print(f"Error setting output path: {e}")
    video_path = os.path.join(os.path.dirname(bpy.data.filepath), 'viewport_animation', os.path.splitext(os.path.basename(bpy.data.filepath))[0] + '.mp4')

# Set the video path
set_settings('RENDERED', False, video_path, 'MPEG4', 50)

"""
jump to frame 1 at first is necessary because if the "per_camera_resolution" add-on is enabled,
specifying the rendering camera (not CamP) is required to avoid using the previous activated
projection mapping camera, which might have a different custom resolution.
"""
bpy.context.scene.frame_set(1)

# Render animation
if not camera_to_view_called:
    bpy.ops.view3d.camera_to_view()
bpy.ops.render.opengl(animation=True, view_context=True)
bpy.ops.render.play_rendered_anim()

# Restore settings and camera state
restore_settings(original_view_matrix, original_space_shading_type, original_video_path, 'PNG', old_percentage)
bpy.context.scene.frame_current = current_frame
bpy.context.scene.camera = original_camera
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.region_3d.view_perspective = current_camera_view
                break

# Restore hidden objects
for obj in bpy.data.objects:
    if obj.name in hidden_objects:
        obj.hide_set(True)

# Restore selected objects
bpy.ops.object.select_all(action='DESELECT')
if selected_objects:
    for obj in bpy.data.objects:
        if obj.name in selected_objects:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[selected_objects[0]]

# End the undo block
bpy.ops.ed.undo_push(message="End of script operation")
