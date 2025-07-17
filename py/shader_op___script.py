import bpy

def shader_reset_CURVE_RGB_curves():
    def show_popup(message):
        bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text=message), title="Error", icon='ERROR')

    # Get the shader editor
    shader_editor = next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)

    if shader_editor is None:
        show_popup("No shader editor found!")
    else:
        try:
            selected_rgb_curve_nodes = [node for node in shader_editor.node_tree.nodes if node.select and node.type == 'CURVE_RGB']
            if not selected_rgb_curve_nodes:
                show_popup("No selected ShaderNodeRGBCurve nodes found!")
            else:
                for node in selected_rgb_curve_nodes:
                    for curve in [node.mapping.curves[0], node.mapping.curves[1], node.mapping.curves[2], node.mapping.curves[3]]:
                        if len(curve.points) > 2:
                            for i in range(len(curve.points) - 2):
                                curve.points.remove(curve.points[-1])
                        elif len(curve.points) < 2:
                            show_popup(f"Not enough points to modify in node {node.name}")
                            continue

                        curve.points[0].location = (0, 0)
                        curve.points[1].location = (1, 1)

                        for p in curve.points:
                            p.handle_type = 'VECTOR'

                        for p in curve.points:
                            print(p.location)

                    node.mapping.update()
                    
                    # Set the default value of input[0] to 1
                    if len(node.inputs) > 0:
                        node.inputs[0].default_value = 1
                        
        except AttributeError as e:
            show_popup(str(e))



def shader_add_gradient_mask():
    # Start the undo block
    bpy.ops.ed.undo_push(message="Start of script operation")

    # Check for the presence of required objects and node groups
    required_objects = ["Linear Gradient", "Spherical Gradient"]
    required_node_groups = [".npr_Linear Gradient", ".npr_Spherical Gradient"]
    missing_objects = [obj for obj in required_objects if obj not in bpy.data.objects]
    missing_node_groups = [ng for ng in required_node_groups if ng not in bpy.data.node_groups]

    if missing_objects or missing_node_groups:
        message = "Required objects and node groups are missing. Please run the scene set first."
        bpy.context.window_manager.popup_menu(lambda self, context, msg=message: self.layout.label(text=msg), title="Missing Requirements")
    else:
        class InputPrefixOperator(bpy.types.Operator):
            """Operator to prompt the user for input"""
            bl_idname = "object.input_prefix"
            bl_label = "Enter a prefix"
            prefix: bpy.props.StringProperty(name="Prefix")
            base_name_options = [("Linear Gradient", "Linear Gradient", ""),
                                 ("Spherical Gradient", "Spherical Gradient", "")]
            base_name: bpy.props.EnumProperty(name="Base Name",
                                              items=base_name_options,
                                              default="Linear Gradient")

            def perform_operations(self, prefix, base_name):
                # Record the currently active object
                orig_active_object = bpy.context.view_layer.objects.active

                # Part 1: Check if the object already exists or duplicate and rename it
                Gradient_empty_obj_name = base_name + " " + prefix
                if Gradient_empty_obj_name in bpy.data.objects:
                    new_object = bpy.data.objects[Gradient_empty_obj_name]
                else:
                    orig_object = bpy.data.objects[base_name]
                    new_object = orig_object.copy()
                    new_object.name = Gradient_empty_obj_name
                    # Link the new object into the current collection
                    bpy.context.collection.objects.link(new_object)

                # Re-activate the originally active object
                bpy.context.view_layer.objects.active = orig_active_object

                # The mouse move callback function
                def handle_mouse_move(context, event):
                    import mathutils
                    # Update the node location to the mouse cursor location
                    node_group.location = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
                    # If the left mouse button is pressed, remove the draw handler and finish the operation
                    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                        bpy.types.SpaceView3D.draw_handler_remove(handle_mouse_move, 'WINDOW')
                        return {'FINISHED'}
                    # If the left mouse button is not pressed, continue the operation
                    return {'RUNNING_MODAL'}

                # Part 2: Append a node group and rename it and its internal node
                Gradient_nodegroup_name = ".npr_" + base_name + " " + prefix
                orig_node_group = bpy.data.node_groups[".npr_" + base_name]
                if Gradient_nodegroup_name in bpy.data.node_groups:
                    new_node_group = bpy.data.node_groups[Gradient_nodegroup_name]
                else:
                    new_node_group = orig_node_group.copy()
                    new_node_group.name = Gradient_nodegroup_name
                # Append the new node group to the current shader editor's node tree
                shader_editor = next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)
                if shader_editor is not None:
                    tree = shader_editor.edit_tree
                    # Deselect all nodes in the tree
                    for node in tree.nodes:
                        node.select = False
                    new_node = tree.nodes.new('ShaderNodeGroup')
                    new_node.node_tree = new_node_group
                    # Move the node to the mouse cursor location
                    new_node.location = bpy.context.space_data.cursor_location
                    # Make the node follow the mouse cursor until the left mouse button is pressed
                    bpy.ops.transform.translate('INVOKE_DEFAULT')
                    # Save the node for use in the mouse move callback
                    # Add a draw handler to update the node location as the mouse moves
                    bpy.types.SpaceView3D.draw_handler_add(handle_mouse_move, (), 'WINDOW', 'POST_VIEW')
                # Set the object of the internal node
                if "driven_object" in new_node_group.nodes:
                    new_node_group.nodes["driven_object"].object = new_object

            def execute(self, context):
                # Call the function to perform the object and node group operations
                self.perform_operations(self.prefix, self.base_name)
                return {'FINISHED'}

            def invoke(self, context, event):
                return context.window_manager.invoke_props_dialog(self)

        # Register the InputPrefixOperator class
        bpy.utils.register_class(InputPrefixOperator)
        # Execute the InputPrefixOperator to show the input dialog
        bpy.ops.object.input_prefix('INVOKE_DEFAULT')


    # End the undo block
    bpy.ops.ed.undo_push(message="End of script operation")


"""class AddObjIndMask(bpy.types.Operator):
    bl_idname = "object.append_node_group"
    bl_label = "Append Node Group"
    index: bpy.props.IntProperty(name="Color ID", min=1, max=256, default=1)

    def generate_colors(self, index):
        import colorsys
        pcyc = -1
        cval = 0
        st = 0
        for i in range(st, index):
            ccyc = 0
            while 2 ** ccyc <= i:
                ccyc += 1
            if ccyc == 0:
                cval = 0
            elif pcyc != ccyc:
                dlt = 1 / (2 ** ccyc)
                cval = dlt
            else:
                cval += 2 * dlt
            pcyc = ccyc
        return colorsys.hsv_to_rgb(cval, 0.5, 0.5)

    def srgb_to_linearrgb(self, c):
        if c < 0:
            return 0
        elif c < 0.04045:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4

    def hex_to_rgba(self, hex_value):
        hex_color = hex_value[1:]
        r = int(hex_color[:2], base=16)
        sr = r / 255.0
        lr = self.srgb_to_linearrgb(sr)
        g = int(hex_color[2:4], base=16)
        sg = g / 255.0
        lg = self.srgb_to_linearrgb(sg)
        b = int(hex_color[4:6], base=16)
        sb = b / 255.0
        lb = self.srgb_to_linearrgb(sb)
        return (lr, lg, lb, 1.0)

    def execute(self, context):
        required_node_group = ".obj_index_mask"
        if required_node_group not in bpy.data.node_groups:
            message = "Required node group is missing. Please check the name or availability of the node group."
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
        else:
            rgb_color = self.generate_colors(self.index)
            srgb_color = [int(c*256) for c in rgb_color]
            hex_color = '#{:02x}{:02x}{:02x}'.format(*srgb_color)
            rgba_color = self.hex_to_rgba(hex_color)

            shader_editor = next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)
            if shader_editor is not None:
                tree = shader_editor.edit_tree
                for node in tree.nodes:
                    node.select = False
                new_node = tree.nodes.new('ShaderNodeGroup')
                new_node.node_tree = bpy.data.node_groups[required_node_group]
                new_node.location = bpy.context.space_data.cursor_location
                new_node.inputs[0].default_value = rgba_color
                new_node.inputs[0].hide = True
                new_node.outputs[0].hide = False
                new_node.label = f"obj_ind_{self.index}"
                new_node.use_custom_color = True
                new_node.color = rgb_color

                # The mouse move callback function
                def handle_mouse_move(context, event):
                    import mathutils
                    new_node.location = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
                    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                        bpy.types.SpaceView3D.draw_handler_remove(handle_mouse_move, 'WINDOW')
                        return {'FINISHED'}
                    return {'RUNNING_MODAL'}
                bpy.ops.transform.translate('INVOKE_DEFAULT')
                bpy.types.SpaceView3D.draw_handler_add(handle_mouse_move, (), 'WINDOW', 'POST_VIEW')
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

def shader_add_obj_index_mask():
    bpy.utils.register_class(AddObjIndMask)
    bpy.ops.object.append_node_group('INVOKE_DEFAULT')"""


class AOV_Manager:
    def __init__(self):
        self.node_group_name = ".AOV"
        self.script_state = bpy.context.window_manager.get('script_state', False)

    def find_node_group(self):
        return bpy.data.node_groups.get(self.node_group_name)

    def execute_script_on(self):
        node_group = self.find_node_group()
 
        if node_group is None:
            self.display_error("AOV nodegroup does not exist, run set scene to get it.")
        else:
            for material in bpy.data.materials:
                if not material.use_nodes:
                    material.use_nodes = True
                if material.name == "NPR_Shader_Library":
                    continue
                if material.node_tree and any(node.node_tree is not None and node.node_tree.name == self.node_group_name for node in material.node_tree.nodes if hasattr(node, 'node_tree')):
                    continue
                if material.node_tree:
                    new_node = material.node_tree.nodes.new('ShaderNodeGroup')
                    new_node.node_tree = node_group

    def execute_script_off(self):
        for material in bpy.data.materials:
            if not material.node_tree:
                continue
            if material.name == "NPR_Shader_Library":
                continue
            nodes_to_remove = [node for node in material.node_tree.nodes if getattr(node, 'node_tree', None) and node.node_tree.name == self.node_group_name]
            for node in nodes_to_remove:
                material.node_tree.nodes.remove(node)

    def toggle_script(self):
        if self.script_state:
            print("Running execute_script_off")
            self.execute_script_off()
            bpy.context.window_manager['script_state'] = False
        else:
            print("Running execute_script_on")
            self.execute_script_on()
            bpy.context.window_manager['script_state'] = True

    def display_error(self, message):
        bpy.context.window_manager.popup_menu(
            lambda self, context: self.layout.label(text=message),
            title="Error",
            icon='ERROR'
        )

def shader_add_del_aov_for_each_mat():
    AOVManager = AOV_Manager()
    AOVManager.toggle_script()



class NprClayDebug:
    def __init__(self):
        self.node_group_name = ".npr_clay debug"
        self.material_name = "npr_clay debug"
        self.script_state = bpy.context.window_manager.get('script_state', False)
        self.node_group = bpy.data.node_groups.get(self.node_group_name)
        self.mat = bpy.data.materials.get(self.material_name)
        if self.node_group is None:
            self.display_error("'.npr_clay debug' node group not found.")
        if self.mat is None:
            self.create_material()

    def create_material(self):
        self.mat = bpy.data.materials.new(self.material_name)
        self.mat.use_nodes = True
        nodes = self.mat.node_tree.nodes
        nodes.remove(nodes.get("Principled BSDF"))
        group_node = nodes.new("ShaderNodeGroup")
        group_node.node_tree = self.node_group
        self.mat.node_tree.links.new(group_node.outputs[0], self.mat.node_tree.nodes["Material Output"].inputs[0])

    def assign_material(self):
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and (not obj.modifiers or all(mod.type != 'NODES' for mod in obj.modifiers)) and (not obj.data.materials or len(obj.data.materials) == 1 and obj.data.materials[0] is None):
                obj.data.materials.append(self.mat)
                if len(obj.data.materials) > 1:
                    obj.data.materials.pop(index=0)

    def remove_material(self):
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                if self.mat.name in obj.data.materials:
                    index = obj.data.materials.find(self.mat.name)
                    obj.data.materials.pop(index=index)
                    if not obj.data.materials:
                        obj.data.materials.append(None)
                    obj.data.materials.pop(index=index)

    def toggle_script(self):
        if self.script_state:
            print("Removing material from objects")
            self.remove_material()
            bpy.context.window_manager['script_state'] = False
        else:
            print("Assigning material to objects")
            self.assign_material()
            bpy.context.window_manager['script_state'] = True

    def display_error(self, message):
        bpy.context.window_manager.popup_menu(
            lambda self, context: self.layout.label(text=message),
            title="Error",
            icon='ERROR'
        )
        
def shader_NPR_clay_debug_on_off():
    manager = NprClayDebug()
    manager.toggle_script()



class NPR_bake_helper:
    def __init__(self, shader_name):
        self.shader_name = shader_name
        self.script_run_count = 0
        self.INPUT_SOCKETS = ['――――――  {}'.format(i) for i in range(1, 10)]
        self.INPUT_FOR_BAKE_SOCKETS_COL = ['{}_col'.format(i) for i in self.INPUT_SOCKETS]
        self.INPUT_FOR_BAKE_SOCKETS_A = ['{}_a'.format(i) for i in self.INPUT_SOCKETS]
        self.NPR_NODES = ['NPR_{}'.format(i) for i in range(1, 10)]

        if 'script_state' in bpy.context.window_manager:
            self.script_state = bpy.context.window_manager['script_state']
        else:
            self.script_state = False
            bpy.context.window_manager['script_state'] = self.script_state

    def execute_script_on(self):
        for mat in bpy.data.materials:
            if mat.node_tree:
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                NPR_shader_node = next((n for n in nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name == self.shader_name), None)
                if NPR_shader_node is None:
                    print(f"LBS shader node not found in material '{mat.name}'. Skipping...")
                    continue

                NPR_shader_node.use_custom_color = True
                NPR_shader_node.color = (0.25, 0.5, 0.0)
                NPR_shader_node.select = True
                nodes.active = NPR_shader_node

                links_to_modify = []
                links_to_remove = []

                for i, socket in enumerate(self.INPUT_SOCKETS):
                    for link in list(links):
                        if link.to_node.name == NPR_shader_node.name and link.to_socket.name == socket:
                            self.NPR_NODES[i] = link.from_node.name

                            from_socket = nodes[self.NPR_NODES[i]].outputs['Color']
                            to_socket = nodes[NPR_shader_node.name].inputs[self.INPUT_FOR_BAKE_SOCKETS_COL[i]]
                            links.new(from_socket, to_socket)

                            from_socket = nodes[self.NPR_NODES[i]].outputs['Mask']
                            to_socket = nodes[NPR_shader_node.name].inputs[self.INPUT_FOR_BAKE_SOCKETS_A[i]]
                            links.new(from_socket, to_socket)

                        elif nodes[NPR_shader_node.name].inputs[socket].is_linked == False:
                            for l in list(nodes[NPR_shader_node.name].inputs[self.INPUT_FOR_BAKE_SOCKETS_A[i]].links):
                                links_to_remove.append(l)
                            for l in list(nodes[NPR_shader_node.name].inputs[self.INPUT_FOR_BAKE_SOCKETS_COL[i]].links):
                                links_to_remove.append(l)

                for link in links_to_remove:
                    try:
                        links.remove(link)
                    except:
                        pass

                nodes[NPR_shader_node.name].inputs['realtime/baked'].default_value = 1

    def execute_script_off(self):
        for mat in bpy.data.materials:
            if mat.node_tree:
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                NPR_shader_node = next((n for n in nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name == self.shader_name), None)
                if NPR_shader_node is None:
                    print(f"LBS shader node not found in material '{mat.name}'. Skipping...")
                    continue

                NPR_shader_node.use_custom_color = True
                NPR_shader_node.color = (0.25, 0.5, 0.5)

                links_to_remove = []

                for socket in self.INPUT_FOR_BAKE_SOCKETS_COL + self.INPUT_FOR_BAKE_SOCKETS_A:
                    for link in list(links):
                        if link.to_node.name == NPR_shader_node.name and link.to_socket.name == socket:
                            links_to_remove.append(link)

                for link in links_to_remove:
                    try:
                        links.remove(link)
                    except:
                        pass

                nodes[NPR_shader_node.name].inputs['realtime/baked'].default_value = 0

    def toggle_script(self):
        if self.script_state:
            print("Running execute_script_off")
            self.execute_script_off()
            bpy.context.window_manager['script_state'] = False
        else:
            print("Running execute_script_on")
            self.execute_script_on()
            bpy.context.window_manager['script_state'] = True


def shader_NPR_bake_helper_toggle():
    NPRBakeHelper = NPR_bake_helper(".(09) npr_layer_mix_shader")
    NPRBakeHelper.toggle_script()



class Cam_Tex_Linker:
    def __init__(self):
        self.vm_output = "cam_projection_vector_and_mask"
        self.input_nodegroup = [item for sublist in [
            [f"projection_layer{str(i).zfill(2)}",
             f"CamP_sub{str(i).zfill(2)}_render"] for i in range(1, 25)
            ] for item in sublist]
        self.input_socket = ["alpha_camera", "Vector"] * 24
        self.script_state = bpy.context.window_manager.get('script_state', False)

    def find_material_with_node_group(self, node_group_name):
        for material in bpy.data.materials:
            if material.use_nodes:
                for node in material.node_tree.nodes:
                    if node.type == 'GROUP' and node_group_name in node.node_tree.name:
                        return material
        return None

    def execute_script_on(self):
        material_tree = self.find_material_with_node_group(".cam_projection_all")

        if material_tree is None:
            self.display_error(f"Material with a node group named '.cam_projection_all' is not found. Please add it and try again.")
        else:
            node = material_tree.node_tree.nodes
            links_new = material_tree.node_tree.links.new

            if self.vm_output not in node:
                self.display_error(f"The material does not contain the required '{self.vm_output}' node. Please add the node and try again.")
            else:
                ind = -1
                ind_step = 1

                for n in range(48):
                    ind = ind + ind_step
                    if self.input_nodegroup[ind] not in node:
                        self.display_error(f"The material does not contain the required '{self.input_nodegroup[ind]}' node. Please add the node and try again.")
                        break
                    else:
                        links_new(
                            node[self.vm_output].outputs[-ind-1],
                            node[self.input_nodegroup[ind]].inputs[self.input_socket[ind]]
                        )

    def execute_script_off(self):
        material_tree = self.find_material_with_node_group(".cam_projection_all")

        if material_tree and material_tree.node_tree:
            node = material_tree.node_tree.nodes
            links_remove = material_tree.node_tree.links.remove

            ind = -1
            ind_step = 1

            for n in range(48):
                ind = ind + ind_step
                try:
                    links_remove(node[self.vm_output].outputs[-ind].links[0])
                except IndexError:
                    pass

    def toggle_script(self):
        if self.script_state:
            print("Running execute_script_off")
            self.execute_script_off()
            bpy.context.window_manager['script_state'] = False
        else:
            print("Running execute_script_on")
            self.execute_script_on()
            bpy.context.window_manager['script_state'] = True

    def display_error(self, message):
        bpy.context.window_manager.popup_menu(
            lambda self, context: self.layout.label(text=message),
            title="Error",
            icon='ERROR'
        )

def shader_camera_tex_link_toggle():
    CameraTexLinker = Cam_Tex_Linker()
    CameraTexLinker.toggle_script()



class shader_alphaSet:
    @staticmethod
    def CamP_ID_alpha_set(o, colname, set_alpha):
        if colname in o.data.attributes:
            for data in o.data.attributes[colname].data:
                data.color[3] = set_alpha
        else:
            try:
                # Ensure the object is selected and active
                bpy.ops.object.select_all(action='DESELECT')
                o.select_set(True)
                bpy.context.view_layer.objects.active = o
                # Create the attribute
                bpy.ops.geometry.color_attribute_add(name=colname, domain='CORNER', data_type='BYTE_COLOR')
                # Now the attribute should exist, so we can set its value
                for data in o.data.attributes[colname].data:
                    data.color[3] = set_alpha
            except KeyError:
                print(f"Error: Unable to create attribute '{colname}'")
            except Exception as e:
                print(f"Error: {str(e)}")

    @staticmethod
    def Mesh_Pass_Index_Switch():
        colname = 'mask_CamP_ID'
        shader_editor = next((space for area in bpy.context.screen.areas if area.type == 'NODE_EDITOR' for space in area.spaces if space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'), None)
        node_group = bpy.data.node_groups.get(".obj_index_mask")
        node_list = []
        if shader_editor and node_group:
            active_material = bpy.context.object.active_material
            if active_material is None:
                bpy.context.window_manager.popup_menu(lambda self, context: None, title="No Active Material", icon='ERROR')
                return
            selected_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and active_material.name in o.data.materials.keys()]
            for o in selected_meshes:
                pass_index = o.pass_index
                if 1 <= pass_index <= 255:
                    shader_alphaSet.CamP_ID_alpha_set(o, colname, pass_index / 255)
                elif pass_index == 0:
                    shader_alphaSet.CamP_ID_alpha_set(o, colname, 0)
            for node in shader_editor.edit_tree.nodes:
                if node.type == 'GROUP' and node.node_tree == node_group:
                    node_list.append(node)
            if node_list:
                first_node_socket = node_list[0].inputs['Index/CamID 0/1']
                if first_node_socket.default_value == 0:
                    for node in node_list:
                        node.inputs['Index/CamID 0/1'].default_value = 1
                        node.use_custom_color = True
                        node.color = (0.25, 0.5, 0.0)
                elif first_node_socket.default_value == 1:
                    for node in node_list:
                        node.inputs['Index/CamID 0/1'].default_value = 0
                        node.use_custom_color = True
                        node.color = (0.25, 0.5, 0.5)
