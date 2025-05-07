import bpy

class InvisibleMeshHider:
    def __init__(self, active_obj, selected_objs, cam, scene, limit=0.0001):
        # Check if active object is a mesh object
        if active_obj.type == 'MESH':
            self.active_obj = active_obj
        else:
            self.active_obj = None
            bpy.context.window_manager.popup_menu(self.popup_draw_not_mesh, title="Invisible Mesh Hider", icon='ERROR')
            return
        # Ignore non-mesh objects from selected objects
        self.selected_objs = [obj for obj in selected_objs if obj.type == 'MESH']
        self.cam = cam
        self.scene = scene
        self.limit = limit
        self.visible_vertices_per_frame = []
        self.invisible_vertices = []
        self.bvh = None
        self.vertices = []
        self.current_frame = self.scene.frame_current
        self.merged_obj = None
        self.selected_obj_copies = []

    def merge_selected_objects(self):
        bpy.ops.object.select_all(action='DESELECT')
        self.merged_obj = self.active_obj.copy()
        self.merged_obj.data = self.active_obj.data.copy()
        bpy.context.collection.objects.link(self.merged_obj)
        self.merged_obj.select_set(True)
        bpy.context.view_layer.objects.active = self.merged_obj
        for obj in self.selected_objs:
            if obj != self.active_obj:
                obj_copy = obj.copy()
                obj_copy.data = obj_copy.data.copy()
                bpy.context.collection.objects.link(obj_copy)
                bpy.context.view_layer.objects.active = obj_copy
                # Apply modifiers to the copied object
                for modifier in obj_copy.modifiers:
                    bpy.ops.object.modifier_apply(modifier=modifier.name)
                self.selected_obj_copies.append(obj_copy)
                obj_copy.select_set(True)  # Deselect the object copy before joining
        self.merged_obj.select_set(True)
        bpy.context.view_layer.objects.active = self.merged_obj
        bpy.ops.object.join()

    def separate_merged_object(self):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(self.merged_obj, do_unlink=True)
        self.merged_obj = None
        bpy.ops.object.select_all(action='DESELECT')
        self.active_obj.select_set(True)
        bpy.context.view_layer.objects.active = self.active_obj

    def bvh_tree_and_vertices_in_world(self):
        from mathutils.bvhtree import BVHTree
        mWorld = self.merged_obj.matrix_world
        self.vertices = [mWorld @ v.co for v in self.merged_obj.data.vertices]
        self.bvh = BVHTree.FromPolygons(self.vertices, [p.vertices for p in self.merged_obj.data.polygons])

    def deselect_edges_and_polygons(self):
        for p in self.active_obj.data.polygons:
            p.select = False
        for e in self.active_obj.data.edges:
            e.select = False

    def get_visible_vertices_per_frame(self):
        # Check if active object is a mesh object
        if self.active_obj is None:
            return
        from bpy_extras.object_utils import world_to_camera_view
        start_frame = self.scene.frame_start
        end_frame = self.scene.frame_end
        self.visible_vertices_per_frame = [[] for _ in range(end_frame + 1)]
        self.merge_selected_objects()
        for frame in range(start_frame, end_frame + 1):
            self.scene.frame_set(frame)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.reveal()
            self.deselect_edges_and_polygons()
            bpy.ops.object.mode_set(mode='OBJECT')
            self.bvh_tree_and_vertices_in_world()
            active_obj_vertex_count = len(self.active_obj.data.vertices)
            for i, v in enumerate(self.vertices[:active_obj_vertex_count]):
                co2D = world_to_camera_view(self.scene, self.cam, v)
                if 0.0 <= co2D.x <= 1.0 and 0.0 <= co2D.y <= 1.0:
                    location, normal, index, distance = self.bvh.ray_cast(self.cam.location, (v - self.cam.location).normalized())
                    if location and (v - location).length < self.limit:
                        self.visible_vertices_per_frame[frame].append(i)
            if not self.visible_vertices_per_frame[frame]:
                # If no vertices are visible at this frame, break the loop
                break
            del self.bvh
        self.invisible_vertices = set(range(active_obj_vertex_count)) - set(vertex for frame_vertices in self.visible_vertices_per_frame for vertex in frame_vertices)
        self.separate_merged_object()
        self.scene.frame_set(self.current_frame)
        bpy.context.window_manager.popup_menu(self.popup_draw, title="Invisible Mesh Hider", icon='INFO')

    def select_and_hide_invisible_meshes(self):
        # Check if active object is a mesh object
        if self.active_obj is None:
            return
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for i in self.invisible_vertices:
            self.active_obj.data.vertices[i].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        self.scene.frame_set(self.current_frame)
        bpy.context.window_manager.popup_menu(self.popup_draw, title="Invisible Mesh Hider", icon='INFO')

    def popup_draw(self, self2, context):
        layout = self2.layout
        layout.label(text="Calculation completed.")
        return None

    def popup_draw_not_mesh(self, self2, context):
        layout = self2.layout
        layout.label(text="Active object is not a mesh object. Please select a mesh object and try again.")
        return None

# To use the class, create an instance of it for each selected mesh object and call its methods
cam = bpy.context.scene.camera
scene = bpy.context.scene
active_object = bpy.context.active_object
selected_objects = bpy.context.selected_objects

mesh_hider = InvisibleMeshHider(active_object, selected_objects, cam, scene)
mesh_hider.get_visible_vertices_per_frame()
mesh_hider.select_and_hide_invisible_meshes()
