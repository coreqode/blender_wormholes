import bpy
import re


def set_gpu(cuda_no, scene):
    scene.cycles.device = "GPU"
    prefs = bpy.context.preferences
    prefs.addons["cycles"].preferences.get_devices()
    cprefs = prefs.addons["cycles"].preferences
    # Attempt to set GPU device types if available
    for compute_device_type in ("CUDA", "OPENCL", "NONE"):
        try:
            cprefs.compute_device_type = compute_device_type
            print("Device found", compute_device_type)
            break
        except TypeError:
            pass

    scene.cycles.use_auto_tile = True
    #  for scene in bpy.data.scenes:
    #  scene.render.tile_x = 256
    #  scene.render.tile_y = 256

    # Enable all CPU and GPU devices
    for device in cprefs.devices:
        print(device)
        if not re.match("intel", device.name, re.I):
            print("Activating", device)
            device.use = False
        else:
            device.use = False

    for n in cuda_no:
        cprefs.devices[n].use = True


def get_objects_in_scene(scene):
    objects = {'MESH': [],
               'LIGHT': [],
               'CAMERA': []}

    for objs in scene.objects:
        try:
            objects[objs.type].append(objs.name)
        except KeyError:
            objects[objs.type] = []
            objects[objs.type].append(objs.name)
    return objects


def get_materials_in_scene():
    materials = []
    for mats in bpy.data.materials:
        materials.append(mats.name)
    return materials
