# advanced_cloners/src/ui/field_panel.py

import bpy
from bpy.types import Panel, Operator
from ..fields.GN_SphereField import spherefield_node_group
from bpy.props import StringProperty, EnumProperty, FloatProperty

class FIELD_OT_create_field(Operator):
    """Create a new field"""
    bl_idname = "object.create_field"
    bl_label = "Create Field"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("Создание сферического поля...")
        
        if not context.active_object:
            self.report({'ERROR'}, "Пожалуйста, выберите объект")
            return {'CANCELLED'}
        
        obj = context.active_object
        print(f"Создание поля на объекте: {obj.name}")
        
        try:
            # Создаем уникальное имя для модификатора
            modifier_name = "Sphere Field"
            counter = 1
            while modifier_name in obj.modifiers:
                modifier_name = f"Sphere Field.{counter:03d}"
                counter += 1
            
            # Добавляем модификатор геометрических нодов
            mod = obj.modifiers.new(name=modifier_name, type='NODES')
            
            # Используем готовую функцию вместо создания своей группы нодов
            node_group = spherefield_node_group()
            
            # Устанавливаем группу нодов в модификатор
            mod.node_group = node_group
            
            # Создаем пустой объект для визуализации поля
            field_empty = bpy.data.objects.new(f"{modifier_name}_Gizmo", None)
            field_empty.empty_display_type = 'SPHERE'
            field_empty.empty_display_size = 1.0
            # Ставим гизмо на позицию объекта
            field_empty.location = obj.location.copy()
            bpy.context.collection.objects.link(field_empty)
            
            # Привязываем пустой объект к полю
            try:
                mod["Sphere"] = field_empty
                print(f"Создан пустой объект {field_empty.name} для визуализации поля")
                
                # Настраиваем размер гизмо в зависимости от параметров поля
                field_empty.empty_display_size = 2.0  # Базовый размер
                
                # Добавляем пользовательские свойства для легкого доступа
                field_empty["field_name"] = modifier_name
                field_empty["field_owner"] = obj.name
            except Exception as e:
                print(f"Ошибка привязки пустого объекта к полю: {e}")
            
            # Устанавливаем начальные параметры поля
            try:
                mod["Falloff"] = 0.5
                mod["Inner Strength"] = 1.0
                mod["Outer Strength"] = 0.0
                mod["Mode"] = 'S-Curve'
                mod["Strength"] = 0.3
            except Exception as e:
                print(f"Ошибка установки начальных параметров: {e}")
            
            # Перемещаем модификатор поля перед эффекторами
            # для правильного порядка выполнения
            # Находим первый эффектор
            effector_index = -1
            for i, modifier in enumerate(obj.modifiers):
                if modifier.type == 'NODES' and modifier.node_group and "Effector" in modifier.node_group.name:
                    effector_index = i
                    break
            
            # Если есть эффектор, перемещаем поле перед ним
            if effector_index > 0:
                # В Blender перемещение происходит последовательно на одну позицию
                current_index = len(obj.modifiers) - 1  # индекс нового модификатора (последний)
                while current_index > effector_index:
                    bpy.ops.object.modifier_move_up(modifier=mod.name)
                    current_index -= 1
            
            # Выбираем созданный гизмо для удобства
            bpy.ops.object.select_all(action='DESELECT')
            field_empty.select_set(True)
            bpy.context.view_layer.objects.active = field_empty
            
            self.report({'INFO'}, f"Поле '{modifier_name}' создано. Вы можете перемещать поле, двигая гизмо.")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка при создании поля: {str(e)}")
            print(f"ERROR: {str(e)}")
            return {'CANCELLED'}


class FIELD_OT_select_gizmo(Operator):
    """Select field gizmo"""
    bl_idname = "object.select_field_gizmo"
    bl_label = "Select Field Gizmo"
    bl_options = {'REGISTER', 'UNDO'}
    
    field_name: StringProperty()
    
    def execute(self, context):
        obj = context.active_object
        mod = obj.modifiers.get(self.field_name)
        
        if not mod or not mod.node_group:
            return {'CANCELLED'}
        
        # Получаем объект-гизмо из параметра Sphere
        gizmo_obj = None
        try:
            gizmo_obj = mod.get("Sphere")
        except:
            pass
            
        if gizmo_obj:
            # Выбираем только гизмо
            bpy.ops.object.select_all(action='DESELECT')
            gizmo_obj.select_set(True)
            bpy.context.view_layer.objects.active = gizmo_obj
            self.report({'INFO'}, f"Выбран гизмо поля {gizmo_obj.name}. Перемещайте его для изменения положения поля.")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Гизмо поля не найден")
            return {'CANCELLED'}


class FIELD_OT_create_sphere_gizmo(Operator):
    """Create a sphere gizmo for this field"""
    bl_idname = "object.create_field_gizmo"
    bl_label = "Create Field Gizmo"
    bl_options = {'REGISTER', 'UNDO'}
    
    field_name: StringProperty()
    
    def execute(self, context):
        obj = context.active_object
        mod = obj.modifiers.get(self.field_name)
        
        if not mod or not mod.node_group:
            return {'CANCELLED'}
        
        # Создаем пустой объект для визуализации поля
        field_empty = bpy.data.objects.new(f"{mod.name}_Gizmo", None)
        field_empty.empty_display_type = 'SPHERE'
        field_empty.empty_display_size = 1.0
        # Размещаем на позиции объекта
        field_empty.location = obj.location.copy()
        bpy.context.collection.objects.link(field_empty)
        
        # Добавляем пользовательские свойства
        field_empty["field_name"] = mod.name
        field_empty["field_owner"] = obj.name
        
        # Привязываем пустой объект к полю
        try:
            mod["Sphere"] = field_empty
            
            # Выбираем созданный гизмо
            bpy.ops.object.select_all(action='DESELECT')
            field_empty.select_set(True)
            bpy.context.view_layer.objects.active = field_empty
            
            self.report({'INFO'}, f"Создан гизмо поля {field_empty.name}. Перемещайте его для управления полем.")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка привязки гизмо к полю: {str(e)}")
            return {'CANCELLED'}


class FIELD_OT_adjust_field_strength(Operator):
    """Adjust field strength"""
    bl_idname = "object.adjust_field_strength"
    bl_label = "Adjust Field"
    bl_options = {'REGISTER', 'UNDO'}
    
    field_name: StringProperty()
    action: EnumProperty(
        items=[
            ('INCREASE', 'Increase', 'Increase field strength'),
            ('DECREASE', 'Decrease', 'Decrease field strength'),
            ('RESET', 'Reset', 'Reset to default')
        ],
        default='INCREASE'
    )
    
    def execute(self, context):
        obj = context.active_object
        mod = obj.modifiers.get(self.field_name)
        
        if not mod or not mod.node_group:
            return {'CANCELLED'}
            
        try:
            # Получаем текущее значение силы поля
            current_inner = mod.get("Inner Strength", 1.0)
            
            # Изменяем в зависимости от действия
            if self.action == 'INCREASE':
                # Увеличиваем на 25%
                mod["Inner Strength"] = min(current_inner + 0.25, 1.0)
                self.report({'INFO'}, f"Сила поля увеличена до {mod['Inner Strength']:.2f}")
            elif self.action == 'DECREASE':
                # Уменьшаем на 25%
                mod["Inner Strength"] = max(current_inner - 0.25, 0.0)
                self.report({'INFO'}, f"Сила поля уменьшена до {mod['Inner Strength']:.2f}")
            else:  # RESET
                mod["Inner Strength"] = 1.0
                mod["Outer Strength"] = 0.0
                mod["Falloff"] = 0.5
                self.report({'INFO'}, "Параметры поля сброшены")
                
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка изменения параметров поля: {str(e)}")
            return {'CANCELLED'}


class FIELD_PT_main_panel(Panel):
    """Panel for fields"""
    bl_label = "Advanced Fields"
    bl_idname = "FIELD_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Cloners"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        # Кнопка создания поля
        create_box = layout.box()
        create_box.label(text="Create Field", icon='ADD')
        create_box.operator("object.create_field", text="Create Sphere Field", icon='OUTLINER_OB_FORCE_FIELD')
        
        # Отобразим активные поля, если есть
        obj = context.active_object
        if not obj:
            layout.label(text="Select an object to see active fields")
            return
            
        fields = [m for m in obj.modifiers if m.type == 'NODES' and m.node_group and "SphereField" in m.node_group.name]
        if not fields:
            layout.label(text="No active fields on this object")
            return
            
        layout.label(text="Active Fields:", icon='OUTLINER_OB_FORCE_FIELD')
        indices = {m.name: i for i, m in enumerate(obj.modifiers)}
        
        for mod in fields:
            if mod.name not in indices:
                continue
                
            self.draw_field_ui(context, layout, obj, mod, indices)
            
    def draw_field_ui(self, context, layout, obj, mod, indices):
        box = layout.box()
        header = box.row(align=True)
        
        # Заголовок с именем поля и кнопками
        header.prop(mod, "show_expanded", text="", icon='OUTLINER_OB_FORCE_FIELD', emboss=False)
        header.label(text=mod.name)
        
        # Кнопки управления полем
        ctrl = header.row(align=True)
        ctrl.alignment = 'RIGHT'
        
        # Кнопки перемещения (используем основной оператор из __init__.py)
        idx = indices[mod.name]
        if idx > 0:
            up = ctrl.operator("object.move_field", text="", icon='TRIA_UP', emboss=False)
            up.modifier_name = mod.name
            up.direction = 'UP'
        else:
            ctrl.label(text="", icon='BLANK1')
            
        if idx < len(obj.modifiers)-1:
            down = ctrl.operator("object.move_field", text="", icon='TRIA_DOWN', emboss=False)
            down.modifier_name = mod.name
            down.direction = 'DOWN'
        else:
            ctrl.label(text="", icon='BLANK1')
            
        # Кнопка удаления
        delete = ctrl.operator("object.delete_field", text="", icon='X', emboss=False)
        delete.modifier_name = mod.name
        
        # Если поле раскрыто, показываем его параметры
        if mod.show_expanded and mod.node_group and hasattr(mod.node_group, 'interface'):
            main_col = box.column(align=True)
            
            # Гизмо для перемещения поля
            gizmo_box = main_col.box()
            gizmo_box.label(text="Поле влияния:", icon='EMPTY_SPHERE')
            
            # Проверяем, есть ли у поля привязанный объект
            has_gizmo = False
            try:
                sphere_obj = mod.get("Sphere")
                if sphere_obj:
                    has_gizmo = True
                    gizmo_row = gizmo_box.row(align=True)
                    gizmo_row.label(text=sphere_obj.name)
                    select_op = gizmo_row.operator("object.select_field_gizmo", text="Выбрать гизмо", icon='RESTRICT_SELECT_OFF')
                    select_op.field_name = mod.name
                    
                    # Подсказка для пользователя
                    gizmo_box.label(text="Перемещайте гизмо для изменения положения поля")
            except Exception as e:
                print(f"Ошибка при получении гизмо: {e}")
                pass
                
            if not has_gizmo:
                create_op = gizmo_box.operator("object.create_field_gizmo", text="Создать гизмо")
                create_op.field_name = mod.name
            
            # Параметры воздействия поля - в более интуитивном порядке
            strength_box = main_col.box()
            strength_box.label(text="Сила влияния:", icon='FORCE_FORCE')
            
            # Быстрые кнопки для регулировки силы
            strength_row = strength_box.row(align=True)
            decrease = strength_row.operator("object.adjust_field_strength", text="", icon='REMOVE')
            decrease.field_name = mod.name
            decrease.action = 'DECREASE'
            
            # Отображаем Inner Strength более заметно
            try:
                for socket in mod.node_group.interface.items_tree:
                    if socket.item_type == 'SOCKET' and socket.in_out == 'INPUT' and socket.name == "Inner Strength":
                        strength_row.prop(mod, f'["{socket.identifier}"]', text="")
                        break
            except Exception as e:
                print(f"Ошибка отображения силы поля: {e}")
                strength_row.label(text="Сила недоступна")
            
            increase = strength_row.operator("object.adjust_field_strength", text="", icon='ADD')
            increase.field_name = mod.name
            increase.action = 'INCREASE'
            
            reset = strength_row.operator("object.adjust_field_strength", text="", icon='LOOP_BACK')
            reset.field_name = mod.name
            reset.action = 'RESET'
            
            # Дополнительные параметры поля
            params_box = main_col.box()
            params_box.label(text="Дополнительные параметры:", icon='OPTIONS')
            
            try:
                # Улучшенная организация параметров
                param_order = ["Falloff", "Outer Strength", "Mode", "Strength"]
                
                for socket_name in param_order:
                    found = False
                    for socket in mod.node_group.interface.items_tree:
                        if socket.item_type == 'SOCKET' and socket.in_out == 'INPUT' and socket.name == socket_name:
                            found = True
                            try:
                                row = params_box.row()
                                # Добавляем понятные подписи
                                if socket_name == "Falloff":
                                    display_name = "Плавность спадания"
                                elif socket_name == "Outer Strength":
                                    display_name = "Сила снаружи"
                                elif socket_name == "Mode":
                                    display_name = "Режим интерполяции"
                                elif socket_name == "Strength":
                                    display_name = "Мощность интерполяции"
                                else:
                                    display_name = socket_name
                                
                                row.prop(mod, f'["{socket.identifier}"]', text=display_name)
                            except Exception as e:
                                print(f"Ошибка отображения параметра {socket_name}: {e}")
                                params_box.label(text=f"Ошибка параметра {socket_name}")
                    
                    if not found and socket_name != "Mode" and socket_name != "Strength":
                        row = params_box.row()
                        row.label(text=f"{socket_name}: Недоступно")
            except Exception as e:
                print(f"Ошибка загрузки параметров: {e}")
                params_box.label(text=f"Ошибка загрузки параметров")


# регистрация панели и операторов
classes = (
    FIELD_OT_create_field,
    FIELD_OT_select_gizmo,
    FIELD_OT_create_sphere_gizmo,
    FIELD_OT_adjust_field_strength,
    FIELD_PT_main_panel,
)

def register():
    print("Registering Field Panel classes...")
    try:
        for cls in classes:
            bpy.utils.register_class(cls)
        print(f"Field Panel registered {len(classes)} classes")
    except Exception as e:
        print(f"Error registering field panel: {e}")

def unregister():
    print("Unregistering Field Panel classes...")
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Error unregistering class {cls.__name__}: {e}")
    print("Field Panel unregistered")
