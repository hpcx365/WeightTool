"""Weight Tool Blender extension."""

from .operators import OPERATOR_CLASSES
from .translations import TRANSLATIONS
from .ui import UI_CLASSES


CLASSES = (*OPERATOR_CLASSES, *UI_CLASSES)


def register():
    import bpy

    bpy.app.translations.register(__name__, TRANSLATIONS)
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    bpy.app.translations.unregister(__name__)
