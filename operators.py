import bpy
from bpy_extras.io_utils import ImportHelper

from ai_animator.client import Client
from ai_animator.action import create_action_with_blendshapes

from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       PointerProperty)

from bpy.types import (Operator,
                       Panel,
                       PropertyGroup,
                       UIList)

class GenerateBlendshapesOperator(bpy.types.Operator):
    bl_idname = "scene.ai_animator_generate_blendshapes_operator"
    bl_label = "ai_animator_generate_blendshapes_button"
    
    def checkPrereqs(self, context):
        if len(context.scene.ai_animator_targets) == 0:
            self.report({"ERROR"}, "No target object selected")
        elif bpy.context.scene.sequence_editor.active_strip is None:
            self.report({"ERROR"}, "No audio is selected in the Sequencer")
        else:
            return True
        return False

    def execute(self, context):
        if self.checkPrereqs(context):
            try:
                client = Client()
                frame_data = client.request(bpy.context.scene.sequence_editor.active_strip.sound.filepath)
                #frame_data = [[float(i)/60.0 for i in range(51)] for _ in range(60)]
                create_action_with_blendshapes([t.obj for t in context.scene.ai_animator_targets], frame_data)
                # do something 
                return {'FINISHED'}
            except Exception as e:
                self.report({"ERROR"}, e)
                return {"CANCELLED"}
        else:
            print("Prereq check failed")
            return {"CANCELLED"}

class SynthesizeSpeechOperator(bpy.types.Operator):
    bl_idname = "scene.ai_animator_synthesize_speech_operator"
    bl_label = "ai_animator_synthesize_speech_button"

    def execute(self, context):
        if len(context.scene.ai_animator_tts_text) == 0:
            self.report({"ERROR"}, "No text specified")
            return {"CANCELLED"}
        else:
            # do something
            return {'FINISHED'}
        

class CUSTOM_OT_actions(Operator):
    """Move items up and down, add and remove"""
    bl_idname = "custom.list_action"
    bl_label = "List Actions"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}
    
    action: bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", "")))

    def invoke(self, context, event):
        scn = context.scene
        idx = scn.ai_animator_targets_index

        try:
            item = scn.ai_animator_targets[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(scn.ai_animator_targets) - 1:
                item_next = scn.ai_animator_targets[idx+1].name
                scn.ai_animator_targets.move(idx, idx+1)
                scn.ai_animator_targets_index += 1
                info = 'Item "%s" moved to position %d' % (item.name, scn.ai_animator_targets_index + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = scn.ai_animator_targets[idx-1].name
                scn.ai_animator_targets.move(idx, idx-1)
                scn.ai_animator_targets_index -= 1
                info = 'Item "%s" moved to position %d' % (item.name, scn.ai_animator_targets_index + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item "%s" removed from list' % (scn.ai_animator_targets[idx].name)
                scn.ai_animator_targets_index -= 1
                scn.ai_animator_targets.remove(idx)
                self.report({'INFO'}, info)
                
        if self.action == 'ADD':
            if context.object:
                if any(target.name == context.object.name for target in scn.ai_animator_targets):
                    self.report({'INFO'}, 'Item already exists in target list')
                else:
                    item = scn.ai_animator_targets.add()
                    item.name = context.object.name
                    item.obj = context.object
                    scn.ai_animator_targets_index = len(scn.ai_animator_targets)-1
                    info = '"%s" added to list' % (item.name)
                    self.report({'INFO'}, info)
            else:
                self.report({'INFO'}, "Nothing selected in the Viewport")
        return {"FINISHED"}
    

class CUSTOM_OT_addViewportSelection(Operator):
    """Add all items currently selected in the viewport"""
    bl_idname = "custom.add_viewport_selection"
    bl_label = "Add Viewport Selection to List"
    bl_description = "Add all items currently selected in the viewport"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scn = context.scene
        selected_objs = context.selected_objects
        if selected_objs:
            new_objs = []
            for i in selected_objs:
                item = scn.ai_animator_targets.add()
                item.name = i.name
                item.obj = i
                new_objs.append(item.name)
            info = ', '.join(map(str, new_objs))
            self.report({'INFO'}, 'Added: "%s"' % (info))
        else:
            self.report({'INFO'}, "Nothing selected in the Viewport")
        return{'FINISHED'}
    
    
class CUSTOM_OT_printItems(Operator):
    """Print all items and their properties to the console"""
    bl_idname = "custom.print_items"
    bl_label = "Print Items to Console"
    bl_description = "Print all items and their properties to the console"
    bl_options = {'REGISTER', 'UNDO'}
    
    reverse_order: BoolProperty(
        default=False,
        name="Reverse Order")
    
    @classmethod
    def poll(cls, context):
        return bool(context.scene.ai_animator_targets)
    
    def execute(self, context):
        scn = context.scene
        if self.reverse_order:
            for i in range(scn.ai_animator_targets_index, -1, -1):        
                ob = scn.ai_animator_targets[i].obj
                print ("Object:", ob,"-",ob.name, ob.type)
        else:
            for item in scn.ai_animator_targets:
                ob = item.obj
                print ("Object:", ob,"-",ob.name, ob.type)
        return{'FINISHED'}


class CUSTOM_OT_clearList(Operator):
    """Clear all items of the list"""
    bl_idname = "custom.clear_list"
    bl_label = "Clear List"
    bl_description = "Clear all items of the list"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.ai_animator_targets)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
        
    def execute(self, context):
        if bool(context.scene.ai_animator_targets):
            context.scene.ai_animator_targets.clear()
            self.report({'INFO'}, "All items removed")
        else:
            self.report({'INFO'}, "Nothing to remove")
        return{'FINISHED'}
    
    
class CUSTOM_OT_removeDuplicates(Operator):
    """Remove all duplicates"""
    bl_idname = "custom.remove_duplicates"
    bl_label = "Remove Duplicates"
    bl_description = "Remove all duplicates"
    bl_options = {'INTERNAL'}

    def find_duplicates(self, context):
        """find all duplicates by name"""
        name_lookup = {}
        for c, i in enumerate(context.scene.ai_animator_targets):
            name_lookup.setdefault(i.obj.name, []).append(c)
        duplicates = set()
        for name, indices in name_lookup.items():
            for i in indices[1:]:
                duplicates.add(i)
        return sorted(list(duplicates))
        
    @classmethod
    def poll(cls, context):
        return bool(context.scene.ai_animator_targets)
        
    def execute(self, context):
        scn = context.scene
        removed_items = []
        # Reverse the list before removing the items
        for i in self.find_duplicates(context)[::-1]:
            scn.ai_animator_targets.remove(i)
            removed_items.append(i)
        if removed_items:
            scn.ai_animator_targets_index = len(scn.ai_animator_targets)-1
            info = ', '.join(map(str, removed_items))
            self.report({'INFO'}, "Removed indices: %s" % (info))
        else:
            self.report({'INFO'}, "No duplicates")
        return{'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
    
class CUSTOM_OT_selectItems(Operator):
    """Select Items in the Viewport"""
    bl_idname = "custom.select_items"
    bl_label = "Select Item(s) in Viewport"
    bl_description = "Select Items in the Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    select_all = BoolProperty(
        default=False,
        name="Select all Items of List",
        options={'SKIP_SAVE'})
        
    @classmethod
    def poll(cls, context):
        return bool(context.scene.ai_animator_targets)
    
    def execute(self, context):
        scn = context.scene
        idx = scn.ai_animator_targets_index
        
        try:
            item = scn.ai_animator_targets[idx]
        except IndexError:
            self.report({'INFO'}, "Nothing selected in the list")
            return{'CANCELLED'}
                   
        obj_error = False
        bpy.ops.object.select_all(action='DESELECT')
        if not self.select_all:
            name = scn.ai_animator_targets[idx].obj.name
            obj = scn.objects.get(name, None)
            if not obj: 
                obj_error = True
            else:
                obj.select_set(True)
                info = '"%s" selected in Vieport' % (obj.name)
        else:
            selected_items = []
            unique_objs = set([i.obj.name for i in scn.ai_animator_targets])
            for i in unique_objs:
                obj = scn.objects.get(i, None)
                if obj:
                    obj.select_set(True)
                    selected_items.append(obj.name)
            
            if not selected_items: 
                obj_error = True
            else:
                missing_items = unique_objs.difference(selected_items)
                if not missing_items:
                    info = '"%s" selected in Viewport' \
                        % (', '.join(map(str, selected_items)))
                else:
                    info = 'Missing items: "%s"' \
                        % (', '.join(map(str, missing_items)))
        if obj_error: 
            info = "Nothing to select, object removed from scene"
        self.report({'INFO'}, info)    
        return{'FINISHED'}

class CUSTOM_OT_deleteObject(Operator):
    """Delete object from scene"""
    bl_idname = "custom.delete_object"
    bl_label = "Remove Object from Scene"
    bl_description = "Remove object from scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.ai_animator_targets)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
        
    def execute(self, context):
        scn = context.scene
        selected_objs = context.selected_objects
        idx = scn.ai_animator_targets_index
        try:
            item = scn.ai_animator_targets[idx]
        except IndexError:
            pass
        else:        
            ob = scn.objects.get(item.obj.name)
            if not ob:
                self.report({'INFO'}, "No object of that name found in scene")
                return {"CANCELLED"}
            else:
                bpy.ops.object.select_all(action='DESELECT')
                ob.select_set(True)
                bpy.ops.object.delete()
                
            info = ' Item "%s" removed from Scene' % (len(selected_objs))
            scn.ai_animator_targets_index -= 1
            scn.ai_animator_targets.remove(idx)
            self.report({'INFO'}, info)
        return{'FINISHED'}
    
class CUSTOM_UL_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        obj = item.obj
        custom_icon = "OUTLINER_OB_%s" % obj.type
        layout.prop(obj, "name", text="", emboss=False, translate=False, icon=custom_icon)
    def invoke(self, context, event):
        pass   

class AIAnimatorTTSTab(bpy.types.Panel):
#    bl_parent_id = "VIEW3D_PT_ai_animator"
    bl_idname = "VIEW3D_PT_ai_animator_tts"
    bl_label = "TTS"
    bl_category = "AI Animator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        box = self.layout.box()
        row.prop(context.scene, "ai_animator_tts_text") 
        row.operator("scene.ai_animator_generate_operator", text="Synthesize Audio")

class AIAnimatorBlendshapeTab(bpy.types.Panel):
#    bl_parent_id = "VIEW3D_PT_ai_animator"
    bl_label = "Blendshapes"
    bl_idname = "VIEW3D_PT_ai_animator_blendshapes"
    bl_category = "AI Animator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        box = self.layout.box()
        box.label(text="Target")
        row = box.row()
        row.template_list("CUSTOM_UL_items", "", bpy.context.scene, "ai_animator_targets", bpy.context.scene, "ai_animator_targets_index", rows=2)
        col = row.column(align=True)
        col.operator("custom.list_action", icon='ADD', text="").action = 'ADD'
        col.operator("custom.list_action", icon='REMOVE', text="").action = 'REMOVE'
        row = box.row()
        row.operator("scene.ai_animator_generate_operator", text="Generate Blendshapes")

#class AIAnimatorPanel(bpy.types.Panel):
#    bl_idname = "VIEW3D_PT_ai_animator"
#    bl_label = "AI Animator Label"
#    bl_category = "AI Animator"
#    bl_space_type = "VIEW_3D"
#    bl_region_type = "UI"
#    bl_options = {"HEADER_LAYOUT_EXPAND"}
#
#    def draw(self, context):
#        pass
#        box = self.layout.box()
#        box.label(text="Target")
#        row = box.row()
#        row.template_list("CUSTOM_UL_items", "", bpy.context.scene, "ai_animator_targets", bpy.context.scene, "ai_animator_targets_index", rows=2)
#        col = row.column(align=True)
#        col.operator("custom.list_action", icon='ADD', text="").action = 'ADD'
#        col.operator("custom.list_action", icon='REMOVE', text="").action = 'REMOVE'
#        row = box.row()
#        row.operator("scene.ai_animator_generate_operator", text="GENERATE")
