import bpy
from bpy.props import *
from bpy.types import PropertyGroup

# -----------
# Import
# -----------

from .api import *

# -----------
# Define
# -----------


class Scene_Spine(Camp_Scene):
    @classmethod
    def register(cls):
        Camp_Scene.spine = PointerProperty(type=cls)

        def get_atlas_folder_name(self):
            sp = self.atlas_folder.split("\\")
            if len(sp) > 1:
                return sp[-2]
            return ""

        if bpy.context.preferences.view.language == "zh_HANS":
            cls.menu_types = EnumProperty(
                default="import",
                items=[
                    ("import", "导入", "", "TAG", 0),
                    ("slots", "插槽", "", "PROP_ON", 1),
                ],
            )

            cls.json_path = StringProperty(name="", description="Spine导入所需的json文件路径", update=_get_abs_path("json_path"))
            cls.atlas_path = StringProperty(name="", description="Spine导入所需的atlas文件路径", update=_get_abs_path("atlas_path"))
            cls.image_path = StringProperty(name="", description="Spine导入所需的image文件路径", update=_get_abs_path("image_path"))
            cls.atlas_folder = StringProperty(name="", description="Spine导入所需的图集文件夹路径", subtype="DIR_PATH", update=_get_abs_path("atlas_folder"))

            cls.json_file_name = StringProperty(name="", get=lambda self: getattr(self, "json_path", "").split("\\")[-1])
            cls.atlas_file_name = StringProperty(name="", get=lambda self: getattr(self, "atlas_path", "").split("\\")[-1])
            cls.image_file_name = StringProperty(name="", get=lambda self: getattr(self, "image_path", "").split("\\")[-1])
            cls.atlas_folder_name = StringProperty(name="", get=get_atlas_folder_name)

            cls.show_file_name = BoolProperty(default=False, description="裁剪路径, 显示文件名")
            cls.import_scale = FloatProperty(default=0.01, min=0.01, max=1)
            cls.import_ik = BoolProperty(default=True)
            cls.import_skin_name = StringProperty(default="default")
            cls.import_version = EnumProperty(
                default="4.2",
                items=[
                    ("4.2", "3.8 / 4.2", ""),
                ],
            )
            cls.import_type = EnumProperty(
                default="arknights",
                items=[
                    (
                        "arknights",
                        "Arknights",
                        "",
                    ),
                    (
                        "redive",
                        "Re:Dive",
                        "",
                    ),
                ],
            )

            cls.armature = StringProperty(search=lambda self, context, edit_text: [i.name for i in bpy.context.scene.objects if i.type == "ARMATURE"])
            cls.character_name = StringProperty(default="character")
            cls.y_sort_scale = IntProperty(default=1, min=1, max=20)
            cls.show_import_slots_menu = BoolProperty(default=False)
        else:
            cls.menu_types = EnumProperty(
                default="import",
                items=[
                    ("import", "Import", "", "TAG", 0),
                    ("slots", "Slots", "", "PROP_ON", 1),
                ],
            )

            cls.json_path = StringProperty(name="", description="Select *.json File", update=_get_abs_path("json_path"))
            cls.atlas_path = StringProperty(name="", description="Select *.atlas File", update=_get_abs_path("atlas_path"))
            cls.image_path = StringProperty(name="", description="Select *.png File", update=_get_abs_path("image_path"))
            cls.atlas_folder = StringProperty(name="", description="Select Atlas Folder", subtype="DIR_PATH", update=_get_abs_path("atlas_folder"))

            cls.json_file_name = StringProperty(name="", get=lambda self: getattr(self, "json_path", "").split("\\")[-1])
            cls.atlas_file_name = StringProperty(name="", get=lambda self: getattr(self, "atlas_path", "").split("\\")[-1])
            cls.image_file_name = StringProperty(name="", get=lambda self: getattr(self, "image_path", "").split("\\")[-1])
            cls.atlas_folder_name = StringProperty(name="", get=get_atlas_folder_name)

            cls.show_file_name = BoolProperty(default=False, description="Crop the path, display the file name.")
            cls.import_scale = FloatProperty(default=0.01, min=0.01, max=1)
            cls.import_ik = BoolProperty(default=True)
            cls.import_skin_name = StringProperty(default="default")
            cls.import_version = EnumProperty(
                default="4.2",
                items=[
                    ("4.2", "3.8 / 4.2", ""),
                ],
            )
            cls.import_type = EnumProperty(
                default="arknights",
                items=[
                    (
                        "arknights",
                        "Arknights",
                        "",
                    ),
                    (
                        "redive",
                        "Re:Dive",
                        "",
                    ),
                ],
            )

            cls.armature = StringProperty(search=lambda self, context, edit_text: [i.name for i in bpy.context.scene.objects if i.type == "ARMATURE"])
            cls.character_name = StringProperty(default="character")
            cls.y_sort_scale = IntProperty(default=1, min=1, max=20)
            cls.show_import_slots_menu = BoolProperty(default=False)


class Attachments(PropertyGroup):
    @classmethod
    def register(cls):
        cls.name = StringProperty()


class Slots(PropertyGroup):
    @classmethod
    def register(cls):
        cls.name = StringProperty()
        cls.bone_name = StringProperty()
        cls.attachment = CollectionProperty(type=Attachments)


class Spine_Slots(Scene_Spine):
    def __getattribute__(self, attr):
        if attr == "active" and self.slot:
            if self.index >= len(self.slot):
                self.index = 0
            return self.slot[self.index]
        return super().__getattribute__(attr)

    @classmethod
    def register(cls):
        Scene_Spine.slots = PointerProperty(type=cls)

        cls.slot = CollectionProperty(type=Slots)
        cls.index = IntProperty()
        cls.active = None


def _get_abs_path(prop=""):
    def wrap(self, context):
        self[prop] = bpy.path.abspath(self[prop])

    return wrap


# -----------
# REGISTER
# -----------

classes = [
    Scene_Spine,
    Attachments,
    Slots,
    Spine_Slots,
]


def register():
    pass


def unregister():
    pass
