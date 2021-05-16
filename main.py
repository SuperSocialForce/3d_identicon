import sys
import ssl
import json
import hashlib
import colorsys
from urllib.request import urlopen
import numpy as np

import bpy
from bpy import context as C
from bpy import data as D

ssl._create_default_https_context = ssl._create_unverified_context

OBJECT_NAME = "Cube"
MESH_NAME = "Cube"
LIGHT_NAME = "Light"
CAMERA_NAME = "Camera"
COLLECTION_NAME = "Collection"
SCENE_NAME = "Scene"
WORLD_NAME = "World"


def get_github_id(login_name):
    url = f"https://api.github.com/users/{login_name}"
    with urlopen(url) as webfile:
        string = webfile.read().decode()
    user_info = json.loads(string)
    user_id = user_info.get("id")

    return user_id


def get_hash(userid):
    if isinstance(userid, int):
        userid = str(userid).encode()
    if isinstance(userid, str):
        userid = userid.encode()
    return hashlib.md5(userid).hexdigest()


def get_pattern(md5):
    code = [int(i, 16) % 2 == 0 for i in md5[:15]]
    pattern = np.zeros((5, 5), dtype=np.int)
    for digit, sign in enumerate(code):
        row = digit % 5
        column = digit // 5 + 2
        pattern[row, column] = sign
    pattern[:, :2] = pattern[:, :2:-1]
    return pattern


def get_color(md5):
    hue = int(md5[25:28], 16) / 4095
    saturation = (65 - int(md5[28:30], 16) * 20 / 255) / 100
    lightness = (75 - int(md5[30:32], 16) * 20 / 255) / 100
    return colorsys.hls_to_rgb(hue, lightness, saturation)


def parse_github_id(username):
    userid = get_github_id(username)
    md5 = get_hash(userid)
    pattern = get_pattern(md5)
    color = get_color(md5)

    return pattern, color


def main(user):
    pattern, color = parse_github_id(user)

    scene = D.scenes[SCENE_NAME]
    collection = D.collections[COLLECTION_NAME]
    mesh_cube = D.meshes[MESH_NAME]

    # render settings
    scene.render.resolution_x = 500
    scene.render.resolution_y = 500

    # build blocks
    D.objects.remove(D.objects[OBJECT_NAME])
    x_offset = -(pattern.shape[1] - 1) / 2
    z_offset = (pattern.shape[0] - 1) / 2
    for i in range(pattern.shape[0]):
        for j in range(pattern.shape[1]):
            sign = pattern[i, j]
            if sign:
                obj = D.objects.new(f"block_{i:02}{j:02}", mesh_cube)
                collection.objects.link(obj)
                obj.location = [x_offset + j, 0, z_offset - i]
                obj.scale = [0.5, 0.5, 0.5]

    # build material
    # D.worlds[WORLD_NAME].node_tree.nodes["Background"].inputs["Color"].default_value = (240/255, 240/255, 240/255, 1)
    material = obj.data.materials[0]
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = [
        c for c in color
    ] + [1.0]
    material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
    # material.node_tree.nodes["Principled BSDF"].inputs["Transmission"].default_value = 0.8
    # material.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1

    # build lighting
    light_config = {
        "key": {"type": "POINT", "location": [-5, -10, 10], "energy": 8000},
        "fill": {"type": "POINT", "location": [10, -10, 0], "energy": 1000},
        "rim": {"type": "POINT", "location": [3, 10, 10], "energy": 1000},
    }
    D.objects.remove(D.objects[LIGHT_NAME])

    for name, config in light_config.items():
        light = D.lights.new(name, config.get("type"))
        obj = D.objects.new(name, light)
        collection.objects.link(obj)
        light.energy = config.get("energy")
        obj.location = config.get("location")

    # set camera
    obj = D.objects[CAMERA_NAME]
    dist = 10
    theta = 75 / 180 * np.pi
    phi = -75 / 180 * np.pi
    obj.location = dist * np.array(
        [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)]
    )
    obj.rotation_euler = [theta, 0, np.pi / 2 + phi]


if __name__ == "__main__":
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    main(argv[0])
