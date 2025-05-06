import bpy
import mathutils

def gridcloner3d_node_group():
    """Create an advanced 3D grid cloner node group with centering and 2D/3D switch"""

    # Create new node group
    node_group = bpy.data.node_groups.new(type='GeometryNodeTree', name="GridCloner3D_Advanced")

    # --- Interface ---
    # Output
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Inputs
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')

    # Grid Settings
    count_x_input = node_group.interface.new_socket(name="Count X", in_out='INPUT', socket_type='NodeSocketInt')
    count_x_input.default_value = 3
    count_x_input.min_value = 1
    count_x_input.max_value = 100

    count_y_input = node_group.interface.new_socket(name="Count Y", in_out='INPUT', socket_type='NodeSocketInt')
    count_y_input.default_value = 3
    count_y_input.min_value = 1
    count_y_input.max_value = 100

    count_z_input = node_group.interface.new_socket(name="Count Z", in_out='INPUT', socket_type='NodeSocketInt')
    count_z_input.default_value = 1 # Default to 1 for a 2D grid initially
    count_z_input.min_value = 1
    count_z_input.max_value = 100

    spacing_input = node_group.interface.new_socket(name="Spacing", in_out='INPUT', socket_type='NodeSocketVector')
    spacing_input.default_value = (1.0, 1.0, 1.0)

    # Global Transform Settings
    global_position_input = node_group.interface.new_socket(name="Global Position", in_out='INPUT', socket_type='NodeSocketVector')
    global_position_input.default_value = (0.0, 0.0, 0.0)
    
    global_rotation_input = node_group.interface.new_socket(name="Global Rotation", in_out='INPUT', socket_type='NodeSocketVector')
    global_rotation_input.default_value = (0.0, 0.0, 0.0)
    global_rotation_input.subtype = 'EULER'

    # Instance Transform Settings
    scale_input = node_group.interface.new_socket(name="Instance Scale", in_out='INPUT', socket_type='NodeSocketVector')
    scale_input.default_value = (1.0, 1.0, 1.0)

    rotation_input = node_group.interface.new_socket(name="Instance Rotation", in_out='INPUT', socket_type='NodeSocketVector')
    rotation_input.default_value = (0.0, 0.0, 0.0)
    rotation_input.subtype = 'EULER'

    # Random Settings
    random_position_input = node_group.interface.new_socket(name="Random Position", in_out='INPUT', socket_type='NodeSocketVector')
    random_position_input.default_value = (0.0, 0.0, 0.0)

    random_rotation_input = node_group.interface.new_socket(name="Random Rotation", in_out='INPUT', socket_type='NodeSocketVector')
    random_rotation_input.default_value = (0.0, 0.0, 0.0)
    random_rotation_input.subtype = 'EULER'

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
    
    # Grid options
    center_grid_input = node_group.interface.new_socket(name="Center Grid", in_out='INPUT', socket_type='NodeSocketBool')
    center_grid_input.default_value = False

    # --- Nodes ---
    nodes = node_group.nodes
    links = node_group.links

    group_input = nodes.new('NodeGroupInput')
    group_output = nodes.new('NodeGroupOutput')

    # --- Spacing Multiplier (for internal scaling) ---
    # Add a vector multiply node to scale the spacing input value
    spacing_multiplier = nodes.new('ShaderNodeVectorMath')
    spacing_multiplier.operation = 'MULTIPLY'
    spacing_multiplier.inputs[1].default_value = (8.0, 8.0, 4.0)  # Multiplier values
    links.new(group_input.outputs['Spacing'], spacing_multiplier.inputs[0])
    
    # --- Point Generation Logic ---

    # Separate Spacing (now using multiplied spacing)
    separate_xyz_spacing = nodes.new('ShaderNodeSeparateXYZ')
    links.new(spacing_multiplier.outputs['Vector'], separate_xyz_spacing.inputs['Vector'])

    # Create 2D grid using Mesh Line technique instead of Mesh Grid
    # This ensures consistent spacing between points

    # Step 1: Create a line of points along X axis with correct spacing
    line_x = nodes.new('GeometryNodeMeshLine')
    line_x.name = "Line X Points"
    line_x.mode = 'OFFSET'  # Use OFFSET mode for consistent spacing
    line_x.count_mode = 'TOTAL'
    links.new(group_input.outputs['Count X'], line_x.inputs['Count'])
    
    # Create offset vector for X axis (Spacing X, 0, 0)
    combine_x_offset = nodes.new('ShaderNodeCombineXYZ')
    links.new(separate_xyz_spacing.outputs['X'], combine_x_offset.inputs['X'])
    combine_x_offset.inputs['Y'].default_value = 0.0
    combine_x_offset.inputs['Z'].default_value = 0.0
    links.new(combine_x_offset.outputs['Vector'], line_x.inputs['Offset'])
    
    # Step 2: Create a line of points along Y axis with correct spacing
    line_y = nodes.new('GeometryNodeMeshLine')
    line_y.name = "Line Y Points"
    line_y.mode = 'OFFSET'
    line_y.count_mode = 'TOTAL'
    links.new(group_input.outputs['Count Y'], line_y.inputs['Count'])
    
    # Create offset vector for Y axis (0, Spacing Y, 0)
    combine_y_offset = nodes.new('ShaderNodeCombineXYZ')
    combine_y_offset.inputs['X'].default_value = 0.0
    links.new(separate_xyz_spacing.outputs['Y'], combine_y_offset.inputs['Y'])
    combine_y_offset.inputs['Z'].default_value = 0.0
    links.new(combine_y_offset.outputs['Vector'], line_y.inputs['Offset'])
    
    # Step 3: Instance line_x along line_y to create a 2D grid
    instance_x_on_y = nodes.new('GeometryNodeInstanceOnPoints')
    instance_x_on_y.name = "Instance X on Y"
    links.new(line_y.outputs['Mesh'], instance_x_on_y.inputs['Points'])
    links.new(line_x.outputs['Mesh'], instance_x_on_y.inputs['Instance'])
    
    # Realize the 2D grid instances
    realize_2d_grid = nodes.new('GeometryNodeRealizeInstances')
    realize_2d_grid.name = "Realize 2D Grid"
    links.new(instance_x_on_y.outputs['Instances'], realize_2d_grid.inputs['Geometry'])
    
    # Step 4: Create a line along Z axis with correct spacing
    line_z = nodes.new('GeometryNodeMeshLine')
    line_z.name = "Line Z Points"
    line_z.mode = 'OFFSET'
    line_z.count_mode = 'TOTAL'
    links.new(group_input.outputs['Count Z'], line_z.inputs['Count'])
    
    # Create offset vector for Z axis (0, 0, Spacing Z)
    combine_z_offset = nodes.new('ShaderNodeCombineXYZ')
    combine_z_offset.inputs['X'].default_value = 0.0
    combine_z_offset.inputs['Y'].default_value = 0.0
    links.new(separate_xyz_spacing.outputs['Z'], combine_z_offset.inputs['Z'])
    links.new(combine_z_offset.outputs['Vector'], line_z.inputs['Offset'])
    
    # Step 5: Instance the 2D grid along the Z line to create a 3D grid
    instance_2d_on_z = nodes.new('GeometryNodeInstanceOnPoints')
    instance_2d_on_z.name = "Instance 2D on Z"
    links.new(line_z.outputs['Mesh'], instance_2d_on_z.inputs['Points'])
    links.new(realize_2d_grid.outputs['Geometry'], instance_2d_on_z.inputs['Instance'])
    
    # Realize the 3D grid instances
    realize_3d_grid = nodes.new('GeometryNodeRealizeInstances')
    realize_3d_grid.name = "Realize 3D Grid"
    links.new(instance_2d_on_z.outputs['Instances'], realize_3d_grid.inputs['Geometry'])
    
    # Switch between 2D grid (if Count Z = 1) and 3D grid (if Count Z > 1)
    compare_z_count = nodes.new('FunctionNodeCompare')
    compare_z_count.data_type = 'INT'
    compare_z_count.operation = 'GREATER_THAN'
    compare_z_count.inputs[3].default_value = 1  # Compare with 1
    links.new(group_input.outputs['Count Z'], compare_z_count.inputs[2])  # Input A
    
    switch_points = nodes.new('GeometryNodeSwitch')
    switch_points.name = "Switch 2D/3D Points"
    switch_points.input_type = 'GEOMETRY'
    links.new(compare_z_count.outputs['Result'], switch_points.inputs['Switch'])
    links.new(realize_2d_grid.outputs['Geometry'], switch_points.inputs[False])  # Use 2D if Count Z = 1
    links.new(realize_3d_grid.outputs['Geometry'], switch_points.inputs[True])  # Use 3D if Count Z > 1
    
    # --- Centering Logic ---
    # Calculate offset for centering the grid based on the total size
    
    # Calculate X size: (Count X - 1) * Spacing X
    count_x_minus_one = nodes.new('ShaderNodeMath')
    count_x_minus_one.operation = 'SUBTRACT'
    count_x_minus_one.inputs[1].default_value = 1.0
    links.new(group_input.outputs['Count X'], count_x_minus_one.inputs[0])
    
    total_size_x = nodes.new('ShaderNodeMath')
    total_size_x.operation = 'MULTIPLY'
    links.new(count_x_minus_one.outputs['Value'], total_size_x.inputs[0])
    links.new(separate_xyz_spacing.outputs['X'], total_size_x.inputs[1])
    
    # Calculate Y size: (Count Y - 1) * Spacing Y
    count_y_minus_one = nodes.new('ShaderNodeMath')
    count_y_minus_one.operation = 'SUBTRACT'
    count_y_minus_one.inputs[1].default_value = 1.0
    links.new(group_input.outputs['Count Y'], count_y_minus_one.inputs[0])
    
    total_size_y = nodes.new('ShaderNodeMath')
    total_size_y.operation = 'MULTIPLY'
    links.new(count_y_minus_one.outputs['Value'], total_size_y.inputs[0])
    links.new(separate_xyz_spacing.outputs['Y'], total_size_y.inputs[1])
    
    # Calculate Z size: (Count Z - 1) * Spacing Z
    count_z_minus_one = nodes.new('ShaderNodeMath')
    count_z_minus_one.operation = 'SUBTRACT'
    count_z_minus_one.inputs[1].default_value = 1.0
    links.new(group_input.outputs['Count Z'], count_z_minus_one.inputs[0])
    
    total_size_z = nodes.new('ShaderNodeMath')
    total_size_z.operation = 'MULTIPLY'
    links.new(count_z_minus_one.outputs['Value'], total_size_z.inputs[0])
    links.new(separate_xyz_spacing.outputs['Z'], total_size_z.inputs[1])
    
    # Calculate center offset (half of total size)
    center_offset_x = nodes.new('ShaderNodeMath')
    center_offset_x.operation = 'DIVIDE'
    center_offset_x.inputs[1].default_value = 2.0
    links.new(total_size_x.outputs['Value'], center_offset_x.inputs[0])
    
    center_offset_y = nodes.new('ShaderNodeMath')
    center_offset_y.operation = 'DIVIDE'
    center_offset_y.inputs[1].default_value = 2.0
    links.new(total_size_y.outputs['Value'], center_offset_y.inputs[0])
    
    center_offset_z = nodes.new('ShaderNodeMath')
    center_offset_z.operation = 'DIVIDE'
    center_offset_z.inputs[1].default_value = 2.0
    links.new(total_size_z.outputs['Value'], center_offset_z.inputs[0])
    
    # Combine center offset
    center_offset = nodes.new('ShaderNodeCombineXYZ')
    links.new(center_offset_x.outputs['Value'], center_offset.inputs['X'])
    links.new(center_offset_y.outputs['Value'], center_offset.inputs['Y'])
    links.new(center_offset_z.outputs['Value'], center_offset.inputs['Z'])
    
    # Negate for correct offset direction
    negate_center = nodes.new('ShaderNodeVectorMath')
    negate_center.operation = 'MULTIPLY'
    negate_center.inputs[1].default_value = (-1.0, -1.0, -1.0)
    links.new(center_offset.outputs['Vector'], negate_center.inputs[0])
    
    # Create zero vector for non-centered option
    zero_vector = nodes.new('ShaderNodeCombineXYZ')
    zero_vector.inputs[0].default_value = 0.0
    zero_vector.inputs[1].default_value = 0.0
    zero_vector.inputs[2].default_value = 0.0
    
    # Switch between centered and non-centered based on Center Grid option
    center_switch = nodes.new('GeometryNodeSwitch')
    center_switch.input_type = 'VECTOR'
    links.new(group_input.outputs['Center Grid'], center_switch.inputs[0])  # Switch
    links.new(zero_vector.outputs['Vector'], center_switch.inputs[False])  # No centering
    links.new(negate_center.outputs['Vector'], center_switch.inputs[True])  # With centering
    
    # Apply the centering offset to the grid points
    set_grid_center = nodes.new('GeometryNodeSetPosition')
    set_grid_center.name = "Center Grid Points"
    links.new(switch_points.outputs['Output'], set_grid_center.inputs['Geometry'])
    links.new(center_switch.outputs['Output'], set_grid_center.inputs['Offset'])
    
    # --- Instance Final Geometry ---
    # Instance the input geometry onto the grid points
    instance_final_geo = nodes.new('GeometryNodeInstanceOnPoints')
    instance_final_geo.name = "Instance Final Geometry"
    links.new(set_grid_center.outputs['Geometry'], instance_final_geo.inputs['Points'])
    links.new(group_input.outputs['Geometry'], instance_final_geo.inputs['Instance'])
    
    # Get index for random values (moved up for use with random instances)
    index = nodes.new('GeometryNodeInputIndex')
    
    # --- Pick Random Instance Logic (if input is a collection) ---
    pick_instance_random = nodes.new('GeometryNodeInstanceOnPoints')
    pick_instance_random.name = "Pick Random Instance"
    
    # Random Index for picking instance
    random_instance_index = nodes.new('FunctionNodeRandomValue')
    random_instance_index.data_type = 'INT'
    links.new(group_input.outputs['Random Seed'], random_instance_index.inputs['Seed'])
    links.new(index.outputs['Index'], random_instance_index.inputs['ID'])
    
    # Connect points and geometry
    links.new(set_grid_center.outputs['Geometry'], pick_instance_random.inputs['Points'])
    links.new(group_input.outputs['Geometry'], pick_instance_random.inputs['Instance'])
    
    # Switch between normal instancing and random pick instancing
    switch_instancing = nodes.new('GeometryNodeSwitch')
    switch_instancing.name = "Switch Instance Mode"
    switch_instancing.input_type = 'GEOMETRY'
    links.new(group_input.outputs['Pick Random Instance'], switch_instancing.inputs['Switch'])
    links.new(instance_final_geo.outputs['Instances'], switch_instancing.inputs[False])
    links.new(pick_instance_random.outputs['Instances'], switch_instancing.inputs[True])

    # --- Randomization and Transforms (Applied to Final Instances) ---
    # Random values nodes
    random_position_node = nodes.new('FunctionNodeRandomValue')
    random_position_node.data_type = 'FLOAT_VECTOR'

    random_rotation_node = nodes.new('FunctionNodeRandomValue')
    random_rotation_node.data_type = 'FLOAT_VECTOR'

    random_scale_node = nodes.new('FunctionNodeRandomValue')
    random_scale_node.data_type = 'FLOAT' # Single float for uniform random scale

    # Vector math for negative ranges (to center the random range around 0)
    vector_math_neg_pos = nodes.new('ShaderNodeVectorMath')
    vector_math_neg_pos.operation = 'MULTIPLY'
    vector_math_neg_pos.inputs[1].default_value = (-1.0, -1.0, -1.0)
    links.new(group_input.outputs['Random Position'], vector_math_neg_pos.inputs[0])

    vector_math_neg_rot = nodes.new('ShaderNodeVectorMath')
    vector_math_neg_rot.operation = 'MULTIPLY'
    vector_math_neg_rot.inputs[1].default_value = (-1.0, -1.0, -1.0)
    links.new(group_input.outputs['Random Rotation'], vector_math_neg_rot.inputs[0])

    # Math for negative random scale
    math_neg_scale = nodes.new('ShaderNodeMath')
    math_neg_scale.operation = 'MULTIPLY'
    math_neg_scale.inputs[1].default_value = -1.0
    links.new(group_input.outputs['Random Scale'], math_neg_scale.inputs[0])

    # Connect Seed and Index to random nodes
    links.new(group_input.outputs['Random Seed'], random_position_node.inputs['Seed'])
    links.new(group_input.outputs['Random Seed'], random_rotation_node.inputs['Seed'])
    links.new(group_input.outputs['Random Seed'], random_scale_node.inputs['Seed'])
    links.new(index.outputs['Index'], random_position_node.inputs['ID'])
    links.new(index.outputs['Index'], random_rotation_node.inputs['ID'])
    links.new(index.outputs['Index'], random_scale_node.inputs['ID'])

    # Set random ranges
    links.new(vector_math_neg_pos.outputs['Vector'], random_position_node.inputs['Min'])
    links.new(group_input.outputs['Random Position'], random_position_node.inputs['Max'])

    links.new(vector_math_neg_rot.outputs['Vector'], random_rotation_node.inputs['Min'])
    links.new(group_input.outputs['Random Rotation'], random_rotation_node.inputs['Max'])

    links.new(math_neg_scale.outputs['Value'], random_scale_node.inputs['Min'])
    links.new(group_input.outputs['Random Scale'], random_scale_node.inputs['Max'])

    # Apply Instance Transforms
    # Apply random position offset using Translate Instances
    translate_instances = nodes.new('GeometryNodeTranslateInstances')
    links.new(switch_instancing.outputs['Output'], translate_instances.inputs['Instances']) # Start with final instances
    links.new(random_position_node.outputs['Value'], translate_instances.inputs['Translation'])

    # Apply rotation (base + random) using Rotate Instances
    rotate_instances = nodes.new('GeometryNodeRotateInstances')
    add_random_rotation = nodes.new('ShaderNodeVectorMath')
    add_random_rotation.operation = 'ADD'
    links.new(translate_instances.outputs['Instances'], rotate_instances.inputs['Instances']) # Chain transforms
    links.new(group_input.outputs['Instance Rotation'], add_random_rotation.inputs[0]) # Base Rotation
    links.new(random_rotation_node.outputs['Value'], add_random_rotation.inputs[1]) # Random Rotation
    links.new(add_random_rotation.outputs['Vector'], rotate_instances.inputs['Rotation'])

    # Apply scale (base + random) using Scale Instances
    scale_instances = nodes.new('GeometryNodeScaleInstances')
    combine_xyz_rand_scale = nodes.new('ShaderNodeCombineXYZ')
    add_random_scale = nodes.new('ShaderNodeVectorMath')
    add_random_scale.operation = 'ADD'
    links.new(random_scale_node.outputs['Value'], combine_xyz_rand_scale.inputs['X'])
    links.new(random_scale_node.outputs['Value'], combine_xyz_rand_scale.inputs['Y'])
    links.new(random_scale_node.outputs['Value'], combine_xyz_rand_scale.inputs['Z'])
    links.new(rotate_instances.outputs['Instances'], scale_instances.inputs['Instances']) # Chain transforms
    links.new(group_input.outputs['Instance Scale'], add_random_scale.inputs[0]) # Base Scale Vector
    links.new(combine_xyz_rand_scale.outputs['Vector'], add_random_scale.inputs[1]) # Added Random Scale Vector
    links.new(add_random_scale.outputs['Vector'], scale_instances.inputs['Scale'])
    
    # --- Apply Material and Color ---
    # Set material with option to keep original
    set_material = nodes.new('GeometryNodeSetMaterial')
    links.new(scale_instances.outputs['Instances'], set_material.inputs['Geometry'])
    links.new(group_input.outputs['Material'], set_material.inputs['Material'])
    links.new(group_input.outputs['Keep Original Materials'], set_material.inputs['Selection'])
    
    # Apply global position directly to the material result
    global_translate = nodes.new('GeometryNodeTransform')
    links.new(set_material.outputs['Geometry'], global_translate.inputs['Geometry'])
    links.new(group_input.outputs['Global Position'], global_translate.inputs['Translation'])
    links.new(group_input.outputs['Global Rotation'], global_translate.inputs['Rotation'])

    # --- Final Output ---
    # Connect instances directly to output without realizing them
    links.new(global_translate.outputs['Geometry'], group_output.inputs['Geometry'])

    return node_group

def register():
    pass

def unregister():
    pass
