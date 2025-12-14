import bpy
from bpy.props import *
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

# -----------
# Import
# -----------

import bmesh
import time
import mathutils
import math
import json
from pprint import pprint

from pathlib import Path
from .api import *

# -----------
# Define
# -----------


class OPS_Import_Spine(Operator):
    bl_idname = "camp.import_spine"
    bl_label = ""

    def execute(self, context):
        spine_setting = get_context_scene_cmd().spine
        if not spine_setting.json_path or not spine_setting.atlas_path:
            if bpy.context.preferences.view.language == "zh_HANS":
                self.report({"WARNING"}, "读取文件错误")
            else:
                self.report({"WARNING"}, "Error reading file.")
            return {"FINISHED"}

        start = time.perf_counter()

        JSON_DATA = load_spine_json(spine_setting.json_path)
        ATLAS_DATA = load_spine_atlas(spine_setting.atlas_path)

        if not JSON_DATA or not ATLAS_DATA:
            if bpy.context.preferences.view.language == "zh_HANS":
                self.report({"WARNING"}, "读取文件错误")
            else:
                self.report({"WARNING"}, "Error reading file.")
            return {"FINISHED"}

        BONES_DICT = load_bones(JSON_DATA)
        SLOTS_DICT = load_slots(JSON_DATA)
        PATH_BONES = get_path_bones(JSON_DATA)
        ATTACHMENTS_DCIT = load_attachments(JSON_DATA, spine_setting.import_skin_name)

        arm_obj = _import_bone(BONES_DICT, apply_pose=True, path_bones=PATH_BONES)
        BONE_MATRIX_DICT = _get_bone_matrix_dict(arm_obj)
        _import_mesh(arm_obj, BONES_DICT, SLOTS_DICT, ATTACHMENTS_DCIT, BONE_MATRIX_DICT, ATLAS_DATA)

        if spine_setting.import_ik:
            _build_ik(JSON_DATA, arm_obj)

        _apply_bone_scale(arm_obj, BONES_DICT)
        end = time.perf_counter()
        self.report({"INFO"}, "Load Spine: " + str(round(end - start, 4)) + "s")
        return {"FINISHED"}


class OPS_Import_Spine_Slots_Data(Operator):
    bl_idname = "camp.import_spine_slots_data"
    bl_label = ""

    def execute(self, context):
        spine_setting = get_context_scene_cmd().spine
        spine_setting.slots.slot.clear()

        if not spine_setting.json_path:
            self.report({"WARNING"}, "文件错误")
            return {"FINISHED"}

        JSON_DATA = load_spine_json(spine_setting.json_path)
        SLOTS_DICT = load_slots(JSON_DATA)
        ATTACHMENTS_DCIT = load_attachments(JSON_DATA, spine_setting.import_skin_name)

        for slot_name, slot_data in SLOTS_DICT.items():
            slot = spine_setting.slots.slot.add()
            slot.name = slot_name
            slot.bone_name = slot_data["bone"]

            attachments = ATTACHMENTS_DCIT.get(slot_name, {})
            for mesh_name in attachments:
                _att = slot.attachment.add()
                _att.name = mesh_name

        return {"FINISHED"}


class OPS_Select_Json_File(Operator, ImportHelper):
    bl_idname = "camp.spine_select_json_file"
    bl_label = "Select Json File"

    filename_ext = ".json"

    filter_glob: StringProperty(default="*.json")  # type: ignore

    filepath: StringProperty(name="文件路径", description="选择Spine文件", subtype="FILE_PATH")  # type: ignore

    def execute(self, context):
        spine_setting = get_context_scene_cmd().spine
        spine_setting.json_path = self.filepath
        return {"FINISHED"}


class OPS_Select_Atlas_File(Operator, ImportHelper):
    bl_idname = "camp.spine_select_atlas_file"
    bl_label = "Select Atlas File"

    filename_ext = ".atlas"

    filter_glob: StringProperty(default="*.atlas")  # type: ignore

    filepath: StringProperty(name="文件路径", description="选择Spine文件", subtype="FILE_PATH")  # type: ignore

    def execute(self, context):
        spine_setting = get_context_scene_cmd().spine
        spine_setting.atlas_path = self.filepath
        return {"FINISHED"}


class OPS_Select_Image_File(Operator, ImportHelper):
    bl_idname = "camp.spine_select_image_file"
    bl_label = "Select Image File"

    filename_ext = ".png"

    filter_glob: StringProperty(default="*.png")  # type: ignore

    filepath: StringProperty(name="文件路径", description="选择Spine文件", subtype="FILE_PATH")  # type: ignore

    def execute(self, context):
        spine_setting = get_context_scene_cmd().spine
        spine_setting.image_path = self.filepath
        return {"FINISHED"}


class OPS_Change_Object_Visible(Operator):
    bl_idname = "camp.spine_change_object_visible"
    bl_label = ""
    bl_description = ""

    obj_name: StringProperty()  # type: ignore

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj_name)
        if obj:
            obj.hide_set(not obj.hide_get())
        return {"FINISHED"}


class OPS_Select_Object(Operator):
    bl_idname = "camp.spine_select_object"
    bl_label = ""
    bl_description = ""

    obj_name: StringProperty()  # type: ignore

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj_name)

        if not obj:
            if bpy.context.preferences.view.language == "zh_HANS":
                self.report({"WARNING"}, "未找到目标")
            else:
                self.report({"WARNING"}, "Target not found.")
            return {"FINISHED"}

        if obj.hide_get() or obj.hide_viewport:
            if bpy.context.preferences.view.language == "zh_HANS":
                self.report({"WARNING"}, "目标不可视")
            else:
                self.report({"WARNING"}, "The target is hidden.")
            return {"FINISHED"}

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        return {"FINISHED"}


class OPS_Select_Pose_Bone(Operator):
    bl_idname = "camp.spine_select_pose_bone"
    bl_label = ""
    bl_description = ""

    obj_name: StringProperty()  # type: ignore
    bone_name: StringProperty()  # type: ignore

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj_name)

        if not obj or obj.type != "ARMATURE":
            if bpy.context.preferences.view.language == "zh_HANS":
                self.report({"WARNING"}, "未找到目标 / 目标不是骨架")
            else:
                self.report({"WARNING"}, "Target not found / The target is not a skeleton.")
            return {"FINISHED"}

        if obj.hide_get() or obj.hide_viewport:
            if bpy.context.preferences.view.language == "zh_HANS":
                self.report({"WARNING"}, "目标不可视")
            else:
                self.report({"WARNING"}, "The target is hidden.")
            return {"FINISHED"}

        pb = obj.pose.bones.get(self.bone_name)
        if not pb:
            if bpy.context.preferences.view.language == "zh_HANS":
                self.report({"WARNING"}, "未找到目标")
            else:
                self.report({"WARNING"}, "Target not found.")
            return {"FINISHED"}

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="POSE")
        bpy.ops.pose.select_all(action="DESELECT")

        pb.select = True
        obj.data.bones.active = obj.data.bones[self.bone_name]

        return {"FINISHED"}


# -----------
# utils
# -----------


def _import_bone(JSON_BONES={}, apply_pose=False, path_bones=[]):
    spine_setting = get_context_scene_cmd().spine

    scale = spine_setting.import_scale
    character_name = spine_setting.character_name
    skin_name = spine_setting.import_skin_name

    arm_name = f"{character_name}-{skin_name}-SpineArm"

    collection = bpy.data.collections.get(character_name)
    if not collection:
        collection = bpy.data.collections.new(character_name)
        bpy.context.scene.collection.children.link(collection)

    arm = bpy.data.armatures.new(arm_name)
    arm_obj = bpy.data.objects.new(arm_name, arm)
    collection.objects.link(arm_obj)

    arm_obj.show_in_front = True
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode="EDIT")
    for bone_name, data in JSON_BONES.items():
        parent = data.get("parent")
        length = data.get("length")

        nb = arm.edit_bones.new(name=bone_name)
        nb.tail = length * scale, 0, 0
        if parent:
            nb.parent = arm.edit_bones[parent]

    bpy.ops.object.mode_set(mode="POSE")
    for bone_name, data in JSON_BONES.items():

        x = data.get("x", 0)
        y = data.get("y", 0)
        rotation = data.get("rotation", 0)
        transform = data.get("transform")
        inherit = data.get("inherit")

        if transform == "noRotationOrReflection" or inherit == "noRotationOrReflection":
            arm.bones[bone_name].use_inherit_rotation = False
        elif transform == "noScale" or inherit == "noScale":
            arm.bones[bone_name].inherit_scale = "NONE"
        elif transform and transform != "normal" or inherit and inherit != "normal":
            print("-" * 10)
            print(f"[ PASS ] json - bones")
            print(f"[ INFO ] transform -> {bone_name} -> {transform} (不支持的类型)")

        pb = arm_obj.pose.bones[bone_name]
        pb.location = 0, x * scale, y * scale
        pb.rotation_mode = "XYZ"
        pb.rotation_euler[0] = math.radians(rotation)

    if apply_pose:
        bpy.ops.pose.armature_apply(selected=False)

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _apply_bone_scale(arm_obj=None, JSON_BONES={}):
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")

    for bone_name, data in JSON_BONES.items():
        scaleX = data.get("scaleX", 1)
        scaleY = data.get("scaleY", 1)
        pb = arm_obj.pose.bones[bone_name]
        pb.scale.y = scaleX
        pb.scale.z = scaleY
    bpy.ops.object.mode_set(mode="OBJECT")


def _import_mesh(arm_obj=None, BONES_DICT={}, SLOTS_DICT={}, ATTACHMENTS_DCIT={}, BONE_MATRIX_DICT={}, ATLAS_DATA={}):
    spine_setting = get_context_scene_cmd().spine

    scale = spine_setting.import_scale
    character_name = spine_setting.character_name
    image_path = spine_setting.image_path
    atlas_folder = spine_setting.atlas_folder
    import_type = spine_setting.import_type
    skin_name = spine_setting.import_skin_name

    _bone_list = list(BONES_DICT)
    _attachment_view = [data.get("attachment") for _, data in SLOTS_DICT.items() if data.get("attachment")]

    # 构建目标skins的附件网格
    for slot_name, slot_data in ATTACHMENTS_DCIT.items():
        slot = SLOTS_DICT.get(slot_name)
        bone_name = "" if not slot else slot.get("bone", "")

        if not slot or not bone_name:
            print("-" * 10)
            print(f"[ PASS ] skins -> attachments")
            print(f"[ PASS ] 导入 {slot_name} 网格错误")
            continue

        for attachment_name, attachment_data in slot_data.items():
            _bone = BONE_MATRIX_DICT.get(bone_name)
            _type = attachment_data.get("type", "region")

            uvs = attachment_data.get("uvs", [])
            triangles = attachment_data.get("triangles", [])
            vertices = attachment_data.get("vertices", [])
            vertexCount = attachment_data.get("vertexCount", [])

            mesh_vertices = []
            mesh_faces = []
            uvs_list = []
            vertices_list = []
            mesh_vertex_weight = {}
            if _type == "region":
                x = attachment_data.get("x", 0) * scale
                y = attachment_data.get("y", 0) * scale

                scaleX = attachment_data.get("scaleX", 1)
                scaleY = attachment_data.get("scaleY", 1)

                width = attachment_data.get("width") * scale
                height = attachment_data.get("height") * scale

                rotation = _bone["matrix_eular"][0] + math.radians(attachment_data.get("rotation", 0))

                region_x = x * math.cos(_bone["matrix_eular"][0]) - y * math.sin(_bone["matrix_eular"][0])
                region_y = x * math.sin(_bone["matrix_eular"][0]) + y * math.cos(_bone["matrix_eular"][0])

                mesh_vertices = [
                    (
                        ((-width / 2) * math.cos(rotation) - (height / 2) * math.sin(rotation) + region_x) * _bone["matrix_scale"][1] + _bone["matrix_translation"][0],
                        0,
                        ((-width / 2) * math.sin(rotation) + (height / 2) * math.cos(rotation) + region_y) * _bone["matrix_scale"][2] + _bone["matrix_translation"][2],
                    ),
                    (
                        ((width / 2) * math.cos(rotation) - (height / 2) * math.sin(rotation) + region_x) * _bone["matrix_scale"][1] + _bone["matrix_translation"][0],
                        0,
                        ((width / 2) * math.sin(rotation) + (height / 2) * math.cos(rotation) + region_y) * _bone["matrix_scale"][2] + _bone["matrix_translation"][2],
                    ),
                    (
                        ((-width / 2) * math.cos(rotation) - (-height / 2) * math.sin(rotation) + region_x) * _bone["matrix_scale"][1] + _bone["matrix_translation"][0],
                        0,
                        ((-width / 2) * math.sin(rotation) + (-height / 2) * math.cos(rotation) + region_y) * _bone["matrix_scale"][2] + _bone["matrix_translation"][2],
                    ),
                    (
                        ((width / 2) * math.cos(rotation) - (-height / 2) * math.sin(rotation) + region_x) * _bone["matrix_scale"][1] + _bone["matrix_translation"][0],
                        0,
                        ((width / 2) * math.sin(rotation) + (-height / 2) * math.cos(rotation) + region_y) * _bone["matrix_scale"][2] + _bone["matrix_translation"][2],
                    ),
                ]

                mesh_faces = [[0, 1, 3, 2]]
                vertices_list = uvs_list = [
                    [0, 0],
                    [1, 0],
                    [0, 1],
                    [1, 1],
                ]

            elif _type == "mesh":
                if len(vertices) == len(set(triangles)) * 2:
                    vertices_list = [(vertices[i : i + 2]) for i in range(0, len(vertices), 2)]

                    for x, y in vertices_list:
                        x *= scale
                        y *= scale
                        weight = 1
                        pos = [
                            (x * math.cos(_bone["matrix_eular"][0]) - y * math.sin(_bone["matrix_eular"][0])) * _bone["matrix_scale"][1] + _bone["matrix_translation"][0] * weight,
                            0,
                            (y * math.cos(_bone["matrix_eular"][0]) + x * math.sin(_bone["matrix_eular"][0])) * _bone["matrix_scale"][1] + _bone["matrix_translation"][2] * weight,
                        ]
                        mesh_vertices.append(mathutils.Vector(pos))

                    mesh_faces = list(zip(triangles[::3], triangles[1::3], triangles[2::3]))

                    uvs_list = [(uvs[i : i + 2]) for i in range(0, len(uvs), 2)]

                else:
                    _vertices = attachment_data.get("vertices", []).copy()
                    vertices_list = get_vertices_list(_vertices, scale=scale, _list=[])
                    for data in vertices_list:
                        x = y = 0
                        for i in data:
                            _bone = BONE_MATRIX_DICT.get(_bone_list[i["bone_idx"]])

                            x += ((i["x"] * math.cos(_bone["matrix_eular"][0]) - i["y"] * math.sin(_bone["matrix_eular"][0])) * _bone["matrix_scale"][1] + _bone["matrix_translation"][0]) * i["weight"]

                            y += ((i["y"] * math.cos(_bone["matrix_eular"][0]) + i["x"] * math.sin(_bone["matrix_eular"][0])) * _bone["matrix_scale"][1] + _bone["matrix_translation"][2]) * i["weight"]

                        pos = [x, 0, y]
                        mesh_vertices.append(mathutils.Vector(pos))

                    mesh_faces = list(zip(triangles[::3], triangles[1::3], triangles[2::3]))

                    uvs_list = [(uvs[i : i + 2]) for i in range(0, len(uvs), 2)]

                    for e, data in enumerate(vertices_list):
                        _vt = []
                        for i in data:
                            _bone = BONE_MATRIX_DICT.get(_bone_list[i["bone_idx"]])
                            _vt.append({"bone_idx": i["bone_idx"], "weight": i["weight"]})
                        mesh_vertex_weight |= {e: _vt}

            elif _type == "clipping":
                if len(vertices) == vertexCount * 2:
                    vertices_list = [(vertices[i : i + 2]) for i in range(0, len(vertices), 2)]

                    for x, y in vertices_list:
                        x *= scale
                        y *= scale
                        weight = 1
                        pos = [
                            (x * math.cos(_bone["matrix_eular"][0]) - y * math.sin(_bone["matrix_eular"][0])) * _bone["matrix_scale"][1] + _bone["matrix_translation"][0] * weight,
                            0,
                            (y * math.cos(_bone["matrix_eular"][0]) + x * math.sin(_bone["matrix_eular"][0])) * _bone["matrix_scale"][1] + _bone["matrix_translation"][2] * weight,
                        ]
                        mesh_vertices.append(mathutils.Vector(pos))

                    mesh_faces = [list(range(vertexCount))]

                else:
                    _vertices = attachment_data.get("vertices", []).copy()
                    vertices_list = get_vertices_list(_vertices, scale=scale, _list=[])
                    for data in vertices_list:
                        x = y = 0
                        for i in data:
                            _bone = BONE_MATRIX_DICT.get(_bone_list[i["bone_idx"]])

                            x += ((i["x"] * math.cos(_bone["matrix_eular"][0]) - i["y"] * math.sin(_bone["matrix_eular"][0])) * _bone["matrix_scale"][1] + _bone["matrix_translation"][0]) * i["weight"]

                            y += ((i["y"] * math.cos(_bone["matrix_eular"][0]) + i["x"] * math.sin(_bone["matrix_eular"][0])) * _bone["matrix_scale"][1] + _bone["matrix_translation"][2]) * i["weight"]

                        pos = [x, 0, y]
                        mesh_vertices.append(mathutils.Vector(pos))

                    mesh_faces = [list(range(vertexCount))]

                    for e, data in enumerate(vertices_list):
                        _vt = []
                        for i in data:
                            _bone = BONE_MATRIX_DICT.get(_bone_list[i["bone_idx"]])
                            _vt.append({"bone_idx": i["bone_idx"], "weight": i["weight"]})
                        mesh_vertex_weight |= {e: _vt}

            # New Mesh
            if mesh_vertices and mesh_faces:
                mesh_name = f"{character_name}-{slot_name}-{attachment_name}"

                mesh = bpy.data.meshes.new(mesh_name)
                mesh_obj = bpy.data.objects.new(mesh_name, mesh)
                mesh.from_pydata(mesh_vertices, [], mesh_faces)
                mesh.update()

                collection = bpy.data.collections.get(character_name)
                if not collection:
                    collection = bpy.data.collections.new(character_name)
                    bpy.context.scene.collection.children.link(collection)
                collection.objects.link(mesh_obj)

                modi = mesh_obj.modifiers.new("Armature", "ARMATURE")
                modi.object = arm_obj
                mesh_obj.parent = arm_obj

                bone_name = SLOTS_DICT.get(slot_name).get("bone")

                # 顶点权重
                if mesh_vertex_weight:
                    for idx, vlist in mesh_vertex_weight.items():
                        for i in vlist:
                            _bone = _bone_list[i["bone_idx"]]
                            vg = mesh_obj.vertex_groups.get(_bone)
                            if not vg:
                                vg = mesh_obj.vertex_groups.new(name=_bone)
                            vg.add([idx], i["weight"], "REPLACE")
                else:
                    _bone = SLOTS_DICT.get(slot_name).get("bone")
                    if _bone:
                        vg = mesh_obj.vertex_groups.new(name=_bone)
                        vg.add(list(range(len(vertices_list))), 1, "REPLACE")

                for e, i in enumerate(SLOTS_DICT):
                    if SLOTS_DICT[i].get("attachment") == attachment_name:
                        mesh_obj.location[1] = e * -0.0001 * spine_setting.y_sort_scale
                        break

                if image_path and Path(image_path).exists():
                    if _type == "region" and import_type == "redive" and Path(atlas_folder).exists():
                        for i in Path(atlas_folder).iterdir():
                            if i.stem == attachment_name:
                                material = create_material(
                                    material_name=f"{character_name}-{skin_name}-{i.stem}",
                                    image_filepath=str(i),
                                )
                                mesh.materials.append(material)
                    else:
                        material = create_material(
                            material_name=f"{character_name}-{skin_name}-{Path(image_path).stem}",
                            image_filepath=image_path,
                        )
                        mesh.materials.append(material)

                if uvs_list:
                    if _type == "region" and import_type == "redive":
                        mesh_obj.select_set(True)
                        bpy.context.view_layer.objects.active = mesh_obj
                        bpy.ops.object.mode_set(mode="OBJECT")
                        bpy.ops.object.select_all(action="DESELECT")
                        bpy.ops.object.mode_set(mode="EDIT")
                        mesh_obj.data.uv_layers.new()
                        _mirror_uv(direction="y", mesh=mesh)
                    else:
                        _mesh_create_uv(ATLAS_DATA, uvs_list, attachment_name, mesh_obj)
                        if attachment_data.get("scaleX", 1) == -1:
                            mesh_obj.select_set(True)
                            bpy.context.view_layer.objects.active = mesh_obj
                            bpy.ops.object.mode_set(mode="OBJECT")
                            bpy.ops.object.select_all(action="DESELECT")
                            bpy.ops.object.mode_set(mode="EDIT")
                            _mirror_uv(direction="x", mesh=mesh)
                        if attachment_data.get("scaleY", 1) == -1:
                            mesh_obj.select_set(True)
                            bpy.context.view_layer.objects.active = mesh_obj
                            bpy.ops.object.mode_set(mode="OBJECT")
                            bpy.ops.object.select_all(action="DESELECT")
                            bpy.ops.object.mode_set(mode="EDIT")
                            _mirror_uv(direction="y", mesh=mesh)

                if attachment_name not in _attachment_view:
                    mesh_obj.hide_set(True)


def load_spine_json(path):
    if not Path(path).exists():
        return
    json_data = json.load(Path(path).open("r"))
    return json_data


def load_spine_atlas(path):
    if not Path(path).exists():
        return

    atlas_text = []
    with open(path, "r") as f:
        atlas_text = f.readlines()
    atlas_text = [i.replace("\n", "") for i in atlas_text if i.replace("\n", "")]

    atlas_data = {}

    _dict = {}
    _prop = {}
    for e, text in enumerate(atlas_text):
        if text.strip() == text and ":" not in text:
            # if ":" in text:
            #     k, v = text.split(":", 1)
            #     _dict = {k.strip(): v.strip()}
            #     atlas_data |= _dict
            if _prop:
                atlas_data |= {list(_dict)[0]: _prop}
                _dict = {text: {}}
            else:
                _dict = {text: {}}
            _prop = {}
        else:
            key, value = text.strip().split(":", 1)
            if key.strip() == "bounds":
                numbers = [int(num.strip()) for num in value.strip().split(",")]
                _prop |= {"xy": f"{numbers[0], numbers[1]}"}
                _prop |= {"size": f"{numbers[2], numbers[3]}"}
                _prop |= {"orig": f"{numbers[2], numbers[3]}"}
                _prop |= {"offset": "0, 0"}

            elif key.strip() == "rotate":
                if value.strip() == "true":
                    value = "90"
                elif value.strip() == "false":
                    value = "0"

            _prop |= {key.strip(): value.strip()}

        if e == len(atlas_text) - 1:
            atlas_data |= {list(_dict)[0]: _prop}

    for key in atlas_data:
        if ".png" in key:
            size = atlas_data[key].get("size")
            if size:
                atlas_data |= {"size": size}
                break
    return atlas_data


def load_bones(JSON_DATA):
    _load = {}
    for data in JSON_DATA.get("bones"):
        _dict = {
            "x": data.get("x", 0),
            "y": data.get("y", 0),
            "length": data.get("length", 5),
            "rotation": data.get("rotation", 0),
            "scaleX": data.get("scaleX", 1),
            "scaleY": data.get("scaleY", 1),
            "transform": data.get("transform", None),
            "parent": data.get("parent", None),
            "inherit": data.get("inherit", None),
        }
        _load |= {data.get("name"): _dict}
    return _load


def get_path_bones(JSON_DATA):
    bones = []
    for data in JSON_DATA.get("path", []):
        bones.extend(data.get("bones", []))
    return bones


def load_slots(JSON_DATA):
    _load = {}
    for data in JSON_DATA.get("slots"):
        _dict = {
            "bone": data.get("bone", ""),
            "attachment": data.get("attachment"),
        }
        _load |= {data.get("name"): _dict}
    return _load


def load_attachments(JSON_DATA, skin_name="default"):
    for data in JSON_DATA.get("skins"):
        if data.get("name") == skin_name:
            return data.get("attachments")


def _get_bone_matrix_dict(arm_obj):
    _matrix_dict = {}
    for i in arm_obj.pose.bones:
        _dict = {
            "matrix_eular": i.matrix.to_euler("XYZ").copy(),
            "matrix_scale": i.matrix.to_scale().copy(),
            "matrix_translation": i.matrix.to_translation().copy(),
        }
        _matrix_dict |= {i.name: _dict}
    return _matrix_dict


def from_slots_get_bone(SLOTS_DICT, slot_name):
    if SLOTS_DICT.get(slot_name) and SLOTS_DICT.get(slot_name).get("bone"):
        return SLOTS_DICT.get(slot_name).get("bone")


def create_material(material_name, image_filepath):
    material = bpy.data.materials.get(material_name)
    if material:
        return material

    material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    material.surface_render_method = "BLENDED"

    for i in material.node_tree.nodes:
        material.node_tree.nodes.remove(i)

    bsdf_node = material.node_tree.nodes.new("ShaderNodeBsdfTransparent")
    image_node = material.node_tree.nodes.new("ShaderNodeTexImage")
    mix_node = material.node_tree.nodes.new("ShaderNodeMixShader")
    output_node = material.node_tree.nodes.new("ShaderNodeOutputMaterial")

    bsdf_node.location = 115, 390
    image_node.location = -155, 390
    mix_node.location = 115, 290
    output_node.location = 290, 290

    image_node.interpolation = "Closest"

    if Path(image_filepath).exists():
        for i in bpy.data.images:
            if i.filepath == image_filepath:
                image_node.image = i
                break
        if not image_node.image:
            image_node.image = bpy.data.images.load(image_filepath)
            image_node.image.alpha_mode = "CHANNEL_PACKED"
            # image_node.image.alpha_mode = "PREMUL"

    links = material.node_tree.links

    links.new(image_node.outputs[0], mix_node.inputs[2])
    links.new(image_node.outputs[1], mix_node.inputs[0])

    links.new(bsdf_node.outputs[0], mix_node.inputs[1])
    links.new(mix_node.outputs[0], output_node.inputs[0])

    return material


def _mesh_create_uv(ATLAS_DATA, uvs_list, attachment_name, mesh_obj):
    atlas_size = eval(f"{ATLAS_DATA.get('size')}")
    uv_attachment = ATLAS_DATA.get(attachment_name)

    if not uv_attachment:
        return

    uv_rotate = eval(f"{uv_attachment.get('rotate')}")
    uv_point_x = eval(f"{uv_attachment.get('xy')}")[0]
    uv_point_y = eval(f"{uv_attachment.get('xy')}")[1]
    uv_orig_x = eval(f"{uv_attachment.get('orig')}")[0]
    uv_orig_y = eval(f"{uv_attachment.get('orig')}")[1]
    uv_size_x = eval(f"{uv_attachment.get('size')}")[0]
    uv_size_y = eval(f"{uv_attachment.get('size')}")[1]
    uv_offset_x = eval(f"{uv_attachment.get('offset')}")[0]
    uv_offset_y = eval(f"{uv_attachment.get('offset')}")[1]

    offset_x = uv_orig_x - uv_size_x
    offset_y = uv_orig_y - uv_size_y

    uv_data = []

    for x, y in uvs_list:

        x *= uv_orig_x / atlas_size[0]
        y *= uv_orig_y / atlas_size[1]

        x -= (uv_orig_x - uv_size_x) / atlas_size[0]
        y -= (uv_orig_y - uv_size_y) / atlas_size[1]

        if uv_rotate == 90:
            x, y = y, x
            x += (uv_point_x + uv_offset_x - offset_x) / atlas_size[0]
            y += 1 - ((uv_orig_x + uv_point_y - offset_y) / atlas_size[1])
        elif uv_rotate == 270:
            x, y = y, x
            x += (uv_point_x + uv_offset_x - offset_x) / atlas_size[0]
            y += 1 - ((uv_orig_x + uv_point_y - offset_y) / atlas_size[1])
        else:
            x += uv_point_x / atlas_size[0]
            y += (uv_point_y + uv_offset_y) / atlas_size[1]
            y = 1 - y
        uv_data.append((x, y))

    uv = mesh_obj.data.uv_layers.new()
    for e, loop in enumerate(mesh_obj.data.loops):
        uv.data[e].uv = uv_data[loop.vertex_index]

    if uv_rotate == 270 or uv_rotate == 180:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

        mesh_obj.select_set(True)
        bpy.context.view_layer.objects.active = mesh_obj
        bpy.ops.object.mode_set(mode="EDIT")

        if uv_rotate == 270:
            _rotation_uv(direction="reverse", mesh=mesh_obj.data, rotate=uv_rotate - 90)

        elif uv_rotate == 180:
            _rotation_uv(direction="reverse", mesh=mesh_obj.data, rotate=uv_rotate)

        bpy.ops.object.mode_set(mode="OBJECT")


def _build_ik(JSON_DATA, spine_arm):
    spine_arm.select_set(True)
    bpy.context.view_layer.objects.active = spine_arm

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="POSE")

    bpy.ops.pose.armature_apply(selected=False)

    iks = JSON_DATA.get("ik")
    if not iks:
        bpy.ops.object.mode_set(mode="OBJECT")
        return

    for data in JSON_DATA.get("ik"):
        subtarget = data.get("target")
        bones = data.get("bones")
        bendPositive = data.get("bendPositive")
        mix = data.get("mix", 1)

        if not subtarget or not bones:
            continue

        cr_bone = spine_arm.pose.bones[bones[-1]]
        cr = cr_bone.constraints.new("IK")

        cr.name = "SPINE_IK"
        cr.chain_count = len(bones)

        cr.target = spine_arm
        cr.subtarget = subtarget
        cr.influence = mix

        if len(bones) != 1:
            for i in bones:
                pb = spine_arm.pose.bones[i]
                pb.lock_ik_y = pb.lock_ik_z = True

            cr_bone.use_ik_limit_x = True
            if bendPositive:
                cr_bone.ik_min_x = 0
            else:
                cr_bone.ik_max_x = 0
    bpy.ops.object.mode_set(mode="OBJECT")


def _rotation_uv(direction="reverse", mesh=None, rotate=90):
    if not mesh:
        return
    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(mesh)
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.active

    faces = list()
    for face in bm.faces:
        if face.select:
            faces.append(face)

    mirrored = False
    for face in faces:
        sum_edges = 0
        for i in range(3):
            uv_A = face.loops[i][uv_layer].uv
            uv_B = face.loops[(i + 1) % 3][uv_layer].uv
            sum_edges += (uv_B.x - uv_A.x) * (uv_B.y + uv_A.y)

        if sum_edges > 0:
            mirrored = True

    xmin, xmax = faces[0].loops[0][uv_layer].uv.x, faces[0].loops[0][uv_layer].uv.x
    ymin, ymax = faces[0].loops[0][uv_layer].uv.y, faces[0].loops[0][uv_layer].uv.y

    for face in faces:
        for vert in face.loops:
            xmin = min(xmin, vert[uv_layer].uv.x)
            xmax = max(xmax, vert[uv_layer].uv.x)
            ymin = min(ymin, vert[uv_layer].uv.y)
            ymax = max(ymax, vert[uv_layer].uv.y)

    xcenter = (xmin + xmax) / 2
    ycenter = (ymin + ymax) / 2

    PI = 3.14159265359 / (180 / rotate)
    delta = (3.14159265359 / 180) * rotate
    if direction == "reverse":
        delta = -delta
    if mirrored:
        delta = -delta

    for face in faces:
        for loop in face.loops:
            loop[uv_layer].uv.x -= xcenter
            loop[uv_layer].uv.y -= ycenter

            oldx = loop[uv_layer].uv.x
            oldy = loop[uv_layer].uv.y

            loop[uv_layer].uv.x = oldx * math.cos(delta) - oldy * math.sin(delta)
            loop[uv_layer].uv.y = oldy * math.cos(delta) + oldx * math.sin(delta)

            loop[uv_layer].uv.x += xcenter
            loop[uv_layer].uv.y += ycenter

    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def _mirror_uv(direction="x", mesh=None):
    if not mesh:
        return

    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(mesh)
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.active

    faces = list()

    for face in bm.faces:
        if face.select:
            faces.append(face)

    xmin, xmax = faces[0].loops[0][uv_layer].uv.x, faces[0].loops[0][uv_layer].uv.x
    ymin, ymax = faces[0].loops[0][uv_layer].uv.y, faces[0].loops[0][uv_layer].uv.y

    for face in faces:
        for vert in face.loops:
            xmin = min(xmin, vert[uv_layer].uv.x)
            xmax = max(xmax, vert[uv_layer].uv.x)
            ymin = min(ymin, vert[uv_layer].uv.y)
            ymax = max(ymax, vert[uv_layer].uv.y)

        if (xmax - xmin) == 0:
            xmin = 0.1
        if (ymax - ymin) == 0:
            ymin = 0.1

    for face in faces:
        for loop in face.loops:
            loop[uv_layer].uv.x -= xmin
            loop[uv_layer].uv.y -= ymin
            loop[uv_layer].uv.x /= xmax - xmin
            loop[uv_layer].uv.y /= ymax - ymin

            if direction == "x":
                loop[uv_layer].uv.x = -loop[uv_layer].uv.x + 1.0
            if direction == "y":
                loop[uv_layer].uv.y = -loop[uv_layer].uv.y + 1.0

            loop[uv_layer].uv.x *= xmax - xmin
            loop[uv_layer].uv.y *= ymax - ymin
            loop[uv_layer].uv.x += xmin
            loop[uv_layer].uv.y += ymin

    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def get_vertices_list(_vertices, scale=1, _list=[]):
    _data = []
    for _ in range(_vertices.pop(0)):
        _data.append(
            {
                "bone_idx": _vertices.pop(0),
                "x": _vertices.pop(0) * scale,
                "y": _vertices.pop(0) * scale,
                "weight": _vertices.pop(0),
            }
        )
    _list.append(_data)
    if len(_vertices) >= 5:
        return get_vertices_list(_vertices, scale=scale, _list=_list)
    return _list


# -----------
# REGISTER
# -----------


classes = [
    OPS_Import_Spine,
    OPS_Import_Spine_Slots_Data,
    OPS_Select_Json_File,
    OPS_Select_Atlas_File,
    OPS_Select_Image_File,
    OPS_Select_Object,
    OPS_Select_Pose_Bone,
    OPS_Change_Object_Visible,
]


def register():
    pass


def unregister():
    pass
