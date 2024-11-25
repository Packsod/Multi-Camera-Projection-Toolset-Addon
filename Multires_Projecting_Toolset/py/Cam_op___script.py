import bpy

class Cam_Visibility:
    @staticmethod
    def has_keyframe(obj, frame):
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if frame in [kf.co[0] for kf in fcurve.keyframe_points]:
                    return True
        return False

    @staticmethod
    def insert_keyframes(obj, frame, visibility):
        obj.hide_render = visibility
        obj.hide_viewport = visibility
        if not Cam_Visibility.has_keyframe(obj, frame):
            obj.keyframe_insert(data_path="hide_render", frame=frame)
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)


    @staticmethod
    def hide_all_objects():
        scene = bpy.context.scene
        original_frame = scene.frame_current
        obj_list = bpy.context.selected_objects
        frame_ranges = [(-24, 0)]

        for obj in obj_list:
            if not Cam_Visibility.has_keyframe(obj, -25):
                Cam_Visibility.insert_keyframes(obj, -25, False)
            if not Cam_Visibility.has_keyframe(obj, 0):
                Cam_Visibility.insert_keyframes(obj, 0, False)

        for start, end in frame_ranges:
            for obj in obj_list:
                Cam_Visibility.insert_keyframes(obj, start, True)
                Cam_Visibility.insert_keyframes(obj, end, True)
                if start == -24:
                    Cam_Visibility.insert_keyframes(obj, start, False)
                if end == 0:
                    Cam_Visibility.insert_keyframes(obj, end, False)
        scene.frame_set(original_frame)


    @staticmethod
    def hide_current_object():
        scene = bpy.context.scene
        original_frame = scene.frame_current
        obj_list = bpy.context.selected_objects
        for obj in obj_list:
            current_frame = scene.frame_current
            if -24 <= current_frame <= -1:
                # Remove existing keyframe if any
                if obj.animation_data and obj.animation_data.action:
                    for fcurve in obj.animation_data.action.fcurves:
                        for kf in fcurve.keyframe_points:
                            if kf.co[0] == current_frame:
                                fcurve.keyframe_points.remove(kf)
                # Insert new keyframes
                Cam_Visibility.insert_keyframes(obj, current_frame, True)
                if not Cam_Visibility.has_keyframe(obj, current_frame - 1):
                    Cam_Visibility.insert_keyframes(obj, current_frame - 1, False)
                if not Cam_Visibility.has_keyframe(obj, current_frame + 1):
                    Cam_Visibility.insert_keyframes(obj, current_frame + 1, False)
        scene.frame_set(original_frame)



    @staticmethod
    def show_all_objects():
        for obj in bpy.context.selected_objects:
            if anim_data := obj.animation_data:
                if anim_data.action:
                    for fcurve in [f for f in anim_data.action.fcurves if f.data_path in ["hide_render", "hide_viewport"]]:
                        fcurve.keyframe_points.clear()
                        anim_data.action.fcurves.remove(fcurve)
                    if len(anim_data.action.fcurves) == 0:
                        anim_data.action.name += "_deleted"
                        obj.animation_data_clear()
            obj.hide_render = obj.hide_viewport = False



class Cam_Switch:
    @staticmethod
    def get_new_cam_name(prefix):
        cam_list = [cam for cam in bpy.data.cameras if cam.name.startswith(prefix)]
        cam_list.sort(key=lambda cam: int(cam.name.split(prefix)[1]))
        if not cam_list:
            return f"{prefix}01"
        last_cam = cam_list[-1]
        last_num = int(last_cam.name.split(prefix)[1])
        if last_num >= 24:
            bpy.context.window_manager.popup_menu(
                lambda self, context: self.layout.label(text=f"Warning: You have set too many {prefix} cameras."),
                title="Warning",
                icon='INFO'
            )
            return None
        new_num = str(last_num + 1).zfill(2)
        return f"{prefix}{new_num}"

    @staticmethod
    def create_new_camera(new_cam_name):
        new_cam = bpy.data.cameras.new(new_cam_name)
        new_obj = bpy.data.objects.new(new_cam_name, new_cam)
        new_cam.passepartout_alpha = 0.5
        bpy.data.collections["projecting"].children["CamO"].objects.link(new_obj)
        active_camera = bpy.context.scene.camera
        if active_camera and bpy.context.space_data.region_3d.view_perspective == 'CAMERA':
            active_cam_data = active_camera.data
            for attr in ["lens", "shift_x", "shift_y", "clip_start", "clip_end", "sensor_width"]:
                setattr(new_cam, attr, getattr(active_cam_data, attr))
            new_obj.location = active_camera.location
            new_obj.rotation_euler = active_camera.rotation_euler
        else:
            new_obj.matrix_world = bpy.context.region_data.view_matrix.inverted()
            for attr in ["lens", "clip_start", "clip_end"]:
                setattr(new_cam, attr, getattr(bpy.context.space_data, attr))
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = new_obj
        new_obj.select_set(True)
        return new_obj

    @staticmethod
    def CamO_fit_to_active():
        if "projecting" in bpy.data.collections and "CamO" in bpy.data.collections["projecting"].children:
            new_cam_name = Cam_Switch.get_new_cam_name("CamO_sub")
            if new_cam_name is not None:
                Cam_Switch.create_new_camera(new_cam_name)
        Cam_Switch.update_markers()

    @staticmethod
    def CamP_fit_to_CamO():
        CamO_objects = [f"CamO_sub{str(i).zfill(2)}" for i in range(1, 25)]
        CamP_objects = [f"CamP_sub{str(i).zfill(2)}" for i in range(1, 25)]
        existing_CamO = [cam for cam in bpy.data.objects if cam.name in CamO_objects and not cam.hide_viewport]
        if not existing_CamO:
            bpy.context.window_manager.popup_menu(
                lambda self, context: self.layout.label(text="Warning: No cameras from CamO_objects exist in data or they are disabled in viewport."),
                title="Warning",
                icon='INFO'
            )
        else:
            existing_CamP = [cam for cam in bpy.data.objects if cam.name in CamP_objects]
            if len(existing_CamP) != len(CamP_objects):
                bpy.context.window_manager.popup_menu(
                    lambda self, context: self.layout.label(text="Warning: Some cameras from CamP_objects do not exist in data. Please check and fix."),
                    title="Warning",
                    icon='INFO'
                )
            elif len(existing_CamP) == 0:
                bpy.context.window_manager.popup_menu(
                    lambda self, context: self.layout.label(text="Warning: Please run the 'set scene' script to import preset components first."),
                    title="Warning",
                    icon='INFO'
                )
            else:
                for CamO in existing_CamO:
                    index = int(CamO.name.split('CamO_sub')[1])
                    CamP_name = CamP_objects[index - 1]
                    CamP = bpy.data.objects.get(CamP_name)
                    if CamP is not None:
                        CamP.location = CamO.location
                        CamP.rotation_euler = CamO.rotation_euler
                        for attr in ["lens", "shift_x", "shift_y", "clip_start", "clip_end", "sensor_width"]:
                            setattr(CamP.data, attr, getattr(CamO.data, attr))

    @staticmethod
    def update_markers():
        scene = bpy.context.scene
        camera_names_1 = [f"CamO_sub{i:02d}" for i in range(1, 25)]
        markers_1 = {f"CamO_sub{i:02d}": {"frame": -100 - i, "camera": f"CamO_sub{i:02d}"} for i in range(1, 25)}
        camera_names_2 = [f"CamP_sub{i:02d}" for i in range(1, 25)]
        markers_2 = {f"CamP_sub{i:02d}": {"frame": -i, "camera": f"CamP_sub{i:02d}", "frame_time": 0.00} for i in range(1, 25)}
        markers = {**markers_1, **markers_2}
        existing_frames = [marker.frame for marker in scene.timeline_markers]
        for name, m_data in markers.items():
            camera = bpy.data.objects.get(m_data["camera"])
            if camera is not None:
                if m_data["frame"] in existing_frames:
                    existing_marker = next(marker for marker in scene.timeline_markers if marker.frame == m_data["frame"])
                    if existing_marker.camera != camera:
                        existing_marker.camera = camera
                else:
                    marker = scene.timeline_markers.new(name, frame=m_data["frame"])
                    marker.camera = camera
            elif m_data["frame"] in existing_frames:
                marker_to_remove = next(marker for marker in scene.timeline_markers if marker.frame == m_data["frame"])
                scene.timeline_markers.remove(marker_to_remove)
                
    @staticmethod
    def QShot_combine():
        cameras = [obj for obj in bpy.context.scene.objects if obj.type == 'CAMERA']
        Shot_cameras = [obj for obj in bpy.context.scene.objects if obj.type == 'CAMERA' and obj.name.startswith("Shot")]

        if not Shot_cameras:
            bpy.context.window_manager.popup_menu(
                lambda self, context: self.layout.label(text="No QShot cameras found "),
                title="Error",
                icon='ERROR'
            )
        else:
            Shot_cameras.sort(key=lambda cam: bpy.context.scene.timeline_markers[cam.name].frame)
            first_shot_camera = Shot_cameras[0]
            new_camera = bpy.data.cameras.new("MergedCamera")
            new_camera_obj = bpy.data.objects.new("MergedCamera", new_camera)
            bpy.context.collection.objects.link(new_camera_obj)
            # Copy over the camera properties
            for attr in ["lens", "shift_x", "shift_y", "clip_start", "clip_end", "sensor_width"]:
                setattr(new_camera, attr, getattr(first_shot_camera.data, attr))
            for camera in Shot_cameras:
                if camera.animation_data.action:
                    if new_camera_obj.animation_data is None:
                        new_camera_obj.animation_data_create()
                    if new_camera_obj.animation_data.action is None:
                        new_camera_obj.animation_data.action = camera.animation_data.action.copy()
                    else:
                        new_camera_obj.animation_data.action.frame_range = (new_camera_obj.animation_data.action.frame_range[0], max(new_camera_obj.animation_data.action.frame_range[1], camera.animation_data.action.frame_range[1]))
                        for fcurve in camera.animation_data.action.fcurves:
                            if fcurve.data_path in [fc.data_path for fc in new_camera_obj.animation_data.action.fcurves]:
                                new_fcurve = new_camera_obj.animation_data.action.fcurves.find(fcurve.data_path, index=fcurve.array_index)
                                for kp in fcurve.keyframe_points:
                                    new_kp = new_fcurve.keyframe_points.insert(kp.co[0], kp.co[1], options={'FAST'})
                                    new_kp.interpolation = kp.interpolation
                                    new_kp.handle_left = kp.handle_left
                                    new_kp.handle_right = kp.handle_right
                            else:
                                new_fcurve = new_camera_obj.animation_data.action.fcurves.new(fcurve.data_path, index=fcurve.array_index)
                                new_fcurve.keyframe_points.add(len(fcurve.keyframe_points))
                                for i, kp in enumerate(fcurve.keyframe_points):
                                    new_fcurve.keyframe_points[i].co = kp.co
                                    new_fcurve.keyframe_points[i].interpolation = kp.interpolation
                                    new_fcurve.keyframe_points[i].handle_left = kp.handle_left
                                    new_fcurve.keyframe_points[i].handle_right = kp.handle_right
            bpy.context.view_layer.objects.active = new_camera_obj
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces[0].region_3d.view_perspective = 'CAMERA'



    @staticmethod
    def backup_CamP_parameters():
        # Create or overwrite the text block
        if "CamP_backups" in bpy.data.texts:
            backup_text = bpy.data.texts["CamP_backups"]
            backup_text.clear()
        else:
            backup_text = bpy.data.texts.new("CamP_backups")
        # Write the parameters to the text block
        CamP_objects = [f"CamP_sub{str(i).zfill(2)}" for i in range(1, 25)]
        existing_CamP = [cam for cam in bpy.data.objects if cam.name in CamP_objects]
        for CamP in existing_CamP:
            backup_text.write(f"{CamP.name}\n")
            backup_text.write(f"Location: {CamP.location.x}, {CamP.location.y}, {CamP.location.z}\n")
            backup_text.write(f"Rotation: {CamP.rotation_euler.x}, {CamP.rotation_euler.y}, {CamP.rotation_euler.z}\n")
            backup_text.write(f"Lens: {CamP.data.lens}\n")
            backup_text.write(f"Shift X: {CamP.data.shift_x}\n")
            backup_text.write(f"Shift Y: {CamP.data.shift_y}\n")
            backup_text.write(f"Clip Start: {CamP.data.clip_start}\n")
            backup_text.write(f"Clip End: {CamP.data.clip_end}\n")
            backup_text.write(f"Sensor Width: {CamP.data.sensor_width}\n")
            backup_text.write("------------------\n")


    @staticmethod
    def apply_CamP_parameters():
        if 'CamP_backups' in bpy.data.texts:
            backup_text = bpy.data.texts['CamP_backups']
            lines = backup_text.as_string().split('\n')
            i = 0
            while i < len(lines):
                if lines[i].startswith('CamP_sub'):
                    CamP_name = lines[i]
                    CamP = bpy.data.objects.get(CamP_name)
                    if CamP is not None:
                        # Read the location
                        location_line = lines[i + 1]
                        location_parts = location_line.split(': ')[1].split(',')
                        location = [float(x) for x in location_parts]
                        CamP.location = location
                        # Read the rotation
                        rotation_line = lines[i + 2]
                        rotation_parts = rotation_line.split(': ')[1].split(',')
                        rotation = [float(x) for x in rotation_parts]
                        CamP.rotation_euler = rotation
                        # Read the lens parameters
                        lens_line = lines[i + 3]
                        lens = float(lens_line.split(': ')[1])
                        CamP.data.lens = lens
                        # Read the shift parameters
                        shift_x_line = lines[i + 4]
                        shift_x = float(shift_x_line.split(': ')[1])
                        CamP.data.shift_x = shift_x
                        shift_y_line = lines[i + 5]
                        shift_y = float(shift_y_line.split(': ')[1])
                        CamP.data.shift_y = shift_y
                        # Read the clip parameters
                        clip_start_line = lines[i + 6]
                        clip_start = float(clip_start_line.split(': ')[1])
                        CamP.data.clip_start = clip_start
                        clip_end_line = lines[i + 7]
                        clip_end = float(clip_end_line.split(': ')[1])
                        CamP.data.clip_end = clip_end
                        # Read the sensor width
                        sensor_width_line = lines[i + 8]
                        sensor_width = float(sensor_width_line.split(': ')[1])
                        CamP.data.sensor_width = sensor_width
                    i += 9
                else:
                    i += 1
        else:      
            bpy.context.window_manager.popup_menu(
                lambda self, context: self.layout.label(text="No 'CamP_backups' text block found."),
                title="Warning",
                icon='INFO'
                )




class Cam_Mist:
    def set_distance():
        import mathutils
        import math
        # Get the camera object
        camera = bpy.context.scene.camera
        # If the scene has no camera, pop up a window and return
        if camera is None:
            bpy.context.window_manager.popup_menu(lambda self, context: 
                self.layout.label(text="No camera in the scene. Please add a camera."), 
                title="Error", icon='ERROR')
            return

        # If the scene has no selected object, display a popup message
        selected_obj = bpy.context.active_object
        if selected_obj is None:
            bpy.context.window_manager.popup_menu(lambda self, context: 
                self.layout.label(text="Please select an object to calculate the distance."), 
                title="Error", icon='ERROR')
            return

        # Calculate the camera's forward direction
        camera_forward = camera.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, -1))
        # Initialize distance and vertex
        max_distance = 0
        farthest_vertex = None
        # Check if the selected object is a mesh
        if selected_obj.type == 'MESH':
            # Check each vertex in the selected object's mesh
            for vertex in selected_obj.data.vertices:
                # Calculate the vertex's location in world coordinates
                vertex_location = selected_obj.matrix_world @ vertex.co
                # Calculate the vector from the camera to the vertex
                to_vertex = vertex_location - camera.location
                # Calculate the angle between the camera's forward direction and the vector to the vertex
                angle = to_vertex.angle(camera_forward)
                # If the angle is within 45 degrees and the distance is greater than the current maximum, update the maximum and the farthest vertex
                if angle < math.radians(45) and to_vertex.length > max_distance:
                    max_distance = to_vertex.length
                    farthest_vertex = vertex_location
        else:
            # If the selected object is not a mesh, calculate the distance to its origin
            max_distance = (camera.location - selected_obj.location).length
        # Increase the distance by 15% of its current value, with a minimum of 5
        distance = max(max_distance * 1.15, 5)
        # Set the distance value as the mist settings depth
        bpy.context.scene.world.mist_settings.depth = distance     
        # Check if current frame number is within the specified ranges
        frame_current = bpy.context.scene.frame_current
        if (-24 <= frame_current <= -1):
            
            # If true, insert a keyframe
            bpy.context.scene.world.mist_settings.keyframe_insert(data_path='depth', frame=bpy.context.scene.frame_current)
        else:
            bpy.context.window_manager.popup_menu(lambda self, context: 
                self.layout.label(text="Current frame is not within the usable range."), 
                title="Warning", icon='ERROR')
                
                
# Placeholder class and def
class Placeholder:
    def nothing():
        # This method is a placeholder and does not perform any actions
        pass
