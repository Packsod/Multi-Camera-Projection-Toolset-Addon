import bpy
from bpy.types import Operator, PropertyGroup, UIList
import os

class PATH_INFO_OT_Info(Operator):
    bl_idname = "object.path_info"
    bl_label = "Path Info"
    bl_description = "Copy all title folder paths to clipboard"

    def execute(self, context):
        backup_text = bpy.data.texts.get('CamP_backups_list.md')
        if backup_text is not None:
            lines = backup_text.as_string().split('\n')
            paths = []
            for line in lines:
                if line.startswith('------------------------------------') and 'CameraArchive_' in line and line.endswith('------------------------------------'):
                    title = line.split('CameraArchive_')[1].split('------------------------------------')[0].strip()
                    base_path = f"//multires_projecting/{title}/"
                    abs_path = bpy.path.abspath(base_path)
                    paths.append(abs_path)
            if paths:
                bpy.context.window_manager.clipboard = '\n'.join(paths)
                self.report({'INFO'}, "Paths copied to clipboard.")
            else:
                self.report({'WARNING'}, "No paths found.")
        else:
            self.report({'WARNING'}, "No 'CamP_backups_list.md' text block found.")
        return {'FINISHED'}

class RESTORE_OT_CamPParameters(Operator):
    bl_idname = "object.restore_camp_parameters"
    bl_label = "Restore CamP Parameters"
    title_index: bpy.props.IntProperty(name="Title Index", default=0)
    title: bpy.props.StringProperty(name="Backup Title")
    titles: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        if self.title_index < len(self.titles):
            self.title = self.titles[self.title_index].name  # Set the title property based on the selected index
            result = self.restore_camera_parameters()
            if result == {'FINISHED'}:
                self.update_base_path()
            return result
        else:
            self.report({'WARNING'}, "Invalid backup index.")
            return {'CANCELLED'}

    def restore_camera_parameters(self):
        backup_text = bpy.data.texts.get('CamP_backups_list.md')
        if backup_text is not None:
            lines = backup_text.as_string().split('\n')
            i = 0
            title_found = False
            while i < len(lines):
                if lines[i] == f'------------------------------------CameraArchive_{self.title}------------------------------------':
                    title_found = True
                elif lines[i].startswith('------------------------------------CameraArchive_'):
                    title_found = False
                if title_found:
                    cam = bpy.data.objects.get(lines[i])
                    if cam is not None and cam.type == 'CAMERA':
                        self.apply_parameters(cam, lines[i + 1:i + 12])
                        i += 12
                        continue
                i += 1
        else:
            self.report({'WARNING'}, "No 'CamP_backups_list.md' text block found.")
            return {'CANCELLED'}
        return {'FINISHED'}

    @staticmethod
    def apply_parameters(cam, lines):
        import math
        prop_map = {
            'Location': lambda x: [float(i) for i in x.split(',')],
            'Rotation': lambda x: [math.degrees(float(i)) for i in x.split(',')],
            'Lens': float,
            'Shift X': float,
            'Shift Y': float,
            'Clip Start': float,
            'Clip End': float,
            'Sensor Width': float,
            'Resolution X': int,
            'Resolution Y': int,
            'Mist Depth': float,
        }
        # Save the current frame
        current_frame = bpy.context.scene.frame_current
        for line in lines:
            if ': ' in line:
                prop, value = line.split(': ', 1)
                if prop in prop_map:
                    value = prop_map[prop](value)
                    if prop == 'Rotation':
                        cam.rotation_euler = [math.radians(val) for val in value]
                    elif prop == 'Location':
                        cam.location = value
                    elif prop in ['Resolution X']:
                        try:
                            cam.data.per_camera_resolution.resolution_x = int(value)
                        except AttributeError:
                            pass
                    elif prop in ['Resolution Y']:
                        try:
                            cam.data.per_camera_resolution.resolution_y = int(value)
                        except AttributeError:
                            pass
                    elif prop == 'Mist Depth':
                        # Set the frame for the camera
                        frame_offset = int(cam.name.split('sub')[1])
                        frame_number = 0 - frame_offset
                        bpy.context.scene.frame_set(frame_number)
                        # Set the mist depth for the current world and frame
                        world = bpy.context.scene.world
                        world.mist_settings.depth = value
                        # Insert a keyframe at the current frame
                        world.mist_settings.keyframe_insert(data_path='depth', frame=frame_number)
                    else:
                        setattr(cam.data, prop.lower().replace(' ', '_'), value)
        # Restore the current frame
        bpy.context.scene.frame_set(current_frame)

    def get_titles(self, context):
        backup_text = bpy.data.texts.get('CamP_backups_list.md')
        if backup_text is not None:
            lines = backup_text.as_string().split('\n')
            for i, line in enumerate(lines):
                if line.startswith('------------------------------------') and 'CameraArchive_' in line and line.endswith('------------------------------------'):
                    title = line.split('CameraArchive_')[1].split('------------------------------------')[0].strip()
                    item = self.titles.add()
                    item.name = title

    def update_titles(self, context):
        self.titles.clear()
        self.get_titles(context)

    def invoke(self, context, event):
        self.update_titles(context)
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.update_titles(context)
        layout = self.layout
        row = layout.row()
        row.template_list("UI_UL_list", "titles", self, "titles", self, "title_index", rows=5)
        remove_op = row.operator("object.remove_camp_backup", text="", icon="TRASH")
        if self.title_index < len(self.titles):
            remove_op.title = self.titles[self.title_index].name
        info_op = row.operator("object.path_info", text="", icon="INFO")
        self.update_titles(context)

    def update_base_path(self):
        base_path = bpy.data.scenes[bpy.context.scene.name].node_tree.nodes["Output_path_MP"].base_path
        new_base_path = f"//multires_projecting/{self.title}/{{camera}}"
        base_path = new_base_path
        bpy.data.scenes[bpy.context.scene.name].node_tree.nodes["Output_path_MP"].base_path = new_base_path

class REMOVE_OT_CamPBackup(Operator):
    bl_idname = "object.remove_camp_backup"
    bl_label = "Remove CamP Backup"
    title: bpy.props.StringProperty(name="Backup Title")
    titles: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        backup_text = bpy.data.texts.get('CamP_backups_list.md')
        if backup_text is not None:
            lines = backup_text.as_string().split('\n')
            title = self.title  # Use the title property
            start_title = f'------------------------------------CameraArchive_{title}------------------------------------'
            if start_title in lines:
                end_title = '------------------'
                start_idx = lines.index(start_title)
                try:
                    end_idx = start_idx + lines[start_idx:].index(end_title) + 1
                    while end_idx < len(lines) and not lines[end_idx].startswith('------------------------------------CameraArchive_'):
                        end_idx += lines[end_idx:].index(end_title) + 1
                except ValueError:
                    end_idx = len(lines)
                lines = lines[:start_idx] + lines[end_idx:]
                backup_text.from_string('\n'.join(lines).rstrip('\n') + '\n')
            else:
                self.report({'WARNING'}, f"No backup found with the title '{title}'.")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "No 'CamP_backups_list.md' text block found.")
            return {'CANCELLED'}
        return {'FINISHED'}

    def get_titles(self, context):
        backup_text = bpy.data.texts.get('CamP_backups_list.md')
        if backup_text is not None:
            lines = backup_text.as_string().split('\n')
            for i, line in enumerate(lines):
                if line.startswith('------------------------------------') and 'CameraArchive_' in line and line.endswith('------------------------------------'):
                    title = line.split('CameraArchive_')[1].split('------------------------------------')[0].strip()
                    item = self.titles.add()
                    item.name = title

    def invoke(self, context, event):
        self.titles.clear()
        self.get_titles(context)
        return self.execute(context)

bpy.utils.register_class(PATH_INFO_OT_Info)
bpy.utils.register_class(RESTORE_OT_CamPParameters)
bpy.utils.register_class(REMOVE_OT_CamPBackup)
bpy.ops.object.restore_camp_parameters('INVOKE_DEFAULT')
