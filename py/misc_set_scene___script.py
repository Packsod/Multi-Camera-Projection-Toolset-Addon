import bpy
import os

# Get the scene and view layer name
scene = bpy.context.scene
view_layer_name = bpy.context.view_layer.name
# Record the current area
previous_area = bpy.context.area.type

# Define AOV names
aov_names = ['normal_cam', 'Segmentation']

# Define collection names to append
collection_names = ['projecting']

# Ensure allow negative frames
if not bpy.context.preferences.edit.use_negative_frames:
    bpy.context.preferences.edit.use_negative_frames = True
    bpy.ops.wm.save_userpref()

# Ensure view_transform is set to 'Standard'
if scene.view_settings.view_transform != 'Standard':
    scene.view_settings.view_transform = 'Standard'

# Enable nodes for the scene and set necessary view layer properties
scene.use_nodes = True
bpy.context.view_layer.use_pass_z = True
bpy.context.view_layer.use_pass_mist = True

# Iterate over the AOV names
for aov_name in aov_names:
    # Check if AOV already exists
    if aov_name not in scene.view_layers[view_layer_name].aovs:
        # If not, add the AOV
        bpy.ops.scene.view_layer_add_aov()
        scene.view_layers[view_layer_name].active_aov.name = aov_name

# Check if collections exist and append if not
filepath = os.path.join(os.path.dirname(__file__), 'projection_packed.blend')
# use try because i often test it as text block, try can skip the error report
try:
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        for collection_name in collection_names:
            if collection_name not in bpy.data.collections:
                # If the collection doesn't exist, append it
                data_to.collections.append(collection_name)

    # Link each collection to the scene
    for collection in data_to.collections:
        if collection is not None:
            scene.collection.children.link(collection)
except Exception as e:
    print("An error occurred while loading collections:", str(e))

# Enable compositing node tree for the scene
scene.use_nodes = True
node_tree = scene.node_tree

# Remove the Composite node if it exists
composite_node = node_tree.nodes.get('Composite')
if composite_node:
    node_tree.nodes.remove(composite_node)

# Create the wrapper_node variable before the if block
wrapper_node = None

# Check if the data already contains a node group named ".Compositing_export_to_SD"
if '.Compositing_export_to_SD' not in bpy.data.node_groups:
    # Import the ".Compositing2SD_Wrapper" node group
    filepath = os.path.join(os.path.dirname(__file__), 'projection_packed.blend')
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        node_group_name = '.Compositing2SD_Wrapper'
        if node_group_name in data_from.node_groups:
            data_to.node_groups.append(node_group_name)

    # Add the ".Compositing2SD_Wrapper" node to the compositing node tree
    wrapper_node = node_tree.nodes.new(type='CompositorNodeGroup')
    wrapper_node.node_tree = data_to.node_groups[0]

    # Move the ".Compositing2SD_Wrapper" node to the right and up by 500 units
    wrapper_node.location.x += 500
    wrapper_node.location.y += 200

# Connect the Render Layers node to the ".Compositing2SD_Wrapper" node
render_layers_node = node_tree.nodes.get('Render Layers')
if render_layers_node and wrapper_node:
    for output in render_layers_node.outputs:
        if output.name in wrapper_node.inputs:
            node_tree.links.new(output, wrapper_node.inputs[output.name])


# Traverse the Compositing NodeTree
nodes = bpy.context.scene.node_tree.nodes
for node in nodes:
    # Check if the node is a group node
    if node.type == 'GROUP':
        # Check if the node group exists before trying to access it
        if ".Compositing2SD_Wrapper" in bpy.data.node_groups:
            if node.node_tree and node.node_tree.name == bpy.data.node_groups[".Compositing2SD_Wrapper"].name:
                # Switch to the compositor
                bpy.context.area.type = 'NODE_EDITOR'
                bpy.context.area.ui_type = 'CompositorNodeTree'
                bpy.context.space_data.tree_type = 'CompositorNodeTree'
                bpy.context.space_data.node_tree = bpy.context.scene.node_tree
                # Select the node
                node.select = True
                bpy.context.scene.node_tree.nodes.active = node
                # Ungroup the node
                bpy.ops.node.group_ungroup()
                # Switch back to the previous area
                bpy.context.area.type = previous_area
                break


# Move all grease pencil layers first frame to frame number -24
for obj in scene.objects:
    if obj.type == 'GPENCIL':
        for layer in obj.data.layers:
            first_frame = layer.frames[0]
            if first_frame.frame_number != -24:
                first_frame.frame_number = -24


def bind_CamPs_to_timeline(prefix="CamP_sub", start_number=1, end_number=24):
    """
    Bind CamP cameras to the timeline with specified naming convention and frame range.
    """
    # Remove markers related to CamPs that are not in the range of -1 to -24 frames
    markers_to_remove = []
    for marker in bpy.context.scene.timeline_markers:
        for i in range(start_number, end_number + 1):
            camera_name = f"{prefix}{i:02d}"
            if marker.name == camera_name and marker.frame not in range(-1, -end_number - 1, -1):
                markers_to_remove.append(marker)

    for marker in markers_to_remove:
        bpy.context.scene.timeline_markers.remove(marker)

    # Traverse each CamP name and bind it to the corresponding frame
    for i in range(start_number, end_number + 1):
        camera_name = f"{prefix}{i:02d}"
        frame_number = -i

        # Check if CamPs exists
        if camera_name in bpy.data.objects:
            camera = bpy.data.objects[camera_name]

            # Check if the CamP is already bound
            is_bound = False
            for marker in bpy.context.scene.timeline_markers:
                if marker.frame == frame_number and marker.camera == camera:
                    is_bound = True
                    break

            # If the CamP is not bound, perform the binding operation
            if not is_bound:
                # Check if there are other markers on the frame and delete them
                markers_to_remove = []
                for marker in bpy.context.scene.timeline_markers:
                    if marker.frame == frame_number:
                        markers_to_remove.append(marker)

                for marker in markers_to_remove:
                    bpy.context.scene.timeline_markers.remove(marker)

                # Create a new marker
                marker = bpy.context.scene.timeline_markers.new(name=camera_name, frame=frame_number)
                # Set the CamP as the marker's data
                marker.camera = camera
        else:
            print(f"Camera {camera_name} does not exist")

    print("All cameras have been successfully bound to the timeline.")

# Bind CamPs to the timeline
bind_CamPs_to_timeline()
