import bpy
from ..src.effectors import EFFECTOR_NODE_GROUP_PREFIXES

def update_cloner_with_effectors(obj, cloner_mod):
    """
    Обновляет нод-группу клонера, применяя связанные эффекторы более эффективным способом.
    
    Args:
        obj: Объект, содержащий модификатор
        cloner_mod: Модификатор клонера с нод-группой
    """
    if not cloner_mod or not cloner_mod.node_group:
        return
    
    node_group = cloner_mod.node_group
    linked_effectors = node_group.get("linked_effectors", [])
    
    # Проверяем валидность списка эффекторов
    valid_linked_effectors = []
    for eff_name in linked_effectors:
        eff_mod = obj.modifiers.get(eff_name)
        if eff_mod is not None and eff_mod.node_group:
            # Проверяем, что этот эффектор реально является эффектором
            is_effector = any(eff_mod.node_group.name.startswith(p) for p in EFFECTOR_NODE_GROUP_PREFIXES)
            if is_effector:
                valid_linked_effectors.append(eff_name)
    
    # Если список изменился, обновляем его
    if len(valid_linked_effectors) != len(linked_effectors):
        node_group["linked_effectors"] = valid_linked_effectors
        linked_effectors = valid_linked_effectors
    
    # Сначала получим список всех связанных эффекторов (старых)
    old_effectors = []
    effector_nodes = [n for n in node_group.nodes if n.name.startswith('Effector_')]
    for node in effector_nodes:
        effector_name = node.name.replace('Effector_', '')
        if effector_name not in old_effectors:
            old_effectors.append(effector_name)
    
    if not linked_effectors:
        # Если нет эффекторов, проверим, не осталось ли от предыдущих связей
        # Найдем старые узлы эффекторов и удалим их
        if effector_nodes:
            # Восстановим прямую связь от основной геометрии к выходу
            restore_direct_connection(node_group)
            
            # Удаляем старые узлы эффекторов
            for node in effector_nodes:
                try:
                    node_group.nodes.remove(node)
                except Exception as e:
                    print(f"Ошибка при удалении узла: {e}")
                
            # Включим видимость всех отвязанных эффекторов (только рендер)
            for effector_name in old_effectors:
                effector_mod = obj.modifiers.get(effector_name)
                if effector_mod:
                    # Включаем рендер эффектора, т.к. он был отвязан
                    effector_mod.show_render = True
        return
        
    # Находим новые и удаляемые эффекторы для управления видимостью
    to_add = [e for e in linked_effectors if e not in old_effectors]
    to_remove = [e for e in old_effectors if e not in linked_effectors]
    
    # Найдем выходной узел и его входящую связь
    group_output = None
    for node in node_group.nodes:
        if node.type == 'GROUP_OUTPUT':
            group_output = node
            break
    
    if not group_output:
        return
    
    # Найдем исходный узел клонера, с которого начнем цепочку
    source_node = None
    # Сначала ищем конкретные типы узлов, которые обычно являются последними в цепочке клонера
    for node in node_group.nodes:
        # Ищем узлы трансформации
        if 'Transform' in node.bl_idname and not node.name.startswith('Effector_'):
            for output in node.outputs:
                if output.name == 'Geometry' and any(link.to_node == group_output for link in output.links):
                    source_node = node
                    source_socket = output
                    break
            if source_node:
                break
    
    # Если не нашли, то ищем любой узел геометрии, связанный с выходом
    if not source_node:
        for node in node_group.nodes:
            if node != group_output and not node.name.startswith('Effector_'):
                for output in node.outputs:
                    if output.name == 'Geometry' and any(link.to_node == group_output for link in output.links):
                        source_node = node
                        source_socket = output
                        break
                if source_node:
                    break
    
    if not source_node:
        print("Не удалось найти исходный узел клонера для подключения эффекторов")
        return
    
    # Находим и удаляем все существующие связи от исходного узла к выходу
    links_to_remove = []
    for link in node_group.links:
        if link.from_node == source_node and link.to_node == group_output:
            links_to_remove.append(link)
    
    for link in links_to_remove:
        try:
            node_group.links.remove(link)
        except RuntimeError:
            # Связь уже была удалена
            pass
    
    # Удалим старые узлы эффекторов, если они есть
    for node in effector_nodes:
        node_group.nodes.remove(node)
    
    # Добавляем эффекторы по цепочке, начиная с исходного узла клонера
    current_geo = source_socket
    
    # Сохраняем позиции для размещения новых узлов
    pos_x = source_node.location.x + 200
    pos_y = source_node.location.y
    spacing = 250
    
    # Проверяем эффекторы перед добавлением, чтобы правильно обработать случай с несколькими эффекторами одного типа
    for effector_name in linked_effectors:
        # Находим модификатор эффектора
        effector_mod = obj.modifiers.get(effector_name)
        if not effector_mod or not effector_mod.node_group:
            continue
            
        # Отключаем только рендер эффектора, но оставляем видимым во viewport,
        # чтобы можно было видеть и настраивать его параметры
        effector_mod.show_render = False
        
        # Проверяем, что нод-группа эффектора действительно содержит нужные входы/выходы
        effector_group = effector_mod.node_group
        
        # Проверка на наличие входного и выходного сокета Geometry через interface.items_tree
        try:
            input_sockets = [s.name for s in effector_group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT']
            output_sockets = [s.name for s in effector_group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'OUTPUT']
            
            if 'Geometry' not in output_sockets:
                print(f"Эффектор {effector_name} не имеет выхода Geometry")
                continue
            if 'Geometry' not in input_sockets:
                print(f"Эффектор {effector_name} не имеет входа Geometry")
                continue
        except Exception as e:
            print(f"Ошибка при проверке сокетов эффектора {effector_name}: {e}")
            continue
    
    # Теперь добавляем узлы эффекторов и создаем связи
    for effector_name in linked_effectors:
        # Находим модификатор эффектора
        effector_mod = obj.modifiers.get(effector_name)
        if not effector_mod or not effector_mod.node_group:
            continue
            
        # Нод-группа эффектора
        effector_group = effector_mod.node_group
        
        # Создаем уникальное имя для узла эффектора
        node_name = f"Effector_{effector_name}"
        
        # Создаем узел группы эффектора
        try:
            effector_node = node_group.nodes.new('GeometryNodeGroup')
            effector_node.name = node_name
            effector_node.node_tree = effector_group
            
            # Устанавливаем положение узла
            effector_node.location = (pos_x, pos_y)
            pos_x += spacing
            
            # Скопируем значения параметров из модификатора эффектора
            for input_socket in [s for s in effector_group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT']:
                if input_socket.name in ['Geometry']:
                    continue  # Пропускаем вход геометрии
                
                # Если параметр не входит в сокеты или не имеет установленного значения в модификаторе, пропускаем
                if input_socket.identifier not in effector_mod:
                    continue
                    
                # Копируем значение параметра из модификатора в узел
                try:
                    effector_node.inputs[input_socket.name].default_value = effector_mod[input_socket.identifier]
                except (KeyError, TypeError) as e:
                    print(f"Не удалось установить значение для {input_socket.name}: {e}")
                    # Если не удалось установить значение, пропускаем
                    pass
            
            # Подключаем геометрию от предыдущего узла к входу эффектора
            try:
                node_group.links.new(current_geo, effector_node.inputs['Geometry'])
            except Exception as e:
                print(f"Ошибка при создании связи к эффектору {effector_name}: {e}")
                continue
            
            # Устанавливаем выход эффектора как текущую геометрию для следующего эффектора
            current_geo = effector_node.outputs['Geometry']
        except Exception as e:
            print(f"Ошибка при создании узла эффектора {effector_name}: {e}")
            # Восстанавливаем прямую связь в случае ошибки
            try:
                node_group.links.new(source_socket, group_output.inputs['Geometry'])
            except:
                pass
            return
    
    # Подключаем последний эффектор к выходу
    try:
        node_group.links.new(current_geo, group_output.inputs['Geometry'])
    except Exception as e:
        print(f"Ошибка при создании финальной связи: {e}")
        # Восстанавливаем прямую связь при ошибке
        restore_direct_connection(node_group)
    
    # Включаем все отвязанные эффекторы (только рендер)
    for effector_name in to_remove:
        effector_mod = obj.modifiers.get(effector_name)
        if effector_mod:
            # Включаем рендер эффектора, т.к. он был отвязан
            effector_mod.show_render = True


def restore_direct_connection(node_group):
    """
    Восстанавливает прямую связь между основной геометрией клонера и выходным узлом.
    Используется при удалении всех эффекторов.
    """
    # Найдем выходной узел
    group_output = None
    for node in node_group.nodes:
        if node.type == 'GROUP_OUTPUT':
            group_output = node
            break
    
    if not group_output:
        return
    
    # Найдем последний узел трансформации клонера
    for node in node_group.nodes:
        # Ищем узел Transform или TransformGeometry
        if 'Transform' in node.bl_idname and node.type != 'GROUP_OUTPUT':
            # Проверяем, что у него есть выход Geometry
            if 'Geometry' in [s.name for s in node.outputs]:
                # Создаем прямую связь с выходом
                node_group.links.new(node.outputs['Geometry'], group_output.inputs['Geometry'])
                return
    
    # Если не нашли узел трансформации, ищем любой узел с выходом Geometry
    for node in node_group.nodes:
        if node.type != 'GROUP_OUTPUT' and 'Geometry' in [s.name for s in node.outputs]:
            node_group.links.new(node.outputs['Geometry'], group_output.inputs['Geometry'])
            return 