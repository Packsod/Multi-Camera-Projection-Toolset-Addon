import bpy
from bpy.types import Operator

class BackupCamPParametersOperator(Operator):
    bl_idname = "object.backup_camp_parameters"
    bl_label = "Backup CamP Parameters"
    from bpy.props import StringProperty
    backup_suffix: StringProperty(name="name (required)")

    def get_titles(self, context):
        titles = []
        if 'CamP_backups_list.md' in bpy.data.texts:
            backup_text = bpy.data.texts['CamP_backups_list.md']
            lines = backup_text.as_string().split('\n')
            for i, line in enumerate(lines):
                if line.startswith('------------------------------------') and 'CameraArchive_' in line and line.endswith('------------------------------------'):
                    title = line.split('CameraArchive_')[1].split('------------------------------------')[0].strip()
                    titles.append((title, title, ""))
        return titles

    def execute(self, context):
        backup_name = "CamP_backups_list.md"
        # Check if the text block exists
        if backup_name not in bpy.data.texts:
            backup_text = bpy.data.texts.new(backup_name)
        else:
            backup_text = bpy.data.texts[backup_name]
            # Move the cursor to the end of the text block
            backup_text.cursor_set(len(backup_text.as_string()))

        # Add a suffix to the title if provided, or use "base" if not
        title = "CameraArchive"
        if self.backup_suffix:
            title += "_" + self.backup_suffix
        else:
            title += "_base"

        # Check if the title with the same suffix already exists
        existing_title = f"------------------------------------{title}------------------------------------\n"
        existing_titles = [title[0] for title in self.get_titles(context)]
        if title.split('_')[-1] in existing_titles:
            # Replace the existing title and its data with the new data
            lines = backup_text.as_string().split('\n')
            title_without_newline = existing_title.strip()
            if title_without_newline in lines:
                start_idx = lines.index(title_without_newline)
                end_idx = start_idx + 1
                while end_idx < len(lines) and not lines[end_idx].startswith('------------------------------------'):
                    end_idx += 1
                # Create a new record for the given title
                new_record = [lines[start_idx]]  # Keep the existing title intact
                CamP_objects = [f"CamP_sub{str(i).zfill(2)}" for i in range(1, 25)]
                existing_CamP = [cam for cam in bpy.data.objects if cam.name in CamP_objects]
                for CamP in existing_CamP:
                    new_record.append(f"{CamP.name}")
                    new_record.append(f"Location: {CamP.location.x}, {CamP.location.y}, {CamP.location.z}")
                    new_record.append(f"Rotation: {CamP.rotation_euler.x}, {CamP.rotation_euler.y}, {CamP.rotation_euler.z}")
                    new_record.append(f"Lens: {CamP.data.lens}")
                    new_record.append(f"Shift X: {CamP.data.shift_x}")
                    new_record.append(f"Shift Y: {CamP.data.shift_y}")
                    new_record.append(f"Clip Start: {CamP.data.clip_start}")
                    new_record.append(f"Clip End: {CamP.data.clip_end}")
                    new_record.append(f"Sensor Width: {CamP.data.sensor_width}")
                    try:
                        new_record.append(f"Resolution X: {CamP.data.per_camera_resolution.resolution_x}")
                        new_record.append(f"Resolution Y: {CamP.data.per_camera_resolution.resolution_y}")
                    except AttributeError:
                        new_record.append(f"Resolution X: 1920")
                        new_record.append(f"Resolution Y: 1080")
                    # Adding the mist_settings.depth attribute
                    # Save the current frame
                    current_frame = bpy.context.scene.frame_current
                    # Set the current frame to the specific frame and record the mist_settings.depth attribute
                    frame_offset = int(CamP.name.split('sub')[1])  # extract the frame offset from the camera name
                    frame_number = 0 - frame_offset
                    bpy.context.scene.frame_set(frame_number)  # set the current frame to the specific frame
                    world_name = bpy.context.scene.world.name  # get the current world name
                    mist_depth = bpy.data.worlds[world_name].mist_settings.depth  # get the mist_settings.depth value for the current world and this frame
                    new_record.append(f"Mist Depth: {mist_depth}")
                    # Restore the current frame
                    bpy.context.scene.frame_set(current_frame)
                    new_record.append("------------------")
                    if CamP == existing_CamP[-1]:
                        new_record.append("")  # Add an extra line here only if it's the last camera
                # Replace the existing record with the new record
                lines[start_idx:end_idx] = new_record
                # Update the text block with the modified lines
                backup_text.from_string('\n'.join(lines))
            else:
                print(f"Title '{title}' not found in the text block.")
        else:
            # Write the title to the text block
            backup_text.write(existing_title)
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
                try:
                    backup_text.write(f"Resolution X: {CamP.data.per_camera_resolution.resolution_x}\n")
                    backup_text.write(f"Resolution Y: {CamP.data.per_camera_resolution.resolution_y}\n")
                except AttributeError:
                    backup_text.write(f"Resolution X: 1920\n")
                    backup_text.write(f"Resolution Y: 1080\n")
                # Adding the mist_settings.depth attribute
                # Save the current frame
                current_frame = bpy.context.scene.frame_current
                # Set the current frame to the specific frame and record the mist_settings.depth attribute
                frame_offset = int(CamP.name.split('sub')[1])  # extract the frame offset from the camera name
                frame_number = 0 - frame_offset
                bpy.context.scene.frame_set(frame_number)  # set the current frame to the specific frame
                world_name = bpy.context.scene.world.name  # get the current world name
                mist_depth = bpy.data.worlds[world_name].mist_settings.depth  # get the mist_settings.depth value for the current world and this frame
                backup_text.write(f"Mist Depth: {mist_depth}\n")
                # Restore the current frame
                bpy.context.scene.frame_set(current_frame)
                backup_text.write("------------------\n")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# Register the operator
bpy.utils.register_class(BackupCamPParametersOperator)

# Call the operator
bpy.ops.object.backup_camp_parameters('INVOKE_DEFAULT')
