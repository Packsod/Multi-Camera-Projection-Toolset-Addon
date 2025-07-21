import bpy

#static method
class misc:
    @staticmethod
    def clear_custom_props():
        def clear_props(obj):
            # Get the list of custom property names for the object
            keys_to_delete = list(obj.keys())
            for key in keys_to_delete:
                del obj[key]

            # Get the list of custom property names for the object's data block
            if obj.data:
                keys_to_delete = list(obj.data.keys())
                for key in keys_to_delete:
                    del obj.data[key]

        # Get all selected objects
        selected_objects = bpy.context.selected_objects

        if not selected_objects:
            # If no objects are selected, show a warning message
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="Please select some objects!"), title="Warning", icon='ERROR')
        else:
            # Clear custom properties for each selected object
            for obj in selected_objects:
                clear_props(obj)

            # Show a success message after clearing custom properties
            bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text="Custom properties cleared!"), title="Success", icon='CHECKMARK')


    @staticmethod
    def UV_sets_all():
        def ensure_two_uv_layers(mesh):
            """
            Ensure the mesh has only two UV layers named 'UVMap' and 'SimpleBake'.
            """
            uv_layers = mesh.uv_layers
            # Fill up UV layers
            while len(uv_layers) < 2:
                if len(uv_layers) == 0:
                    uv_layers.new(name='UVMap')
                else:
                    uv_layers.new(name='SimpleBake')
            # Remove extra UV layers
            while len(uv_layers) > 2:
                uv_layers.remove(uv_layers[-1])

            # Set names
            uv_layers[0].name = 'UVMap'
            uv_layers[1].name = 'SimpleBake'

        def get_current_active_uv_index(mesh):
            """
            Return the active_index of the first mesh with UV layers.
            """
            for m in bpy.data.meshes:
                if len(m.uv_layers) >= 2:
                    return m.uv_layers.active_index
            return 0  # Return 0 if no mesh has UV layers

        def set_all_meshes_active_uv(index):
            """
            Set the active_index for all meshes.
            """
            for mesh in bpy.data.meshes:
                if len(mesh.uv_layers) >= 2:
                    mesh.uv_layers.active_index = index
                    mesh.uv_layers[index].active_render = True  # For baking

        # Step 1: Ensure all meshes have only two UV layers and rename them
        for mesh in bpy.data.meshes:
            ensure_two_uv_layers(mesh)

        # Step 2: Determine which index to switch to
        current_active = get_current_active_uv_index(bpy.data.meshes[0])
        next_active = 1 if current_active == 0 else 0

        # Step 3: Synchronize the active UV index for all meshes
        set_all_meshes_active_uv(next_active)

        # Popup message
        uv_name = ['UVMap', 'SimpleBake'][next_active]
        def draw_popup(self, context):
            self.layout.label(text=f"Active UV layer for all meshes switched to {uv_name} (index {next_active})")
        bpy.context.window_manager.popup_menu(draw_popup, title="UV Layer Toggle", icon='INFO')





# Example usage:
# misc.clear_custom_props()
# misc.UV_sets_all()
