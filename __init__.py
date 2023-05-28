bl_info = {
    "name": "Character Assembler",
    "blender": (3, 5, 0),
    "category": "Object",
}

import bpy
import json
import os
import time
from bpy.props import IntProperty, StringProperty, PointerProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

# Get the path of the directory where your addon is located.
addon_directory = os.path.dirname(os.path.realpath(__file__))

def clear_scene():
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select all objects except cameras and lights
    for obj in bpy.context.scene.objects:
        if obj.type not in {'CAMERA', 'LIGHT'}:
            obj.select_set(True)

    # Delete all selected objects
    bpy.ops.object.delete()

def clean_unused_data():
    # Clean orphan meshes
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    # Clean orphan materials
    for material in bpy.data.materials:
        if material.users == 0:
            bpy.data.materials.remove(material)

    # Clean orphan textures
    for texture in bpy.data.textures:
        if texture.users == 0:
            bpy.data.textures.remove(texture)

    # Clean orphan images
    for image in bpy.data.images:
        if image.users == 0:
            bpy.data.images.remove(image)

def update_token_number(self, context):
    # Call the display attributes and build character function when the token number changes
    bpy.ops.object.character_assembler()
    bpy.ops.object.build_character()


class CharacterAssemblerPanel(bpy.types.Panel):
    bl_label = "Character Assembler"
    bl_idname = "OBJECT_PT_character_assembler"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Character Assembler"

    def draw(self, context):
        layout = self.layout
        props = context.scene.character_props

        layout.prop(props, "token_number")

        attribute_list = context.scene.attribute_list
        attribute_list_index = context.scene.attribute_list_index

        layout.template_list("ATTRIBUTE_UL_items", "", context.scene, "attribute_list", context.scene, "attribute_list_index")

        #layout.operator(CharacterAssemblerOperator.bl_idname, text="Display Attributes")
        #layout.operator(CharacterBuilderOperator.bl_idname, text="Build Character")
        layout.prop(props, "glb_folder")
        layout.operator(SaveCharacterGLBOperator.bl_idname, text="Save GLB")
        layout.operator(BatchCharacterImportOperator.bl_idname, text="Batch Import Characters")

class CharacterProperties(bpy.types.PropertyGroup):
    token_number: IntProperty(
        name="Token Number",
        description="Enter a token number from 1 to 10000",
        min=1,
        max=10000,
        default=1,
        update=update_token_number, 
    )
    attribute_keys: StringProperty(default="")
    batch_import_file: StringProperty(name="Batch Import File", subtype='FILE_PATH')
    glb_folder: StringProperty(name="Export GLB Folder", subtype='DIR_PATH',)


class ATTRIBUTE_UL_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index): 
        layout.label(text=item.name, icon='NONE')

class CharacterAssemblerOperator(bpy.types.Operator):
    bl_idname = "object.character_assembler"
    bl_label = "Display Attributes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.character_props
        token_number = props.token_number

        # Load the JSON data from the character file
        json_file_path = os.path.join(addon_directory, "resources", "combined_data.json")
        with open(json_file_path, 'r') as file:
            character_data = json.load(file)

        # Get the attribute keys for the selected token ID
        attribute_keys = character_data.get(str(token_number), {})
        props.attribute_keys = json.dumps(attribute_keys, indent=2)

        # Load the JSON data from the available file
        available_file_path = os.path.join(addon_directory, "resources", "available.json")
        with open(available_file_path, 'r') as file:
            available_data = json.load(file)

        # Create a dictionary of part names based on the attribute keys
        part_names = {}
        for part_category, parts in available_data['assets'].items():
            for part_id, part_info in parts.items():
                if "name" in part_info:
                    part_names[part_id] = part_info["name"]


        # Update the UIList
        attribute_list = context.scene.attribute_list
        attribute_list.clear()
        for key, value in attribute_keys.items():
            item = attribute_list.add()
            item.name = f"{key}: {part_names.get(value, 'Unknown')} ({value})"

        return {'FINISHED'}

class CharacterBuilderOperator(bpy.types.Operator):
    bl_idname = "object.build_character"
    bl_label = "Build Character"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        clear_scene()
        clean_unused_data()
        props = context.scene.character_props
        token_number = props.token_number
        attribute_keys = json.loads(props.attribute_keys)

        base_folder = os.path.join(addon_directory, "resources", "All_Assets_FWY")

        for part, asset_key in attribute_keys.items():
            if not asset_key:  # Skip empty asset keys
                continue

            # Use asset_key to create the file path
            file_path = os.path.join(base_folder, f"{asset_key}.glb")

            if os.path.exists(file_path):
                bpy.ops.import_scene.gltf(filepath=file_path)

                # Rename imported meshes to match their attribute names
                for obj in bpy.context.selected_objects:
                    if obj.type == 'MESH':
                        obj.name = part

                print(f"Imported {file_path}")
            else:
                print(f"File not found: {file_path}")

        # Apply the face texture after importing all assets and renaming them
        face_asset_key = attribute_keys.get("face")
        head_asset_key = attribute_keys.get("head")  # Get head asset key
        if face_asset_key is not None:
            apply_face_texture(face_asset_key, head_asset_key)  # Pass head_asset_key to the function

        rig_character(token_number)
        # export_character_glb(token_number)

        return {'FINISHED'}

def apply_face_texture(face_asset_key, head_asset_key):  # Add head_asset_key as an argument
    face_file_path = os.path.join(addon_directory, "resources", "All_Assets_FWY", f"{face_asset_key}.png")

    if not os.path.exists(face_file_path):
        print(f"Face texture file not found: {face_file_path}")
        return

    # Find the head object and its material
    head_obj = None
    for obj in bpy.data.objects:
        if "head" in obj.name.lower():
            head_obj = obj
            break

    if head_obj is None:
        print("Head object not found.")
        return

    mat = head_obj.active_material
    if mat is None:
        print("Material not found on the head object.")
        return

    # Create a new image node and load the face texture
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    face_texture_node = nodes.new(type="ShaderNodeTexImage")
    face_texture_node.image = bpy.data.images.load(face_file_path)

    # Find the target node (Principled BSDF) and the base color/emission image node connected to it
    target_node = None
    base_color_image_node = None
    emission_image_node = None
    for node in nodes:
        if node.type == "BSDF_PRINCIPLED":
            target_node = node
            for input in target_node.inputs:
                if input.name == "Base Color" and input.links and input.links[0].from_node.type == "TEX_IMAGE":
                    base_color_image_node = input.links[0].from_node
                elif input.name == "Emission" and input.links and input.links[0].from_node.type == "TEX_IMAGE" and input.links[0].from_node.label == "EMISSIVE":
                    emission_image_node = input.links[0].from_node
            break

    if target_node is None:
        print("Target node not found.")
        return

    if head_asset_key == "678d5c8760":
        if emission_image_node is None:
            print("Emission image node not found for asset key {}.".format(face_asset_key))
            return

        # Create a new MixRGB node
        mix_node = nodes.new(type="ShaderNodeMixRGB")
        mix_node.blend_type = 'LINEAR_LIGHT'
        mix_node.location = (emission_image_node.location.x + 300, emission_image_node.location.y)

        # Connect the image nodes and MixRGB node as described
        links.new(emission_image_node.outputs["Color"], mix_node.inputs[1])
        links.new(face_texture_node.outputs["Color"], mix_node.inputs[2])
        links.new(face_texture_node.outputs["Alpha"], mix_node.inputs["Fac"])
        links.new(mix_node.outputs["Color"], target_node.inputs["Emission"])

    elif base_color_image_node is not None:
        # Create a new MixRGB node
        mix_node = nodes.new(type="ShaderNodeMixRGB")
        mix_node.location = (base_color_image_node.location.x + 300, base_color_image_node.location.y)

        # Connect the image nodes and MixRGB node as described
        links.new(base_color_image_node.outputs["Color"], mix_node.inputs[1])
        links.new(face_texture_node.outputs["Color"], mix_node.inputs[2])
        links.new(face_texture_node.outputs["Alpha"], mix_node.inputs["Fac"])
        links.new(mix_node.outputs["Color"], target_node.inputs["Base Color"])
    else:
        print("Neither base color nor emission image node found for asset key {}.".format(face_asset_key))
        return

def rig_character(token_number):
    armatures = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armatures.append(obj)
        elif obj.type == 'MESH':
            obj.select_set(True)
        else:
            obj.select_set(False)

    # Delete all but the first armature
    for armature in armatures[1:]:
        bpy.data.objects.remove(armature, do_unlink=True)

    # Get a reference to the first armature
    armature = armatures[0] if armatures else None
    if armature:
        armature.select_set(True)
    # Rename the armature based on the token number
    armature.name = f"fRiENDSiES {token_number}"

    # Clear any parenting to the armature
    for obj in bpy.context.selected_objects:
        obj.parent = None

    # Set the active object to the armature and change its mode to Pose mode
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Parent all selected objects to the first armature using Armature Deform
    bpy.ops.object.parent_set(type='ARMATURE', keep_transform=True)
    armature.parent = None

    # Switch back to Object mode
    bpy.ops.object.mode_set(mode='OBJECT')

def export_character_glb(token_number):
    props = bpy.context.scene.character_props
    glb_folder = props.glb_folder  # Update this path to the folder where you want to save the .glb files
    glb_file_name = f"Character_{token_number}.glb"
    glb_file_path = os.path.join(glb_folder, glb_file_name)

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select the generated character's objects (meshes and armature)
    armature_name = f"fRiENDSiES {token_number}"
    if armature_name in bpy.data.objects:
        armature = bpy.data.objects[armature_name]
        armature.select_set(True)

        # Select all mesh objects parented to the armature
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.parent == armature:
                obj.select_set(True)

    # Export the selected objects as a glb file
    bpy.ops.export_scene.gltf(filepath=glb_file_path, use_selection=True)  # Replace export_selected with use_selection


class AttributeItem(bpy.types.PropertyGroup):
    name: StringProperty()


class SaveCharacterGLBOperator(bpy.types.Operator):
    bl_idname = "object.save_character_glb"
    bl_label = "Save GLB"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.character_props
        token_number = props.token_number

        export_character_glb(token_number)

        return {'FINISHED'}


# Create a new operator for batch import
class BatchCharacterImportOperator(bpy.types.Operator, ImportHelper):
    bl_idname = "object.batch_character_import"
    bl_label = "Batch Import Characters"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    def execute(self, context):
        props = context.scene.character_props
        batch_import_file = props.batch_import_file

        if not batch_import_file.endswith('.json'):
            self.report({'ERROR'}, "Please select a JSON file.")
            return {'CANCELLED'}

        with open(batch_import_file, 'r') as file:
            token_numbers = json.load(file)

        for i, token_number in enumerate(token_numbers):
            props.token_number = int(token_number)  # Convert token_number to an integer
            bpy.ops.object.character_assembler()
            bpy.ops.object.build_character()

            # Move the character to the right
            for obj in bpy.context.selected_objects:
                obj.location.x += i * 0.5
            
            # Add a delay of 0.25 seconds before importing the next character
            time.sleep(1)

        return {'FINISHED'}

classes = (
    CharacterProperties,
    CharacterAssemblerOperator,
    CharacterBuilderOperator,
    SaveCharacterGLBOperator,
    BatchCharacterImportOperator,
    CharacterAssemblerPanel,
    ATTRIBUTE_UL_items,
    AttributeItem,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.character_props = PointerProperty(type=CharacterProperties)
    bpy.types.Scene.attribute_list = CollectionProperty(type=AttributeItem)
    bpy.types.Scene.attribute_list_index = IntProperty()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.character_props
    del bpy.types.Scene.attribute_list
    del bpy.types.Scene.attribute_list_index

if __name__ == "__main__":
    register()