bl_info = {
    "name": "Advanced Cloners",
    "author": "Serhii Marchenko",
    "version": (1, 9, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Cloners",
    "description": "Implements Cinema 4D-like cloner system using Geometry Nodes",
    "warning": "BETA",
    "wiki_url": "",
    "category": "Object",
}

import bpy

# Geometry Nodes модули (с register()/unregister() внутри)
from .src.cloners import GN_GridCloner
from .src.cloners import GN_LinearCloner
from .src.cloners import GN_CircleCloner
from .src.effectors import GN_RandomEffector
from .src.effectors import GN_NoiseEffector
# from .src.fields import GN_SphereField

# Функции создания нод-групп
from .src.cloners.GN_GridCloner import gridcloner3d_node_group
from .src.cloners.GN_LinearCloner import advancedlinearcloner_node_group
from .src.cloners.GN_CircleCloner import circlecloner_node_group
from .src.effectors.GN_RandomEffector import randomeffector_node_group
from .src.effectors.GN_NoiseEffector import noiseeffector_node_group
# from .src.fields.GN_SphereField import spherefield_node_group

# UI-панели (они сами регистрируют свои классы внутри)
from .src.ui import cloner_panel, effector_panel

# Импортируем утилиты
from .utils.cloner_utils import update_cloner_with_effectors

# Импортируем определения полей
# from .src.fields import FIELD_CREATORS, FIELD_TYPES, FIELD_MOD_NAMES, FIELD_GROUP_NAMES, FIELD_NODE_GROUP_PREFIXES

# Определяем типы клонеров
CLONER_TYPES = [
    ("GRID", "Grid Cloner", "Create a 3D grid of clones", "MESH_GRID"),
    ("LINEAR", "Linear Cloner", "Create a linear array of clones", "SORTSIZE"),
    ("CIRCLE", "Circle Cloner", "Create a circular array of clones", "MESH_CIRCLE"),
]

# Функции создания для каждого типа клонера
CLONER_CREATORS = {
    "GRID": gridcloner3d_node_group,
    "LINEAR": advancedlinearcloner_node_group,
    "CIRCLE": circlecloner_node_group,
}

# Имена групп узлов для клонеров
CLONER_GROUP_NAMES = {
    "GRID": "GridCloner3D_Advanced",
    "LINEAR": "AdvancedLinearCloner",
    "CIRCLE": "CircleCloner",
}

# Имена модификаторов для клонеров
CLONER_MOD_NAMES = {
    "GRID": "Grid Cloner",
    "LINEAR": "Linear Cloner",
    "CIRCLE": "Circle Cloner",
}

# Определяем типы эффекторов
EFFECTOR_TYPES = [
    ("RANDOM", "Random Effector", "Apply random transformations to clones", "RNDCURVE"),
    ("NOISE", "Noise Effector", "Apply noise-based transformations to clones", "FORCE_TURBULENCE"),
]

# Функции создания для каждого типа эффектора
EFFECTOR_CREATORS = {
    "RANDOM": randomeffector_node_group,
    "NOISE": noiseeffector_node_group,
}

# Имена групп узлов для эффекторов
EFFECTOR_GROUP_NAMES = {
    "RANDOM": "RandomEffector",
    "NOISE": "NoiseEffector",
}

# Имена модификаторов для эффекторов
EFFECTOR_MOD_NAMES = {
    "RANDOM": "Random Effector",
    "NOISE": "Noise Effector",
}

# Префиксы для распознавания типов модификаторов
CLONER_NODE_GROUP_PREFIXES = list(CLONER_GROUP_NAMES.values())
EFFECTOR_NODE_GROUP_PREFIXES = list(EFFECTOR_GROUP_NAMES.values())

# Общие функции для работы с нодами
def create_independent_node_group(template_creator_func, base_node_name):
    """Создает независимую копию группы узлов"""
    # Создаем базовую группу узлов
    template_node_group = template_creator_func()
    if template_node_group is None:
        return None
    
    # Создаем независимую копию
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
    
    # Удаляем шаблон или переименовываем его
    if template_node_group.users == 0:
        try:
            bpy.data.node_groups.remove(template_node_group, do_unlink=True)
        except Exception as e:
            print(f"Warning: Could not remove template node group: {e}")
    else:
        template_node_group.name += ".template"
    
    # Создаем уникальное имя для копии
    unique_node_name = base_node_name
    counter = 1
    while unique_node_name in bpy.data.node_groups:
        unique_node_name = f"{base_node_name}.{counter:03d}"
        counter += 1
    independent_node_group.name = unique_node_name
    
    return independent_node_group

# ОПЕРАТОРЫ ДЛЯ КЛОНЕРОВ

class CLONER_OT_create_cloner(bpy.types.Operator):
    """Create a new cloner"""
    bl_idname = "object.create_cloner"
    bl_label = "Create Cloner"
    bl_options = {'REGISTER', 'UNDO'}
    
    cloner_type: bpy.props.StringProperty(default="GRID")

    def execute(self, context):
        if not context.active_object:
            self.report({'ERROR'}, "Please select an object")
            return {'CANCELLED'}
        
        obj = context.active_object
        
        # Проверяем тип клонера
        if self.cloner_type not in CLONER_CREATORS:
            self.report({'ERROR'}, f"Unknown cloner type: {self.cloner_type}")
            return {'CANCELLED'}
        
        # Получаем функцию создания и имена
        creator_func = CLONER_CREATORS[self.cloner_type]
        base_node_name = CLONER_GROUP_NAMES[self.cloner_type]
        base_mod_name = CLONER_MOD_NAMES[self.cloner_type]
        
        # Создаем группу узлов
        node_group = create_independent_node_group(creator_func, base_node_name)
        if node_group is None:
            self.report({'ERROR'}, f"Failed to create node group for {base_mod_name}")
            return {'CANCELLED'}
        
        # Инициализируем список эффекторов
        node_group["linked_effectors"] = []
        
        # Создаем уникальное имя для модификатора
        modifier_name = base_mod_name
        counter = 1
        while modifier_name in obj.modifiers:
            modifier_name = f"{base_mod_name}.{counter:03d}"
            counter += 1
        
        # Добавляем модификатор
        modifier = obj.modifiers.new(name=modifier_name, type='NODES')
        
        # Сначала устанавливаем правильный порядок модификатора:
        # Переместим новый эффектор в самый конец стека модификаторов,
        # чтобы он не влиял на клонеры, пока не будет привязан
        # Blender автоматически добавляет новые модификаторы в начало стека
        
        # Ограничиваем количество попыток перемещения, чтобы избежать зависания
        max_attempts = len(obj.modifiers) + 1
        attempts = 0
        last_index = len(obj.modifiers) - 1
        
        # Находим текущий индекс нового модификатора
        current_index = -1
        for i, mod in enumerate(obj.modifiers):
            if mod.name == modifier_name:
                current_index = i
                break
        
        # Перемещаем модификатор вниз только если он не последний
        while current_index >= 0 and current_index < last_index and attempts < max_attempts:
            try:
                bpy.ops.object.modifier_move_down(modifier=modifier_name)
                current_index += 1
                attempts += 1
            except:
                break
        
        # Теперь безопасно устанавливаем группу узлов
        modifier.node_group = node_group
        
        # Обновляем с эффекторами (изначально пустой список)
        update_cloner_with_effectors(obj, modifier)
        
        self.report({'INFO'}, f"{base_mod_name} '{modifier_name}' created")
        return {'FINISHED'}


class CLONER_OT_delete_cloner(bpy.types.Operator):
    """Delete this cloner"""
    bl_idname = "object.delete_cloner"
    bl_label = "Delete Cloner"
    bl_options = {'REGISTER', 'UNDO'}

    modifier_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.active_object
        if obj and self.modifier_name in obj.modifiers:
            modifier = obj.modifiers[self.modifier_name]
            node_group = modifier.node_group
            
            # Удаляем модификатор
            obj.modifiers.remove(modifier)
            
            # Удаляем группу узлов, если она больше не используется
            if node_group and node_group.users == 0:
                bpy.data.node_groups.remove(node_group)
        
        return {'FINISHED'}


class CLONER_OT_move_modifier(bpy.types.Operator):
    """Move modifier up or down"""
    bl_idname = "object.move_cloner"
    bl_label = "Move Cloner"
    bl_options = {'REGISTER', 'UNDO'}

    modifier_name: bpy.props.StringProperty()
    direction: bpy.props.EnumProperty(
        items=[
            ('UP', 'Up', 'Move up'),
            ('DOWN', 'Down', 'Move down')
        ]
    )

    def execute(self, context):
        obj = context.active_object
        if obj and self.modifier_name in obj.modifiers:
            if self.direction == 'UP':
                bpy.ops.object.modifier_move_up(modifier=self.modifier_name)
            else:
                bpy.ops.object.modifier_move_down(modifier=self.modifier_name)
        return {'FINISHED'}


# ОПЕРАТОРЫ ДЛЯ ЭФФЕКТОРОВ

class EFFECTOR_OT_create_effector(bpy.types.Operator):
    """Create a new effector"""
    bl_idname = "object.create_effector"
    bl_label = "Create Effector"
    bl_options = {'REGISTER', 'UNDO'}
    
    effector_type: bpy.props.StringProperty(default="RANDOM")

    def execute(self, context):
        if not context.active_object:
            self.report({'ERROR'}, "Please select an object")
            return {'CANCELLED'}
        
        obj = context.active_object
        
        # Проверяем тип эффектора
        if self.effector_type not in EFFECTOR_CREATORS:
            self.report({'ERROR'}, f"Unknown effector type: {self.effector_type}")
            return {'CANCELLED'}
        
        # Используем стандартный подход для всех эффекторов, включая Noise Effector
        creator_func = EFFECTOR_CREATORS[self.effector_type]
        base_node_name = EFFECTOR_GROUP_NAMES[self.effector_type]
        base_mod_name = EFFECTOR_MOD_NAMES[self.effector_type]
        
        # Создаем группу узлов
        node_group = create_independent_node_group(creator_func, base_node_name)
        if node_group is None:
            self.report({'ERROR'}, f"Failed to create node group for {base_mod_name}")
            return {'CANCELLED'}
        
        # Создаем уникальное имя для модификатора
        modifier_name = base_mod_name
        counter = 1
        while modifier_name in obj.modifiers:
            modifier_name = f"{base_mod_name}.{counter:03d}"
            counter += 1
        
        # Добавляем модификатор, но НЕ АКТИВИРУЕМ его автоматически
        modifier = obj.modifiers.new(name=modifier_name, type='NODES')
        
        # Выключаем модификатор временно до привязки к клонеру
        # Это предотвратит исчезновение геометрии
        modifier.show_viewport = False  # Отключаем отображение эффектора вообще
        
        # Теперь безопасно устанавливаем группу узлов
        modifier.node_group = node_group
        
        # Явно устанавливаем начальные значения для параметров эффектора
        # Это предотвратит влияние на клонеры до привязки
        try:
            for socket in node_group.interface.items_tree:
                if socket.item_type == 'SOCKET' and socket.in_out == 'INPUT':
                    if socket.name == "Enable":
                        try:
                            modifier[socket.identifier] = False
                        except:
                            pass
                    elif socket.name == "Strength":
                        try:
                            modifier[socket.identifier] = 0.0
                        except:
                            pass
                    elif socket.name == "Position":
                        try:
                            modifier[socket.identifier] = (0.0, 0.0, 0.0)
                        except:
                            pass
                    elif socket.name == "Rotation":
                        try:
                            modifier[socket.identifier] = (0.0, 0.0, 0.0)
                        except:
                            pass
                    elif socket.name == "Scale":
                        try:
                            modifier[socket.identifier] = (0.0, 0.0, 0.0)
                        except:
                            pass
        except Exception as e:
            print(f"Ошибка при установке начальных значений: {e}")
        
        # По Cinema 4D подходу, эффекторы не имеют эффекта сами по себе,
        # они должны быть связаны с клонером, чтобы работать.
        # Для удобства настройки показываем в интерфейсе, но скрываем в viewport
        modifier.show_render = True
        modifier.show_viewport = False  # Отключаем отображение эффектора вообще
        
        self.report({'INFO'}, f"{base_mod_name} '{modifier_name}' created. Link it to a cloner to use.")
        return {'FINISHED'}


class EFFECTOR_OT_delete_effector(bpy.types.Operator):
    """Delete this effector"""
    bl_idname = "object.delete_effector"
    bl_label = "Delete Effector"
    bl_options = {'REGISTER', 'UNDO'}

    modifier_name: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.active_object
        if obj and self.modifier_name in obj.modifiers:
            modifier = obj.modifiers[self.modifier_name]
            node_group = modifier.node_group
            
            # Удаляем модификатор
            obj.modifiers.remove(modifier)
            
            # Удаляем группу узлов, если она больше не используется
            if node_group and node_group.users == 0:
                bpy.data.node_groups.remove(node_group)
        
        return {'FINISHED'}


class EFFECTOR_OT_move_modifier(bpy.types.Operator):
    """Move modifier up or down"""
    bl_idname = "object.move_effector"
    bl_label = "Move Effector"
    bl_options = {'REGISTER', 'UNDO'}

    modifier_name: bpy.props.StringProperty()
    direction: bpy.props.EnumProperty(
        items=[
            ('UP', 'Up', 'Move up'),
            ('DOWN', 'Down', 'Move down')
        ]
    )

    def execute(self, context):
        obj = context.active_object
        if obj and self.modifier_name in obj.modifiers:
            if self.direction == 'UP':
                bpy.ops.object.modifier_move_up(modifier=self.modifier_name)
            else:
                bpy.ops.object.modifier_move_down(modifier=self.modifier_name)
        return {'FINISHED'}


# ОПЕРАТОРЫ ДЛЯ ПОЛЕЙ - ЗАКОММЕНТИРОВАНЫ

# class FIELD_OT_create_field(bpy.types.Operator):
#     """Create a new field"""
#     bl_idname = "object.create_field"
#     bl_label = "Create Field"
#     bl_options = {'REGISTER', 'UNDO'}
#     
#     field_type: bpy.props.StringProperty(default="SPHERE")
# 
#     def execute(self, context):
#         print(f"Создание поля типа: {self.field_type}")
#         
#         if not context.active_object:
#             self.report({'ERROR'}, "Пожалуйста, выберите объект")
#             return {'CANCELLED'}
#         
#         obj = context.active_object
#         
#         # Создаем уникальное имя для модификатора
#         modifier_name = "Sphere Field"
#         counter = 1
#         while modifier_name in obj.modifiers:
#             modifier_name = f"Sphere Field.{counter:03d}"
#             counter += 1
#         
#         try:
#             # Создаем модификатор напрямую
#             mod = obj.modifiers.new(name=modifier_name, type='NODES')
#             
#             # Используем функцию из модуля полей
#             node_group = spherefield_node_group()
#             
#             # Присваиваем группу модификатору
#             mod.node_group = node_group
#             
#             # Перемещаем модификатор поля перед эффекторами
#             effector_index = -1
#             for i, modifier in enumerate(obj.modifiers):
#                 if modifier.type == 'NODES' and modifier.node_group and "Effector" in modifier.node_group.name:
#                     effector_index = i
#                     break
#             
#             # Если есть эффектор, перемещаем поле перед ним
#             if effector_index > 0:
#                 # В Blender перемещение происходит последовательно на одну позицию
#                 current_index = len(obj.modifiers) - 1  # индекс нового модификатора (последний)
#                 while current_index > effector_index:
#                     bpy.ops.object.modifier_move_up(modifier=mod.name)
#                     current_index -= 1
#             
#             self.report({'INFO'}, f"Поле '{modifier_name}' создано")
#             return {'FINISHED'}
#         except Exception as e:
#             self.report({'ERROR'}, f"Ошибка при создании поля: {str(e)}")
#             print(f"Ошибка при создании поля: {str(e)}")
#             return {'CANCELLED'}
# 
# 
# class FIELD_OT_delete_field(bpy.types.Operator):
#     """Delete this field"""
#     bl_idname = "object.delete_field"
#     bl_label = "Delete Field"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     modifier_name: bpy.props.StringProperty()
# 
#     def execute(self, context):
#         obj = context.active_object
#         if obj and self.modifier_name in obj.modifiers:
#             modifier = obj.modifiers[self.modifier_name]
#             node_group = modifier.node_group
#             
#             # Удаляем модификатор
#             obj.modifiers.remove(modifier)
#             
#             # Удаляем группу узлов, если она больше не используется
#             if node_group and node_group.users == 0:
#                 bpy.data.node_groups.remove(node_group)
#         
#         return {'FINISHED'}
# 
# 
# class FIELD_OT_move_field(bpy.types.Operator):
#     """Move field up or down"""
#     bl_idname = "object.move_field"
#     bl_label = "Move Field"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     modifier_name: bpy.props.StringProperty()
#     direction: bpy.props.EnumProperty(
#         items=[
#             ('UP', 'Up', 'Move up'),
#             ('DOWN', 'Down', 'Move down')
#         ]
#     )
# 
#     def execute(self, context):
#         obj = context.active_object
#         if obj and self.modifier_name in obj.modifiers:
#             if self.direction == 'UP':
#                 bpy.ops.object.modifier_move_up(modifier=self.modifier_name)
#             else:
#                 bpy.ops.object.modifier_move_down(modifier=self.modifier_name)
#         return {'FINISHED'}

# РЕГИСТРАЦИЯ

# операторов и панелей, определённых в этом файле
classes = (
    CLONER_OT_create_cloner,
    CLONER_OT_delete_cloner,
    CLONER_OT_move_modifier,
    EFFECTOR_OT_create_effector,
    EFFECTOR_OT_delete_effector,
    EFFECTOR_OT_move_modifier,
    # FIELD_OT_create_field,
    # FIELD_OT_delete_field,
    # FIELD_OT_move_field,
)

def register():
    print("Registering Advanced Cloners addon...")
    
    # Register GN modules
    print("Registering GN modules...")
    GN_GridCloner.register()
    GN_LinearCloner.register()
    GN_CircleCloner.register()
    GN_RandomEffector.register()
    GN_NoiseEffector.register()
    # GN_SphereField.register()
    print("GN modules registered")

    # Register UI components
    print("Registering UI components...")
    cloner_panel.register()
    effector_panel.register()
    # field_panel.register()
    print("UI components registered")
    
    # Register operators
    print("Registering operators...")
    for cls in classes:
        bpy.utils.register_class(cls)
    print("Operators registered")
    
    print("Advanced Cloners addon registered successfully")

def unregister():
    print("Unregistering Advanced Cloners addon...")
    
    # Unregister operators
    print("Unregistering operators...")
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("Operators unregistered")
    
    # Unregister UI components
    print("Unregistering UI components...")
    # field_panel.unregister()
    effector_panel.unregister()
    cloner_panel.unregister()
    print("UI components unregistered")
    
    # Unregister GN modules
    print("Unregistering GN modules...")
    # GN_SphereField.unregister()
    GN_RandomEffector.unregister()
    GN_NoiseEffector.unregister()
    GN_CircleCloner.unregister()
    GN_LinearCloner.unregister()
    GN_GridCloner.unregister()
    print("GN modules unregistered")
    
    print("Advanced Cloners addon unregistered successfully")



if __name__ == "__main__":
    register()
