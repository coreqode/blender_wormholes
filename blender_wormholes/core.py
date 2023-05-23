import os
import bpy
import numpy as np
import random
from mathutils import Matrix, Vector
from .constants import SHADER_NODE_TYPE


class Scene:
    def __init__(self):
        self.scene = bpy.context.scene
        
    def initialize_image_settings(self, settings):
        self.scene.render.resolution_x = settings['resolution'][0]
        self.scene.render.resolution_y = settings['resolution'][1]
        self.scene.render.filepath = settings['output_path']
        self.scene.render.image_settings.file_format = settings['file_format']
        self.scene.render.film_transparent = settings['film_transparent'] 

    def initialize_rendering_settings(self, settings):
        self.scene.render.engine = settings['engine']
        self.scene.cycles.progressive = settings['engine_type']
        self.scene.cycles.use_adaptive_sampling = settings['use_adaptive_sampling']
        self.scene.cycles.max_bounces = settings['max_bounces']
        self.scene.cycles.samples = settings['sample_size']

    def add_objects(self, filepath):
        old_objs = set(self.scene.objects)
        if '.obj' in filepath:
                bpy.ops.import_scene.obj(filepath=filepath, split_mode='OFF')
        elif '.ply' in filepath:
                bpy.ops.import_mesh.ply(filepath = filepath)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        imported_objs = set(self.scene.objects) - old_objs
        name = list(imported_objs)[0].name
        return Object(obj_name = name)

    def delete_objects(self, obj_name):
        self.deselect_all()
        self.select_object(obj_name)
        bpy.ops.object.delete()

    def set_camera(self):
        pass

    def render(self, path = None, animation=False):
        if path is not None:
            self.scene.render.filepath = path
        bpy.ops.render.render(write_still=True, animation=animation)

    def current_mode(self):
        return self.obj.mode

    def toggle_mode_to(self, mode):
        bpy.ops.object.mode_set(mode=mode)

    def deselect_object(self):
        pass

    def select_object(self, obj_name):
        self.deselect_all()
        obj = bpy.data.objects[obj_name]
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

    def select_bone(self, bone):
        self.toggle_mode_to('POSE')
        self.armature.bones[bone].select = True

    def deselect_all(self):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = None

    def apply_hdri(self, image_path):
        self.env_texture_node.image = bpy.data.images.load(image_path)
        self.mapping_node.inputs[2].default_value[2] = random.randint(
            -180, 180)
        bpy.context.view_layer.update()

    def create_world_shader_nodes(self):
        world = bpy.data.worlds[0]
        world_output_node = world.node_tree.nodes.new('ShaderNodeOutputWorld')
        background_node = world.node_tree.nodes.new('ShaderNodeBackground')
        self.env_texture_node = world.node_tree.nodes.new(
            'ShaderNodeTexEnvironment')
        self.mapping_node = world.node_tree.nodes.new('ShaderNodeMapping')
        tex_coord_node = world.node_tree.nodes.new('ShaderNodeTexCoord')

        # Mapping
        world.node_tree.links.new(
            background_node.outputs['Background'], world_output_node.inputs['Surface'])
        world.node_tree.links.new(
            self.env_texture_node.outputs['Color'], background_node.inputs['Color'])
        world.node_tree.links.new(
            self.env_texture_node.outputs['Color'], background_node.inputs['Color'])
        world.node_tree.links.new(
            self.mapping_node.outputs['Vector'], self.env_texture_node.inputs['Vector'])
        world.node_tree.links.new(
            tex_coord_node.outputs['Generated'], self.mapping_node.inputs['Vector'])

    def setup_composite_for_scene(self, scene, image_id):
        scene.node_tree.nodes.clear()

        render_node = scene.node_tree.nodes.new('CompositorNodeRLayers')
        composite = scene.node_tree.nodes.new('CompositorNodeComposite')

        # For Segmentation
        file_out = scene.node_tree.nodes.new('CompositorNodeOutputFile')
        file_out.base_path = f'{self.tmp_file_path}'
        file_out.format.exr_codec = 'PIZ'
        file_out.format.file_format = 'OPEN_EXR'

        # For depth image
        file_out_1 = scene.node_tree.nodes.new('CompositorNodeOutputFile')
        file_out_1.base_path = f'{self.tmp_file_path}'
        file_out_1.format.exr_codec = 'PIZ'
        file_out_1.format.file_format = 'OPEN_EXR'

        # math_node  = scene.node_tree.nodes.new('CompositorNodeMath')
        # math_node.operation = 'DIVIDE'
        # math_node.inputs[1].default_value = 255

        file_out.file_slots[0].path = 'segmentation'
        file_out_1.file_slots[0].path = 'depth'

        scene.node_tree.links.new(
            render_node.outputs['Image'], composite.inputs['Image'])
        scene.node_tree.links.new(
            render_node.outputs['IndexOB'], file_out.inputs[0])
        # scene.node_tree.links.new(math_node.outputs['Value'], file_out.inputs[0])
        scene.node_tree.links.new(
            render_node.outputs['Depth'], file_out_1.inputs[0])

    def apply_render_settings(self, high_quality):
        scene = bpy.context.scene
        bpy.context.scene.cycles.progressive = self.cycles_type
        bpy.context.scene.cycles.use_adaptive_sampling = self.use_adaptive_sampling
        scene.cycles.max_bounces = 12
        if high_quality:
            scene.cycles.samples = self.sample_size_hi
            if self.subsurface_scattering:
                value = random.uniform(0, 0.015)
                bpy.data.materials[1].node_tree.nodes['Principled BSDF'].inputs[1].default_value = value
                bpy.data.materials[1].node_tree.nodes['Principled BSDF'].inputs[2].default_value[0] = 1.0
                bpy.data.materials[1].node_tree.nodes['Principled BSDF'].inputs[2].default_value[1] = 0.2
                bpy.data.materials[1].node_tree.nodes['Principled BSDF'].inputs[2].default_value[2] = 0.3

            # specularity and roughness setttings
            bpy.data.materials[1].node_tree.nodes['Principled BSDF'].inputs[5].default_value = 0.155
            bpy.data.materials[1].node_tree.nodes['Principled BSDF'].inputs[7].default_value = 0.932

            if self.denoising:
                render_node = scene.node_tree.nodes.new(
                    'CompositorNodeRLayers')
                composite = scene.node_tree.nodes.new(
                    'CompositorNodeComposite')
                bpy.context.view_layer.cycles.denoising_store_passes = True
                denoiser = scene.node_tree.nodes.new('CompositorNodeDenoise')
                scene.node_tree.links.new(
                    render_node.outputs['Noisy Image'], denoiser.inputs['Image'])
                scene.node_tree.links.new(
                    render_node.outputs['Denoising Normal'], denoiser.inputs['Normal'])
                scene.node_tree.links.new(
                    render_node.outputs['Denoising Albedo'], denoiser.inputs['Albedo'])
                scene.node_tree.links.new(
                    denoiser.outputs['Image'], composite.inputs['Image'])
        else:
            scene.cycles.samples = self.sample_size_low
            bpy.data.materials[1].node_tree.nodes['Principled BSDF'].inputs[1].default_value = 0

    def render_one_frame(self, high_quality=True,  write_still=True):
        self.apply_render_settings(high_quality)
        self.scene.render.filepath = self.render_filepath
        self.scene.render.image_settings.file_format = self.config['image_format']

        bpy.ops.render.render(write_still=write_still)
        bpy.context.scene.node_tree.nodes.clear()

    def get_rendered_outputs(self, scene, img_id, K):
        depth = self.get_depth(scene, img_id, K)
        # rendered_img = self.get_rendered_img(scene, img_id, K)
        seg_img = self.get_segmentation_mask(scene, img_id, K)
        return seg_img, depth

    def get_rendered_img(self, scene, img_id, K):
        tmp_file_path = f'{self.tmp_file_path}{img_id}.png'
        out_data = bpy.data.images.load(tmp_file_path)
        pixels_numpy = np.array(out_data.pixels[:])
        res_x = self.resolution_x
        res_y = self.resolution_y
        # Numpy works with (y, x, channels)
        pixels_numpy.resize((res_y, res_x, 4))
        # flip vertically (in Blender y in the image points up instead of down)
        pixels_numpy = np.flip(pixels_numpy, 0)
        img = pixels_numpy[:, :, :3]
        img = np.clip(img, 0, 1)
        return img

    def get_segmentation_mask(self, scene, img_id, K):
        tmp_file_path = f'{self.tmp_file_path}/segmentation0001.exr'
        out_data = bpy.data.images.load(tmp_file_path)
        pixels_numpy = np.array(out_data.pixels[:])
        res_x = self.resolution_x
        res_y = self.resolution_y
        # Numpy works with (y, x, channels)
        pixels_numpy.resize((res_y, res_x, 4))
        # flip vertically (in Blender y in the image points up instead of down)
        pixels_numpy = np.flip(pixels_numpy, 0)
        mask = pixels_numpy[:, :, 0].astype(np.uint8)
        os.remove(tmp_file_path)
        return mask

    def get_depth(self, scene, img_id, K):
        """
        Taken from vision blender
        """
        tmp_file_path = f'{self.tmp_file_path}/depth0001.exr'
        out_data = bpy.data.images.load(tmp_file_path)
        pixels_numpy = np.array(out_data.pixels[:])
        res_x = self.resolution_x
        res_y = self.resolution_y
        # Numpy works with (y, x, channels)
        pixels_numpy.resize((res_y, res_x, 4))
        # flip vertically (in Blender y in the image points up instead of down)
        pixels_numpy = np.flip(pixels_numpy, 0)

        z = pixels_numpy[:, :, 0]
        # Points at infinity get a -1 value
        max_dist = scene.camera.data.clip_end
        INVALID_POINT = -1.0
        z[z > max_dist] = INVALID_POINT
        f_x = K[0][0]
        f_y = K[1][1]
        c_x = K[0][2]
        c_y = K[1][2]

        for y in range(res_y):
            b = ((c_y - y) / f_y)
            for x in range(res_x):
                val = z[y][x]
                if val != INVALID_POINT:
                    a = ((c_x - x) / f_x)
                    z[y][x] = val / np.linalg.norm([1, a, b])
        os.remove(tmp_file_path)
        return z


class Object:
    def __init__(self, obj_name = None, obj_path = None):
        self.name = obj_name
        self.obj = bpy.data.objects[self.name]
        self.mode = self.obj.mode

    def select_object(self):
        bpy.context.view_layer.objects.active = self.obj

    def visibility(self, hide=True):
        if hide:
            self.obj.hide_render = True
        else:
            self.obj.hide_render = False

    def link_material(self, mat):
        if self.obj.data.materials:
            self.obj.data.materials[0] = mat
        else:
            self.obj.data.materials.append(mat)

    def rotate(self, angle, axis):
        self.obj.rotation_euler[axis] = angle

    def scale(self, value):
        self.obj.scale = (value[0], value[1], value[2])

    def translate(self, value):
        self.obj.location = (value[0], value[1], value[2])

    def add_keyframe(self, data_path, frame):
        self.obj.keyframe_insert(data_path=data_path, frame=frame)

    def remove_keyframe(self, data_path, frame):
        self.obj.keyframe_delete(data_path=data_path, frame=frame)

    def uv_parameterize(self, type):
        if type == 'smart_uv':
            if self.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.uv.smart_project()
            bpy.ops.object.mode_set(mode='OBJECT')

    def save_mesh(self, path, materials=True, uv=True):
        bpy.ops.wm.obj_export(filepath=path, export_materials=materials,
                              export_uv=uv, )


class Shaders:
    def __init__(self, name):
        self.mat = self.material(mat_name=name)
        self.node_names = [node.name for node in self.mat.node_tree.nodes]
        self.nodes = self.mat.node_tree.nodes
        self.links = self.mat.node_tree.links

    def get_node(self, node_name):
        if node_name in self.node_names:
            return self.nodes[node_name]
        else:
            shader_node_type = str(SHADER_NODE_TYPE[node_name])
            self.node_names.append(node_name)
            node = self.nodes.new(type=shader_node_type)
            node.name = node_name
        return node

    def get_link(self, socket_name):
        for link in self.links:
            if link.to_socket.name == socket_name:
                return link

    def remove_link(self, link):
        self.links.remove(link)

    def material(self, mat_name, reset=False):
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        if reset:
            if mat.node_tree:
                mat.node_tree.links.clear()
                mat.node_tree.nodes.clear()
        return mat

    def change_node_name(self, node, tar_name):
        cur_name = node.name
        self.nodes[cur_name].name = tar_name
        self.node_names.remove(cur_name)
        self.node_names.append(tar_name)


class Camera:
    def __init__(self, name=None):
        if name:
            self.name = name
            self.camera = bpy.data.objects[self.name]
        else:
            self.add_camera()

    def add_camera(self,  matrix=None, lens=None):
        bpy.ops.object.camera_add(enter_editmode=False, align="WORLD")

        if lens:
            bpy.context.object.data.lens = lens

        cam = bpy.data.objects['Camera']

        if self.name:
            cam.name = self.name

        if matrix:
            cam.matrix_world = Matrix(matrix)

        self.camera = cam

    def get_intrinsic_camera_parameters(self, scene):
        focal_length = scene.camera.data.lens
        resolution_scale = (scene.render.resolution_percentage / 100.0)
        resolution_x = scene.render.resolution_x * resolution_scale  # [pixels]
        resolution_y = scene.render.resolution_y * resolution_scale  # [pixels]
        res_x = int(resolution_x)
        res_y = int(resolution_y)

        cam_data = scene.camera.data
        if cam_data.sensor_fit == 'VERTICAL':
            sensor_size_in_mm = cam_data.sensor_height
        else:
            sensor_size_in_mm = cam_data.sensor_width

        if cam_data.sensor_fit == 'AUTO':

            size_x = scene.render.pixel_aspect_x * res_x
            size_y = scene.render.pixel_aspect_y * res_y

            if size_x >= size_y:
                sensor_fit = 'HORIZONTAL'
            else:
                sensor_fit = 'VERTICAL'

        pixel_aspect_ratio = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x
        if sensor_fit == 'HORIZONTAL':
            view_fac_in_px = res_x
        else:
            view_fac_in_px = pixel_aspect_ratio * res_y
        pixel_size_mm_per_px = (
            sensor_size_in_mm / focal_length) / view_fac_in_px
        f_x = 1.0 / pixel_size_mm_per_px
        f_y = (1.0 / pixel_size_mm_per_px) / pixel_aspect_ratio
        c_x = (res_x - 1) / 2.0 - cam_data.shift_x * view_fac_in_px
        c_y = (res_y - 1) / 2.0 + (cam_data.shift_y *
                                   view_fac_in_px) / pixel_aspect_ratio
        K = [[f_x, 0, c_x],
             [0, f_y, c_y],
             [0,  0,   1]]
        return K

    def get_extrinsic_camera_parameters(self, scene):
        bcam = scene.camera
        R_bcam2cv = np.array([[1,  0,  0],
                              [0, -1,  0],
                              [0,  0, -1]])

        location = np.array([bcam.matrix_world.decompose()[0]]).T
        RT_blender = np.array(bcam.matrix_world)
        R_world2bcam = np.array(bcam.matrix_world.decompose()[
                                1].to_matrix().transposed())

        T_world2bcam = np.matmul(R_world2bcam.dot(-1), location)

        R_world2cv = np.matmul(R_bcam2cv, R_world2bcam)
        T_world2cv = np.matmul(R_bcam2cv, T_world2bcam)

        extr = np.concatenate((R_world2cv, T_world2cv), axis=1)
        return RT_blender, extr

    def get_camera_parameters(self, scene):
        bpy.context.view_layer.update()
        K = self.get_intrinsic_camera_parameters(scene)
        RT_blender, RT_cv = self.get_extrinsic_camera_parameters(scene)
        P = np.matmul(K, RT_cv)
        return P, K, RT_cv, RT_blender