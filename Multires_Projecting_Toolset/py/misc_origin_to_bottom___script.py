import bpy
def CenterOrigin():
    #Get cursor
    cursor = bpy.context.scene.cursor
    #Get original cursor location
    original_cursor_location = (cursor.location[0], cursor.location[1], cursor.location[2])
    #Get initially selected objects, 
    #.copy() do not means it copy the object,but create a copy of selected list,
    #.copy()not strictly necessary, but it can be a good practice.
    initially_selected_objects = bpy.context.selected_objects.copy()
    #Get initially active object
    initially_active_object = bpy.context.active_object
    #Loop over each selected object
    for act_obj in bpy.context.selected_objects:
        #Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        #Make sure object is selected
        act_obj.select_set(True)
        bpy.context.view_layer.objects.active = act_obj
        #Make sure origin is set to geometry for cursor z move
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        #Set cursor location to object location
        cursor.location = act_obj.location
        #Get cursor z move
        half_act_obj_z_dim = act_obj.dimensions[2] / 2
        cursor_z_move = cursor.location[2] - half_act_obj_z_dim
        #Move cursor to bottom of object
        cursor.location[2] = cursor_z_move
        #Set origin to cursor
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    #Reset cursor back to original location
    cursor.location = original_cursor_location
    #Restore initially selected objects
    for obj in initially_selected_objects:
        obj.select_set(True)
    #Restore initially active object
    bpy.context.view_layer.objects.active = initially_active_object
    #Assuming you're wanting object center to grid
    #bpy.ops.object.location_clear(clear_delta=False)
CenterOrigin()
