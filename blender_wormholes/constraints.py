import bpy

class Constraints:
    def __init__(self, name = None):
        self.name = name

    def track_to(self, target_name, subtarget_name, influence, name):
        bpy.ops.object.constraint_add(type="TRACK_TO")
        # if self.name is not None:
        #     self.name = 'Track To.001'
        bpy.context.object.constraints[name].target = bpy.data.objects[target_name]
        bpy.context.object.constraints[name].subtarget = subtarget_name
        bpy.context.object.constraints[name].track_axis = "TRACK_NEGATIVE_Z"
        bpy.context.object.constraints[name].up_axis = "UP_Y"
        bpy.context.object.constraints[name].influence = influence

    def follow_path(self, target_name, influence, name):
        bpy.ops.object.constraint_add(type="FOLLOW_PATH")
        bpy.context.object.constraints[name].target = bpy.data.objects[target_name]
        bpy.context.object.constraints[name].influence = influence
