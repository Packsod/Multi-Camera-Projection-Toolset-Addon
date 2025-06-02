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
    def CamP_fit_to_active():
        active_camera = bpy.context.scene.camera
        if not active_camera:
            bpy.context.window_manager.popup_menu(
                lambda self, context: self.layout.label(text="Error: No active camera."),
                title="Error",
                icon='ERROR'
            )
            return

        cam_list = [f"CamP_sub{str(i).zfill(2)}" for i in range(1, 25)]
        cam_objects = {name: bpy.data.objects.get(name) for name in cam_list}
        existing_cam_names = [name for name, cam in cam_objects.items() if cam]

        class CamP_fit_to_active_Operator(bpy.types.Operator):
            bl_idname = "object.camp_fit_to_active"
            bl_label = "CamP_fit_to_active"
            bl_options = {'REGISTER'}

            selected_cam_index: bpy.props.IntProperty(name="CamP ind(1~24)", description="Specific a CamP_sub to apply", default=1, min=1, max=24)

            def invoke(self, context, event):
                wm = context.window_manager
                return wm.invoke_props_dialog(self)

            def execute(self, context):
                selected_cam_name = f"CamP_sub{str(self.selected_cam_index).zfill(2)}"
                target_cam = bpy.data.objects.get(selected_cam_name)
                if target_cam:
                    if active_camera and context.space_data.region_3d.view_perspective == 'CAMERA':
                        active_cam_data = active_camera.data
                        for attr in ["lens", "shift_x", "shift_y", "clip_start", "clip_end", "sensor_width"]:
                            setattr(target_cam.data, attr, getattr(active_cam_data, attr))
                        target_cam.location = active_camera.location
                        target_cam.rotation_euler = active_camera.rotation_euler
                    else:
                        target_cam.matrix_world = context.region_data.view_matrix.inverted()
                        for attr in ["lens", "clip_start", "clip_end"]:
                            setattr(target_cam.data, attr, getattr(context.space_data, attr))
                    self.report({'INFO'}, f"CamP_sub{self.selected_cam_index} updated successfully.")
                else:
                    bpy.context.window_manager.popup_menu(
                        lambda self, context: self.layout.label(text=f"Error: Camera {selected_cam_name} does not exist."),
                        title="Error",
                        icon='ERROR'
                    )
                return {'FINISHED'}

        # Register the operator if it hasn't been registered yet
        if CamP_fit_to_active_Operator.bl_idname not in bpy.types.Operator.__subclasses__():
            bpy.utils.register_class(CamP_fit_to_active_Operator)

        bpy.ops.object.camp_fit_to_active('INVOKE_DEFAULT')
                
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

class Cam_Main:
    @staticmethod
    def MainCam_Switch():
        class MainCamSwitchOperator(bpy.types.Operator):
            """Bind Camera to Marker"""
            bl_idname = "object.main_cam_switch"
            bl_label = "MainCam Switch"
            bl_options = {'REGISTER', 'UNDO'}

            def get_camera_items(self, context):
                items = []
                for obj in bpy.data.objects:
                    if obj.type == 'CAMERA' and not (obj.name.startswith("CamO_sub") or obj.name.startswith("CamP_sub")):
                        items.append((obj.name, obj.name, ""))
                return items

            camera_name: bpy.props.EnumProperty(
                name="Camera",
                items=get_camera_items
            )

            def __init__(self):
                # Get the marker at the first frame
                scene = bpy.context.scene
                frame_number = 1  # First frame in the timeline
                camera_name = None

                for marker in scene.timeline_markers:
                    if marker.frame == frame_number:
                        camera_name = marker.camera.name
                        break

                # If no marker, use the first valid camera as default
                if camera_name is None:
                    camera_objects = [obj for obj in bpy.data.objects if obj.type == 'CAMERA' and not (obj.name.startswith("CamO_sub") or obj.name.startswith("CamP_sub"))]
                    if camera_objects:
                        camera_name = camera_objects[0].name

                # Set the default value
                self.camera_name = camera_name

            def execute(self, context):
                if self.camera_name in bpy.data.objects:
                    camera = bpy.data.objects[self.camera_name]
                    scene = bpy.context.scene
                    frame_number = 1  # First frame in the timeline

                    # Check if there's already a marker at the first frame
                    existing_marker = None
                    for marker in scene.timeline_markers:
                        if marker.frame == frame_number:
                            existing_marker = marker
                            break

                    if existing_marker:
                        # If the marker already exists, update its camera
                        existing_marker.camera = camera
                    else:
                        # If no marker exists at the first frame, create a new one
                        new_marker = scene.timeline_markers.new(name="Camera Marker", frame=frame_number)
                        new_marker.camera = camera

                else:
                    self.report({'ERROR'}, "Camera not found")
                return {'FINISHED'}

            def invoke(self, context, event):
                return context.window_manager.invoke_props_dialog(self)

        # Register the operator if it hasn't been registered yet
        if MainCamSwitchOperator.bl_idname not in bpy.types.Operator.__subclasses__():
            bpy.utils.register_class(MainCamSwitchOperator)

        bpy.ops.object.main_cam_switch('INVOKE_DEFAULT')

    @staticmethod
    def MainCam_Anim_Bake():
        class MainCamAnimBakeOperator(bpy.types.Operator):
            """MainCam Anim Bake"""
            bl_idname = "object.main_cam_anim_bake"
            bl_label = "MainCam Anim Bake"
            bl_options = {'REGISTER', 'UNDO'}

            def get_camera_items(self, context):
                items = []
                for obj in bpy.data.objects:
                    if obj.type == 'CAMERA' and not (obj.name.startswith("CamO") or obj.name.startswith("CamP")):
                        items.append((obj.name, obj.name, ""))
                return items

            camera_name: bpy.props.EnumProperty(
                name="Camera Name",
                items=get_camera_items
            )

            start_frame: bpy.props.IntProperty(
                name="Start Frame",
                default=bpy.context.scene.frame_start,
                description="The start frame for baking the animation"
            )

            end_frame: bpy.props.IntProperty(
                name="End Frame",
                default=bpy.context.scene.frame_end,
                description="The end frame for baking the animation"
            )

            def execute(self, context):
                original_start_frame = bpy.context.scene.frame_start
                original_end_frame = bpy.context.scene.frame_end

                if self.camera_name in bpy.data.objects:
                    source_camera = bpy.data.objects[self.camera_name]
                    # Duplicate the source camera
                    bpy.ops.object.select_all(action='DESELECT')
                    source_camera.select_set(True)
                    bpy.context.view_layer.objects.active = source_camera
                    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
                    target_camera = bpy.context.active_object

                    # Rename the target camera
                    target_camera.name = f"{self.camera_name}_baked"

                    # Rename the target camera's data
                    target_camera.data.name = f"{self.camera_name}_baked"

                    # Bake the source camera's animation to the target camera
                    self.bake_camera_animation(source_camera, target_camera, self.start_frame, self.end_frame)

                else:
                    self.report({'ERROR'}, "Camera not found")

                # Restore original frame range
                bpy.context.scene.frame_start = original_start_frame
                bpy.context.scene.frame_end = original_end_frame

                return {'FINISHED'}

            def bake_camera_animation(self, source_camera, target_camera, start_frame, end_frame):
                # Select the target camera
                bpy.context.view_layer.objects.active = target_camera
                target_camera.select_set(True)

                # Set the frame range
                bpy.context.scene.frame_start = start_frame
                bpy.context.scene.frame_end = end_frame

                # Bake the animation
                bpy.ops.object.select_all(action='DESELECT')
                target_camera.select_set(True)
                bpy.context.view_layer.objects.active = target_camera
                bpy.ops.nla.bake(frame_start=start_frame, frame_end=end_frame, step=1, only_selected=True, visual_keying=True, clear_constraints=True, clear_parents=True, bake_types={'OBJECT'}, use_current_action=False)

            def invoke(self, context, event):
                return context.window_manager.invoke_props_dialog(self)

        # Register the operator if it hasn't been registered yet
        if MainCamAnimBakeOperator.bl_idname not in bpy.types.Operator.__subclasses__():
            bpy.utils.register_class(MainCamAnimBakeOperator)

        bpy.ops.object.main_cam_anim_bake('INVOKE_DEFAULT')

                
# Placeholder class and def
class Placeholder:
    def nothing():
        # This method is a placeholder and does not perform any actions
        pass
