# advanced_cloners/src/ui/effector_panel.py

import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty
from ..effectors import EFFECTOR_TYPES, EFFECTOR_NODE_GROUP_PREFIXES
from ..fields import FIELD_NODE_GROUP_PREFIXES as FIELD_PREFIXES

# ——— Операторы для привязки/отвязки полей ———

class EFFECTOR_OT_add_field(Operator):
    bl_idname = "object.effector_add_field"
    bl_label  = "Add Field to Effector"
    effector_name: StringProperty()

    def execute(self, context):
        obj = context.active_object
        mod = obj.modifiers.get(self.effector_name)
        if not mod or not mod.node_group:
            return {'CANCELLED'}
            
        # Найдем первое поле на объекте
        field_mod = None
        for m in obj.modifiers:
            if m.type == 'NODES' and m.node_group and "SphereField" in m.node_group.name:
                field_mod = m
                break
                
        if not field_mod:
            self.report({'ERROR'}, "Поле не найдено. Сначала создайте поле.")
            return {'CANCELLED'}
            
        # Подключим поле к эффектору
        # Для RandomEffector у нас уже есть входной сокет 'Field'
        if mod.node_group.name.startswith("RandomEffector"):
            # 1. Сначала отключаем Use Field для безопасности
            try:
                mod["Use Field"] = False
            except:
                pass
                
            # 2. Устанавливаем значение Field = 1.0 до включения Use Field
            try:
                mod["Field"] = 1.0
                print("Установлено Field = 1.0")
            except Exception as e:
                print(f"Ошибка при установке Field: {e}")
                
            # 3. Устанавливаем драйвер при отключенном Use Field
            try:
                # Находим сокет Value в поле
                value_socket = None
                for item in field_mod.node_group.interface.items_tree:
                    if item.item_type == 'SOCKET' and item.in_out == 'OUTPUT' and item.name == "Value":
                        value_socket = item.identifier
                        break
                        
                if value_socket:
                    # Создаем ссылку на выход поля
                    field_path = f'modifiers["{field_mod.name}"]'
                    socket_path = f'["{value_socket}"]'
                    full_path = field_path + socket_path
                    
                    # Устанавливаем драйвер
                    try:
                        # Удаляем старый драйвер, если есть
                        try:
                            mod.driver_remove('Field')
                        except:
                            pass
                            
                        # Создаем новый драйвер
                        driver = mod.driver_add('Field').driver
                        driver.type = 'AVERAGE'
                        var = driver.variables.new()
                        var.name = "field_value"
                        var.type = 'SINGLE_PROP'
                        var.targets[0].id_type = 'OBJECT'
                        var.targets[0].id = obj
                        var.targets[0].data_path = full_path
                        print(f"Драйвер установлен: {full_path}")
                        
                        # Проверка, что драйвер работает
                        try:
                            test_val = driver.evaluate()
                            print(f"Драйвер возвращает: {test_val}")
                        except:
                            pass
                    except Exception as e:
                        print(f"Ошибка при установке драйвера: {e}")
            except Exception as e:
                print(f"Ошибка при настройке драйвера: {e}")
                        
            # 4. Наконец, включаем использование поля
            try:
                mod["Use Field"] = True
                print("Use Field включено")
                self.report({'INFO'}, f"Поле '{field_mod.name}' подключено к эффектору")
                return {'FINISHED'}
            except Exception as e:
                print(f"Ошибка при включении Use Field: {e}")
                mod["Field"] = 1.0  # безопасное значение на случай ошибки
                return {'CANCELLED'}
                
        self.report({'ERROR'}, "Этот тип эффектора не поддерживает поля")
        return {'CANCELLED'}
        
class EFFECTOR_OT_remove_field(Operator):
    bl_idname = "object.effector_remove_field"
    bl_label  = "Remove Field from Effector"
    effector_name: StringProperty()

    def execute(self, context):
        obj = context.active_object
        mod = obj.modifiers.get(self.effector_name)
        if not mod or not mod.node_group:
            return {'CANCELLED'}
            
        # Для RandomEffector просто отключаем использование поля
        # и удаляем драйвер
        if mod.node_group.name.startswith("RandomEffector"):
            # Сначала установим безопасное значение поля
            try:
                mod["Field"] = 1.0
            except:
                pass
                
            # Удаляем драйвер до отключения Use Field
            try:
                mod.driver_remove('Field')
                print("Драйвер поля удален")
            except Exception as e:
                print(f"Ошибка при удалении драйвера: {e}")
                
            # Отключаем использование поля
            try:
                mod["Use Field"] = False
                self.report({'INFO'}, "Поле отключено от эффектора")
                return {'FINISHED'}
            except Exception as e:
                print(f"Ошибка при отключении поля: {e}")
                return {'CANCELLED'}
            
        self.report({'ERROR'}, "Этот тип эффектора не поддерживает поля")
        return {'CANCELLED'}

class EFFECTOR_OT_auto_link(Operator):
    bl_idname = "object.auto_link_effector"
    bl_label  = "Auto-Link Effector to Cloners"
    effector_name: StringProperty()

    def execute(self, context):
        obj = context.active_object
        effector_mod = obj.modifiers.get(self.effector_name)
        if not effector_mod or not effector_mod.node_group:
            self.report({'ERROR'}, "Эффектор не найден")
            return {'CANCELLED'}
        
        # Найдем все клонеры на объекте
        cloner_mods = [
            m for m in obj.modifiers
            if m.type == 'NODES' and m.node_group
               and m.node_group.get("linked_effectors") is not None
        ]
        
        if not cloner_mods:
            self.report({'ERROR'}, "На объекте нет клонеров")
            return {'CANCELLED'}
        
        # Активируем эффектор, устанавливая его параметры
        if effector_mod and effector_mod.node_group:
            # Включаем отображение эффектора, так как он будет привязан
            effector_mod.show_viewport = True
            
            # Ищем параметры Enable и Strength в интерфейсе эффектора
            for socket in effector_mod.node_group.interface.items_tree:
                if socket.item_type == 'SOCKET' and socket.in_out == 'INPUT':
                    if socket.name == "Enable":
                        try:
                            effector_mod[socket.identifier] = True
                        except:
                            pass
                    elif socket.name == "Strength":
                        try:
                            effector_mod[socket.identifier] = 1.0
                        except:
                            pass
        
        # Связываем эффектор со всеми клонерами, к которым он еще не привязан
        linked_count = 0
        for cloner in cloner_mods:
            # Преобразуем IDPropertyArray в обычный список Python
            linked_effectors_prop = cloner.node_group.get("linked_effectors", [])
            
            # Конвертируем в список Python, если это не список
            linked_effectors = list(linked_effectors_prop) if linked_effectors_prop else []
            
            # Добавляем эффектор, если он еще не связан с этим клонером
            if self.effector_name not in linked_effectors:
                linked_effectors.append(self.effector_name)
                cloner.node_group["linked_effectors"] = linked_effectors
                
                # Обновляем клонер с новыми эффекторами
                from ...utils.cloner_utils import update_cloner_with_effectors
                update_cloner_with_effectors(obj, cloner)
                linked_count += 1
        
        if linked_count > 0:
            self.report({'INFO'}, f"Эффектор '{self.effector_name}' связан с {linked_count} клонерами")
        else:
            self.report({'INFO'}, "Эффектор уже связан со всеми клонерами")
            
        return {'FINISHED'}

class EFFECTOR_PT_main_panel(Panel):
    """Panel for effectors"""
    bl_label = "Advanced Effectors"
    bl_idname = "EFFECTOR_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Cloners"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        # Кнопки создания эффекторов
        create_box = layout.box()
        create_box.label(text="Create:", icon='ADD')
        for eff_id, eff_name, _, eff_icon in EFFECTOR_TYPES:
            op = create_box.operator("object.create_effector", text=eff_name, icon=eff_icon)
            op.effector_type = eff_id

        if not obj:
            layout.label(text="Select an object")
            return

        eff_mods = [
            m for m in obj.modifiers
            if m.type == 'NODES' and m.node_group
               and any(m.node_group.name.startswith(p) for p in EFFECTOR_NODE_GROUP_PREFIXES)
        ]
        if not eff_mods:
            layout.label(text="No effectors")
            return

        layout.label(text="Effectors:", icon='FORCE_FORCE')
        indices = {m.name: i for i, m in enumerate(obj.modifiers)}
        
        # Находим клонеры на объекте
        cloner_mods = [
            m for m in obj.modifiers
            if m.type == 'NODES' and m.node_group
               and m.node_group.get("linked_effectors") is not None
        ]
        
        for mod in eff_mods:
            if mod.name not in indices:
                continue
            self.draw_effector_ui(context, layout, obj, mod, indices, cloner_mods)

    def draw_effector_ui(self, context, layout, obj, mod, indices, cloner_mods):
        box = layout.box()
        header = box.row(align=True)
        icon = 'FORCE_FORCE'
        if mod.node_group.name.startswith("RandomEffector"):
            icon = 'RNDCURVE'
            
        # Добавляем треугольник раскрытия для большей наглядности
        if mod.show_expanded:
            header.prop(mod, "show_expanded", text="", icon='DISCLOSURE_TRI_DOWN', emboss=False)
        else:
            header.prop(mod, "show_expanded", text="", icon='DISCLOSURE_TRI_RIGHT', emboss=False)
            
        # Иконка эффектора    
        header.label(text="", icon=icon)
        
        # Отображаем имя эффектора
        name_row = header.row()
        name_row.label(text=mod.name)
        
        # Кнопки управления
        ctrl = header.row(align=True)
        ctrl.alignment = 'RIGHT'
        idx = indices[mod.name]
        if idx > 0:
            up = ctrl.operator("object.move_effector", text="", icon='TRIA_UP', emboss=False)
            up.modifier_name = mod.name; up.direction = 'UP'
        else:
            ctrl.label(text="", icon='BLANK1')
        if idx < len(obj.modifiers)-1:
            down = ctrl.operator("object.move_effector", text="", icon='TRIA_DOWN', emboss=False)
            down.modifier_name = mod.name; down.direction = 'DOWN'
        else:
            ctrl.label(text="", icon='BLANK1')
        delete = ctrl.operator("object.delete_effector", text="", icon='X', emboss=False)
        delete.modifier_name = mod.name

        if mod.show_expanded and mod.node_group and hasattr(mod.node_group, 'interface'):
            # --- Показываем связи с клонерами ---
            linked_cloners = []
            for cloner in cloner_mods:
                if mod.name in cloner.node_group.get("linked_effectors", []):
                    linked_cloners.append(cloner)
            
            # Компактный список связанных клонеров
            if linked_cloners:
                link_box = box.box()
                row = link_box.row()
                row.label(text="Linked to:", icon='LINKED')
                for cloner in linked_cloners:
                    row.label(text=cloner.name)
            
            # Кнопка автопривязки
            if not linked_cloners and cloner_mods:
                link_op = box.operator("object.auto_link_effector", text="Auto-Link to Cloners", icon='LINKED')
                link_op.effector_name = mod.name
            
            # Группируем параметры по категориям для лучшей организации
            transform_params = []
            strength_params = []
            field_params = []
            other_params = []
            
            # Сортируем параметры по категориям
            if mod.type == 'NODES' and mod.node_group:
                for socket in mod.node_group.interface.items_tree:
                    if socket.item_type == 'SOCKET' and socket.in_out == 'INPUT' and socket.name not in ["Geometry"]:
                        name = socket.name
                        if name in ["Position", "Rotation", "Scale", "Uniform Scale"]:
                            transform_params.append(socket)
                        elif name in ["Strength", "Enable"]:
                            strength_params.append(socket)
                        elif name in ["Field", "Use Field"]:
                            field_params.append(socket)
                        else:
                            other_params.append(socket)
            
            # Отображаем параметры по категориям
            if strength_params:
                strength_box = box.box()
                strength_box.label(text="Effect:", icon='FORCE_FORCE')
                for socket in strength_params:
                    row = strength_box.row()
                    try:
                        row.prop(mod, f'["{socket.identifier}"]', text=socket.name)
                    except Exception as e:
                        row.label(text=f"Error: {socket.name}")
            
            if transform_params:
                transform_box = box.box()
                transform_box.label(text="Transform:", icon='ORIENTATION_GLOBAL')
                for socket in transform_params:
                    row = transform_box.row()
                    try:
                        row.prop(mod, f'["{socket.identifier}"]', text=socket.name)
                    except Exception as e:
                        row.label(text=f"Error: {socket.name}")
            
            if field_params:
                field_box = box.box()
                field_box.label(text="Field:", icon='OUTLINER_OB_FORCE_FIELD')
                
                # Поля для управления
                for socket in field_params:
                    row = field_box.row()
                    try:
                        row.prop(mod, f'["{socket.identifier}"]', text=socket.name)
                    except Exception as e:
                        row.label(text=f"Error: {socket.name}")
                
                # Проверяем наличие поля
                using_field = mod.get("Use Field", False)
                if using_field:
                    has_driver = False
                    try:
                        if hasattr(mod, "animation_data") and mod.animation_data and mod.animation_data.drivers:
                            drivers = mod.animation_data.drivers
                            for dr in drivers:
                                if dr.data_path == 'Field':
                                    has_driver = True
                                    break
                    except:
                        pass
                    
                    # Кнопка отключения поля
                    field_box.operator("object.effector_remove_field", text="Disconnect", icon='X').effector_name = mod.name
                else:
                    # Кнопка подключения поля
                    field_box.operator("object.effector_add_field", text="Connect Field", icon='ADD').effector_name = mod.name
            
            if other_params:
                other_box = box.box()
                other_box.label(text="Other:", icon='PREFERENCES')
                for socket in other_params:
                    row = other_box.row()
                    try:
                        row.prop(mod, f'["{socket.identifier}"]', text=socket.name)
                    except Exception as e:
                        row.label(text=f"Error: {socket.name}")

# регистрация операторов и панели
classes = (
    EFFECTOR_OT_add_field,
    EFFECTOR_OT_remove_field,
    EFFECTOR_OT_auto_link,
    EFFECTOR_PT_main_panel,
)

def register():
    print("Registering Effector Panel classes...")
    for cls in classes:
        bpy.utils.register_class(cls)
    print(f"Effector Panel registered {len(classes)} classes")

def unregister():
    print("Unregistering Effector Panel classes...")
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("Effector Panel unregistered")
