bl_info = {
    "author": "RinCamp",
    "name": "Spine_To_Blender",
    "category": "Rin",
    "blender": (4, 5, 0),
    "version": (0, 0, 2),
    "doc_url": "",
    "location": "3D View > N Panel > Spine",
    "description": "",
    "warning": "不支持动画导入, 仅适配Spine3.8.json的部分内容导入(骨骼/网格)",
    # "tracker_url": "",
}

import bpy
from bpy.props import *
from bpy.types import PropertyGroup, Operator, Panel
from bpy_extras.io_utils import ImportHelper

import bmesh

import time
import mathutils
import math
import json
from pathlib import Path
      
# ----------- 
# Panel
# ----------- 

def common_draw(self, context):
    if bpy.context.preferences.view.language == 'zh_HANS':
        common_draw_zh_cn(self, context)
    else:
        common_draw_en_us(self, context)


def common_draw_en_us(self, context):
    spine_setting = bpy.context.scene.RHS_SPINE

    layout = self.layout
    col = layout.column(align=True)
    
    box = col.box()
    br = box.row()
    br.scale_y = 1.2
    br.prop(spine_setting, 'ui_type', expand=True)

    if spine_setting.ui_type == 'import':
        bc = box.column()
        bc.scale_x = 1.2
        bc.scale_y = 1.2
        br = bc.row()
        br.label(text='Select File', icon='DUPLICATE')
        br.prop(spine_setting, 'show_file_name', text='', icon='CON_TRANSFORM_CACHE')
        br = bc.row()
        br.label(icon='BLANK1')
        sp = br.split()

        spc = sp.column(align=True)
        cr = spc.row(align=True)
        cr.prop(spine_setting, 'spine_json', text='', icon='EVENT_J')
        cr.operator("rhs.select_json_file", text="", icon='FILEBROWSER')

        cr = spc.row(align=True)
        cr.prop(spine_setting, 'spine_atlas', text='', icon='EVENT_A')
        cr.operator("rhs.select_atlas_file", text="", icon='FILEBROWSER')

        cr = spc.row(align=True)
        cr.prop(spine_setting, 'spine_image', text='', icon='IMAGE_PLANE')
        cr.operator("rhs.select_png_file", text="", icon='FILEBROWSER')
        
        spc2 = spc.column(align=True)
        _type = True if spine_setting.import_type == 'redive' else False
        spc2.active = _type
        spc2.prop(spine_setting, 'spine_image_atlas', text='', icon='RENDERLAYERS' if _type else 'X')

        if spine_setting.show_file_name:
            row = spc.row(align=True)
            row.alignment = 'LEFT'
            row.label(text='json')
            row.label(text=spine_setting.spine_json.split('\\')[-1], icon='TRIA_RIGHT')
            row = spc.row(align=True)
            row.alignment = 'LEFT'
            row.label(text='atlas')
            row.label(text=spine_setting.spine_atlas.split('\\')[-1], icon='TRIA_RIGHT')
            row = spc.row(align=True)
            row.alignment = 'LEFT'
            row.label(text='image', translate=False)
            row.label(text=spine_setting.spine_image.split('\\')[-1], icon='TRIA_RIGHT')
            row = spc.row(align=True)
            row.alignment = 'LEFT'
            row.label(text='dir', translate=False)
            if Path(spine_setting.spine_image_atlas).exists():
                row.label(text=Path(spine_setting.spine_image_atlas).name, icon='TRIA_RIGHT', translate=False)

        box = col.box()
        bc = box.column()
        bc.scale_y = 1.2
        bc.label(text='Import Config', icon='DUPLICATE')
        bc = box.column()
        bc.use_property_split = True
        bc.use_property_decorate = False

        bc.prop(spine_setting, 'spine_build_ik', text='IK', icon='CON_KINEMATIC')
        bc.prop(spine_setting, 'spine_import_scale', text='Scale', slider=True)
        bc.prop(spine_setting, 'character_name', text='Character')

        box = col.box()
        bc = box.column()
        bc.use_property_split = True
        bc.use_property_decorate = False
        bc.scale_y = 1.2
        bc.prop(spine_setting, 'import_version', text='Spine Version')
        bc.prop(spine_setting, 'import_type', text='Type')
        row = bc.row()
        row.scale_y = 2
        row.operator('rhs.spine_loader', text='Import', icon='IMPORT')

    elif spine_setting.ui_type == 'layer':
        bc = box.column()
        bc.scale_x = 1.2
        bc.scale_y = 1.2
        bc.prop(spine_setting, 'armature', text='', icon='OUTLINER_OB_ARMATURE')
        br = bc.row(align=True)
        br.prop(spine_setting, 'replace_prefix', text='', icon='SHADERFX')
        br.prop(spine_setting, 'search_filter', text='', icon='FILTER')

        obj = bpy.data.objects.get(spine_setting.armature)

        if not obj or obj and obj.type != 'ARMATURE':
            box = col.box()
            box.scale_y = 3
            br = box.row()
            br.alignment = 'CENTER'
            br.alert = True
            br.label(text='No armature set')
        else:
            child = []
            for i in obj.children_recursive:
                if spine_setting.hide_zero and i.location[1] == 0:
                    continue
                if spine_setting.hide_view:
                    if i.hide_get() == True or i.hide_viewport == True:
                        continue
                if spine_setting.search_filter:
                    if spine_setting.search_filter.lower() not in i.name.replace(spine_setting.replace_prefix, '', 1).lower():
                        continue
                child.append(i)

            box = col.box()
            br = box.row()
            br.scale_x = 1.2
            br.scale_y = 1.2
            br.prop(spine_setting, 'hide_view',text='', icon='FILE_3D')
            br.prop(spine_setting, 'hide_zero',text='', icon='DECORATE')
            br.prop(spine_setting, 'page_limit',text='Limit')

            box = col.box()
            bc = box.column()
            bc.scale_x = 1.2
            bc.scale_y = 1.2
            act_obj = bpy.context.object
            if act_obj and act_obj in child:
                br = bc.row()
                sp = br.split()
                spr = sp.row(align=True)
                spr.label(icon='SHADING_BBOX')
                spr.label(text=act_obj.name.replace(spine_setting.replace_prefix, '', 1))
                spr.prop(act_obj, 'location', index=1, text='')
                spr.separator()
                spr.operator("rhs.spine_object_hide", text="", icon='HIDE_ON' if act_obj.hide_get() else 'HIDE_OFF').obj_name=act_obj.name
                spr.prop(act_obj, 'hide_viewport', text='', toggle=True)
                spr.prop(act_obj, 'hide_render', text='', toggle=True)
            else:
                br = bc.row()
                br.alignment = 'CENTER'
                br.alert = True
                br.label(text='活动物体不属于骨架子集')
                
            box = col.box()
            bc = box.column()
            bc.scale_x = 1.2
            bc.scale_y = 1.2
            for e, mesh in enumerate(sorted(child, key=lambda x:x.location[1])):
                if e == spine_setting.page_limit:
                    break
                br = bc.row()
                sp = br.split()
                spr = sp.row(align=True)
                spr.active = True if mesh.hide_get() == False and mesh.hide_viewport == False else False
                spr.operator('rhs.spine_object_select', text='', 
                            icon='RESTRICT_SELECT_OFF' if bpy.context.object == mesh else 'RESTRICT_SELECT_ON',
                            emboss=0).obj_name=mesh.name
                spr.label(text=mesh.name.replace(spine_setting.replace_prefix, '', 1))
                spr.prop(mesh, 'location', index=1, text='')
                
                spr.separator()
                spr.operator("rhs.spine_object_hide", text="", icon='HIDE_ON' if mesh.hide_get() else 'HIDE_OFF').obj_name=mesh.name
                spr.prop(mesh, 'hide_viewport', text='', toggle=True)
                spr.prop(mesh, 'hide_render', text='', toggle=True)

      
def common_draw_zh_cn(self, context):
    spine_setting = bpy.context.scene.RHS_SPINE

    layout = self.layout
    col = layout.column(align=True)
    
    box = col.box()
    br = box.row()
    br.scale_y = 1.2
    br.prop(spine_setting, 'ui_type', expand=True)

    if spine_setting.ui_type == 'import':
        bc = box.column()
        bc.scale_x = 1.2
        bc.scale_y = 1.2
        br = bc.row()
        br.label(text='文件', icon='DUPLICATE')
        br.prop(spine_setting, 'show_file_name', text='', icon='CON_TRANSFORM_CACHE')
        br = bc.row()
        br.label(icon='BLANK1')
        sp = br.split()
        spc = sp.column(align=True)

        cr = spc.row(align=True)
        cr.prop(spine_setting, 'spine_json', text='', icon='EVENT_J')
        cr.operator("rhs.select_json_file", text="", icon='FILEBROWSER')

        cr = spc.row(align=True)
        cr.prop(spine_setting, 'spine_atlas', text='', icon='EVENT_A')
        cr.operator("rhs.select_atlas_file", text="", icon='FILEBROWSER')

        cr = spc.row(align=True)
        cr.prop(spine_setting, 'spine_image', text='', icon='IMAGE_PLANE')
        cr.operator("rhs.select_png_file", text="", icon='FILEBROWSER')
        
        spc2 = spc.column(align=True)
        _type = True if spine_setting.import_type == 'redive' else False
        spc2.active = _type
        spc2.prop(spine_setting, 'spine_image_atlas', text='', icon='RENDERLAYERS' if _type else 'X')

        if spine_setting.show_file_name:
            row = spc.row(align=True)
            row.alignment = 'LEFT'
            row.label(text='json')
            row.label(text=spine_setting.spine_json.split('\\')[-1], icon='TRIA_RIGHT')
            row = spc.row(align=True)
            row.alignment = 'LEFT'
            row.label(text='atlas')
            row.label(text=spine_setting.spine_atlas.split('\\')[-1], icon='TRIA_RIGHT')
            row = spc.row(align=True)
            row.alignment = 'LEFT'
            row.label(text='image', translate=False)
            row.label(text=spine_setting.spine_image.split('\\')[-1], icon='TRIA_RIGHT')
            row = spc.row(align=True)
            row.alignment = 'LEFT'
            row.label(text='dir', translate=False)
            if Path(spine_setting.spine_image_atlas).exists():
                row.label(text=Path(spine_setting.spine_image_atlas).name, icon='TRIA_RIGHT', translate=False)

        box = col.box()
        bc = box.column()
        bc.scale_y = 1.2
        bc.label(text='配置', icon='DUPLICATE')
        bc = box.column()
        bc.use_property_split = True
        bc.use_property_decorate = False

        bc.prop(spine_setting, 'spine_build_ik', text='IK', icon='CON_KINEMATIC')
        bc.prop(spine_setting, 'spine_import_scale', text='缩放', slider=True)
        bc.prop(spine_setting, 'character_name', text='角色')

        box = col.box()
        bc = box.column()
        bc.use_property_split = True
        bc.use_property_decorate = False
        bc.scale_y = 1.2
        bc.prop(spine_setting, 'import_version', text='版本')
        bc.prop(spine_setting, 'import_type', text='类型')
        row = bc.row()
        row.scale_y = 2
        row.operator('rhs.spine_loader', text='导入', icon='IMPORT')

    elif spine_setting.ui_type == 'layer':
        bc = box.column()
        bc.scale_x = 1.2
        bc.scale_y = 1.2
        bc.prop(spine_setting, 'armature', text='', icon='OUTLINER_OB_ARMATURE')
        br = bc.row(align=True)
        br.prop(spine_setting, 'replace_prefix', text='', icon='SHADERFX')
        br.prop(spine_setting, 'search_filter', text='', icon='FILTER')

        obj = bpy.data.objects.get(spine_setting.armature)

        if not obj or obj and obj.type != 'ARMATURE':
            box = col.box()
            box.scale_y = 3
            br = box.row()
            br.alignment = 'CENTER'
            br.alert = True
            br.label(text='未指定骨架')
        else:
            child = []
            for i in obj.children_recursive:
                if spine_setting.hide_zero and i.location[1] == 0:
                    continue
                if spine_setting.hide_view:
                    if i.hide_get() == True or i.hide_viewport == True:
                        continue
                if spine_setting.search_filter:
                    if spine_setting.search_filter.lower() not in i.name.replace(spine_setting.replace_prefix, '', 1).lower():
                        continue
                child.append(i)

            box = col.box()
            br = box.row()
            br.scale_x = 1.2
            br.scale_y = 1.2
            br.prop(spine_setting, 'hide_view',text='', icon='FILE_3D')
            br.prop(spine_setting, 'hide_zero',text='', icon='DECORATE')
            br.prop(spine_setting, 'page_limit',text='显示数量')

            box = col.box()
            bc = box.column()
            bc.scale_x = 1.2
            bc.scale_y = 1.2
            act_obj = bpy.context.object
            if act_obj and act_obj in child:
                br = bc.row()
                sp = br.split()
                spr = sp.row(align=True)
                spr.label(icon='SHADING_BBOX')
                spr.label(text=act_obj.name.replace(spine_setting.replace_prefix, '', 1))
                spr.prop(act_obj, 'location', index=1, text='')
                spr.separator()

                spr.operator("rhs.spine_object_hide", text="", icon='HIDE_ON' if act_obj.hide_get() else 'HIDE_OFF').obj_name=act_obj.name
                spr.prop(act_obj, 'hide_viewport', text='', toggle=True)
                spr.prop(act_obj, 'hide_render', text='', toggle=True)
            else:
                br = bc.row()
                br.alignment = 'CENTER'
                br.alert = True
                br.label(text='活动物体不属于骨架子集')
                
            box = col.box()
            bc = box.column()
            bc.scale_x = 1.2
            bc.scale_y = 1.2
            
            for e, mesh in enumerate(sorted(child, key=lambda x:x.location[1])):
                if e == spine_setting.page_limit:
                    break
                br = bc.row()
                sp = br.split()
                spr = sp.row(align=True)
                spr.active = True if mesh.hide_get() == False and mesh.hide_viewport == False else False
                spr.operator('rhs.spine_object_select', text='', 
                            icon='RESTRICT_SELECT_OFF' if bpy.context.object == mesh else 'RESTRICT_SELECT_ON',
                            emboss=0).obj_name=mesh.name
                spr.label(text=mesh.name.replace(spine_setting.replace_prefix, '', 1))
                spr.prop(mesh, 'location', index=1, text='')
                
                spr.separator()
                spr.operator("rhs.spine_object_hide", text="", icon='HIDE_ON' if mesh.hide_get() else 'HIDE_OFF').obj_name=mesh.name
            
                spr.prop(mesh, 'hide_viewport', text='', toggle=True)
                spr.prop(mesh, 'hide_render', text='', toggle=True)

            
def get_abs_path(prop=""):
    def wrap(self, context):
        self[prop] = bpy.path.abspath(self[prop])
    return wrap


class Scene_Spine(PropertyGroup):
    import_version : EnumProperty(
        default = '3.8',
        items = [
                ('3.8', '3.8', ''),
                ],
        )
    import_type : EnumProperty(
        default = 'arknights',
        items = [
                ('arknights', 'Arknights', '',),
                ('redive', 'Re:Dive', '',),
                ],
        )
    
    spine_json : StringProperty(name='', description='json文件路径', update=get_abs_path('spine_json'))
    spine_atlas : StringProperty(name='', description='atlas文件路径', update=get_abs_path('spine_atlas'))
    spine_image : StringProperty(name='', description='image文件路径', update=get_abs_path('spine_image'))
    spine_image_atlas : StringProperty(name='', description='图集文件夹', update=get_abs_path('spine_image_atlas'))

    spine_import_scale : FloatProperty(default=0.01, min=0.01, max=1)
    spine_build_ik : BoolProperty(default=True)

    ui_type : EnumProperty(
        default = 'import',
        items = [
                ('import', 'Import', '', 'OPTIONS', 0),
                ('layer', 'Mesh', '', 'RENDERLAYERS', 1),
                ],
        )
    
    show_file_name : BoolProperty()
    character_name : StringProperty(default='default')

    armature : StringProperty(search=lambda self, context, edit_text: [i.name for i in bpy.context.scene.objects if i.type == 'ARMATURE'])
    replace_prefix : StringProperty(name='', description='Replace list prefix\n替换列表前缀', default='default_')
    page : IntProperty(min=1)
    page_limit : IntProperty(name='', description='Limit\n列表数量, -1 is not restricted.', default=-1, min=-1, max=1000)
    search_filter : StringProperty(name='Search keywords\n检索关键字')
    
    hide_zero : BoolProperty(name='', description='Filter objects with Y-axis value of 0\n列表过滤处于0坐标的物体')
    hide_view : BoolProperty(name='', description='Filter out invisible objects\n列表过滤不可视的物体')
    

class SPINE_PT_VIEW3D_DRAW(Panel):
    bl_label = 'Spine'
    bl_idname = 'SPINE_PT_VIEW3D_DRAW'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Spine'
    
    def draw(self,context):
        common_draw(self, context)

# ----------- 
# Operator
# ----------- 

class Spine_Loader(Operator):
    bl_idname = "rhs.spine_loader"  
    bl_label = ''
    
    def execute(self, context):
        start = time.perf_counter()
        spine_setting = bpy.context.scene.RHS_SPINE

        JSON_DATA = load_spine_json(spine_setting.spine_json)
        ATLAS_DATA = load_spine_atlas(spine_setting.spine_atlas)
        if not JSON_DATA and not ATLAS_DATA:
            self.report({'WARNING'}, "文件错误")
            return {'FINISHED'}
        
        BONES_DICT = load_bones(JSON_DATA)
        SLOTS_DICT = load_slots(JSON_DATA)
        ATTACHMENTS_DCIT = load_attachments(JSON_DATA, skin_name='default')
        
        arm_obj = _import_bone(spine_setting, BONES_DICT, suffix='_arm', apply_pose=True)
        # anim_obj = _import_bone(spine_setting, BONES_DICT, suffix='_anim', apply_pose=False)

        BONE_MATRIX_DICT = _get_bone_matrix_dict(arm_obj)

        _import_mesh(spine_setting, arm_obj, BONES_DICT, SLOTS_DICT, ATTACHMENTS_DCIT, BONE_MATRIX_DICT, ATLAS_DATA)
        
        if spine_setting.spine_build_ik:
            _build_ik(JSON_DATA, arm_obj)

        end = time.perf_counter()
        self.report({'INFO'}, "Load Spine: " + str(round(end - start,4)) + "s")
        return {'FINISHED'}

class Select_Object_Hide(Operator):
    bl_idname = "rhs.spine_object_hide"  
    bl_label = ''
    bl_description = ''
    
    obj_name : StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj_name)
        if obj:
            print(obj)
            obj.hide_set(not obj.hide_get())
        return {'FINISHED'}

class Select_Object_Select(Operator):
    bl_idname = "rhs.spine_object_select"  
    bl_label = ''
    bl_description = ''
    
    obj_name : StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.obj_name)
        if obj and obj.hide_get() == False and obj.hide_viewport == False:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
        return {'FINISHED'}

# ----------- 
# utils
# -----------

def _import_bone(spine_setting, JSON_BONES={}, suffix='', apply_pose=False):
    _scale = spine_setting.spine_import_scale
    _character_name = spine_setting.character_name

    arm_name = "Spine_" + _character_name + suffix

    collection = bpy.data.collections.get(_character_name)
    if not collection:
        collection = bpy.data.collections.new(_character_name)
        bpy.context.scene.collection.children.link(collection)

    arm = bpy.data.armatures.new(arm_name)
    arm_obj = bpy.data.objects.new(arm_name, arm)
    collection.objects.link(arm_obj)

    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    arm_obj.show_in_front = True

    bpy.ops.object.mode_set(mode='EDIT')
    for bone_name, data in JSON_BONES.items():
        parent = data.get('parent')
        length = data.get('length')

        nb = arm.edit_bones.new(name=bone_name)
        nb.tail = length * _scale, 0 ,0
        if parent:
            nb.parent = arm.edit_bones[parent]

    bpy.ops.object.mode_set(mode='POSE')
    for bone_name, data in JSON_BONES.items():
        x = data.get('x')
        y = data.get('y')
        scaleX = data.get('scaleX')
        scaleY = data.get('scaleY')
        rotation = data.get('rotation')
        transform = data.get('transform')

        if transform == 'noRotationOrReflection':
            arm.bones[bone_name].use_inherit_rotation = True
        elif transform == 'noScale':
            arm.bones[bone_name].inherit_scale = 'NONE'
        elif transform and transform != 'normal':
            print('-'*10)
            print(f'[ PASS ] json - bones')
            print(f'[ INFO ] transform -> {bone_name} -> {transform} (not support)')
            
        pb = arm_obj.pose.bones[bone_name]

        pb.location = 0, x * _scale, y * _scale
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler[0] = math.radians(rotation)
        pb.scale = 1, scaleX, scaleY

    if apply_pose:
        bpy.ops.pose.armature_apply(selected=False)

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


def _import_mesh(spine_setting, arm_obj=None, BONES_DICT={}, SLOTS_DICT={}, ATTACHMENTS_DCIT={}, BONE_MATRIX_DICT={}, ATLAS_DATA={}):
    _scale = spine_setting.spine_import_scale
    _character_name = spine_setting.character_name
    _image = spine_setting.spine_image
    _bone_list = list(BONES_DICT)
    _attachment_view = [data.get('attachment') for _, data in SLOTS_DICT.items() if data.get('attachment')]
    
    for slot_name, slot_data in ATTACHMENTS_DCIT.items():
        for attachment_name, attachment_data in slot_data.items():
            _type = attachment_data.get('type', 'region')
            _uvs = attachment_data.get('uvs', [])

            mesh_vertices = []
            mesh_faces = []
            uvs_list = []
            vertices_list = []
            mesh_vertex_weight = {}

            if _type == 'region' and attachment_data.get('width') and attachment_data.get('height'):
                if not attachment_data.get('x') or not attachment_data.get('y'):
                    continue

                for key, value in SLOTS_DICT.items():
                    if key == slot_name:
                        _bone = BONE_MATRIX_DICT.get(value.get('bone', ''))
                        break
                if not _bone:
                    print('-'*10)
                    print(f'[ PASS ] skins -> attachments')
                    print(f'[ PASS ] 导入 {slot_name} 网格错误')
                    continue

                x = attachment_data.get('x') * _scale
                y = attachment_data.get('y') * _scale
                width = attachment_data.get('width') * _scale
                height = attachment_data.get('height') * _scale
                
                region_x = x * math.cos(_bone['matrix_eular'][0]) - y * math.sin(_bone['matrix_eular'][0])
                region_y = x * math.sin(_bone['matrix_eular'][0]) + y * math.cos(_bone['matrix_eular'][0])

                rotate = _bone['matrix_eular'][0] + math.radians(attachment_data.get('rotation', 0))
                
                mesh_vertices = [
                    (
                        (
                            (-width / 2) * math.cos(rotate) - (height / 2) * math.sin(rotate) + region_x) 
                            * _bone['matrix_scale'][1] + _bone['matrix_translation'][0],
                        0,
                        (
                            (-width / 2) * math.sin(rotate) + (height / 2) * math.cos(rotate) + region_y) 
                            * _bone['matrix_scale'][2] + _bone['matrix_translation'][2]
                    ), (
                        (
                            (width / 2) * math.cos(rotate) - (height / 2) * math.sin(rotate) + region_x) 
                            * _bone['matrix_scale'][1] + _bone['matrix_translation'][0],
                        0,
                        (
                            (width / 2) * math.sin(rotate) + (height / 2) * math.cos(rotate) + region_y) 
                            * _bone['matrix_scale'][2] + _bone['matrix_translation'][2]
                    ), (
                        (
                            (-width / 2) * math.cos(rotate) - (-height / 2) * math.sin(rotate) + region_x) 
                            * _bone['matrix_scale'][1] + _bone['matrix_translation'][0],
                        0,
                        (
                            (-width / 2) * math.sin(rotate) + (-height / 2) * math.cos(rotate) + region_y) 
                            * _bone['matrix_scale'][2] + _bone['matrix_translation'][2]
                    ), (
                        (
                            (width / 2) * math.cos(rotate) - (-height / 2) * math.sin(rotate) + region_x) 
                            * _bone['matrix_scale'][1] + _bone['matrix_translation'][0],
                        0,
                        (
                            (width / 2) * math.sin(rotate) + (-height / 2) * math.cos(rotate) + region_y) 
                            * _bone['matrix_scale'][2] + _bone['matrix_translation'][2]
                    )
                ] 
                

                mesh_faces = [[0, 1, 3, 2]]
                
                vertices_list = uvs_list = [
                    [0,0], 
                    [1,0], 
                    [0,1], 
                    [1,1],
                ]

            elif _type == 'mesh':
                vertices = attachment_data.get('vertices', [])
                triangles = attachment_data.get('triangles', [])

                if len(vertices) == len(set(triangles)) * 2:
                    for key, value in SLOTS_DICT.items():
                        if key == slot_name:
                            _bone = BONE_MATRIX_DICT.get(value.get('bone', ''))
                            break
                    if not _bone:
                        print('-'*10)
                        print(f'[ PASS ] skins -> attachments')
                        print(f'[ PASS ] 导入 {slot_name} 网格错误')
                        continue

                    vertices_list = [(vertices[i:i+2]) for i in range(0, len(vertices), 2)]
                        
                    for x, y in vertices_list:
                        x *= _scale
                        y *= _scale
                        weight = 1
                        pos = [
                                (x * math.cos(_bone['matrix_eular'][0]) - y * math.sin(_bone['matrix_eular'][0])) 
                                * _bone['matrix_scale'][1] + _bone['matrix_translation'][0] * weight, 

                                0,

                                (y * math.cos(_bone['matrix_eular'][0]) + x * math.sin(_bone['matrix_eular'][0])) 
                                * _bone['matrix_scale'][1] + _bone['matrix_translation'][2] * weight,
                        ]
                        mesh_vertices.append(mathutils.Vector(pos))

                    mesh_faces = list(zip(triangles[::3], triangles[1::3], triangles[2::3]))

                    uvs_list = [(_uvs[i:i+2]) for i in range(0, len(_uvs), 2)]
                
                else:
                    _vertices = attachment_data.get('vertices', []).copy()
                    vertices_list = get_vertices_list(_vertices, scale=_scale, _list=[])
                    for data in vertices_list:
                        x = y = 0
                        for i in data:
                            _bone = BONE_MATRIX_DICT.get(_bone_list[i['bone_idx']])

                            x += (
                                (i['x'] * math.cos(_bone['matrix_eular'][0]) - i['y'] * math.sin(_bone['matrix_eular'][0])) \
                                * _bone['matrix_scale'][1] + _bone['matrix_translation'][0]
                                ) * i['weight']
                            
                            y += (
                                (i['y'] * math.cos(_bone['matrix_eular'][0]) + i['x'] * math.sin(_bone['matrix_eular'][0])) \
                                * _bone['matrix_scale'][1] + _bone['matrix_translation'][2]
                                ) * i['weight']
                            
                        pos = [x, 0, y]
                        mesh_vertices.append(mathutils.Vector(pos))
                        
                    mesh_faces = list(zip(triangles[::3], triangles[1::3], triangles[2::3]))

                    uvs_list = [(_uvs[i:i+2]) for i in range(0, len(_uvs), 2)]

                    for e, data in enumerate(vertices_list):
                        _vt = []
                        for i in data:
                            _bone = BONE_MATRIX_DICT.get(_bone_list[i['bone_idx']])
                            _vt.append({"bone_idx" : i['bone_idx'], "weight" : i['weight']})
                        mesh_vertex_weight |= {e: _vt}
                        
            elif _type == 'clipping':
                vertices = attachment_data.get('vertices', [])
                vertexCount = attachment_data.get('vertexCount', [])

                if len(vertices) == vertexCount * 2:
                    for key, value in SLOTS_DICT.items():
                        if key == slot_name:
                            _bone = BONE_MATRIX_DICT.get(value.get('bone', ''))
                            break
                    if not _bone:
                        print('-'*10)
                        print(f'[ PASS ] skins -> attachments')
                        print(f'[ PASS ] 导入 {slot_name} 网格错误')
                        continue

                    vertices_list = [(vertices[i:i+2]) for i in range(0, len(vertices), 2)]
                        
                    for x, y in vertices_list:
                        x *= _scale
                        y *= _scale
                        weight = 1
                        pos = [
                                (x * math.cos(_bone['matrix_eular'][0]) - y * math.sin(_bone['matrix_eular'][0])) 
                                * _bone['matrix_scale'][1] + _bone['matrix_translation'][0] * weight, 

                                0,

                                (y * math.cos(_bone['matrix_eular'][0]) + x * math.sin(_bone['matrix_eular'][0])) 
                                * _bone['matrix_scale'][1] + _bone['matrix_translation'][2] * weight,
                        ]
                        mesh_vertices.append(mathutils.Vector(pos))

                    mesh_faces = [list(range(vertexCount))]

                    _uvs = []

                else:
                    _vertices = attachment_data.get('vertices', []).copy()
                    vertices_list = get_vertices_list(_vertices, scale=_scale, _list=[])
                    for data in vertices_list:
                        x = y = 0
                        for i in data:
                            _bone = BONE_MATRIX_DICT.get(_bone_list[i['bone_idx']])

                            x += (
                                (i['x'] * math.cos(_bone['matrix_eular'][0]) - i['y'] * math.sin(_bone['matrix_eular'][0])) \
                                * _bone['matrix_scale'][1] + _bone['matrix_translation'][0]
                                ) * i['weight']
                            
                            y += (
                                (i['y'] * math.cos(_bone['matrix_eular'][0]) + i['x'] * math.sin(_bone['matrix_eular'][0])) \
                                * _bone['matrix_scale'][1] + _bone['matrix_translation'][2]
                                ) * i['weight']
                            
                        pos = [x, 0, y]
                        mesh_vertices.append(mathutils.Vector(pos))
                        
                    mesh_faces = [list(range(vertexCount))]

                    _uvs = []

                    for e, data in enumerate(vertices_list):
                        _vt = []
                        for i in data:
                            _bone = BONE_MATRIX_DICT.get(_bone_list[i['bone_idx']])
                            _vt.append({"bone_idx" : i['bone_idx'], "weight" : i['weight']})
                        mesh_vertex_weight |= {e: _vt}

            if mesh_vertices and mesh_faces:
                mesh_name = f"{_character_name}_" + slot_name
                if bpy.data.objects.get(mesh_name):
                    mesh_name = f"{_character_name}_" + attachment_name

                # mesh
                mesh = bpy.data.meshes.new(mesh_name)
                mesh_obj = bpy.data.objects.new(mesh_name, mesh)
                mesh.from_pydata(mesh_vertices, [], mesh_faces)
                mesh.update()

                collection = bpy.data.collections.get(_character_name)
                if not collection:
                    collection = bpy.data.collections.new(_character_name)
                    bpy.context.scene.collection.children.link(collection)
                collection.objects.link(mesh_obj)

                modi = mesh_obj.modifiers.new('Armature', 'ARMATURE')
                modi.object = arm_obj
                mesh_obj.parent = arm_obj

                if mesh_vertex_weight:
                    {0: [{'bone_idx': 40, 'weight': 1}], 
                     1: [{'bone_idx': 40, 'weight': 0.01183}, {'bone_idx': 41, 'weight': 0.98817}], 
                     2: [{'bone_idx': 41, 'weight': 1}], 
                     3: [{'bone_idx': 41, 'weight': 1}], 
                     4: [{'bone_idx': 40, 'weight': 0.99934}, {'bone_idx': 41, 'weight': 0.00066}], 
                     5: [{'bone_idx': 40, 'weight': 1}], 6: [{'bone_idx': 40, 'weight': 1}]}
                    for idx, vlist in mesh_vertex_weight.items():
                        for i in vlist:
                            _bone = _bone_list[i['bone_idx']]
                            vg = mesh_obj.vertex_groups.get(_bone)
                            if not vg:
                                vg = mesh_obj.vertex_groups.new(name=_bone)
                            vg.add([idx], i['weight'], 'REPLACE')
                else:
                    _bone = SLOTS_DICT.get(slot_name).get('bone')
                    if _bone:
                        vg = mesh_obj.vertex_groups.new(name=_bone)
                        vg.add(list(range(len(vertices_list))), 1, 'REPLACE')
                        
                for e, i in enumerate(SLOTS_DICT):
                    if SLOTS_DICT[i].get('attachment') == attachment_name:
                        mesh_obj.location[1] = e * -0.0001
                        break

                if _image and Path(_image).exists():
                    if Path(spine_setting.spine_image_atlas).exists() and spine_setting.import_type == 'redive' and _type == 'region':
                        for i in Path(spine_setting.spine_image_atlas).iterdir():
                            if i.stem == attachment_name:
                                material = create_material(material_name=f"{_character_name}_{i.stem}", image_filepath=str(i))
                                mesh.materials.append(material)
                    else:
                        material = create_material(material_name=f"{_character_name}_{Path(_image).stem}", image_filepath=_image)
                        mesh.materials.append(material)
                
                if uvs_list:
                    if spine_setting.import_type == 'redive' and _type == 'region':
                        mesh_obj.select_set(True)
                        bpy.context.view_layer.objects.active = mesh_obj
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.select_all(action='DESELECT')

                        bpy.ops.object.mode_set(mode='EDIT')
                        
                        mesh_obj.data.uv_layers.new()
                        _mirror_uv(direction='y', mesh=mesh)
                    else:
                        _mesh_create_uv(ATLAS_DATA, uvs_list, attachment_name, mesh_obj)
   

                if attachment_name not in _attachment_view:
                    mesh_obj.hide_set(True)


def _get_bone_matrix_dict(arm_obj):
    _matrix_dict = {}
    for i in arm_obj.pose.bones:
        _dict = {
            "matrix_eular" : i.matrix.to_euler('XYZ').copy(),
            "matrix_scale" : i.matrix.to_scale().copy(),
            "matrix_translation" : i.matrix.to_translation().copy(),
            }
        _matrix_dict |= {i.name : _dict}
    return _matrix_dict
     
     
def from_slots_get_bone(SLOTS_DICT, slot_name):
    if SLOTS_DICT.get(slot_name) and SLOTS_DICT.get(slot_name).get('bone'):
        return SLOTS_DICT.get(slot_name).get('bone')


def create_material(material_name, image_filepath):
    material = bpy.data.materials.get(material_name)
    if material:
        return material
    
    material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    material.blend_method = 'BLEND'

    for i in material.node_tree.nodes:
        material.node_tree.nodes.remove(i)
            
    bsdf_node = material.node_tree.nodes.new('ShaderNodeBsdfTransparent')
    image_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    mix_node = material.node_tree.nodes.new('ShaderNodeMixShader')
    output_node = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    
    bsdf_node.location = 115, 390
    image_node.location = -155, 390
    mix_node.location = 115, 290
    output_node.location = 290, 290

    image_node.interpolation = 'Closest'
    
    if Path(image_filepath).exists():
        for i in bpy.data.images:
            if i.filepath == image_filepath:
                image_node.image = i
                break
        if not image_node.image:
            image_node.image = bpy.data.images.load(image_filepath)
            image_node.image.alpha_mode = 'PREMUL'
            
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
        
        x -= (uv_orig_x-uv_size_x) / atlas_size[0]
        y -= (uv_orig_y-uv_size_y) / atlas_size[1]

        if uv_rotate == 90:
            x, y = y, x
            x += (uv_point_x + uv_offset_x - offset_x) / atlas_size[0]
            y += 1 - ((uv_orig_x + uv_point_y - offset_y) / atlas_size[1])
        elif  uv_rotate == 270:
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

    if uv_rotate:
        if uv_rotate == 270:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

            mesh_obj.select_set(True)
            bpy.context.view_layer.objects.active = mesh_obj
            bpy.ops.object.mode_set(mode='EDIT')
    
            _rotation_uv(direction='reverse', mesh=mesh_obj.data, rotate=uv_rotate-90)
            bpy.ops.object.mode_set(mode='OBJECT')
        if uv_rotate == 180:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

            mesh_obj.select_set(True)
            bpy.context.view_layer.objects.active = mesh_obj
            bpy.ops.object.mode_set(mode='EDIT')
    
            _rotation_uv(direction='reverse', mesh=mesh_obj.data, rotate=uv_rotate)
            bpy.ops.object.mode_set(mode='OBJECT')


def _build_ik(JSON_DATA, spine_arm):
    spine_arm.select_set(True)
    bpy.context.view_layer.objects.active = spine_arm
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='POSE')
    
    bpy.ops.pose.armature_apply(selected=False)
    
    iks = JSON_DATA.get('ik')
    if not iks:
        bpy.ops.object.mode_set(mode='OBJECT')
        return
    
    for data in JSON_DATA.get('ik'):
        subtarget = data.get('target')
        bones = data.get('bones')
        bendPositive = data.get('bendPositive')
        mix = data.get('mix', 1)
        
        if not subtarget or not bones:
            continue

        cr_bone = spine_arm.pose.bones[bones[-1]]
        cr = cr_bone.constraints.new('IK')
        
        cr.name = 'SPINE_IK'
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
    bpy.ops.object.mode_set(mode='OBJECT')


def _rotation_uv(direction='reverse', mesh=None, rotate=90):
    if not mesh:
        return
    bpy.ops.object.mode_set(mode='EDIT')

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
            uv_B = face.loops[(i+1)%3][uv_layer].uv
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
    
    xcenter=(xmin+xmax)/2
    ycenter=(ymin+ymax)/2

    PIdiv = 3.14159265359 / (180 / rotate)
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
    bpy.ops.object.mode_set(mode='OBJECT')
    

def _mirror_uv(direction='x', mesh=None):
    if not mesh:
        return
    
    bpy.ops.object.mode_set(mode='EDIT')

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
            xmin = .1
        if (ymax - ymin) == 0:
            ymin = .1

    for face in faces:
            for loop in face.loops:
                loop[uv_layer].uv.x -= xmin
                loop[uv_layer].uv.y -= ymin
                loop[uv_layer].uv.x /= (xmax-xmin)
                loop[uv_layer].uv.y /= (ymax-ymin)
                
                if direction == "x":
                    loop[uv_layer].uv.x = -loop[uv_layer].uv.x + 1.0
                if direction == "y":
                    loop[uv_layer].uv.y = -loop[uv_layer].uv.y + 1.0

                loop[uv_layer].uv.x *= xmax-xmin
                loop[uv_layer].uv.y *= ymax-ymin
                loop[uv_layer].uv.x += xmin
                loop[uv_layer].uv.y += ymin                    

    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    bpy.ops.object.mode_set(mode='OBJECT')

# ----------- 
# load
# -----------

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
    atlas_text = [i.replace('\n','') for i in atlas_text if i.replace('\n','')]
    
    atlas_data = {}

    _dict = {}
    _prop = {}
    for e, text in enumerate(atlas_text):
        if text.strip() == text:
            if ':' in text:
                k, v = text.split(':', 1)
                _dict = {k.strip() : v.strip()}
                atlas_data |= _dict
            elif _prop:
                atlas_data |= {list(_dict)[0] : _prop}
                _dict = {text : {}}
            else:
                _dict = {text : {}}
            _prop = {}
        else:
            key, value = text.strip().split(':', 1)
            if key.strip() == 'rotate':
                if value.strip() == 'true':
                    value = '90'
                elif value.strip() == 'false':
                    value = '0'
            _prop |= {key.strip() : value.strip()}
        if e == len(atlas_text) - 1:
            atlas_data |= {list(_dict)[0] : _prop}
    return atlas_data


def load_bones(JSON_DATA):
    _load = {}
    for data in JSON_DATA.get('bones'):
        _dict = {
            "x" : data.get('x', 0),
            "y" : data.get('y', 0),
            "length" : data.get('length', 10),
            "rotation" : data.get('rotation', 0),
            "scaleX" : data.get('scaleX', 1),
            "scaleY" : data.get('scaleY', 1),
            "transform" : data.get('transform', None),
            "parent" : data.get('parent', None),
        }
        _load |= {data.get('name') : _dict}
    return _load


def load_slots(JSON_DATA):
    _load = {}
    for data in JSON_DATA.get('slots'):
        _dict = {
            "bone" : data.get('bone', ''),
            "attachment" : data.get('attachment'),
        }
        _load |= {data.get('name') : _dict}
    return _load


def load_attachments(JSON_DATA, skin_name='default'):
    for data in JSON_DATA.get('skins'):
        if data.get('name') == skin_name:
            return data.get('attachments')


def get_vertices_list(_vertices, scale=1, _list=[]):
    _data = []
    for _ in range(_vertices.pop(0)):
        _data.append(
            {
                'bone_idx' : _vertices.pop(0),
                'x' : _vertices.pop(0) * scale,
                'y' : _vertices.pop(0) * scale,
                'weight' : _vertices.pop(0),
            }
        )
    _list.append(_data)
    if len(_vertices) >= 5:
        return get_vertices_list(_vertices, scale=scale, _list=_list)
    return _list


class OT_select_json_file(Operator, ImportHelper):
    bl_idname = "rhs.select_json_file"
    bl_label = "Select Json File"
    
    filter_glob: bpy.props.StringProperty(default="*.json")
    
    filename_ext = ".json"
    
    filepath: bpy.props.StringProperty(
        name="文件路径",
        description="选择Spine文件",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        spine_setting = bpy.context.scene.RHS_SPINE
        spine_setting.spine_json = self.filepath
        return {'FINISHED'}
    

class OT_select_atlas_file(Operator, ImportHelper):
    bl_idname = "rhs.select_atlas_file"
    bl_label = "Select Atlas File"
    
    filter_glob: bpy.props.StringProperty(default="*.atlas")
    
    filename_ext = ".atlas"
    
    filepath: bpy.props.StringProperty(
        name="文件路径",
        description="选择Spine文件",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        spine_setting = bpy.context.scene.RHS_SPINE
        spine_setting.spine_atlas = self.filepath
        return {'FINISHED'}


class OT_select_png_file(Operator, ImportHelper):
    bl_idname = "rhs.select_png_file"
    bl_label = "Select Png File"
    
    filter_glob: bpy.props.StringProperty(default="*.png")
    
    filename_ext = ".png"
    
    filepath: bpy.props.StringProperty(
        name="文件路径",
        description="选择Spine文件",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        spine_setting = bpy.context.scene.RHS_SPINE
        spine_setting.spine_image = self.filepath
        return {'FINISHED'}
    
# ----------- 
# REGISTER
# ----------- 

classes = [
    Scene_Spine,
    Spine_Loader,

    Select_Object_Select,
    Select_Object_Hide,

    SPINE_PT_VIEW3D_DRAW,

    OT_select_json_file,
    OT_select_atlas_file,
    OT_select_png_file,
]


def register():
    for i in classes:
        bpy.utils.register_class(i)
    bpy.types.Scene.RHS_SPINE = bpy.props.PointerProperty(type=Scene_Spine)
        

def unregister():
    del bpy.types.Scene.RHS_SPINE 
    for i in classes:
        bpy.utils.unregister_class(i)
