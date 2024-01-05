import bpy
import time
import socket 
import csv
import random 

_ARKIT_BLENDSHAPES = ['eyeBlinkLeft', 'eyeLookDownLeft', 'eyeLookInLeft', 'eyeLookOutLeft', 'eyeLookUpLeft', 'eyeSquintLeft', 'eyeWideLeft', 'eyeBlinkRight', 'eyeLookDownRight', 'eyeLookInRight', 'eyeLookOutRight', 'eyeLookUpRight', 'eyeSquintRight', 'eyeWideRight', 'jawForward', 'jawRight', 'jawLeft', 'jawOpen', 'mouthClose', 'mouthFunnel', 'mouthPucker', 'mouthRight', 'mouthLeft', 'mouthSmileLeft', 'mouthSmileRight', 'mouthFrownLeft', 'mouthFrownRight', 'mouthDimpleLeft', 'mouthDimpleRight', 'mouthStretchLeft', 'mouthStretchRight', 'mouthRollLower', 'mouthRollUpper', 'mouthShrugLower', 'mouthShrugUpper', 'mouthPressLeft', 'mouthPressRight', 'mouthLowerDownLeft', 'mouthLowerDownRight', 'mouthUpperUpLeft', 'mouthUpperUpRight', 'browDownLeft', 'browDownRight', 'browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 'cheekPuff', 'cheekSquintLeft', 'cheekSquintRight', 'noseSneerLeft', 'noseSneerRight', 'tongueOut']

'''
Interface for looking up shape key/custom properties by name and setting their respective weights on frames.
'''
class AnimatableObject:
    '''
    Construct an instance to manipulate frames on a single target object (which is an object within the Blender context).
    If the number of frames is known ahead of time (i.e. you are not working with streaming), this can be passed here.
    If you are streaming, pass num_frames=0 (or simply don't pass anything for the parameter and leave empty).
    The target should have at least one shape key or custom property with a name that corresponds to one of the entries in LIVE_LINK_FACE_HEADER.
    An exception will be raised if neither of these are present.
    '''
    def __init__(self, target, num_frames=0, action_name=None):
        self.target = target
        # first, let's create a placeholder for all shape keys that exist on the target mesh
        # sk_frames is a list where each entry (itself a list) represents one frame
        # each frame will contain N values (where N is the number of shape keys in the target mesh)
        # (note this will also create keyframes for non-LiveLinkFace shape keys on the mesh)
        # I can't find a better way to check if an object has shapekeys, so just use try-except
        try:
            self.sk_frames = [ [0] * len(self.target.data.shape_keys.key_blocks) for _ in range(num_frames) ] 
        except:
            self.sk_frames = None
        print(f"Created {num_frames} empty frames for {len(self.target.data.shape_keys.key_blocks)} existing blendshapes in mesh")
        # some ARKit blendshapes may drive bone rotations, rather than mesh-deforming shape keys
        # if a custom property exists on the target object whose name matches the incoming ARkit shape, the property will be animated
        # it is then your responsibility to create a driver in Blender to rotate the bone between its extremities (blendshape values -1 to 1 )
#        self.custom_props = [] 
#        for i in range(len(LIVE_LINK_FACE_HEADER) - 2):
#            custom_prop = self.livelink_to_custom_prop(i)
#            if custom_prop is not None:
#                self.custom_props += [custom_prop]
#                print(f"Found custom property {custom_prop} for ARkit blendshape : {LIVE_LINK_FACE_HEADER[i+2]}")
                
#        for k in ["HeadPitch","HeadRoll","HeadYaw"]:
#            if k not in self.custom_props:
#                self.target[k] = 0.0
#                print(f"Created custom property {k} on target object")
#                self.custom_props += [ k ] 
#        print(f"Set custom_props to {self.custom_props}")
#        self.custom_prop_frames = [[0] * len(self.custom_props) for _ in range(num_frames)]               
#        print(f"Created {len(self.custom_prop_frames)} frames for {len(self.custom_props)} custom properties")
        if action_name is not None:
            self.create_action(action_name, num_frames)
            
    '''
    Try and resolve an ARKit blendshape-id to a named shape key in the target object.
    ARKit blendshape IDs are the integer index within LIVE_LINK_FACE_HEADER (offset to exclude the first two columns.
    '''
    def arkit_to_shapekey_idx(self, arkit_bs_idx):
        name = _ARKIT_BLENDSHAPES[arkit_bs_idx]
        for n in [name, name[0].lower() + name[1:]]:
            idx = self.target.data.shape_keys.key_blocks.find(n)
            if idx != -1:
                return idx
        return idx

    '''
    Try and resolve an ARKit blendshape-id to a custom property in the target object.
    ARKit blendshape IDs are the integer index within LIVE_LINK_FACE_HEADER (offset to exclude the first two columns.
    '''
    def livelink_to_custom_prop(self, ll_idx):
        name = LIVE_LINK_FACE_HEADER[ll_idx+2]

        # Invert Mouth Left and Rigth shapes to compensate for LiveLinkFace bug
        if bpy.context.scene.invert_lr_mouth:
            if name == 'MouthLeft':
                name = 'MouthRight'
            elif name == 'MouthRight':
                name = 'MouthLeft'
                
        for n in [name, name[0].lower() + name[1:]]:
            try:
                self.target[n]
                return n
            except:
                pass
        return None    
            
    '''Sets the value for the ARKit blendshape at index [arkit_bs_idxl] to [val] for frame [frame] (note the underlying target may be a blendshape or a bone).'''
    def set_frame_value(self, arkit_bs_idx, frame, val):
        i_sk = self.arkit_to_shapekey_idx(arkit_bs_idx)
        
        if i_sk != -1:
            self.sk_frames[frame][i_sk] = val
        else:
            #custom_prop = self.livelink_to_custom_prop(i_ll)
            #if custom_prop is not None:
            #    custom_prop_idx =self.custom_props.index(custom_prop)
            #    self.custom_prop_frames[frame][custom_prop_idx] = val
#            else:
            print(f"Failed to find custom property for ARkit blendshape {_ARKIT_BLENDSHAPES[arkit_bs_idx]}")
            pass

    # this method actually sets the keyframe values via bpy
    def update_keyframes(self):
        # a bit slow to use bpy.context.object.data.shape_keys.keyframe_insert(datapath,frame=frame)
        # (where datapath is 'key_blocks["MouthOpen"].value') 
        # better to add a new fcurve for each shape key then set the points in one go        
        frame_nums = list(range(len(self.sk_frames)))
        print(frame_nums)
        for i_sk,fc in enumerate(self.sk_fcurves):
            frame_values = [self.sk_frames[i][i_sk] for i in frame_nums]
            
            frame_data = [x for co in zip(frame_nums, frame_values) for x in co]
            print(f"frame-values len {len(frame_values)} frame_Data len {len(frame_data)}")
            print(frame_data)
            fc.keyframe_points.foreach_set('co',frame_data)
            
        for i_b,fc, in enumerate(self.custom_prop_fcurves):
            frame_values = [self.custom_prop_frames[i][i_b] for i in frame_nums]
            frame_data = [x for co in zip(frame_nums, frame_values) for x in co]
            fc.keyframe_points.foreach_set('co',frame_data)
       
    def create_action(self, action_name, num_frames):
        # create a new Action so we can directly create fcurves and set the keyframe points
        try:
            self.sk_action = bpy.data.actions[f"{action_name}_shapekey"]
        except: 
            self.sk_action = bpy.data.actions.new(f"{action_name}_shapekey") 
                
        # create the bone AnimData if it doesn't exist 
        # important - we create this on the target (e.g. bpy.context.object), not its data (bpy.context.object.data)
        if self.target.animation_data is None:
            self.target.animation_data_create()
                                   
        # create the shape key AnimData if it doesn't exist 
        if self.target.data.shape_keys.animation_data is None:
            self.target.data.shape_keys.animation_data_create()
            
        self.target.data.shape_keys.animation_data.action = self.sk_action
        
        self.sk_fcurves = []
        self.custom_prop_fcurves = []
        
        for sk in self.target.data.shape_keys.key_blocks:
            datapath = f"{sk.path_from_id()}.value"
            
            fc = self.sk_action.fcurves.find(datapath)
            if fc is None:
                print(f"Creating fcurve for shape key {sk.path_from_id()}")
                fc = self.sk_action.fcurves.new(datapath)                
                fc.keyframe_points.add(count=num_frames)
            else:
                print(f"Found fcurve for shape key {sk.path_from_id()}")
            self.sk_fcurves += [fc]

        #for custom_prop in self.custom_props:
        #    datapath = f"[\"{custom_prop}\"]"
        #    for i in range(num_frames):
        #        self.target.keyframe_insert(datapath,frame=i)
        #    self.custom_prop_fcurves += [fc for fc in self.target.animation_data.action.fcurves if fc.data_path == datapath]
    
    def update_to_frame(self, frame=0):
        self.target.data.shape_keys.key_blocks.foreach_set("value", self.sk_frames[frame])        
        for i,custom_prop in enumerate(self.custom_props):
            self.target[custom_prop] = self.custom_prop_frames[frame][i]
        self.target.data.shape_keys.user.update()

def create_action_with_blendshapes(targets, frame_data, action_name="BlenderAIAnimatorAction"):
    num_frames = len(frame_data)
    animatable_objects = [AnimatableObject(t, num_frames, action_name=action_name) for t in targets]
    for frame_num in range(num_frames):
        for target in animatable_objects:
            frame = frame_data[frame_num]
            assert len(frame) == len(_ARKIT_BLENDSHAPES), f"Expected frame to contain {len(_ARKIT_BLENDSHAPES)} values, but {len(frame)} were found"
            for arkit_bs_idx in range(len(frame)):
                val = frame[arkit_bs_idx]
                target.set_frame_value(arkit_bs_idx, frame_num, val)
            target.update_keyframes()
