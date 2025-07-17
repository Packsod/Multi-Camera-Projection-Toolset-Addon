import bpy

def main():
    """Main function to execute the AO baking process."""
    # Save the current render engine and scene
    current_render_engine = bpy.context.scene.render.engine
    current_scene = bpy.context.scene

    # Switch to Cycles render engine
    bpy.context.scene.render.engine = 'CYCLES'

    # Get selected mesh objects
    selected_objects = bpy.context.selected_objects
    mesh_objects = [obj for obj in selected_objects if obj.type == 'MESH']

    # Ensure the "AO" vertex color layer exists and activate it
    for obj in mesh_objects:
        if "AO" not in obj.data.vertex_colors:
            obj.data.vertex_colors.new(name="AO")
        obj.data.vertex_colors.active_index = obj.data.vertex_colors.keys().index("AO")

    # Bake AO to vertex colors for the specified object
    for obj in mesh_objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.context.scene.render.bake.use_selected_to_active = False
        bpy.context.scene.cycles.bake_type = 'AO'
        bpy.context.scene.render.bake.target = 'VERTEX_COLORS'
        bpy.ops.object.bake(type='AO')

    # Restore the original render engine and scene
    bpy.context.window.scene = current_scene
    bpy.context.scene.render.engine = current_render_engine

if __name__ == "__main__":
    main()
