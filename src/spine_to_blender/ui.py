import bpy
from bpy.props import *
from bpy.types import Panel, UIList

# -----------
# Import
# -----------

from .api import *

# -----------
# Define
# -----------


class CAMP_PT_SPINE_PANEL(Panel):
    bl_label = "Spine To Blender"
    bl_idname = "CAMP_PT_SPINE"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Spine"

    def draw_header_preset(self, context):
        pass

    def draw(self, context):
        common_draw(self, context)


class CAMP_UL_SPINE_SLOTS(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        active = bool(data.index == index)

        row = layout.row(align=True)
        row.label(text="", icon="PROP_CON" if active else "RADIOBUT_OFF")
        row.prop(item, "name", text="", emboss=False)


def common_draw(self, context):
    spine_setting = get_context_scene_cmd().spine
    if bpy.context.preferences.view.language == "zh_HANS" and bpy.context.preferences.view.use_translate_interface == True:
        match spine_setting.menu_types:
            case "import":
                _import_draw(self, context)
            case "slots":
                _slots_draw(self, context)
    else:
        match spine_setting.menu_types:
            case "import":
                _import_draw_en_us(self, context)
            case "slots":
                _slots_draw_en_us(self, context)


def _import_draw(self, context):
    layout = self.layout

    spine_setting = get_context_scene_cmd().spine

    col = layout.column(align=True)
    row = col.row()
    row.scale_x = 1.2
    row.scale_y = 1.2
    row.prop(spine_setting, "menu_types", expand=True)

    if spine_setting.show_file_name:
        box = col.box()
        box.scale_x = 1.2
        box.scale_y = 1.2

        bc = box.column()
        br = bc.row()
        br.label(text="文件名", icon="FILE_HIDDEN")
        br.prop(spine_setting, "show_file_name", text="", icon="CON_TRANSFORM_CACHE")

        br = bc.row()
        br.label(icon="BLANK1")
        sp = br.split()
        spc = sp.column(align=True)

        cr = spc.row(align=True)
        cr.prop(spine_setting, "json_file_name", text="", icon="EVENT_J")
        cr.operator("camp.spine_select_json_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        cr.prop(spine_setting, "atlas_file_name", text="", icon="EVENT_A")
        cr.operator("camp.spine_select_atlas_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        cr.prop(spine_setting, "image_file_name", text="", icon="EVENT_P")
        cr.operator("camp.spine_select_image_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        _type = True if spine_setting.import_type == "redive" else False
        cr.active = _type
        cr.prop(spine_setting, "atlas_folder_name", text="", icon="RENDERLAYERS" if _type else "X")
    else:
        box = col.box()
        box.scale_x = 1.2
        box.scale_y = 1.2

        bc = box.column()
        br = bc.row()
        br.label(text="文件路径", icon="FILE")
        br.prop(spine_setting, "show_file_name", text="", icon="CON_TRANSFORM_CACHE")

        br = bc.row()
        br.label(icon="BLANK1")
        sp = br.split()
        spc = sp.column(align=True)

        cr = spc.row(align=True)
        cr.prop(spine_setting, "json_path", text="", icon="EVENT_J")
        cr.operator("camp.spine_select_json_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        cr.prop(spine_setting, "atlas_path", text="", icon="EVENT_A")
        cr.operator("camp.spine_select_atlas_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        cr.prop(spine_setting, "image_path", text="", icon="EVENT_P")
        cr.operator("camp.spine_select_image_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        _type = True if spine_setting.import_type == "redive" else False
        cr.active = _type
        cr.prop(spine_setting, "atlas_folder", text="", icon="RENDERLAYERS" if _type else "X")

    box = col.box()
    box.scale_x = 1.2
    box.scale_y = 1.2
    bc = box.column()
    br = bc.row()
    br.label(text="导入配置", icon="SETTINGS")

    bc = box.column()
    bc.use_property_split = True
    bc.use_property_decorate = False

    bc.prop(spine_setting, "import_ik", text="IK", icon="CON_KINEMATIC")
    bc.prop(spine_setting, "import_scale", text="缩放", slider=True)
    bc.prop(spine_setting, "import_skin_name", text="皮肤", icon="MATCLOTH")

    box = col.box()
    box.scale_x = 1.2
    box.scale_y = 1.2
    bc = box.column()
    bc.use_property_split = True
    bc.use_property_decorate = False
    bc.prop(spine_setting, "character_name", text="角色名", icon="CON_ACTION")
    bc.prop(spine_setting, "import_version", text="版本")
    bc.prop(spine_setting, "import_type", text="类型")
    bc.prop(spine_setting, "y_sort_scale", text="Y排序缩放", slider=True)
    br = box.row()
    br.scale_x = 1.5
    br.scale_y = 1.5
    br.operator("camp.import_spine_slots_data", text="", icon="PROP_ON")
    br.operator("camp.import_spine", text="导入Spine", icon="MATCLOTH")


def _slots_draw(self, context):
    layout = self.layout

    spine_setting = get_context_scene_cmd().spine

    col = layout.column(align=True)
    row = col.row()
    row.scale_x = 1.2
    row.scale_y = 1.2
    row.prop(spine_setting, "menu_types", expand=True)

    box = col.box()
    box.scale_x = 1.2
    box.scale_y = 1.2

    bc = box.column()
    br = bc.row()
    br.label(text="插槽列表", icon="FILE_VOLUME")
    br.prop(spine_setting, "show_import_slots_menu", text="", icon="MATCLOTH")

    br = bc.row()
    br.template_list("CAMP_UL_SPINE_SLOTS", "", spine_setting.slots, "slot", spine_setting.slots, "index", rows=5)

    if spine_setting.show_import_slots_menu:
        box = col.box()
        row = box.row()
        row.scale_y = 1.5
        row.label(icon="TRIA_RIGHT")
        row.operator("camp.import_spine_slots_data", text="更新插槽数据")
        row.label(icon="TRIA_LEFT")

        if spine_setting.show_file_name:
            box = col.box()
            box.scale_x = 1.2
            box.scale_y = 1.2

            bc = box.column()
            br = bc.row()
            br.label(text="文件名", icon="FILE_HIDDEN")
            br.prop(spine_setting, "show_file_name", text="", icon="CON_TRANSFORM_CACHE")

            br = bc.row()
            br.label(icon="BLANK1")
            sp = br.split()
            spc = sp.column(align=True)

            cr = spc.row(align=True)
            cr.prop(spine_setting, "json_file_name", text="", icon="EVENT_J")
            cr.operator("camp.spine_select_json_file", text="", icon="FILEBROWSER")

        else:
            box = col.box()
            box.scale_x = 1.2
            box.scale_y = 1.2

            bc = box.column()
            br = bc.row()
            br.label(text="文件路径", icon="FILE")
            br.prop(spine_setting, "show_file_name", text="", icon="CON_TRANSFORM_CACHE")

            br = bc.row()
            br.label(icon="BLANK1")
            sp = br.split()
            spc = sp.column(align=True)

            cr = spc.row(align=True)
            cr.prop(spine_setting, "json_path", text="", icon="EVENT_J")
            cr.operator("camp.spine_select_json_file", text="", icon="FILEBROWSER")

        box = col.box()
        box.scale_x = 1.2
        box.scale_y = 1.2
        bc = box.column()
        br = bc.row()
        br.label(text="导入配置", icon="SETTINGS")
        br = bc.row()
        bc = br.column()
        bc.use_property_split = True
        bc.use_property_decorate = False
        bc.prop(spine_setting, "import_skin_name", text="皮肤", icon="MATCLOTH")
        bc.prop(spine_setting, "character_name", text="角色名", icon="CON_ACTION")

    box = col.box()
    box.active = not spine_setting.show_import_slots_menu
    box.scale_x = 1.2
    box.scale_y = 1.2
    bc = box.column()
    br = bc.row(align=True)
    br.label(text="目标骨架", icon="MOD_LINEART")

    br = bc.row(align=True)
    br.label(icon="BLANK1")
    br.prop(spine_setting, "armature", text="", icon="OUTLINER_OB_ARMATURE")

    br = bc.row(align=True)
    br.label(icon="BLANK1")
    br.prop(spine_setting, "character_name", text="", icon="CON_ACTION")

    arm = bpy.data.objects.get(spine_setting.armature)

    if arm and spine_setting.character_name:
        active_slot = spine_setting.slots.active
        if active_slot:
            bone_name = active_slot.bone_name
            bone = arm.data.bones.get(bone_name)
            if bone:
                ops_icon = "PMARKER"
                if bpy.context.object == arm and bpy.context.mode == "POSE":
                    if arm.pose.bones[bone_name].select:
                        ops_icon = "PMARKER_SEL"

                br = bc.row(align=True)
                br.label(text="骨骼", icon="BONE_DATA")
                br = bc.row(align=True)
                br.label(icon="BLANK1")

                op = br.operator(
                    "camp.spine_select_pose_bone",
                    icon=ops_icon,
                    emboss=False,
                )
                op.obj_name = arm.name
                op.bone_name = bone_name

                bone = arm.data.bones[bone_name]
                pb = arm.pose.bones[bone_name]

                br.label(text=bone_name)
                br.prop(
                    bone,
                    "hide_select",
                    text="",
                    icon="RESTRICT_SELECT_ON" if bone.hide_select else "RESTRICT_SELECT_OFF",
                    emboss=False,
                )
                br.prop(pb, "hide", text="", emboss=False)
                character_name = spine_setting.character_name

                invalid_mesh = []

                br = bc.row()
                br.label(text="网格", icon="OUTLINER_OB_MESH")
                for i in active_slot.attachment:

                    mesh_name = f"{character_name}-{active_slot.name}-{i.name}"
                    mesh = bpy.data.objects.get(mesh_name)
                    if not mesh:
                        invalid_mesh.append(mesh_name)
                        continue

                    ops_icon = "RESTRICT_SELECT_ON"
                    if bpy.context.object == mesh:
                        ops_icon = "RESTRICT_SELECT_OFF"

                    br = bc.row(align=True)
                    br.label(icon="BLANK1")

                    op = br.operator(
                        "camp.spine_select_object",
                        icon=ops_icon,
                        emboss=False,
                    )
                    op.obj_name = mesh_name
                    br.label(text=i.name)
                    br.prop(mesh, "location", index=1, text="")

                    br.operator("camp.spine_change_object_visible", text="", icon="HIDE_ON" if mesh.hide_get() else "HIDE_OFF").obj_name = mesh.name
                    br.prop(mesh, "hide_viewport", text="", toggle=True)

                if len(invalid_mesh) > 0:
                    box = col.box()
                    br = box.row()
                    br.alert = True
                    br.label(text=f"找不到以下网格", icon="CANCEL")
                    for mesh_name in invalid_mesh:
                        br = box.row()
                        br.label(text="", icon="BLANK1")
                        br.alert = True
                        br.label(text=f"{mesh_name}", icon="OUTLINER_OB_MESH")

            else:
                box = col.box()
                box.scale_y = 3
                br = box.row()
                br.alignment = "CENTER"
                br.alert = True
                br.label(text="目标骨架未找到骨骼")
    else:
        box = col.box()
        box.scale_y = 3
        br = box.row()
        br.alignment = "CENTER"
        br.alert = True
        br.label(text="目标骨架不可用")


def _import_draw_en_us(self, context):
    layout = self.layout

    spine_setting = get_context_scene_cmd().spine

    col = layout.column(align=True)
    row = col.row()
    row.scale_x = 1.2
    row.scale_y = 1.2
    row.prop(spine_setting, "menu_types", expand=True)

    if spine_setting.show_file_name:
        box = col.box()
        box.scale_x = 1.2
        box.scale_y = 1.2

        bc = box.column()
        br = bc.row()
        br.label(text="File Name", icon="FILE_HIDDEN")
        br.prop(spine_setting, "show_file_name", text="", icon="CON_TRANSFORM_CACHE")

        br = bc.row()
        br.label(icon="BLANK1")
        sp = br.split()
        spc = sp.column(align=True)

        cr = spc.row(align=True)
        cr.prop(spine_setting, "json_file_name", text="", icon="EVENT_J")
        cr.operator("camp.spine_select_json_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        cr.prop(spine_setting, "atlas_file_name", text="", icon="EVENT_A")
        cr.operator("camp.spine_select_atlas_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        cr.prop(spine_setting, "image_file_name", text="", icon="EVENT_P")
        cr.operator("camp.spine_select_image_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        _type = True if spine_setting.import_type == "redive" else False
        cr.active = _type
        cr.prop(spine_setting, "atlas_folder_name", text="", icon="RENDERLAYERS" if _type else "X")
    else:
        box = col.box()
        box.scale_x = 1.2
        box.scale_y = 1.2

        bc = box.column()
        br = bc.row()
        br.label(text="File Path", icon="FILE")
        br.prop(spine_setting, "show_file_name", text="", icon="CON_TRANSFORM_CACHE")

        br = bc.row()
        br.label(icon="BLANK1")
        sp = br.split()
        spc = sp.column(align=True)

        cr = spc.row(align=True)
        cr.prop(spine_setting, "json_path", text="", icon="EVENT_J")
        cr.operator("camp.spine_select_json_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        cr.prop(spine_setting, "atlas_path", text="", icon="EVENT_A")
        cr.operator("camp.spine_select_atlas_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        cr.prop(spine_setting, "image_path", text="", icon="EVENT_P")
        cr.operator("camp.spine_select_image_file", text="", icon="FILEBROWSER")

        cr = spc.row(align=True)
        _type = True if spine_setting.import_type == "redive" else False
        cr.active = _type
        cr.prop(spine_setting, "atlas_folder", text="", icon="RENDERLAYERS" if _type else "X")

    box = col.box()
    box.scale_x = 1.2
    box.scale_y = 1.2
    bc = box.column()
    br = bc.row()
    br.label(text="Import Config", icon="SETTINGS")

    bc = box.column()
    bc.use_property_split = True
    bc.use_property_decorate = False

    bc.prop(spine_setting, "import_ik", text="IK", icon="CON_KINEMATIC")
    bc.prop(spine_setting, "import_scale", text="Scale", slider=True)
    bc.prop(spine_setting, "import_skin_name", text="Skin", icon="MATCLOTH")

    box = col.box()
    box.scale_x = 1.2
    box.scale_y = 1.2
    bc = box.column()
    bc.use_property_split = True
    bc.use_property_decorate = False
    bc.prop(spine_setting, "character_name", text="Name", icon="CON_ACTION")
    bc.prop(spine_setting, "import_version", text="Version")
    bc.prop(spine_setting, "import_type", text="Type")
    bc.prop(spine_setting, "y_sort_scale", text="Y-Sort-Scale", slider=True)
    br = box.row()
    br.scale_x = 1.5
    br.scale_y = 1.5
    br.operator("camp.import_spine_slots_data", text="", icon="PROP_ON")
    br.operator("camp.import_spine", text="Import Spine", icon="MATCLOTH")


def _slots_draw_en_us(self, context):
    layout = self.layout

    spine_setting = get_context_scene_cmd().spine

    col = layout.column(align=True)
    row = col.row()
    row.scale_x = 1.2
    row.scale_y = 1.2
    row.prop(spine_setting, "menu_types", expand=True)

    box = col.box()
    box.scale_x = 1.2
    box.scale_y = 1.2

    bc = box.column()
    br = bc.row()
    br.label(text="Slots List", icon="FILE_VOLUME")
    br.prop(spine_setting, "show_import_slots_menu", text="", icon="MATCLOTH")

    br = bc.row()
    br.template_list("CAMP_UL_SPINE_SLOTS", "", spine_setting.slots, "slot", spine_setting.slots, "index", rows=5)

    if spine_setting.show_import_slots_menu:
        box = col.box()
        row = box.row()
        row.scale_y = 1.5
        row.label(icon="TRIA_RIGHT")
        row.operator("camp.import_spine_slots_data", text="Update Slots Data")
        row.label(icon="TRIA_LEFT")

        if spine_setting.show_file_name:
            box = col.box()
            box.scale_x = 1.2
            box.scale_y = 1.2

            bc = box.column()
            br = bc.row()
            br.label(text="File Name", icon="FILE_HIDDEN")
            br.prop(spine_setting, "show_file_name", text="", icon="CON_TRANSFORM_CACHE")

            br = bc.row()
            br.label(icon="BLANK1")
            sp = br.split()
            spc = sp.column(align=True)

            cr = spc.row(align=True)
            cr.prop(spine_setting, "json_file_name", text="", icon="EVENT_J")
            cr.operator("camp.spine_select_json_file", text="", icon="FILEBROWSER")

        else:
            box = col.box()
            box.scale_x = 1.2
            box.scale_y = 1.2

            bc = box.column()
            br = bc.row()
            br.label(text="File Path", icon="FILE")
            br.prop(spine_setting, "show_file_name", text="", icon="CON_TRANSFORM_CACHE")

            br = bc.row()
            br.label(icon="BLANK1")
            sp = br.split()
            spc = sp.column(align=True)

            cr = spc.row(align=True)
            cr.prop(spine_setting, "json_path", text="", icon="EVENT_J")
            cr.operator("camp.spine_select_json_file", text="", icon="FILEBROWSER")

        box = col.box()
        box.scale_x = 1.2
        box.scale_y = 1.2
        bc = box.column()
        br = bc.row()
        br.label(text="Import Config", icon="SETTINGS")
        br = bc.row()
        bc = br.column()
        bc.use_property_split = True
        bc.use_property_decorate = False
        bc.prop(spine_setting, "import_skin_name", text="Skin", icon="MATCLOTH")
        bc.prop(spine_setting, "character_name", text="Name", icon="CON_ACTION")

    box = col.box()
    box.active = not spine_setting.show_import_slots_menu
    box.scale_x = 1.2
    box.scale_y = 1.2
    bc = box.column()
    br = bc.row(align=True)
    br.label(text="Target Armature", icon="MOD_LINEART")

    br = bc.row(align=True)
    br.label(icon="BLANK1")
    br.prop(spine_setting, "armature", text="", icon="OUTLINER_OB_ARMATURE")

    br = bc.row(align=True)
    br.label(icon="BLANK1")
    br.prop(spine_setting, "character_name", text="", icon="CON_ACTION")

    arm = bpy.data.objects.get(spine_setting.armature)

    if arm and spine_setting.character_name:
        active_slot = spine_setting.slots.active
        if active_slot:
            bone_name = active_slot.bone_name
            bone = arm.data.bones.get(bone_name)
            if bone:
                ops_icon = "PMARKER"
                if bpy.context.object == arm and bpy.context.mode == "POSE":
                    if arm.pose.bones[bone_name].select:
                        ops_icon = "PMARKER_SEL"

                br = bc.row(align=True)
                br.label(text="Bone", icon="BONE_DATA")
                br = bc.row(align=True)
                br.label(icon="BLANK1")

                op = br.operator(
                    "camp.spine_select_pose_bone",
                    icon=ops_icon,
                    emboss=False,
                )
                op.obj_name = arm.name
                op.bone_name = bone_name

                bone = arm.data.bones[bone_name]
                pb = arm.pose.bones[bone_name]

                br.label(text=bone_name)
                br.prop(
                    bone,
                    "hide_select",
                    text="",
                    icon="RESTRICT_SELECT_ON" if bone.hide_select else "RESTRICT_SELECT_OFF",
                    emboss=False,
                )
                br.prop(pb, "hide", text="", emboss=False)
                character_name = spine_setting.character_name

                invalid_mesh = []

                br = bc.row()
                br.label(text="Mesh", icon="OUTLINER_OB_MESH")
                for i in active_slot.attachment:

                    mesh_name = f"{character_name}-{active_slot.name}-{i.name}"
                    mesh = bpy.data.objects.get(mesh_name)
                    if not mesh:
                        invalid_mesh.append(mesh_name)
                        continue

                    ops_icon = "RESTRICT_SELECT_ON"
                    if bpy.context.object == mesh:
                        ops_icon = "RESTRICT_SELECT_OFF"

                    br = bc.row(align=True)
                    br.label(icon="BLANK1")

                    op = br.operator(
                        "camp.spine_select_object",
                        icon=ops_icon,
                        emboss=False,
                    )
                    op.obj_name = mesh_name
                    br.label(text=i.name)
                    br.prop(mesh, "location", index=1, text="")

                    br.operator("camp.spine_change_object_visible", text="", icon="HIDE_ON" if mesh.hide_get() else "HIDE_OFF").obj_name = mesh.name
                    br.prop(mesh, "hide_viewport", text="", toggle=True)

                if len(invalid_mesh) > 0:
                    box = col.box()
                    br = box.row()
                    br.alert = True
                    br.label(text="The following mesh could not be found.", icon="CANCEL")
                    for mesh_name in invalid_mesh:
                        br = box.row()
                        br.label(text="", icon="BLANK1")
                        br.alert = True
                        br.label(text=f"{mesh_name}", icon="OUTLINER_OB_MESH")

            else:
                box = col.box()
                box.scale_y = 3
                br = box.row()
                br.alignment = "CENTER"
                br.alert = True
                br.label(text="The target skeleton does not contain the specified bone.")
    else:
        box = col.box()
        box.scale_y = 3
        br = box.row()
        br.alignment = "CENTER"
        br.alert = True
        br.label(text="The target skeleton is unavailable.")


# -----------
# REGISTER
# -----------

classes = [
    CAMP_PT_SPINE_PANEL,
    CAMP_UL_SPINE_SLOTS,
]


def register():
    pass


def unregister():
    pass
