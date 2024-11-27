import bpy
import os

"""run this script in 3d viewport, not in text editor"""

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
def restore_settings(original_view_matrix, original_space_shading_type, fp, format, percentage):
    scn = bpy.context.scene
    scn.render.filepath = fp
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

fp, old_percentage = bpy.context.scene.render.filepath, bpy.context.scene.render.resolution_percentage

# Try to get the output path from the node in the current scene's node tree
try:
    video_path = os.path.join(bpy.data.scenes[bpy.context.scene.name].node_tree.nodes["Output_path_TestAnim"].base_path, os.path.splitext(os.path.basename(bpy.data.filepath))[0] + '.mp4')
except Exception:
    # If failed, use default path
    video_path = os.path.join(os.path.dirname(bpy.data.filepath), 'viewport_animation', os.path.splitext(os.path.basename(bpy.data.filepath))[0] + '.mp4')

set_settings('RENDERED', False, video_path, 'MPEG4', 50)

# no need to set start frame to 1, but need to jump to frame 1
# beacuse If per_camera_resolution addon is enabled,
# Therefore, need to specify the rendering camera, 
# Otherwise it will default to using the first activated projection mapping camera, 
# that has a different custom resolution.
bpy.context.scene.frame_set(1)

# Render animation
if not camera_to_view_called:
    bpy.ops.view3d.camera_to_view()
bpy.ops.render.opengl(animation=True, view_context=True)
bpy.ops.render.play_rendered_anim()

# Restore settings and camera state
restore_settings(original_view_matrix, original_space_shading_type, fp, 'PNG', old_percentage)
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
