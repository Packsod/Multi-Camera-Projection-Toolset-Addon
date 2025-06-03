import bpy
import os

class OverpaintCameraBatchProjection(bpy.types.Operator):
    bl_idname = "object.overpaint_camera_batch_projection"
    bl_label = "Overpaint Camera Batch Projection"
    bl_options = {'REGISTER', 'UNDO'}

    image_directory: bpy.props.StringProperty(name="Image Directory", subtype='DIR_PATH')
    start_frame: bpy.props.IntProperty(name="Start Frame", default=bpy.context.scene.frame_start, min=0)
    end_frame: bpy.props.IntProperty(name="End Frame", default=bpy.context.scene.frame_end, min=0)
    skip_first_images: bpy.props.IntProperty(name="Skip First Images", default=7, min=0)
    project_every_nth: bpy.props.IntProperty(name="Project Every nth", default=2, min=1)
    merge_mesh: bpy.props.BoolProperty(name="Merge Mesh", default=False)

    def execute(self, context):
        original_frame = bpy.context.scene.frame_current
        bpy.context.scene.frame_set(self.start_frame)
        import re
        # Get all image files in the directory
        image_files = [f for f in os.listdir(self.image_directory) if os.path.isfile(os.path.join(self.image_directory, f))]
        image_files.sort(key=lambda x: int(re.search(r'\d+', x).group()))

        # Skip the first images
        image_files = image_files[self.skip_first_images:]

        # If merging mesh, duplicate and join active and selected objects
        active_obj = bpy.context.active_object
        selected_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH' and obj != active_obj]
        merged_obj = None

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

        for frame in range(self.start_frame, self.end_frame + 1, self.project_every_nth):
            if frame >= bpy.context.scene.frame_start and frame <= bpy.context.scene.frame_end:
                bpy.context.scene.frame_set(frame)
                image_path = os.path.join(self.image_directory, image_files[frame - self.start_frame - self.skip_first_images])
                image_name = os.path.basename(image_path)
                bpy.data.images.load(image_path, check_existing=True)
                bpy.context.scene.camera = bpy.context.scene.camera
                bpy.ops.paint.texture_paint_toggle()
                bpy.context.scene.tool_settings.image_paint.seam_bleed = 3
                bpy.context.scene.tool_settings.image_paint.use_occlude = True
                bpy.context.scene.tool_settings.image_paint.use_backface_culling = True
                if merged_obj:
                    bpy.context.view_layer.objects.active = merged_obj
                bpy.ops.paint.project_image(image=image_name)
                bpy.ops.paint.texture_paint_toggle()  # Exit texture paint mode

        bpy.context.scene.frame_set(original_frame)
        if merged_obj:
            bpy.data.objects.remove(merged_obj, do_unlink=True)
        if merged_obj is None:
            bpy.data.objects.remove(active_obj_copy, do_unlink=True)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "image_directory")
        layout.prop(self, "merge_mesh")
        layout.prop(self, "start_frame")
        layout.prop(self, "end_frame")
        layout.prop(self, "skip_first_images")
        layout.prop(self, "project_every_nth")

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
            acceptable_names = ["overpaint", "ov", "op", "project", "projecting", "billboard", "BR"]
            if node.bl_idname == 'ShaderNodeTexImage' and node.image and any(name.lower() in node.image.name.lower() or name.lower() in node.label.lower() for name in acceptable_names):
                nodes.active = None
                node.select = True
                nodes.active = node
                node_found = True
                break
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
                    # Activate the group node in the shader node tree
                    node.select = True
                    nodes.active = node
                    break
            if node_found:
                break
        if not node_found:
            self.popup_message("The active material does not use an image containing 'overpaint' in the name or label. Please select an object with a suitable material for overpainting.")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)

    def popup_message(self, message):
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title="Information", icon='INFO')

# Register the operator if it hasn't been registered yet
if OverpaintCameraBatchProjection.bl_idname not in bpy.types.Operator.__subclasses__():
    bpy.utils.register_class(OverpaintCameraBatchProjection)

bpy.ops.object.overpaint_camera_batch_projection('INVOKE_DEFAULT')
