import bpy
import os
os.chdir(os.path.dirname(bpy.data.filepath))

class OverpaintCameraProjection(bpy.types.Operator):
    bl_idname = "object.overpaint_camera_projection"
    bl_label = "Overpaint Camera Projection"
    bl_options = {'REGISTER', 'UNDO'}
    camera_indexes: bpy.props.BoolVectorProperty(name="Camera Indexes", size=24)
    specified_camera: bpy.props.BoolProperty(name="Specify Camera Projection", default=False)
    merge_mesh: bpy.props.BoolProperty(name="Merge Mesh", default=False)

    def __init__(self):
        self.CamP_objects = [f"CamP_sub{str(i).zfill(2)}" for i in range(1, 25)]
        self.psd_op_paths = []
        self.available_camera_indexes = []
        self.image_modification_times = {}
        for i in range(1, 25):
            psd_image = f"CamP_sub{i:02d}_render.psd"
            if "Output_path_MP" in bpy.context.scene.node_tree.nodes:
                base_path = bpy.data.scenes[bpy.context.scene.name].node_tree.nodes["Output_path_MP"].base_path.replace("//", "")
                base_path = base_path.format(camera=f"CamP_sub{i:02d}")
                psd_path = os.path.relpath(os.path.join(os.path.dirname(bpy.data.filepath), base_path, psd_image), bpy.path.abspath("//"))
                psd_path = "//" + psd_path.replace("\\", "/")
            else:
                psd_path = os.path.join(os.path.dirname(bpy.data.filepath), f"multires_projecting/CamP_sub{str(i).zfill(2)}/{psd_image}")
            self.psd_op_paths.append(psd_path)
            if os.path.exists(bpy.path.abspath(psd_path)):
                self.available_camera_indexes.append(i)
                modification_time = os.path.getmtime(bpy.path.abspath(psd_path))
                if psd_image not in self.image_modification_times or self.image_modification_times[psd_image] != modification_time:
                    if psd_image not in bpy.data.images:
                        bpy.data.images.load(bpy.path.abspath(psd_path))
                    else:
                        bpy.data.images[psd_image].reload()
                    self.image_modification_times[psd_image] = modification_time

    def popup_message(self, message):
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title="Information", icon='INFO')

    def duplicate_object(self, obj):
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        bpy.context.collection.objects.link(new_obj)
        return new_obj

    def ensure_all_faces_selected(self, obj):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

    def execute_projection(self, camera_indexes=None, merged_obj=None):
        bpy.ops.object.mode_set(mode='OBJECT')
        if merged_obj is None:
            active_obj = bpy.context.active_object
            selected_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH' and obj != active_obj]
            active_obj_copy = self.duplicate_object(active_obj)
            selected_objs_copy = [self.duplicate_object(obj) for obj in selected_objs]

            for modifier in active_obj_copy.modifiers:
                bpy.context.view_layer.objects.active = active_obj_copy
                bpy.ops.object.modifier_apply(modifier=modifier.name)

            for obj in selected_objs_copy:
                if obj.material_slots:
                    for i in range(len(obj.material_slots)):
                        obj.material_slots[i].material = None
                for modifier in obj.modifiers:
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.modifier_apply(modifier=modifier.name)
                while obj.data.uv_layers:
                    obj.data.uv_layers.remove(obj.data.uv_layers[0])
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                active_obj_copy.select_set(True)
                bpy.context.view_layer.objects.active = active_obj_copy
                bpy.ops.object.join()
            for i in reversed(range(len(active_obj_copy.material_slots))):
                if active_obj_copy.material_slots[i].material is None:
                    active_obj_copy.active_material_index = i
                    bpy.ops.object.material_slot_remove()
        else:
            active_obj_copy = merged_obj

        if camera_indexes is None:
            for i in self.available_camera_indexes:
                if self.CamP_objects[i-1] in bpy.data.objects:
                    try:
                        bpy.data.images.load(self.psd_op_paths[i-1], check_existing=True)
                        psd_op_in_data = self.psd_op_paths[i-1].split('/')[-1]
                        bpy.context.scene.camera = bpy.data.objects[self.CamP_objects[i-1]]
                        bpy.ops.paint.texture_paint_toggle()
                        bpy.context.scene.tool_settings.image_paint.seam_bleed = 3
                        bpy.context.scene.tool_settings.image_paint.use_occlude = True
                        bpy.context.scene.tool_settings.image_paint.use_backface_culling = True
                        bpy.ops.paint.project_image(image=psd_op_in_data)
                        self.report({'INFO'}, 'Image projected successfully.')
                    except Exception as e:
                        self.popup_message(f"Error occurred: {e}")
        else:
            for i in camera_indexes:
                if self.CamP_objects[i-1] in bpy.data.objects:
                    try:
                        bpy.data.images.load(self.psd_op_paths[i-1], check_existing=True)
                        psd_op_in_data = self.psd_op_paths[i-1].split('/')[-1]
                        bpy.context.scene.camera = bpy.data.objects[self.CamP_objects[i-1]]
                        bpy.ops.paint.texture_paint_toggle()
                        bpy.context.scene.tool_settings.image_paint.seam_bleed = 0
                        bpy.context.scene.tool_settings.image_paint.use_occlude = True
                        bpy.context.scene.tool_settings.image_paint.use_backface_culling = True
                        bpy.ops.paint.project_image(image=psd_op_in_data)
                        self.report({'INFO'}, 'Image projected successfully.')
                    except Exception as e:
                        self.popup_message(f"Camera {self.CamP_objects[i-1]} does not exist.")
        bpy.ops.object.mode_set(mode='OBJECT')
        if merged_obj is None:
            bpy.data.objects.remove(active_obj_copy, do_unlink=True)
        return {'FINISHED'}

    def execute(self, context):
        original_global_undo = bpy.context.preferences.edit.use_global_undo
        bpy.context.preferences.edit.use_global_undo = False

        active_camera = bpy.context.scene.camera
        selected_camera_indexes = [i + 1 for i in range(24) if self.camera_indexes[i]]
        if self.specified_camera:
            if not selected_camera_indexes:
                self.popup_message("No camera selected. Please select a camera to proceed.")
                bpy.context.preferences.edit.use_global_undo = original_global_undo
                return {'CANCELLED'}
            camera_indexes = selected_camera_indexes
        else:
            camera_indexes = self.available_camera_indexes

        active_obj = bpy.context.active_object
        selected_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH' and obj != active_obj]

        if self.merge_mesh and selected_objs:
            # Create a merged copy of active and selected objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objs:
                obj.select_set(True)
            active_obj.select_set(True)
            bpy.context.view_layer.objects.active = active_obj
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
            bpy.ops.object.join()
            merged_obj = bpy.context.active_object
            self.ensure_all_faces_selected(merged_obj)
        else:
            merged_obj = None

        result = self.execute_projection(camera_indexes, merged_obj)
        bpy.context.scene.camera = active_camera
        if merged_obj:
            bpy.data.objects.remove(merged_obj, do_unlink=True)
        # Restore original selection and active object
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objs:
            obj.select_set(True)
        active_obj.select_set(True)
        bpy.context.view_layer.objects.active = active_obj

        bpy.context.preferences.edit.use_global_undo = original_global_undo
        return result

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "specified_camera")
        row.prop(self, "merge_mesh")

        if not self.specified_camera:
            layout.label(text="Camera Indexes: All available")
        else:
            for i in range(0, 24, 6):
                row = layout.row()
                for j in range(i, min(i + 6, 24)):
                    index = j + 1
                    if index in self.available_camera_indexes:
                        row.prop(self, "camera_indexes", index=j, text=str(index))

    def invoke(self, context, event):
        active_obj = bpy.context.active_object
        if not active_obj:
            self.popup_message("No object selected. Please select an object to proceed.")
            return {'CANCELLED'}
        if active_obj.type != 'MESH':
            self.popup_message("Selected object is not a mesh. Please select a mesh object.")
            return {'CANCELLED'}
        if not active_obj.active_material:
            self.popup_message("The active object does not have an active material. Please assign a material.")
            return {'CANCELLED'}
        active_mat = active_obj.active_material
        nodes = active_mat.node_tree.nodes
        node_found = False
        for node in nodes:
            # Define a list of acceptable names
            acceptable_names = ["overpaint", "ov", "op", "project", "projecting", "billboard", "BR"]  # Add or modify as needed
            # Check if the node's image name or label is in the acceptable names list
            if node.bl_idname == 'ShaderNodeTexImage' and node.image and any(name.lower() in node.image.name.lower() or name.lower() in node.label.lower() for name in acceptable_names):
                nodes.active = None
                node.select = True
                nodes.active = node
                node_found = True
                break

            # Check if the node in a group tree has an image with an acceptable name
            if node.bl_idname == 'ShaderNodeGroup':
                group_nodes = node.node_tree.nodes
                group_nodes.active = None
                for group_node in group_nodes:
                    if group_node.bl_idname == 'ShaderNodeTexImage' and group_node.image and any(name.lower() in group_node.image.name.lower() or name.lower() in group_node.label.lower() for name in acceptable_names):
                        group_nodes.active = None
                        group_node.select = True
                        group_nodes.active = group_node
                        node_found = True
                        break

            if node_found:
                break
        if not node_found:
            self.popup_message("The active material does not use an image containing 'overpaint' in the name or label. Please assign a material with the correct image.")
            return {'CANCELLED'}
        if not self.available_camera_indexes:
            self.popup_message("No PSD files found. Please ensure the PSD files exist in the specified paths.")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)

bpy.utils.register_class(OverpaintCameraProjection)
bpy.ops.object.overpaint_camera_projection('INVOKE_DEFAULT')
