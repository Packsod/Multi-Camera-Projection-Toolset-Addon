"""This script now calculates the new x-coordinate of each object as the sum of the x-offset
and half the x-dimension of the rotated bounding box. 
The x-offset is then updated to be the sum of the new x-coordinate 
and half the x-dimension of the rotated bounding box. 
This ensures that the x-coordinate of each object is the sum of the x-coordinates 
of the previous objects and their rotated bounding box dimensions."""


import bpy
import bmesh
from mathutils import Vector

# Get the selected objects
selected_objects = bpy.context.selected_objects

# Sort the objects by their x-coordinate
selected_objects.sort(key=lambda obj: obj.location.x)

# Record the initial x coordinate of the first object
initial_x = selected_objects[0].location.x

# Get the y and z coordinates of the first object
first_obj = selected_objects[0]
y_coord = first_obj.location.y
z_coord = first_obj.location.z

# Initialize the previous object and offset
prev_object = None
x_offset = first_obj.location.x

for obj in selected_objects:
    # Set the y and z coordinates to those of the first object
    obj.location.y = y_coord
    obj.location.z = z_coord

    # Calculate the dimensions of the rotated bounding box
    bbox = obj.dimensions
    rotated_bbox = obj.rotation_euler.to_matrix() @ Vector(bbox)
    rotated_x_dim = abs(rotated_bbox.x)

    # Calculate the new x-coordinate
    new_x_coord = x_offset + rotated_x_dim / 2

    # Calculate the new position
    new_position = Vector((new_x_coord, y_coord, z_coord))
    obj.location = new_position

    # Update the previous object and x-offset
    prev_object = obj
    x_offset = new_x_coord + rotated_x_dim / 2

# Calculate the x offset
x_offset = selected_objects[0].location.x - initial_x

# Adjust the x coordinates of all selected objects
for obj in selected_objects:
    obj.location.x -= x_offset
