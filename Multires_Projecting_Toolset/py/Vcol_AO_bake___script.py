import bpy

# Step 1: Save the current render engine and scene
current_render_engine = bpy.context.scene.render.engine
current_scene = bpy.context.scene

# Step 3: Bake AO to vertex colors
selected_objects = bpy.context.selected_objects
mesh_objects = [obj for obj in selected_objects if obj.type == 'MESH']
if mesh_objects:
    # Create a new scene
    bpy.ops.scene.new(type='NEW')
    new_scene = bpy.context.scene
    new_scene.render.engine = 'CYCLES'
    new_scene.cycles.device = 'GPU'
    new_scene.cycles.samples = 24
    # Link the selected mesh objects to the new scene
    for obj in mesh_objects:
        bpy.context.collection.objects.link(obj)
    # Switch to the new scene and bake AO to vertex colors
    bpy.context.window.scene = new_scene
    for obj in mesh_objects:
        # Check if "AO" vertex color layer exists
        if obj.data.vertex_colors and "AO" in obj.data.vertex_colors:
            # Activate "AO" vertex color layer
            obj.data.vertex_colors.active_index = obj.data.vertex_colors.keys().index("AO")
        else:
            # Create "AO" vertex color layer
            obj.data.vertex_colors.new(name="AO")
            obj.data.vertex_colors.active_index = len(obj.data.vertex_colors) - 1
        # Bake AO to vertex colors
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        new_scene.render.bake.use_selected_to_active = False
        new_scene.cycles.bake_type = 'AO'
        new_scene.render.bake.target = 'VERTEX_COLORS'
        bpy.ops.object.bake(type='AO')
    # Remove the new scene and switch back to the original scene
    bpy.ops.scene.delete()
    bpy.context.window.scene = current_scene
    # Switch back to the original render engine
    bpy.context.scene.render.engine = current_render_engine
