import bpy
import mathutils

def advancedlinearcloner_node_group():
    """Create a linear cloner node group with scale and rotation interpolation"""
    
    # Create new node group
    node_group = bpy.data.node_groups.new(type='GeometryNodeTree', name="AdvancedLinearCloner")
    
    # --- Interface ---
    # Output
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    # Inputs
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    
    # Basic Settings
    count_input = node_group.interface.new_socket(name="Count", in_out='INPUT', socket_type='NodeSocketInt')
    count_input.default_value = 5
    count_input.min_value = 1
    count_input.max_value = 1000
    
    offset_input = node_group.interface.new_socket(name="Offset", in_out='INPUT', socket_type='NodeSocketVector')
    offset_input.default_value = (1.0, 0.0, 0.0)
    
    # Global Transform Settings
    global_position_input = node_group.interface.new_socket(name="Global Position", in_out='INPUT', socket_type='NodeSocketVector')
    global_position_input.default_value = (0.0, 0.0, 0.0)
    
    global_rotation_input = node_group.interface.new_socket(name="Global Rotation", in_out='INPUT', socket_type='NodeSocketVector')
    global_rotation_input.default_value = (0.0, 0.0, 0.0)
    global_rotation_input.subtype = 'EULER'
    
    # Scale Start/End Settings
    scale_start_input = node_group.interface.new_socket(name="Scale Start", in_out='INPUT', socket_type='NodeSocketVector')
    scale_start_input.default_value = (1.0, 1.0, 1.0)
    
    scale_end_input = node_group.interface.new_socket(name="Scale End", in_out='INPUT', socket_type='NodeSocketVector')
    scale_end_input.default_value = (1.0, 1.0, 1.0)
    
    # Rotation Start/End Settings
    rotation_start_input = node_group.interface.new_socket(name="Rotation Start", in_out='INPUT', socket_type='NodeSocketVector')
    rotation_start_input.default_value = (0.0, 0.0, 0.0)
    rotation_start_input.subtype = 'EULER'
    
    rotation_end_input = node_group.interface.new_socket(name="Rotation End", in_out='INPUT', socket_type='NodeSocketVector')
    rotation_end_input.default_value = (0.0, 0.0, 0.0)
    rotation_end_input.subtype = 'EULER'
    
    # Random Settings
    random_position_input = node_group.interface.new_socket(name="Random Position", in_out='INPUT', socket_type='NodeSocketVector')
    random_position_input.default_value = (0.0, 0.0, 0.0)
    
    random_rotation_input = node_group.interface.new_socket(name="Random Rotation", in_out='INPUT', socket_type='NodeSocketVector')
    random_rotation_input.default_value = (0.0, 0.0, 0.0)
    
    random_scale_input = node_group.interface.new_socket(name="Random Scale", in_out='INPUT', socket_type='NodeSocketFloat')
    random_scale_input.default_value = 0.0
    random_scale_input.min_value = 0.0
    random_scale_input.max_value = 1.0
    
    seed_input = node_group.interface.new_socket(name="Random Seed", in_out='INPUT', socket_type='NodeSocketInt')
    seed_input.default_value = 0
    seed_input.min_value = 0
    seed_input.max_value = 10000
    
    # Material Settings
    material_input = node_group.interface.new_socket(name="Material", in_out='INPUT', socket_type='NodeSocketMaterial')
    material_input.default_value = None
    
    color_input = node_group.interface.new_socket(name="Color", in_out='INPUT', socket_type='NodeSocketColor')
    color_input.default_value = (1.0, 1.0, 1.0, 1.0)
    
    keep_materials_input = node_group.interface.new_socket(name="Keep Original Materials", in_out='INPUT', socket_type='NodeSocketBool')
    keep_materials_input.default_value = True
    
    # Instance Collection options
    pick_instance_input = node_group.interface.new_socket(name="Pick Random Instance", in_out='INPUT', socket_type='NodeSocketBool')
    pick_instance_input.default_value = False
    
    # --- Nodes ---
    nodes = node_group.nodes
    
    # Add group input and output
    group_input = nodes.new('NodeGroupInput')
    group_output = nodes.new('NodeGroupOutput')
    
    # Offset Multiplier (for internal scaling)
    offset_multiplier = nodes.new('ShaderNodeVectorMath')
    offset_multiplier.operation = 'MULTIPLY'
    offset_multiplier.inputs[1].default_value = (8.0, 8.0, 4.0)  # Multiplier values
    links = node_group.links
    links.new(group_input.outputs['Offset'], offset_multiplier.inputs[0])
    
    # Base cloner elements
    mesh_line = nodes.new('GeometryNodeMeshLine')
    mesh_line.mode = 'OFFSET'
    mesh_line.count_mode = 'TOTAL'
    
    # Instance on points
    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    
    # Interpolation setup for scale and rotation
    index = nodes.new('GeometryNodeInputIndex')
    math_subtract = nodes.new('ShaderNodeMath')
    math_subtract.operation = 'SUBTRACT'
    math_subtract.inputs[1].default_value = 1.0
    
    math_max = nodes.new('ShaderNodeMath')
    math_max.operation = 'MAXIMUM'
    math_max.inputs[1].default_value = 1.0
    
    math_divide = nodes.new('ShaderNodeMath')
    math_divide.operation = 'DIVIDE'
    
    # Map Range for factor (0-1)
    map_range = nodes.new('ShaderNodeMapRange')
    map_range.inputs['From Min'].default_value = 0.0
    map_range.inputs['From Max'].default_value = 1.0
    map_range.inputs['To Min'].default_value = 0.0
    map_range.inputs['To Max'].default_value = 1.0
    
    # Mix nodes for interpolation
    mix_scale = nodes.new('ShaderNodeMix')
    mix_scale.data_type = 'VECTOR'
    mix_scale.clamp_factor = True
    
    mix_rotation = nodes.new('ShaderNodeMix')
    mix_rotation.data_type = 'VECTOR'
    mix_rotation.clamp_factor = True
    
    # Random value nodes
    random_position = nodes.new('FunctionNodeRandomValue')
    random_position.data_type = 'FLOAT_VECTOR'
    
    random_rotation = nodes.new('FunctionNodeRandomValue')
    random_rotation.data_type = 'FLOAT_VECTOR'
    
    random_scale = nodes.new('FunctionNodeRandomValue')
    random_scale.data_type = 'FLOAT'
    
    # Vector math for negative ranges (to center the random range around 0)
    vector_math_neg_pos = nodes.new('ShaderNodeVectorMath')
    vector_math_neg_pos.operation = 'MULTIPLY'
    vector_math_neg_pos.inputs[1].default_value = (-1.0, -1.0, -1.0)
    
    vector_math_neg_rot = nodes.new('ShaderNodeVectorMath')
    vector_math_neg_rot.operation = 'MULTIPLY'
    vector_math_neg_rot.inputs[1].default_value = (-1.0, -1.0, -1.0)
    
    math_neg_scale = nodes.new('ShaderNodeMath')
    math_neg_scale.operation = 'MULTIPLY'
    math_neg_scale.inputs[1].default_value = -1.0
    
    # For combining random scale into vector
    combine_xyz_scale = nodes.new('ShaderNodeCombineXYZ')
    
    # Add vector math nodes
    add_random_rotation = nodes.new('ShaderNodeVectorMath')
    add_random_rotation.operation = 'ADD'
    
    add_random_scale = nodes.new('ShaderNodeVectorMath')
    add_random_scale.operation = 'ADD'
    
    # Global transform
    global_transform = nodes.new('GeometryNodeTransform')
    
    # Create links
    links = node_group.links
    
    # --- Pick Random Instance Logic (if input is a collection) ---
    pick_instance_random = nodes.new('GeometryNodeInstanceOnPoints')
    pick_instance_random.name = "Pick Random Instance"
    
    # Random Index for picking instance
    random_instance_index = nodes.new('FunctionNodeRandomValue')
    random_instance_index.data_type = 'INT'
    
    # Connect random seed and ID
    links.new(group_input.outputs['Random Seed'], random_instance_index.inputs['Seed'])
    links.new(index.outputs['Index'], random_instance_index.inputs['ID'])
    
    # Connect points and geometry
    links.new(mesh_line.outputs['Mesh'], pick_instance_random.inputs['Points'])
    links.new(group_input.outputs['Geometry'], pick_instance_random.inputs['Instance'])
    
    # Switch between normal instancing and random pick instancing
    switch_instancing = nodes.new('GeometryNodeSwitch')
    switch_instancing.name = "Switch Instance Mode"
    switch_instancing.input_type = 'GEOMETRY'
    
    # Transform instances
    set_position = nodes.new('GeometryNodeSetPosition')
    rotate_instances = nodes.new('GeometryNodeRotateInstances')
    scale_instances = nodes.new('GeometryNodeScaleInstances')
    
    # Material and Color nodes
    set_material = nodes.new('GeometryNodeSetMaterial')
    
    # Basic cloning setup
    links.new(group_input.outputs['Count'], mesh_line.inputs['Count'])
    links.new(offset_multiplier.outputs['Vector'], mesh_line.inputs['Offset'])
    links.new(mesh_line.outputs['Mesh'], instance_on_points.inputs['Points'])
    links.new(group_input.outputs['Geometry'], instance_on_points.inputs['Instance'])
    
    # Calculate interpolation factor
    links.new(index.outputs['Index'], math_divide.inputs[0])
    links.new(group_input.outputs['Count'], math_subtract.inputs[0])
    links.new(math_subtract.outputs['Value'], math_max.inputs[0])
    links.new(math_max.outputs['Value'], math_divide.inputs[1])
    links.new(math_divide.outputs['Value'], map_range.inputs['Value'])
    
    # Scale interpolation
    links.new(group_input.outputs['Scale Start'], mix_scale.inputs['A'])
    links.new(group_input.outputs['Scale End'], mix_scale.inputs['B'])
    links.new(map_range.outputs['Result'], mix_scale.inputs['Factor'])
    
    # Rotation interpolation
    links.new(group_input.outputs['Rotation Start'], mix_rotation.inputs['A'])
    links.new(group_input.outputs['Rotation End'], mix_rotation.inputs['B'])
    links.new(map_range.outputs['Result'], mix_rotation.inputs['Factor'])
    
    # Random values setup
    links.new(group_input.outputs['Random Seed'], random_position.inputs['Seed'])
    links.new(group_input.outputs['Random Seed'], random_rotation.inputs['Seed'])
    links.new(group_input.outputs['Random Seed'], random_scale.inputs['Seed'])
    
    links.new(index.outputs['Index'], random_position.inputs['ID'])
    links.new(index.outputs['Index'], random_rotation.inputs['ID'])
    links.new(index.outputs['Index'], random_scale.inputs['ID'])
    
    # Random position range
    links.new(group_input.outputs['Random Position'], vector_math_neg_pos.inputs[0])
    links.new(vector_math_neg_pos.outputs['Vector'], random_position.inputs['Min'])
    links.new(group_input.outputs['Random Position'], random_position.inputs['Max'])
    
    # Random rotation range
    links.new(group_input.outputs['Random Rotation'], vector_math_neg_rot.inputs[0])
    links.new(vector_math_neg_rot.outputs['Vector'], random_rotation.inputs['Min'])
    links.new(group_input.outputs['Random Rotation'], random_rotation.inputs['Max'])
    
    # Random scale range
    links.new(group_input.outputs['Random Scale'], math_neg_scale.inputs[0])
    links.new(math_neg_scale.outputs['Value'], random_scale.inputs['Min'])
    links.new(group_input.outputs['Random Scale'], random_scale.inputs['Max'])
    
    # Switch between normal instancing and random pick instancing
    links.new(group_input.outputs['Pick Random Instance'], switch_instancing.inputs['Switch'])
    links.new(instance_on_points.outputs['Instances'], switch_instancing.inputs[False])
    links.new(pick_instance_random.outputs['Instances'], switch_instancing.inputs[True])
    
    # Apply transforms
    links.new(switch_instancing.outputs['Output'], set_position.inputs['Geometry'])
    links.new(random_position.outputs['Value'], set_position.inputs['Offset'])
    
    # Apply rotation (base interpolated + random)
    links.new(set_position.outputs['Geometry'], rotate_instances.inputs['Instances'])
    links.new(mix_rotation.outputs['Result'], add_random_rotation.inputs[0])
    links.new(random_rotation.outputs['Value'], add_random_rotation.inputs[1])
    links.new(add_random_rotation.outputs['Vector'], rotate_instances.inputs['Rotation'])
    
    # Apply scale (base interpolated + random)
    links.new(rotate_instances.outputs['Instances'], scale_instances.inputs['Instances'])
    
    links.new(random_scale.outputs['Value'], combine_xyz_scale.inputs['X'])
    links.new(random_scale.outputs['Value'], combine_xyz_scale.inputs['Y'])
    links.new(random_scale.outputs['Value'], combine_xyz_scale.inputs['Z'])
    
    links.new(mix_scale.outputs['Result'], add_random_scale.inputs[0])
    links.new(combine_xyz_scale.outputs['Vector'], add_random_scale.inputs[1])
    links.new(add_random_scale.outputs['Vector'], scale_instances.inputs['Scale'])
    
    # Apply Material and Color
    links.new(scale_instances.outputs['Instances'], set_material.inputs['Geometry'])
    links.new(group_input.outputs['Material'], set_material.inputs['Material'])
    links.new(group_input.outputs['Keep Original Materials'], set_material.inputs['Selection'])
    
    # Apply Global Transform
    links.new(set_material.outputs['Geometry'], global_transform.inputs['Geometry'])
    links.new(group_input.outputs['Global Position'], global_transform.inputs['Translation'])
    links.new(group_input.outputs['Global Rotation'], global_transform.inputs['Rotation'])
    
    # Connect to output
    links.new(global_transform.outputs['Geometry'], group_output.inputs['Geometry'])
    
    return node_group

def register():
    pass

def unregister():
    pass