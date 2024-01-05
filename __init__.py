bl_info = { 
"author":"Nick Fisher <nick.fisher@avinium.com>",
"name":"AI Animator",
"blender":(3,1,0),
"category":"3D View",
"location": "View3D > Sidebar > LiveLinkFace"
}

import bpy

from ai_animator.operators import AIAnimatorTTSTab,AIAnimatorBlendshapeTab,GenerateOperator, CUSTOM_OT_actions, CUSTOM_OT_addViewportSelection, CUSTOM_OT_printItems, CUSTOM_OT_clearList, CUSTOM_OT_removeDuplicates, CUSTOM_OT_selectItems, CUSTOM_OT_deleteObject, CUSTOM_UL_items

class ObjectSlot(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(name="Object",type=bpy.types.Object)

classes = (
    AIAnimatorBlendshapeTab,
    AIAnimatorTTSTab,
    GenerateBlendshapesOperator,
    SynthesizeSpeechOperator,
    ObjectSlot,
    CUSTOM_OT_actions,
    CUSTOM_OT_addViewportSelection,
    CUSTOM_OT_printItems,
    CUSTOM_OT_clearList,
    CUSTOM_OT_removeDuplicates,
    CUSTOM_OT_selectItems,
    CUSTOM_OT_deleteObject,
    CUSTOM_UL_items,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.ai_animator_targets = bpy.props.CollectionProperty(
        type = ObjectSlot,
        name = "Target object(s) containing blendshapes that will be animated according to audio",
    )
    bpy.types.Scene.ai_animator_targets_index = bpy.props.IntProperty()
    bpy.types.Scene.ai_animator_selected_audio = bpy.props.StringProperty()
    bpy.types.Scene.ai_animator_tts_text = bpy.props.StringProperty()

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.ai_animator_targets
    del bpy.types.Scene.ai_animator_targets_index
        
if __name__ == "main":
    register()        
