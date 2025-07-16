import bpy

def switch_uv_layers():
    # List of all meshes
    meshes = list(bpy.data.meshes)
    uv_changed = False  # Flag to track UV layer changes
    active_uv_layer = ''  # Variable to store the name of the activated UV layer
    layer_names = ['SimpleBake', 'Caustic'] # without 'UVMap', because it is in slotindex 0, iteration starts from 1

    for mesh in meshes:
        if mesh.uv_layers:
            try:
                mesh.uv_layers[0].name = 'UVMap'
            except RuntimeError:
                pass
            for uv_layer in reversed(mesh.uv_layers[1:]):
                if uv_layer.name not in layer_names:
                    try:
                        mesh.uv_layers.remove(uv_layer)
                    except RuntimeError:
                        continue
            # Check if 'SimpleBake' exists, if not, create a new one
            if 'SimpleBake' not in mesh.uv_layers:
                mesh.uv_layers.new(name='SimpleBake')
        else:
            # If no UV layers exist, create both 'UVMap' and 'SimpleBake'
            mesh.uv_layers.new(name='UVMap')
            mesh.uv_layers.new(name='SimpleBake')

        # Check the active UV layer of the first mesh
        if len(meshes) > 0:
            if meshes[0].uv_layers.active.name == 'UVMap':
                # If the first mesh's active UV layer is 'UVMap', set 'SimpleBake' active for the current mesh
                if 'SimpleBake' in mesh.uv_layers:
                    mesh.uv_layers['SimpleBake'].active = True
                    active_uv_layer = 'SimpleBake'
                    uv_changed = True
            elif meshes[0].uv_layers.active.name == 'SimpleBake':
                # If the first mesh's active UV layer is 'SimpleBake', set 'UVMap' active for the current mesh
                if 'UVMap' in mesh.uv_layers:
                    mesh.uv_layers['UVMap'].active = True
                    active_uv_layer = 'UVMap'
                    uv_changed = True

    def draw_popup(self, context):
        self.layout.label(text=f"Active UV layer has been switched to {active_uv_layer}")

    # Display the popup
    bpy.context.window_manager.popup_menu(draw_popup, title="UV Layer Switch", icon='INFO')
    return active_uv_layer

# Run the function and get the active UV layer
active_uv_layer = switch_uv_layers()