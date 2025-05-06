# src/effectors/GN_RandomEffector.py
import bpy
import mathutils

def randomeffector_node_group():
    """Create a random effector node group that applies random transformations to geometry"""
    
    # Create new node group
    node_group = bpy.data.node_groups.new(type='GeometryNodeTree', name="RandomEffector")
    
    # --- Interface ---
    # Output
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    # Inputs
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    
    # Strength
    enable_input = node_group.interface.new_socket(name="Enable", in_out='INPUT', socket_type='NodeSocketBool')
    enable_input.default_value = False
    
    strength_input = node_group.interface.new_socket(name="Strength", in_out='INPUT', socket_type='NodeSocketFloat')
    strength_input.default_value = 0.0
    strength_input.min_value = 0.0
    strength_input.max_value = 1.0
    
    # Transform controls
    position_input = node_group.interface.new_socket(name="Position", in_out='INPUT', socket_type='NodeSocketVector')
    position_input.default_value = (0.0, 0.0, 0.0)
    
    rotation_input = node_group.interface.new_socket(name="Rotation", in_out='INPUT', socket_type='NodeSocketVector')
    rotation_input.default_value = (0.0, 0.0, 0.0)
    rotation_input.subtype = 'EULER'
    
    scale_input = node_group.interface.new_socket(name="Scale", in_out='INPUT', socket_type='NodeSocketVector')
    scale_input.default_value = (0.0, 0.0, 0.0)
    
    uniform_scale_input = node_group.interface.new_socket(name="Uniform Scale", in_out='INPUT', socket_type='NodeSocketBool')
    uniform_scale_input.default_value = True
    
    # Seed and ID control
    seed_input = node_group.interface.new_socket(name="Seed", in_out='INPUT', socket_type='NodeSocketInt')
    seed_input.default_value = 0
    seed_input.min_value = 0
    
    # --- Nodes ---
    nodes = node_group.nodes
    links = node_group.links
    
    group_input = nodes.new('NodeGroupInput')
    group_output = nodes.new('NodeGroupOutput')
    
    # Basic switch for enabling/disabling the effector
    switch = nodes.new('GeometryNodeSwitch')
    switch.input_type = 'GEOMETRY'
    links.new(group_input.outputs['Enable'], switch.inputs[0])  # Switch
    links.new(group_input.outputs['Geometry'], switch.inputs[2])  # False (bypass)
    
    # Get index for random per-instance values
    index = nodes.new('GeometryNodeInputIndex')
    
    # Random position
    random_position = nodes.new('FunctionNodeRandomValue')
    random_position.data_type = 'FLOAT_VECTOR'
    
    # Link seed and ID
    links.new(group_input.outputs['Seed'], random_position.inputs['Seed'])
    links.new(index.outputs['Index'], random_position.inputs['ID'])
    
    # Set random position range (-Position to +Position)
    vector_math_neg = nodes.new('ShaderNodeVectorMath')
    vector_math_neg.operation = 'MULTIPLY'
    vector_math_neg.inputs[1].default_value = (-1.0, -1.0, -1.0)
    links.new(group_input.outputs['Position'], vector_math_neg.inputs[0])
    
    links.new(vector_math_neg.outputs['Vector'], random_position.inputs['Min'])
    links.new(group_input.outputs['Position'], random_position.inputs['Max'])
    
    # Random rotation
    random_rotation = nodes.new('FunctionNodeRandomValue')
    random_rotation.data_type = 'FLOAT_VECTOR'
    
    # Link seed and ID
    links.new(group_input.outputs['Seed'], random_rotation.inputs['Seed'])
    links.new(index.outputs['Index'], random_rotation.inputs['ID'])
    
    # Set rotation range (-Rotation to +Rotation)
    vector_math_neg_rot = nodes.new('ShaderNodeVectorMath')
    vector_math_neg_rot.operation = 'MULTIPLY'
    vector_math_neg_rot.inputs[1].default_value = (-1.0, -1.0, -1.0)
    links.new(group_input.outputs['Rotation'], vector_math_neg_rot.inputs[0])
    
    links.new(vector_math_neg_rot.outputs['Vector'], random_rotation.inputs['Min'])
    links.new(group_input.outputs['Rotation'], random_rotation.inputs['Max'])
    
    # Random scale
    random_scale = nodes.new('FunctionNodeRandomValue')
    random_scale.data_type = 'FLOAT_VECTOR'
    
    # For uniform scale
    random_uniform_scale = nodes.new('FunctionNodeRandomValue')
    random_uniform_scale.data_type = 'FLOAT'
    
    # Link seed and ID
    links.new(group_input.outputs['Seed'], random_scale.inputs['Seed'])
    links.new(index.outputs['Index'], random_scale.inputs['ID'])
    links.new(group_input.outputs['Seed'], random_uniform_scale.inputs['Seed'])
    links.new(index.outputs['Index'], random_uniform_scale.inputs['ID'])
    
    # Set scale range (1-Scale to 1+Scale)
    one_minus_scale = nodes.new('ShaderNodeVectorMath')
    one_minus_scale.operation = 'SUBTRACT'
    one_minus_scale.inputs[0].default_value = (1.0, 1.0, 1.0)
    links.new(group_input.outputs['Scale'], one_minus_scale.inputs[1])
    
    one_plus_scale = nodes.new('ShaderNodeVectorMath')
    one_plus_scale.operation = 'ADD'
    one_plus_scale.inputs[0].default_value = (1.0, 1.0, 1.0)
    links.new(group_input.outputs['Scale'], one_plus_scale.inputs[1])
    
    links.new(one_minus_scale.outputs['Vector'], random_scale.inputs['Min'])
    links.new(one_plus_scale.outputs['Vector'], random_scale.inputs['Max'])
    
    # For uniform scale (single float)
    scale_max = nodes.new('ShaderNodeMath')
    scale_max.operation = 'MAXIMUM'
    links.new(group_input.outputs['Scale'], scale_max.inputs[0])  # X
    scale_max_temp = nodes.new('ShaderNodeMath')
    scale_max_temp.operation = 'MAXIMUM'
    links.new(group_input.outputs['Scale'], scale_max_temp.inputs[0])  # Y
    links.new(group_input.outputs['Scale'], scale_max_temp.inputs[1])  # Z
    links.new(scale_max_temp.outputs[0], scale_max.inputs[1])
    
    one_minus_uniform = nodes.new('ShaderNodeMath')
    one_minus_uniform.operation = 'SUBTRACT'
    one_minus_uniform.inputs[0].default_value = 1.0
    links.new(scale_max.outputs[0], one_minus_uniform.inputs[1])
    
    one_plus_uniform = nodes.new('ShaderNodeMath')
    one_plus_uniform.operation = 'ADD'
    one_plus_uniform.inputs[0].default_value = 1.0
    links.new(scale_max.outputs[0], one_plus_uniform.inputs[1])
    
    links.new(one_minus_uniform.outputs[0], random_uniform_scale.inputs['Min'])
    links.new(one_plus_uniform.outputs[0], random_uniform_scale.inputs['Max'])
    
    # Switch between uniform and non-uniform scale
    scale_switch = nodes.new('GeometryNodeSwitch')
    scale_switch.input_type = 'VECTOR'
    links.new(group_input.outputs['Uniform Scale'], scale_switch.inputs[0])  # Switch
    links.new(random_scale.outputs['Value'], scale_switch.inputs['False'])  # False (vector scale)
    
    # Create uniform scale vector
    uniform_vector = nodes.new('ShaderNodeCombineXYZ')
    links.new(random_uniform_scale.outputs['Value'], uniform_vector.inputs['X'])
    links.new(random_uniform_scale.outputs['Value'], uniform_vector.inputs['Y'])
    links.new(random_uniform_scale.outputs['Value'], uniform_vector.inputs['Z'])
    
    links.new(uniform_vector.outputs['Vector'], scale_switch.inputs['True'])  # True (uniform scale)
    
    # Apply global strength multiplier to position and rotation
    strength_mul_pos = nodes.new('ShaderNodeVectorMath')
    strength_mul_pos.operation = 'MULTIPLY'
    links.new(random_position.outputs['Value'], strength_mul_pos.inputs[0])
    links.new(group_input.outputs['Strength'], strength_mul_pos.inputs[1])  # Strength
    
    strength_mul_rot = nodes.new('ShaderNodeVectorMath')
    strength_mul_rot.operation = 'MULTIPLY'
    links.new(random_rotation.outputs['Value'], strength_mul_rot.inputs[0])
    links.new(group_input.outputs['Strength'], strength_mul_rot.inputs[1])  # Strength
    
    # Apply transformations to instances
    # Start with the input geometry
    translate_instances = nodes.new('GeometryNodeTranslateInstances')
    links.new(group_input.outputs['Geometry'], translate_instances.inputs['Instances'])
    links.new(strength_mul_pos.outputs['Vector'], translate_instances.inputs['Translation'])
    
    # Rotate instances
    rotate_instances = nodes.new('GeometryNodeRotateInstances')
    links.new(translate_instances.outputs['Instances'], rotate_instances.inputs['Instances'])
    links.new(strength_mul_rot.outputs['Vector'], rotate_instances.inputs['Rotation'])
    
    # Scale instances
    scale_instances = nodes.new('GeometryNodeScaleInstances')
    links.new(rotate_instances.outputs['Instances'], scale_instances.inputs['Instances'])
    links.new(scale_switch.outputs['Output'], scale_instances.inputs['Scale'])
    
    # Connect the transformed geometry to the switch (if enabled)
    links.new(scale_instances.outputs['Instances'], switch.inputs['True'])  # True (with effect)
    
    # Output
    links.new(switch.outputs['Output'], group_output.inputs['Geometry'])
    
    return node_group

def register():
    pass

def unregister():
    pass