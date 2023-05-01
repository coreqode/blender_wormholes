import os
import bpy
import glob
import math
import blender_wormholes as bl
from natsort import natsorted
import numpy as np


def create_wireframe_shaders(material):
    shader = bl.core.Shaders(material)
    wire = shader.get_node('wireframe')
    mix_shader = shader.get_node('mix_shader')
    bsdf = shader.get_node('Principled BSDF')
    mat_out = shader.get_node('Material Output')

    #Changing bsdf propoerties
    subsurface = bsdf.inputs[1]
    metallic = bsdf.inputs[6]
    specular = bsdf.inputs[7]
    roughness = bsdf.inputs[9]

    subsurface.default_value = 0
    metallic.default_value = 0.4
    specular.default_value = 0.0
    roughness.default_value = 0.7

    wire.use_pixel_size = True
    wire.inputs[0].default_value = 0.1
    shader.links.new(bsdf.outputs[0], mix_shader.inputs[1])
    shader.links.new(wire.outputs[0], mix_shader.inputs[2])
    shader.links.new(mix_shader.outputs[0], mat_out.inputs[0])


def change_texture_map(obj, material, tex_path):
    shader = bl.core.Shaders(material)
    img_tex = shader.get_node('image_texture')
    bsdf = shader.get_node('Principled BSDF')

    #Changing bsdf propoerties
    link = shader.links.new(img_tex.outputs[0], bsdf.inputs[0])
    obj.link_material(shader.mat)
    img_tex.image = bpy.data.images.load(tex_path)
    return shader

def rendering_360_patch_dynamic_patch(sc, root_path, obj_paths):
    SCALE = 3.0
    EULER_ROTATION = 90
    LOCATION = (-4.26, -14.42, 3.84)

    counter = 0
    print(obj_paths)
    for obj_path in obj_paths:
        #  name = obj_path.split('/')[-2].split('_')[0]
        #  patch_path = f'./files/spot_wo_geo_patches/{name}_sphere.obj'
        obj = sc.add_objects(obj_path)

        scene_materials = bl.utility.get_materials_in_scene()
        for material in scene_materials:
            if 'material' in material:
                create_wireframe_shaders(material)

        obj.scale((SCALE, SCALE, SCALE))
        obj.rotate(math.radians(EULER_ROTATION), 0)
        obj.translate(LOCATION)
        obj.visibility(hide=False)
        sc.select_object(obj.name)
        bpy.ops.object.shade_flat()

        angle = counter + 0.5*counter
        obj.rotate(math.radians(angle), 2)
        out_path = os.path.join(root_path, f'{counter}.png')
        sc.render(path = out_path, animation=False)
        obj.visibility(hide=True)
        counter +=1
        #  bpy.ops.wm.save_as_mainfile(filepath='/home/cvit/coreqode/visualization/SIGG_video/patch.blend')
        #  exit()
        sc.delete_objects(obj.name)
        del obj
        if counter > 250:
                break

def rendering_360_patch_dynamic_conformal(sc, root_path, obj_paths, check = False):
    scene_materials = bl.utility.get_materials_in_scene()
    for material in scene_materials:
        #if 'material' in material:
        create_wireframe_shaders(material)

    SCALE = 3.0
    EULER_ROTATION = 90
    LOCATION = (-4.26, -14.42, 3.84)

    counter = 0
    for obj_path in obj_paths:
        tex_path = '/'.join(obj_path.split('/')[:-1])
        obj_name = obj_path.split('/')[-1].split('.')[0]
        if check:
                tex_path = './check.png'
        else:
                tex_path = os.path.join(tex_path, f'{obj_name}_angle.png')
        obj = sc.add_objects(obj_path)
        obj.scale((SCALE, SCALE, SCALE))
        obj.rotate(math.radians(EULER_ROTATION), 0)
        obj.translate(LOCATION)
        shader = change_texture_map(obj, material, tex_path)
        obj.link_material(shader.mat)
        obj.visibility(hide=False)
        sc.select_object(obj.name)
        bpy.ops.object.shade_flat()


        # TODO Change the camera angle rather than the object

        #angle = 40*np.sin(counter/1000)
        angle = counter + 0.5*counter
        obj.rotate(math.radians(angle), 2)
        out_path = os.path.join(root_path, f'{counter}.png')
        sc.render(path = out_path, animation=False)
        obj.visibility(hide=True)
        counter +=1
        #  bpy.ops.wm.save_as_mainfile(filepath='/home/cvit/coreqode/visualization/SIGG_video/test.blend')
        sc.delete_objects(obj.name)
        del obj
        if counter > 250:
                break

def render_point_cloud(sc, root_path, ply_paths):
    counter = 0
    scale = 3.0
    angle = 90
    location = (-2.26, -10.42, 3.84)

    node_group = bpy.data.objects['dummy'].modifiers[-1].node_group

    for ply_path in ply_paths:
        name = ply_path.split('/')[-2].split('_')[0]
        ply_path = f"/home/cvit/shan/differentiable_parameterization/src/output/reconstructed_pc/bob_ppt/train/{name}_combined_pc.ply"
        obj = sc.add_objects(ply_path)
        bpy.ops.object.modifier_add(type='NODES')
        obj.scale((scale, scale, scale))
        obj.rotate(math.radians(angle), 0)
        obj.translate(location)
        obj.visibility(hide=False)
        sc.select_object(obj.name)
        obj.obj.modifiers[-1].node_group = node_group
        bpy.ops.object.shade_flat()
        angle = counter + 0.5*counter
        obj.rotate(math.radians(angle), 2)

        out_path = os.path.join(root_path, f'{counter}.png')
        sc.render(path = out_path, animation=False)
        obj.visibility(hide=True)
        counter +=1
        #  bpy.ops.wm.save_as_mainfile(filepath='/home/cvit/coreqode/visualization/SIGG_video/test.blend')
        sc.delete_objects(obj.name)
        del obj
        if counter > 250:
                break

def main():
    sc = bl.core.Scene()
    bl.utility.set_gpu([0,1,2, 3], sc.scene)

    rendering_settings = {
        'engine': 'CYCLES',
        'use_adaptive_sampling': True,
        'engine_type': 'PATH',
        'sample_size': 64,
        'max_bounces': 8
    }

    image_settings = {
        'resolution': [1024, 1024],
        'output_path': './render/'
    }

    mesh_name = 'spot_patches'
    obj_paths = natsorted(glob.glob(f'./files/{mesh_name}/*.obj'))
    #  ply_paths = natsorted(glob.glob(f'./files/{mesh_name}/*.ply'))

    # initialize_settings
    #  image_settings['output_path'] = f'./render/'
    os.makedirs(image_settings['output_path'], exist_ok = True)
    sc.initialize_rendering_settings(rendering_settings)
    sc.initialize_image_settings(image_settings)
    root_path = f'./render/{mesh_name}/'

    bpy.data.lights['Area.001'].energy = 4000
    bpy.data.lights['Area'].energy = 4000

    out_chec = os.path.join(root_path, 'patch_pred')
    os.makedirs(out_chec, exist_ok = True)
    rendering_360_patch_dynamic_patch(sc, out_chec, obj_paths)

    #  out_conf = os.path.join(root_path, 'conformal')
    #  os.makedirs(out_conf, exist_ok = True)
    #  rendering_360_patch_dynamic_conformal(sc, out_conf, obj_paths, False)

    #  out_chec = os.path.join(root_path, 'checkerboard')
    #  os.makedirs(out_chec, exist_ok = True)
    #  rendering_360_patch_dynamic_conformal(sc, out_chec, obj_paths, True)

    #  ply_paths = natsorted(glob.glob("/home/cvit/shan/differentiable_parameterization/src/output/reconstructed_pc/bob_ppt/train/*.ply"))
    #  out_pc = os.path.join(root_path, 'point_cloud')
    #  os.makedirs(out_pc, exist_ok = True)
    #  render_point_cloud(sc, out_pc, obj_paths)

if __name__ == '__main__':
    main()
