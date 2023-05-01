import os
import bpy
import glob
import math
import blender_wormholes as bl

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
    roughness.default_value = 0.9

    wire.use_pixel_size = True
    wire.inputs[0].default_value = 0.1
    shader.links.new(bsdf.outputs[0], mix_shader.inputs[1])
    shader.links.new(wire.outputs[0], mix_shader.inputs[2])
    shader.links.new(mix_shader.outputs[0], mat_out.inputs[0])

def rendering_360_patch_single(sc, obj_name, animation = False):
    scene_materials = bl.utility.get_materials_in_scene()
    for material in scene_materials:
        if 'material' in material:
            create_wireframe_shaders(material)

    obj = bl.core.Object(obj_name)
    obj.visibility(hide=False)
    sc.select_object(obj_name)
    bpy.ops.object.shade_flat()

    if animation:
        obj.add_keyframe('rotation_euler', 0)
        obj.rotate(math.radians(330), 2)
        obj.add_keyframe('rotation_euler', 250)
        sc.render(animation=True)
    else:
        sc.render(animation=False)
    obj.visibility(hide=True)


def change_texture_map(material, tex_path):
    shader = bl.core.Shaders(material)
    img_tex = shader.get_node('image_texture')
    bsdf = shader.get_node('Principled BSDF')

    #Changing bsdf propoerties
    link = shader.links.new(img_tex.outputs[0], bsdf.inputs[0])
    obj = bl.core.Object(obj_name)
    obj.link_material(distort.mat)
    img_tex.image = bpy.data.images.load(tex_path)
    return shader



def rendering_360_patch_dynamic(sc, obj_name, tex_paths, animation = False):
    scene_materials = bl.utility.get_materials_in_scene()
    for material in scene_materials:
        if 'material' in material:
            create_wireframe_shaders(material)

    obj = bl.core.Object(obj_name)
    for tex_path in tex_paths:
        shader = change_texture_map(material, tex_path)
        obj.link_material(shader.mat)
        obj.visibility(hide=False)
        sc.select_object(obj_name)
        bpy.ops.object.shade_flat()

        if animation:
            obj.add_keyframe('rotation_euler', 0)
            obj.rotate(math.radians(330), 2)
            obj.add_keyframe('rotation_euler', 20)
            sc.render(animation=True)
        else:
            sc.render(animation=False)
        obj.visibility(hide=True)

def rendering_360_distortion_single(obj_name, texture_path):
    distort = bl.core.Shaders('distortion')
    bsdf = distort.get_node('Principled BSDF')
    img_tex = distort.get_node('image_texture')
    link = distort.links.new(img_tex.outputs[0], bsdf.inputs[0])
    obj = bl.core.Object(obj_name)
    obj.link_material(distort.mat)
    img_tex.image = bpy.data.images.load(texture_path)


def main():
    sc = bl.core.Scene()
    bl.utility.set_gpu([0,1,2, 3], sc.scene)

    rendering_settings = {
        'engine': 'CYCLES',
        'use_adaptive_sampling': True,
        'engine_type': 'PATH',
        'sample_size': 128,
        'max_bounces': 8
    }

    image_settings = {
        'resolution': [1024, 1024],
        'output_path': './render/'
    }

    # initialize_settings
    sc.initialize_rendering_settings(rendering_settings)
    sc.initialize_image_settings(image_settings)

    #  mesh_names  = ['all', 'no_geodesic']
    mesh_names = ['Plane']
    os.makedirs(image_settings['output_path'], exist_ok = True)

    for name in mesh_names:
        image_settings['output_path'] = f'./render/{name}.png'
        sc.initialize_image_settings(image_settings)
        #  rendering_360_patch_single(sc, name, animation = False)
        rendering_360_patch_dynamic(sc, name, tex_paths, animation = False)

    # rendering_360_distortion_single('armadillo_obj')

    # texture_path = '/home/coreqode/work/raytracing/rendered_image.png'


if __name__ == '__main__':
    main()
