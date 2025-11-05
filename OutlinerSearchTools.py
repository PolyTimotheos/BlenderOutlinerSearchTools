bl_info = {
    "name": "Outliner Search Tools",
    "author": "Your Name",
    "version": (1, 2, 0),
    "blender": (4, 5, 0),
    "location": "Outliner > Header",
    "description": "Select all objects matching the outliner search filter",
    "category": "Interface",
}

import bpy

# Store the original draw function
original_draw = None

# Custom type filters (stored as scene properties)
def get_type_filters(scene):
    """Get type filters from scene properties"""
    return {
        'MESH': scene.outliner_search_filter_mesh,
        'CURVE': scene.outliner_search_filter_curve,
        'EMPTY': scene.outliner_search_filter_empty,
        'ARMATURE': scene.outliner_search_filter_armature,
        'LIGHT': scene.outliner_search_filter_light,
        'FONT': scene.outliner_search_filter_font,
        'SURFACE': scene.outliner_search_filter_surface,
        'CAMERA': scene.outliner_search_filter_camera,
        'META': scene.outliner_search_filter_meta,
    }


class OUTLINER_OT_select_matching(bpy.types.Operator):
    """Select all objects that match the current outliner search and filters.\nHold Shift to only select viewport-visible objects"""
    bl_idname = "outliner.select_matching"
    bl_label = "Select Matching"
    bl_description = "Select all objects matching the outliner search filter. Hold Ctrl to select only visible objects, Shift to add to selection, Alt to subtract from selection."
    bl_options = {'REGISTER', 'UNDO'}
    
    visible_only: bpy.props.BoolProperty(
        name="Visible Only",
        description="Only select objects visible in viewport",
        default=False,
    )  
    
    add_selection: bpy.props.BoolProperty(
        name="Add Selection",
        description="Add to existing selection",
        default=False
    )      

    subtract_selection: bpy.props.BoolProperty(
        name="Subtract Selection",
        description="Subtract from existing selection",
        default=False
    )  
    
    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == 'OUTLINER'
    
    def invoke(self, context, event):
        self.visible_only = event.ctrl
        self.add_selection = event.shift
        self.subtract_selection = event.alt

        return self.execute(context)
    
    def execute(self, context):
        outliner = context.space_data
        search_string = outliner.filter_text.lower()
        
        if not search_string:
            self.report({'INFO'}, "No search filter active")
            return {'CANCELLED'}
        
        if not self.add_selection and not self.subtract_selection:
            bpy.ops.object.select_all(action='DESELECT')

        # Get filter settings
        filter_state = outliner.filter_state
        use_filter_object_mesh = outliner.use_filter_object_mesh
        use_filter_object_armature = outliner.use_filter_object_armature
        use_filter_object_empty = outliner.use_filter_object_empty
        use_filter_object_light = outliner.use_filter_object_light
        use_filter_object_camera = outliner.use_filter_object_camera
        use_filter_object_others = outliner.use_filter_object_others
        use_filter_children = outliner.use_filter_children
        filter_invert = outliner.filter_invert
        
        # Get custom type filters
        type_filters = get_type_filters(context.scene)
        
        # Deselect all first
        bpy.ops.object.select_all(action='DESELECT')
        
        selected_count = 0
        view_layer = context.view_layer
        
        # Search through all objects in the scene
        for obj in context.scene.objects:
            # Check if name matches search
            if search_string not in obj.name.lower():
                continue
            
            # Check filter_state (selected/visible)
            if filter_state == 'VISIBLE':
                if obj.hide_get():
                    if not filter_invert:
                        continue

            elif filter_state == 'SELECTED':
                if not obj.select_get():
                    if not filter_invert:
                        continue

            elif filter_state == 'SELECTABLE':
                if obj.hide_select:
                    if not filter_invert:
                        continue

            elif filter_state == 'ACTIVE ':
                if obj != context.view_layer.objects.active:
                    if not filter_invert:
                        continue
            
            # 'ALL' means no filtering by state
            
            # Check object type filters (default outliner filters)
            type_match = False
            
            if obj.type == 'MESH' and use_filter_object_mesh:
                type_match = True
            elif obj.type == 'ARMATURE' and use_filter_object_armature:
                type_match = True
            elif obj.type == 'EMPTY' and use_filter_object_empty:
                type_match = True
            elif obj.type == 'LIGHT' and use_filter_object_light:
                type_match = True
            elif obj.type == 'CAMERA' and use_filter_object_camera:
                type_match = True
            elif obj.type in ('CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'GPENCIL', 'LATTICE', 'SPEAKER', 'LIGHTPROBE') and use_filter_object_others:
                type_match = True
            
            if not type_match:
                continue
            
            # Check custom type filters
            if obj.type not in type_filters or not type_filters[obj.type]:
                continue
            
            # If shift is held, check viewport visibility
            if self.visible_only:
                print('Outliner Search Tools -> Shift clicked: Selecting only visible objects')
                # Check if hidden in viewport
                if not obj.visible_get():
                    print(f'Outliner Search Tools -> Object {obj.name} is hidden in viewport, skipping')
                    continue

            if self.subtract_selection:
                obj.select_set(False)
            else:
                obj.select_set(True)

            selected_count += 1
        
        if selected_count > 0:
            suffix = " (visible only)" if self.visible_only else ""
            if self.subtract_selection:
                self.report({'INFO'}, f"Subtracted {selected_count} object(s){suffix} from selection")
            elif self.add_selection:
                self.report({'INFO'}, f"Added {selected_count} object(s){suffix} to selection")
            else:
                self.report({'INFO'}, f"Selected {selected_count} object(s){suffix}")
        else:
            self.report({'INFO'}, "No matching objects found")
        
        return {'FINISHED'}


class OUTLINER_OT_toggle_type_filter(bpy.types.Operator):
    """Toggle object type filter"""
    bl_idname = "outliner.toggle_type_filter"
    bl_label = "Toggle Type Filter"
    bl_options = {'REGISTER', 'UNDO'}
    
    object_type: bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        
        if event.shift:
            # Shift-click: enable only this type, disable all others
            scene.outliner_search_filter_mesh = (self.object_type == 'MESH')
            scene.outliner_search_filter_curve = (self.object_type == 'CURVE')
            scene.outliner_search_filter_empty = (self.object_type == 'EMPTY')
            scene.outliner_search_filter_armature = (self.object_type == 'ARMATURE')
            scene.outliner_search_filter_light = (self.object_type == 'LIGHT')
            scene.outliner_search_filter_font = (self.object_type == 'FONT')
            scene.outliner_search_filter_surface = (self.object_type == 'SURFACE')
            scene.outliner_search_filter_camera = (self.object_type == 'CAMERA')
            scene.outliner_search_filter_meta = (self.object_type == 'META')
        else:
            # Normal click: toggle this type
            prop_name = f"outliner_search_filter_{self.object_type.lower()}"
            current_value = getattr(scene, prop_name)
            setattr(scene, prop_name, not current_value)
        
        return {'FINISHED'}


class OUTLINER_OT_reset_type_filters(bpy.types.Operator):
    """Reset all type filters to enabled"""
    bl_idname = "outliner.reset_type_filters"
    bl_label = "Reset Filters"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        scene.outliner_search_filter_mesh = True
        scene.outliner_search_filter_curve = True
        scene.outliner_search_filter_empty = True
        scene.outliner_search_filter_armature = True
        scene.outliner_search_filter_light = True
        scene.outliner_search_filter_font = True
        scene.outliner_search_filter_surface = True
        scene.outliner_search_filter_camera = True
        scene.outliner_search_filter_meta = True
        
        self.report({'INFO'}, "Type filters reset")
        return {'FINISHED'}


class OUTLINER_PT_type_filter(bpy.types.Panel):
    """Panel for the type filter dropdown"""
    bl_idname = "OUTLINER_PT_type_filter"
    bl_label = "Type Filters"
    bl_description = "Filter selection by object type. Shift-click to isolate a type."
    bl_space_type = 'OUTLINER'
    bl_region_type = 'HEADER'
    
    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 5  # Adjust this number to change width (default is ~10)
        scene = context.scene
        
        # Type filter toggles with icons
        type_configs = [
            ('MESH', 'MESH_DATA', 'Mesh'),
            ('CURVE', 'CURVE_DATA', 'Curve'),
            ('EMPTY', 'EMPTY_DATA', 'Empty'),
            ('ARMATURE', 'ARMATURE_DATA', 'Armature'),
            ('LIGHT', 'LIGHT_DATA', 'Light'),
            ('FONT', 'FONT_DATA', 'Font'),
            ('SURFACE', 'SURFACE_DATA', 'Surface'),
            ('CAMERA', 'CAMERA_DATA', 'Camera'),
            ('META', 'META_DATA', 'Meta'),
        ]
        
        for obj_type, icon, label in type_configs:
            prop_name = f"outliner_search_filter_{obj_type.lower()}"
            row = layout.row(align=True)
            
            # Create operator button with icon and checkmark
            op = row.operator("outliner.toggle_type_filter", 
                            text=label, 
                            icon=icon,
                            depress=getattr(scene, prop_name))
            op.object_type = obj_type
        
        layout.separator()
        
        # Reset button
        layout.operator("outliner.reset_type_filters", text="Reset All", icon='LOOP_BACK')


def custom_outliner_header_draw(self, context):
    """Custom draw function that includes our button next to the search field"""
    layout = self.layout
    space = context.space_data
    scene = context.scene
    
    # 1. UI Type (editor type selector)
    layout.template_header()
    
    # 2. Display mode (icon only)
    layout.prop(space, "display_mode", text="", icon_only=True)
    
    layout.separator_spacer()
    
    # 3. Search field with our custom buttons (centered)
    row = layout.row(align=True)
    row.prop(space, "filter_text", text="", icon='VIEWZOOM')
    # Our custom select button - right next to the search field!
    row.operator("outliner.select_matching", text="", icon='RESTRICT_SELECT_OFF')
    
    # Small space before the type filter dropdown
    row.separator(factor=0.5)
    
    # Type filter dropdown
    row.popover(panel="OUTLINER_PT_type_filter", text="", icon='HOLDOUT_ON')
    
    layout.separator_spacer()
    
    # 4. Filter button dropdown
    layout.popover(panel="OUTLINER_PT_filter", text="", icon='FILTER')
    
    # 5. New Collection button (only show in appropriate display modes)
    if space.display_mode == 'VIEW_LAYER':
        row = layout.row(align=True)
        row.operator("outliner.collection_new", text="", icon='COLLECTION_NEW').nested = True


def register():
    global original_draw
    
    # Register properties for type filters
    bpy.types.Scene.outliner_search_filter_mesh = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.outliner_search_filter_curve = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.outliner_search_filter_empty = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.outliner_search_filter_armature = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.outliner_search_filter_light = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.outliner_search_filter_font = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.outliner_search_filter_surface = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.outliner_search_filter_camera = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.outliner_search_filter_meta = bpy.props.BoolProperty(default=True)
    
    # Register classes
    bpy.utils.register_class(OUTLINER_OT_select_matching)
    bpy.utils.register_class(OUTLINER_OT_toggle_type_filter)
    bpy.utils.register_class(OUTLINER_OT_reset_type_filters)
    bpy.utils.register_class(OUTLINER_PT_type_filter)
    
    # Store the original draw function and replace it with ours
    original_draw = bpy.types.OUTLINER_HT_header.draw
    bpy.types.OUTLINER_HT_header.draw = custom_outliner_header_draw


def unregister():
    global original_draw
    
    # Restore the original draw function
    if original_draw:
        bpy.types.OUTLINER_HT_header.draw = original_draw
    
    # Unregister classes
    bpy.utils.unregister_class(OUTLINER_PT_type_filter)
    bpy.utils.unregister_class(OUTLINER_OT_reset_type_filters)
    bpy.utils.unregister_class(OUTLINER_OT_toggle_type_filter)
    bpy.utils.unregister_class(OUTLINER_OT_select_matching)
    
    # Remove properties
    del bpy.types.Scene.outliner_search_filter_mesh
    del bpy.types.Scene.outliner_search_filter_curve
    del bpy.types.Scene.outliner_search_filter_empty
    del bpy.types.Scene.outliner_search_filter_armature
    del bpy.types.Scene.outliner_search_filter_light
    del bpy.types.Scene.outliner_search_filter_font
    del bpy.types.Scene.outliner_search_filter_surface
    del bpy.types.Scene.outliner_search_filter_camera
    del bpy.types.Scene.outliner_search_filter_meta


if __name__ == "__main__":
    register()