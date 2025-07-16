import bpy

class AtlasGenerator:
    def __init__(self):
        import sys
        import bmesh
        import os
        self.bmesh = bmesh
        self.atlas = None
        self.bmeshes = []
        self.object_data = set()
        self.ngons = []
        self.python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
        self.import_modules()
        self.create_pack_options()

    def import_modules(self):
        import subprocess
        try:
            import xatlas
            self.xatlas = xatlas
        except ImportError:
            subprocess.call([self.python_exe, '-m', 'pip', 'install', 'xatlas'])
            try:
                import xatlas
                self.xatlas = xatlas
            except ImportError:
                self.show_message_box("Unable to install xatlas module to Blender's python environment", title="Installation Failed", icon='ERROR')
                return

    def create_pack_options(self):
        import xatlas #necessary
        self.pack_options = xatlas.PackOptions()
        self.pack_options.bruteForce = True
        self.pack_options.padding = 1
        self.pack_options.texels_per_unit = 16
        self.pixel_perfect = True

    def store_ngons(self, bm):
        for face in bm.faces:
            if len(face.verts) > 4:
                self.ngons.append([v.index for v in face.verts])

    def recreate_ngons(self, bm):
        bm.verts.ensure_lookup_table()  # Update the internal index table
        for ngon in self.ngons:
            verts = [bm.verts[i] for i in ngon if i < len(bm.verts)]
            if len(verts) >= 3:
                try:
                    bm.faces.new(verts)
                except ValueError:
                    # Some n-gons might not be possible to recreate
                    pass
        self.ngons = []  # Clear the data after recreating



    def add_to_atlas(self, object):
        if object.data in self.object_data:
            return
        self.object_data.add(object.data)
        bpy.context.view_layer.objects.active = object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bm = self.bmesh.new()
        bm.from_mesh(object.data)
        self.store_ngons(bm)
        # Triangulate the mesh
        self.bmesh.ops.triangulate(bm, faces=bm.faces)
        self.bmeshes.append((object, bm, len(self.bmeshes)))
        triangles = bm.calc_loop_triangles()
        indices = [[a.vert.index, b.vert.index, c.vert.index] for a, b, c in triangles]
        positions = [list(vert.co) for vert in bm.verts]
        if self.atlas is None:
            self.atlas = self.xatlas.Atlas()
        self.atlas.add_mesh(positions, indices)

    def convert_triangles_to_quads(self, object):
        # Switch to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Select all faces in the mesh
        bpy.context.view_layer.objects.active = object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.mark_seam(clear=False)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        # Convert triangles to quads
        bpy.ops.mesh.tris_convert_to_quads(
            face_threshold=3.1415927,
            shape_threshold=3.1415927,
            uvs=True, vcols=False, seam=True,
            sharp=False,
            materials=False
        )
        bpy.ops.mesh.mark_seam(clear=True)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')


    def generate_atlas(self):
        for obj in bpy.context.selected_objects:
            if obj.mode == 'EDIT':
                self.show_message_box(f"Object {obj.name} is in Edit Mode. Please exit Edit Mode and try again.", title="Error", icon='ERROR')
                return
        self.atlas.generate(verbose=True, pack_options=self.pack_options)
        aspect_ratio = self.atlas.width / self.atlas.height
        self.show_message_box(f"width {self.atlas.width} height {self.atlas.height} aspect ratio {aspect_ratio}")
        for i, (object, bm, mesh_index) in enumerate(self.bmeshes):
            self.apply_uv_coordinates(bm, i, mesh_index)
            self.recreate_ngons(bm)
            bm.to_mesh(object.data)
            bm.free()
            # Convert triangles to quads
            self.convert_triangles_to_quads(object)
        self.bmeshes.clear()
        self.object_data.clear()
        self.ngons = []  # Clear the data after recreating
        self.atlas = None  # Reset the atlas

    def apply_uv_coordinates(self, bm, i, mesh_index):
        if not "SimpleBake" in bm.loops.layers.uv:
            bm.loops.layers.uv.new("SimpleBake")
        uv_layer = bm.loops.layers.uv["SimpleBake"]
        vmapping, indices, uvs = self.atlas.get_mesh(mesh_index)
        triangles = bm.calc_loop_triangles()
        aspect_ratio = self.atlas.width / self.atlas.height
        for triangle, indices in zip(triangles, indices):
            for loop, uv in zip(triangle, uvs[indices]):
                if self.pixel_perfect:
                    uv[0] -= 0.5 / self.atlas.width
                    uv[1] -= 0.5 / self.atlas.height
                loop[uv_layer].uv = [uv[0] * aspect_ratio, uv[1]]
                
    @staticmethod
    def show_message_box(message="", title="Message Box", icon='INFO'):
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

# Create an instance of AtlasGenerator and add selected objects to the atlas
atlas_generator = AtlasGenerator()
for object in bpy.context.selected_objects:
    if object.type != "MESH":
        continue
    atlas_generator.add_to_atlas(object)
atlas_generator.generate_atlas()
