import bpy
import os
os.chdir(os.path.dirname(bpy.data.filepath))

class OverpaintCameraProjection(bpy.types.Operator):
    bl_idname = "object.overpaint_camera_projection"
    bl_label = "Overpaint Camera Projection"
    bl_options = {'REGISTER', 'UNDO'}
    camera_indexes: bpy.props.BoolVectorProperty(name="Camera Indexes", size=24)
    specified_camera: bpy.props.BoolProperty(name="Specify Camera Projection", default=False)

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

    def execute_projection(self, camera_indexes=None):
        bpy.ops.object.mode_set(mode='OBJECT')
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
        if camera_indexes is None:
            for i in self.available_camera_indexes:
                if self.CamP_objects[i-1] in bpy.data.objects:
                    try:
                        bpy.data.images.load(self.psd_op_paths[i-1], check_existing=True)
                        psd_op_in_data = self.psd_op_paths[i-1].split('/')[-1]
                        bpy.context.scene.camera = bpy.data.objects[self.CamP_objects[i-1]]
                        bpy.context.scene.render.resolution_x = bpy.data.images[psd_op_in_data].size[0]
                        bpy.context.scene.render.resolution_y = bpy.data.images[psd_op_in_data].size[1]
                        bpy.ops.paint.texture_paint_toggle()
                        bpy.context.scene.tool_settings.image_paint.seam_bleed = 0
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
                        bpy.context.scene.render.resolution_x = bpy.data.images[psd_op_in_data].size[0]
                        bpy.context.scene.render.resolution_y = bpy.data.images[psd_op_in_data].size[1]
                        bpy.ops.paint.texture_paint_toggle()
                        bpy.context.scene.tool_settings.image_paint.seam_bleed = 0
                        bpy.context.scene.tool_settings.image_paint.use_occlude = True
                        bpy.context.scene.tool_settings.image_paint.use_backface_culling = True
                        bpy.ops.paint.project_image(image=psd_op_in_data)
                        self.report({'INFO'}, 'Image projected successfully.')
                    except Exception as e:
                        self.popup_message(f"Camera {self.CamP_objects[i-1]} does not exist.")
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(active_obj_copy, do_unlink=True)
        for obj in selected_objs + [active_obj]:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active_obj
        return {'FINISHED'}  
    
    def execute(self, context):
        original_res_x = bpy.context.scene.render.resolution_x
        original_res_y = bpy.context.scene.render.resolution_y
        active_camera = bpy.context.scene.camera
        selected_camera_indexes = [i + 1 for i in range(24) if self.camera_indexes[i]]
        if self.specified_camera:
            if not selected_camera_indexes:
                self.popup_message("No camera selected. Please select a camera to proceed.")
                return {'CANCELLED'}
            camera_indexes = selected_camera_indexes
        else:
            camera_indexes = self.available_camera_indexes
        result = self.execute_projection(camera_indexes)
        bpy.context.scene.camera = active_camera
        bpy.context.scene.render.resolution_x = original_res_x
        bpy.context.scene.render.resolution_y = original_res_y
        return result
            
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "specified_camera")
        if not self.specified_camera:
            layout.label(text="Camera Indexes: All available")
        else:
            row = layout.row()
            for i in self.available_camera_indexes:
                row.prop(self, "camera_indexes", index=i-1, text=str(i))
                if i % 6 == 0:
                    row = layout.row()

    def invoke(self, context, event):
        active_obj = bpy.context.active_object
        if not active_obj:
            self.popup_message("No object selected. Please select a mesh object with an appropriate material for overpainting.")
            return {'CANCELLED'}
        if active_obj.type != 'MESH':
            self.popup_message("Selected object is not a mesh. Please select a mesh object with a suitable material for overpainting.")
            return {'CANCELLED'}
        if not active_obj.active_material:
            self.popup_message("The active object does not have an active material. Please select an object with a suitable material for overpainting.")
            return {'CANCELLED'}
        active_mat = active_obj.active_material
        nodes = active_mat.node_tree.nodes
        node_found = False
        for node in nodes:
            # Define a list of acceptable names
            acceptable_names = ["overpaint", "ov", "op", "project", "projecting", "billboard", "BR"]  # Add or modify as needed
            # Check if the node's image name or label is in the acceptable names list
            if node.bl_idname == 'ShaderNodeTexImage' and node.image and any(name.lower() in node.image.name.lower() or name.lower() in node.label.lower() for name in acceptable_names):
                node.select = True
                nodes.active = node
                node_found = True
                break

            # Check if the node in a group tree has an image with an acceptable name
            if node.bl_idname == 'ShaderNodeGroup':
                group_nodes = node.node_tree.nodes
                for group_node in group_nodes:
                    if group_node.bl_idname == 'ShaderNodeTexImage' and group_node.image and any(name.lower() in group_node.image.name.lower() or name.lower() in group_node.label.lower() for name in acceptable_names):
                        node.select = True
                        nodes.active = node
                        node_found = True
                        break

            if node_found:
                break
        if not node_found:
            self.popup_message("The active material does not use a image containing 'overpaint' in the name or label. Please select an object with a suitable material for overpainting.")
            return {'CANCELLED'}
        if not self.available_camera_indexes:
            self.popup_message("No PSD files found. Please make sure the PSD files exist in the specified paths.")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)

bpy.utils.register_class(OverpaintCameraProjection)
bpy.ops.object.overpaint_camera_projection('INVOKE_DEFAULT')
