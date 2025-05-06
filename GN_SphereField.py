import bpy

def simplest_spherefield_node_group():
    """Создаёт максимально простую версию нод-группы поля"""
    # Создаем новую нод-группу
    node_group = bpy.data.node_groups.new(
        type='GeometryNodeTree',
        name="SphereField"
    )
    
    # Добавляем минимальный интерфейс
    # Выходы
    # ВАЖНО: Geometry должен быть ПЕРВЫМ выходом
    geo_out = node_group.interface.new_socket(
        name="Geometry", 
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )
    
    value_socket = node_group.interface.new_socket(
        name="Value", 
        in_out='OUTPUT',
        socket_type='NodeSocketFloat'
    )
    
    # Входы 
    geo_in = node_group.interface.new_socket(
        name="Geometry", 
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )
    
    # Создаем ноды
    nodes = node_group.nodes
    links = node_group.links
    
    # Входной и выходной узлы
    input_node = nodes.new('NodeGroupInput')
    output_node = nodes.new('NodeGroupOutput')
    
    # Просто прокидываем геометрию без изменений
    links.new(input_node.outputs["Geometry"], output_node.inputs["Geometry"])
    
    # Создаем константный узел со значением 1.0
    value_node = nodes.new('ShaderNodeValue')
    value_node.outputs[0].default_value = 1.0
    links.new(value_node.outputs[0], output_node.inputs["Value"])
    
    return node_group

def advanced_spherefield_node_group():
    """Создаёт продвинутую версию нод-группы сферического поля"""
    sphere_field = bpy.data.node_groups.new(type='GeometryNodeTree', name="SphereField")

    sphere_field.color_tag = 'NONE'
    sphere_field.description = ""
    sphere_field.default_group_node_width = 140
    sphere_field.is_modifier = True

    # Сперва добавляем ОБЯЗАТЕЛЬНЫЙ выход Geometry
    geo_out = sphere_field.interface.new_socket(
        name="Geometry", 
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )
    
    # Добавляем обязательный вход Geometry
    geo_in = sphere_field.interface.new_socket(
        name="Geometry", 
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )

    # Далее интерфейс из примера
    # Socket Field
    field_socket = sphere_field.interface.new_socket(name="Field", in_out='OUTPUT', socket_type='NodeSocketFloat')
    field_socket.default_value = 0.0
    field_socket.min_value = -3.4028234663852886e+38
    field_socket.max_value = 3.4028234663852886e+38
    field_socket.subtype = 'NONE'
    field_socket.attribute_domain = 'POINT'

    # Socket Sphere
    sphere_socket = sphere_field.interface.new_socket(name="Sphere", in_out='INPUT', socket_type='NodeSocketObject')
    sphere_socket.attribute_domain = 'POINT'

    # Socket Falloff
    falloff_socket = sphere_field.interface.new_socket(name="Falloff", in_out='INPUT', socket_type='NodeSocketFloat')
    falloff_socket.default_value = 0.0
    falloff_socket.min_value = 0.0
    falloff_socket.max_value = 1.0
    falloff_socket.subtype = 'NONE'
    falloff_socket.attribute_domain = 'POINT'

    # Socket Inner Strength
    inner_strength_socket = sphere_field.interface.new_socket(name="Inner Strength", in_out='INPUT', socket_type='NodeSocketFloat')
    inner_strength_socket.default_value = 1.0
    inner_strength_socket.min_value = 0.0
    inner_strength_socket.max_value = 1.0
    inner_strength_socket.subtype = 'NONE'
    inner_strength_socket.attribute_domain = 'POINT'

    # Socket Outer Strength
    outer_strength_socket = sphere_field.interface.new_socket(name="Outer Strength", in_out='INPUT', socket_type='NodeSocketFloat')
    outer_strength_socket.default_value = 0.0
    outer_strength_socket.min_value = 0.0
    outer_strength_socket.max_value = 1.0
    outer_strength_socket.subtype = 'NONE'
    outer_strength_socket.attribute_domain = 'POINT'

    # Panel Interpolation
    interpolation_panel = sphere_field.interface.new_panel("Interpolation")
    # Socket Mode
    mode_socket = sphere_field.interface.new_socket(name="Mode", in_out='INPUT', socket_type='NodeSocketMenu', parent=interpolation_panel)
    mode_socket.attribute_domain = 'POINT'

    # Socket Strength
    strength_socket = sphere_field.interface.new_socket(name="Strength", in_out='INPUT', socket_type='NodeSocketFloat', parent=interpolation_panel)
    strength_socket.default_value = 0.0
    strength_socket.min_value = 0.0
    strength_socket.max_value = 1.0
    strength_socket.subtype = 'NONE'
    strength_socket.attribute_domain = 'POINT'
    strength_socket.description = "0 = Linear"

    # Создаем ноды
    # node Object Info
    object_info = sphere_field.nodes.new("GeometryNodeObjectInfo")
    object_info.name = "Object Info"
    object_info.transform_space = 'ORIGINAL'
    # As Instance
    object_info.inputs[1].default_value = False

    # node Position
    position = sphere_field.nodes.new("GeometryNodeInputPosition")
    position.name = "Position"

    # node Vector Math
    vector_math = sphere_field.nodes.new("ShaderNodeVectorMath")
    vector_math.name = "Vector Math"
    vector_math.operation = 'DISTANCE'

    # node Separate XYZ
    separate_xyz = sphere_field.nodes.new("ShaderNodeSeparateXYZ")
    separate_xyz.name = "Separate XYZ"

    # node Map Range
    map_range = sphere_field.nodes.new("ShaderNodeMapRange")
    map_range.name = "Map Range"
    map_range.clamp = True
    map_range.data_type = 'FLOAT'
    map_range.interpolation_type = 'LINEAR'
    # To Min
    map_range.inputs[3].default_value = 0.0
    # To Max
    map_range.inputs[4].default_value = 1.0

    # node Map Range.001
    map_range_001 = sphere_field.nodes.new("ShaderNodeMapRange")
    map_range_001.name = "Map Range.001"
    map_range_001.clamp = True
    map_range_001.data_type = 'FLOAT'
    map_range_001.interpolation_type = 'LINEAR'
    # From Min
    map_range_001.inputs[1].default_value = 0.0
    # From Max
    map_range_001.inputs[2].default_value = 1.0
    # To Min
    map_range_001.inputs[3].default_value = 0.0

    # node Math
    math = sphere_field.nodes.new("ShaderNodeMath")
    math.name = "Math"
    math.operation = 'MULTIPLY'
    math.use_clamp = False
    # Value_001
    math.inputs[1].default_value = 0.9990000128746033

    # node Group Input
    group_input = sphere_field.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    # node Group Output
    group_output = sphere_field.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    # node Math.001
    math_001 = sphere_field.nodes.new("ShaderNodeMath")
    math_001.name = "Math.001"
    math_001.operation = 'DIVIDE'
    math_001.use_clamp = False
    # Value_001
    math_001.inputs[1].default_value = 0.5

    # node Vector Math.001
    vector_math_001 = sphere_field.nodes.new("ShaderNodeVectorMath")
    vector_math_001.name = "Vector Math.001"
    vector_math_001.operation = 'ABSOLUTE'

    # node Vector Math.002
    vector_math_002 = sphere_field.nodes.new("ShaderNodeVectorMath")
    vector_math_002.name = "Vector Math.002"
    vector_math_002.operation = 'SCALE'
    # Scale
    vector_math_002.inputs[3].default_value = 2.0

    # node Float Curve
    float_curve = sphere_field.nodes.new("ShaderNodeFloatCurve")
    float_curve.name = "Float Curve"
    # mapping settings
    float_curve.mapping.extend = 'EXTRAPOLATED'
    float_curve.mapping.tone = 'STANDARD'
    float_curve.mapping.black_level = (0.0, 0.0, 0.0)
    float_curve.mapping.white_level = (1.0, 1.0, 1.0)
    float_curve.mapping.clip_min_x = 0.0
    float_curve.mapping.clip_min_y = 0.0
    float_curve.mapping.clip_max_x = 1.0
    float_curve.mapping.clip_max_y = 1.0
    float_curve.mapping.use_clip = True
    # curve 0
    float_curve_curve_0 = float_curve.mapping.curves[0]
    float_curve_curve_0_point_0 = float_curve_curve_0.points[0]
    float_curve_curve_0_point_0.location = (0.0, 0.0)
    float_curve_curve_0_point_0.handle_type = 'AUTO'
    float_curve_curve_0_point_1 = float_curve_curve_0.points[1]
    float_curve_curve_0_point_1.location = (0.2500000298023224, 0.125)
    float_curve_curve_0_point_1.handle_type = 'AUTO'
    float_curve_curve_0_point_2 = float_curve_curve_0.points.new(0.75, 0.875)
    float_curve_curve_0_point_2.handle_type = 'AUTO'
    float_curve_curve_0_point_3 = float_curve_curve_0.points.new(1.0, 1.0)
    float_curve_curve_0_point_3.handle_type = 'AUTO'
    # update curve after changes
    float_curve.mapping.update()

    # node Float Curve.001
    float_curve_001 = sphere_field.nodes.new("ShaderNodeFloatCurve")
    float_curve_001.name = "Float Curve.001"
    # mapping settings
    float_curve_001.mapping.extend = 'EXTRAPOLATED'
    float_curve_001.mapping.tone = 'STANDARD'
    float_curve_001.mapping.black_level = (0.0, 0.0, 0.0)
    float_curve_001.mapping.white_level = (1.0, 1.0, 1.0)
    float_curve_001.mapping.clip_min_x = 0.0
    float_curve_001.mapping.clip_min_y = 0.0
    float_curve_001.mapping.clip_max_x = 1.0
    float_curve_001.mapping.clip_max_y = 1.0
    float_curve_001.mapping.use_clip = True
    # curve 0
    float_curve_001_curve_0 = float_curve_001.mapping.curves[0]
    float_curve_001_curve_0_point_0 = float_curve_001_curve_0.points[0]
    float_curve_001_curve_0_point_0.location = (0.0, 0.0)
    float_curve_001_curve_0_point_0.handle_type = 'AUTO'
    float_curve_001_curve_0_point_1 = float_curve_001_curve_0.points[1]
    float_curve_001_curve_0_point_1.location = (0.5, 0.15000000596046448)
    float_curve_001_curve_0_point_1.handle_type = 'AUTO'
    float_curve_001_curve_0_point_2 = float_curve_001_curve_0.points.new(1.0, 1.0)
    float_curve_001_curve_0_point_2.handle_type = 'AUTO'
    # update curve after changes
    float_curve_001.mapping.update()

    # node Menu Switch
    menu_switch = sphere_field.nodes.new("GeometryNodeMenuSwitch")
    menu_switch.name = "Menu Switch"
    menu_switch.active_index = 2
    menu_switch.data_type = 'FLOAT'
    menu_switch.enum_items.clear()
    menu_switch.enum_items.new("S-Curve")
    menu_switch.enum_items[0].description = ""
    menu_switch.enum_items.new("Ease In")
    menu_switch.enum_items[1].description = ""
    menu_switch.enum_items.new("Ease Out")
    menu_switch.enum_items[2].description = ""

    # node Float Curve.002
    float_curve_002 = sphere_field.nodes.new("ShaderNodeFloatCurve")
    float_curve_002.name = "Float Curve.002"
    # mapping settings
    float_curve_002.mapping.extend = 'EXTRAPOLATED'
    float_curve_002.mapping.tone = 'STANDARD'
    float_curve_002.mapping.black_level = (0.0, 0.0, 0.0)
    float_curve_002.mapping.white_level = (1.0, 1.0, 1.0)
    float_curve_002.mapping.clip_min_x = 0.0
    float_curve_002.mapping.clip_min_y = 0.0
    float_curve_002.mapping.clip_max_x = 1.0
    float_curve_002.mapping.clip_max_y = 1.0
    float_curve_002.mapping.use_clip = True
    # curve 0
    float_curve_002_curve_0 = float_curve_002.mapping.curves[0]
    float_curve_002_curve_0_point_0 = float_curve_002_curve_0.points[0]
    float_curve_002_curve_0_point_0.location = (0.0, 0.0)
    float_curve_002_curve_0_point_0.handle_type = 'AUTO'
    float_curve_002_curve_0_point_1 = float_curve_002_curve_0.points[1]
    float_curve_002_curve_0_point_1.location = (0.5, 0.8500000238418579)
    float_curve_002_curve_0_point_1.handle_type = 'AUTO'
    float_curve_002_curve_0_point_2 = float_curve_002_curve_0.points.new(1.0, 1.0)
    float_curve_002_curve_0_point_2.handle_type = 'AUTO'
    # update curve after changes
    float_curve_002.mapping.update()

    # node Map Range.003
    map_range_003 = sphere_field.nodes.new("ShaderNodeMapRange")
    map_range_003.name = "Map Range.003"
    map_range_003.clamp = True
    map_range_003.data_type = 'FLOAT'
    map_range_003.interpolation_type = 'LINEAR'
    # From Min
    map_range_003.inputs[1].default_value = 0.0
    # From Max
    map_range_003.inputs[2].default_value = 1.0

    # Set locations
    object_info.location = (-209.4088897705078, -151.8125)
    position.location = (-206.02076721191406, -93.03483581542969)
    vector_math.location = (-18.321346282958984, -107.2778549194336)
    separate_xyz.location = (-20.14255142211914, -245.765625)
    map_range.location = (681.0960693359375, -98.4025650024414)
    map_range_001.location = (374.06707763671875, -309.86920166015625)
    math.location = (166.3639678955078, -365.9002990722656)
    group_input.location = (-441.130859375, -1.1997389793395996)
    group_output.location = (2129.137451171875, -277.3480224609375)
    math_001.location = (252.32833862304688, -110.31519317626953)
    vector_math_001.location = (-240.23388671875, -398.0293884277344)
    vector_math_002.location = (-42.46455764770508, -397.5208435058594)
    float_curve.location = (1087.6787109375, 41.6961669921875)
    float_curve_001.location = (1094.581298828125, -313.67828369140625)
    menu_switch.location = (1599.4703369140625, -289.85516357421875)
    float_curve_002.location = (1100.2386474609375, -672.5582885742188)
    map_range_003.location = (1874.29638671875, -273.31591796875)

    # Set dimensions
    object_info.width, object_info.height = 140.0, 100.0
    position.width, position.height = 140.0, 100.0
    vector_math.width, vector_math.height = 140.0, 100.0
    separate_xyz.width, separate_xyz.height = 140.0, 100.0
    map_range.width, map_range.height = 140.0, 100.0
    map_range_001.width, map_range_001.height = 140.0, 100.0
    math.width, math.height = 140.0, 100.0
    group_input.width, group_input.height = 140.0, 100.0
    group_output.width, group_output.height = 140.0, 100.0
    math_001.width, math_001.height = 140.0, 100.0
    vector_math_001.width, vector_math_001.height = 140.0, 100.0
    vector_math_002.width, vector_math_002.height = 140.0, 100.0
    float_curve.width, float_curve.height = 240.0, 100.0
    float_curve_001.width, float_curve_001.height = 251.041748046875, 100.0
    menu_switch.width, menu_switch.height = 140.0, 100.0
    float_curve_002.width, float_curve_002.height = 240.0, 100.0
    map_range_003.width, map_range_003.height = 140.0, 100.0

    # Initialize links
    # Прокидываем геометрию (обязательно для модификаторов)
    sphere_field.links.new(group_input.outputs["Geometry"], group_output.inputs["Geometry"])
    
    # Ссылки из примера
    # group_input.Sphere -> object_info.Object
    sphere_field.links.new(group_input.outputs["Sphere"], object_info.inputs[0])
    # position.Position -> vector_math.Vector
    sphere_field.links.new(position.outputs[0], vector_math.inputs[0])
    # object_info.Location -> vector_math.Vector
    sphere_field.links.new(object_info.outputs[1], vector_math.inputs[1])
    # math_001.Value -> map_range.Value
    sphere_field.links.new(math_001.outputs[0], map_range.inputs[0])
    # separate_xyz.X -> map_range.From Min
    sphere_field.links.new(separate_xyz.outputs[0], map_range.inputs[1])
    # separate_xyz.X -> math.Value
    sphere_field.links.new(separate_xyz.outputs[0], math.inputs[0])
    # math.Value -> map_range_001.To Max
    sphere_field.links.new(math.outputs[0], map_range_001.inputs[4])
    # group_input.Falloff -> map_range_001.Value
    sphere_field.links.new(group_input.outputs["Falloff"], map_range_001.inputs[0])
    # map_range_001.Result -> map_range.From Max
    sphere_field.links.new(map_range_001.outputs[0], map_range.inputs[2])
    # vector_math.Value -> math_001.Value
    sphere_field.links.new(vector_math.outputs[1], math_001.inputs[0])
    # object_info.Scale -> vector_math_001.Vector
    sphere_field.links.new(object_info.outputs[3], vector_math_001.inputs[0])
    # vector_math_001.Vector -> vector_math_002.Vector
    sphere_field.links.new(vector_math_001.outputs[0], vector_math_002.inputs[0])
    # vector_math_002.Vector -> separate_xyz.Vector
    sphere_field.links.new(vector_math_002.outputs[0], separate_xyz.inputs[0])
    # float_curve.Value -> menu_switch.S-Curve
    sphere_field.links.new(float_curve.outputs[0], menu_switch.inputs[1])
    # float_curve_002.Value -> menu_switch.Ease In
    sphere_field.links.new(float_curve_002.outputs[0], menu_switch.inputs[2])
    # float_curve_001.Value -> menu_switch.Ease Out
    sphere_field.links.new(float_curve_001.outputs[0], menu_switch.inputs[3])
    # menu_switch.Output -> map_range_003.Value
    sphere_field.links.new(menu_switch.outputs[0], map_range_003.inputs[0])
    # group_input.Outer Strength -> map_range_003.To Min
    sphere_field.links.new(group_input.outputs["Outer Strength"], map_range_003.inputs[3])
    # group_input.Inner Strength -> map_range_003.To Max
    sphere_field.links.new(group_input.outputs["Inner Strength"], map_range_003.inputs[4])
    # map_range_003.Result -> group_output.Field
    sphere_field.links.new(map_range_003.outputs[0], group_output.inputs["Field"])
    # group_input.Mode -> menu_switch.Menu
    sphere_field.links.new(group_input.outputs["Mode"], menu_switch.inputs[0])
    # group_input.Strength -> float_curve.Factor
    sphere_field.links.new(group_input.outputs["Strength"], float_curve.inputs[0])
    # group_input.Strength -> float_curve_001.Factor
    sphere_field.links.new(group_input.outputs["Strength"], float_curve_001.inputs[0])
    # group_input.Strength -> float_curve_002.Factor
    sphere_field.links.new(group_input.outputs["Strength"], float_curve_002.inputs[0])
    # map_range.Result -> float_curve.Value
    sphere_field.links.new(map_range.outputs[0], float_curve.inputs[1])
    # map_range.Result -> float_curve_001.Value
    sphere_field.links.new(map_range.outputs[0], float_curve_001.inputs[1])
    # map_range.Result -> float_curve_002.Value
    sphere_field.links.new(map_range.outputs[0], float_curve_002.inputs[1])
    
    # Установка значения по умолчанию
    mode_socket.default_value = 'S-Curve'
    return sphere_field

def spherefield_node_group():
    """Обертка для выбора между простой и сложной версией поля"""
    return advanced_spherefield_node_group()  # Используем продвинутую версию

def register():
    pass

def unregister():
    pass

