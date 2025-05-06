import bpy
import mathutils

def create_unique_name(base_name, existing_collection, counter_format="{}.{:03d}"):
    """Create a unique name in a collection by adding an incremental suffix if needed"""
    unique_name = base_name
    counter = 1
    while unique_name in existing_collection:
        unique_name = counter_format.format(base_name, counter)
        counter += 1
    return unique_name

def add_effector_sockets(node_group):
    """Add standard effector input sockets to a node group"""
    
    # Position influence
    position_influence = node_group.interface.new_socket(
        name="Position Influence", 
        in_out='INPUT', 
        socket_type='NodeSocketVector'
    )
    position_influence.default_value = (0.0, 0.0, 0.0)
    
    # Rotation influence
    rotation_influence = node_group.interface.new_socket(
        name="Rotation Influence", 
        in_out='INPUT', 
        socket_type='NodeSocketVector'
    )
    rotation_influence.default_value = (0.0, 0.0, 0.0)
    rotation_influence.subtype = 'EULER'
    
    # Scale influence
    scale_influence = node_group.interface.new_socket(
        name="Scale Influence", 
        in_out='INPUT', 
        socket_type='NodeSocketVector'
    )
    scale_influence.default_value = (1.0, 1.0, 1.0)
    
    return {
        "position": position_influence,
        "rotation": rotation_influence,
        "scale": scale_influence
    }

def create_independent_node_group(template_creator_func, base_node_name):
    """Create an independent copy of a node group using a template creator function"""
    # 1. Create template node group
    template_node_group = template_creator_func()
    if template_node_group is None:
        return None
    
    # 2. Create independent copy
    try:
        independent_node_group = template_node_group.copy()
    except Exception as e:
        print(f"Failed to copy node group: {e}")
        if template_node_group.users == 0:
            try:
                bpy.data.node_groups.remove(template_node_group, do_unlink=True)
            except Exception as remove_e:
                print(f"Warning: Could not remove template node group: {remove_e}")
        return None
    
    # 3. Remove template
    if template_node_group.users == 0:
        try:
            bpy.data.node_groups.remove(template_node_group, do_unlink=True)
        except Exception as e:
            print(f"Warning: Could not remove template node group: {e}")
    else:
        template_node_group.name += ".template"
        print(f"Warning: Template node group has users, renamed instead of removing.")
    
    # 4. Assign unique name to copy
    unique_node_name = create_unique_name(base_node_name, bpy.data.node_groups)
    independent_node_group.name = unique_node_name
    
    return independent_node_group