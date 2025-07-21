import bpy

#static method
class clear:
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

# Example usage:
# clear.clear_custom_props()
