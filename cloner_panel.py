import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty

from ..cloners import CLONER_TYPES, CLONER_NODE_GROUP_PREFIXES
from ..effectors import EFFECTOR_NODE_GROUP_PREFIXES as EFF_PREFIXES

# Import the update_cloner_with_effectors function
from ...utils.cloner_utils import update_cloner_with_effectors

# ——— Операторы для привязки/отвязки эффекторов ———

class CLONER_OT_add_effector(Operator):
    bl_idname = "object.cloner_add_effector"
    bl_label  = "Add Effector to Cloner"
    cloner_name: StringProperty()

    def execute(self, context):
        obj = context.active_object
        mod = obj.modifiers.get(self.cloner_name)
        if not mod or not mod.node_group:
            return {'CANCELLED'}
        grp = mod.node_group
        linked = list(grp.get("linked_effectors", []))
        
        # Найдем все эффекторы на объекте
        unlinked_effectors = []
        for m in obj.modifiers:
            if not m.node_group:
                continue
                
            # Проверяем, что это эффектор
            is_effector = False
            for prefix in EFF_PREFIXES:
                if m.node_group.name.startswith(prefix):
                    is_effector = True
                    break
                    
            # Проверяем, что эффектор еще не связан с этим клонером
            if is_effector and m.name not in linked:
                unlinked_effectors.append(m.name)
        
        # Если нет несвязанных эффекторов, сообщаем об этом
        if not unlinked_effectors:
            self.report({'INFO'}, "Нет доступных эффекторов для привязки")
            return {'CANCELLED'}
            
        # Добавляем первый несвязанный эффектор
        added_effector_name = unlinked_effectors[0]
        linked.append(added_effector_name)
        grp["linked_effectors"] = linked
        
        # Активируем эффектор, устанавливая его параметры
        effector_mod = obj.modifiers.get(added_effector_name)
        if effector_mod and effector_mod.node_group:
            # Включаем отображение эффектора, так как он теперь привязан
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
        
        # Обновляем нод-группу клонера с эффекторами
        update_cloner_with_effectors(obj, mod)
        
        return {'FINISHED'}

class CLONER_OT_remove_effector(Operator):
    bl_idname = "object.cloner_remove_effector"
    bl_label  = "Remove Effector from Cloner"
    cloner_name:   StringProperty()
    effector_name: StringProperty()

    def execute(self, context):
        obj = context.active_object
        mod = obj.modifiers.get(self.cloner_name)
        if not mod or not mod.node_group:
            return {'CANCELLED'}
        grp = mod.node_group
        linked = list(grp.get("linked_effectors", []))
        if self.effector_name in linked:
            linked.remove(self.effector_name)
            grp["linked_effectors"] = linked
            
            # Проверим, нужно ли отключить эффектор полностью
            # Проверяем, связан ли эффектор с другими клонерами
            effector_still_used = False
            for m in obj.modifiers:
                if m != mod and m.type == 'NODES' and m.node_group and m.node_group.get("linked_effectors") is not None:
                    if self.effector_name in m.node_group.get("linked_effectors", []):
                        effector_still_used = True
                        break
            
            # Если эффектор больше не используется нигде, отключаем его
            if not effector_still_used:
                effector_mod = obj.modifiers.get(self.effector_name)
                if effector_mod and effector_mod.node_group:
                    # Отключаем видимость эффектора, так как он больше не привязан ни к одному клонеру
                    effector_mod.show_viewport = False
                    
                    # Ищем параметры Enable и Strength в интерфейсе эффектора
                    for socket in effector_mod.node_group.interface.items_tree:
                        if socket.item_type == 'SOCKET' and socket.in_out == 'INPUT':
                            if socket.name == "Enable":
                                try:
                                    effector_mod[socket.identifier] = False
                                except:
                                    pass
                            elif socket.name == "Strength":
                                try:
                                    effector_mod[socket.identifier] = 0.0
                                except:
                                    pass
            
            # Обновляем нод-группу клонера с эффекторами
            update_cloner_with_effectors(obj, mod)
            
        return {'FINISHED'}

class CLONER_OT_create_material(Operator):
    bl_idname = "object.cloner_create_material"
    bl_label = "Create New Material"
    bl_options = {'REGISTER', 'UNDO'}
    
    cloner_name: StringProperty()
    
    def execute(self, context):
        obj = context.active_object
        mod = obj.modifiers.get(self.cloner_name)
        if not mod or not mod.node_group:
            return {'CANCELLED'}
            
        # Создаем новый материал
        new_material = bpy.data.materials.new(name=f"Cloner_{self.cloner_name}_Material")
        new_material.use_nodes = True
        
        # Получаем текущий цвет из параметра Color клонера
        color_param_name = None
        for item in mod.node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == "Color":
                color_param_name = item.identifier
                break
                
        if color_param_name:
            try:
                color = mod[color_param_name]
                # Применяем цвет к материалу
                if new_material.node_tree and new_material.node_tree.nodes:
                    principled = new_material.node_tree.nodes.get('Principled BSDF')
                    if principled:
                        principled.inputs['Base Color'].default_value = color
            except:
                pass
                
        # Устанавливаем созданный материал в параметр Material клонера
        material_param_name = None
        for item in mod.node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == "Material":
                material_param_name = item.identifier
                break
                
        if material_param_name:
            try:
                mod[material_param_name] = new_material
            except:
                pass
                
        self.report({'INFO'}, f"Created new material: {new_material.name}")
        return {'FINISHED'}

# ——— Панель Cloners ———

class CLONER_PT_main_panel(Panel):
    bl_label = "Advanced Cloners"
    bl_idname = "CLONER_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Cloners"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        # секция создания клонера
        box = layout.box()
        box.label(text="Create:", icon='ADD')
        col = box.column(align=True)
        for cid, name, _, icon in CLONER_TYPES:
            op = col.operator("object.create_cloner", text=name, icon=icon)
            op.cloner_type = cid

        if not obj:
            layout.label(text="Select an object")
            return

        # найдём ваши модификаторы-клонеры
        mods = [
            m for m in obj.modifiers
            if m.type == 'NODES' and m.node_group
               and any(m.node_group.name.startswith(p) for p in CLONER_NODE_GROUP_PREFIXES)
        ]
        if not mods:
            layout.label(text="No cloners")
            return

        layout.label(text="Cloners:", icon='MODIFIER')
        idxs = {m.name: i for i, m in enumerate(obj.modifiers)}
        for m in mods:
            if m.name in idxs:
                self.draw_cloner_ui(context, layout, obj, m, idxs)

    def draw_cloner_ui(self, context, layout, obj, mod, indices):
        box = layout.box()
        row = box.row(align=True)

        # иконка по префиксу имени нод-группы
        ng = mod.node_group.name
        if ng.startswith("GridCloner3D_"):
            ic = 'MESH_GRID'
        elif ng.startswith("AdvancedLinearCloner"):
            ic = 'SORTSIZE'
        elif ng.startswith("CircleCloner"):
            ic = 'MESH_CIRCLE'
        else:
            ic = 'OBJECT_DATAMODE'

        # Добавляем треугольник раскрытия для большей наглядности
        if mod.show_expanded:
            row.prop(mod, "show_expanded", text="", icon='DISCLOSURE_TRI_DOWN', emboss=False)
        else:
            row.prop(mod, "show_expanded", text="", icon='DISCLOSURE_TRI_RIGHT', emboss=False)
            
        # Иконка типа клонера
        row.label(text="", icon=ic)
        
        # Имя клонера
        row.label(text=mod.name)

        ctrl = row.row(align=True)
        ctrl.alignment = 'RIGHT'
        i = indices[mod.name]
        if i > 0:
            up = ctrl.operator("object.move_cloner", text="", icon='TRIA_UP', emboss=False)
            up.modifier_name = mod.name; up.direction = 'UP'
        else:
            ctrl.label(text="", icon='BLANK1')
        if i < len(obj.modifiers) - 1:
            down = ctrl.operator("object.move_cloner", text="", icon='TRIA_DOWN', emboss=False)
            down.modifier_name = mod.name; down.direction = 'DOWN'
        else:
            ctrl.label(text="", icon='BLANK1')
        rm = ctrl.operator("object.delete_cloner", text="", icon='X', emboss=False)
        rm.modifier_name = mod.name

        if mod.show_expanded and mod.node_group and hasattr(mod.node_group, 'interface'):
            # — Linked Effectors —
            linked = mod.node_group.get("linked_effectors", [])
            if linked or has_unlinked_effectors(obj, linked):
                eff_box = box.box()
                eff_box.label(text="Effectors:", icon='LINKED')
                
                # Список связанных эффекторов
                for en in linked:
                    r = eff_box.row(align=True)
                    r.label(text=en)
                    op = r.operator("object.cloner_remove_effector", text="", icon='X', emboss=False)
                    op.cloner_name = mod.name
                    op.effector_name = en
                
                # Кнопка добавления эффектора
                if has_unlinked_effectors(obj, linked):
                    add = eff_box.operator("object.cloner_add_effector", text="Add Effector", icon='ADD')
                    add.cloner_name = mod.name

            # Параметры клонера, сгруппированные по категориям
            # Group parameters by category for better organization
            basic_params = []
            global_transform_params = []
            instance_transform_params = []
            material_params = []
            random_params = []
            collection_params = []
            other_params = []
            
            for item in mod.node_group.interface.items_tree:
                if item.item_type=='SOCKET' and item.in_out=='INPUT' and item.name!="Geometry":
                    # Categorize parameters
                    if item.name in ["Count", "Count X", "Count Y", "Count Z", "Spacing", "Offset", "Radius", "Height"]:
                        basic_params.append(item)
                    elif item.name.startswith("Global "):
                        global_transform_params.append(item)
                    elif item.name.startswith("Instance ") or item.name in ["Scale Start", "Scale End", "Rotation Start", "Rotation End", "Scale", "Rotation"]:
                        instance_transform_params.append(item)
                    elif item.name in ["Material", "Color", "Keep Original Materials"]:
                        material_params.append(item)
                    elif item.name.startswith("Random "):
                        random_params.append(item)
                    elif item.name in ["Pick Random Instance"]:
                        collection_params.append(item)
                    else:
                        other_params.append(item)
            
            # Draw Basic Parameters
            if basic_params:
                basic_box = box.box()
                basic_box.label(text="Basic:", icon='PREFERENCES')
                for item in basic_params:
                    r = basic_box.row()
                    r.context_pointer_set("modifier", mod)
                    r.prop(mod, f'["{item.identifier}"]', text=item.name)
            
            # Draw Global Transform Parameters
            if global_transform_params:
                global_box = box.box()
                global_box.label(text="Global:", icon='WORLD')
                for item in global_transform_params:
                    r = global_box.row()
                    r.context_pointer_set("modifier", mod)
                    r.prop(mod, f'["{item.identifier}"]', text=item.name.replace("Global ", ""))
            
            # Draw Instance Transform Parameters
            if instance_transform_params:
                instance_box = box.box()
                instance_box.label(text="Instance:", icon='TOOL_SETTINGS')
                for item in instance_transform_params:
                    r = instance_box.row()
                    r.context_pointer_set("modifier", mod)
                    label = item.name
                    if item.name.startswith("Instance "):
                        label = item.name.replace("Instance ", "")
                    r.prop(mod, f'["{item.identifier}"]', text=label)
            
            # Draw Material Parameters
            if material_params:
                material_box = box.box()
                material_box.label(text="Material:", icon='MATERIAL')
                
                # Выбор материала из списка доступных материалов
                material_item = None
                color_item = None
                
                # Сначала ищем параметры материала и цвета
                for item in material_params:
                    if item.name == "Material":
                        material_item = item
                    elif item.name == "Color":
                        color_item = item
                
                # Отображаем элементы интерфейса материала
                if material_item and color_item:
                    # Цвет показываем как цветовой пикер
                    r = material_box.row()
                    r.context_pointer_set("modifier", mod)
                    r.prop(mod, f'["{color_item.identifier}"]', text="Color")
                    
                    # Кнопка создания нового материала с текущим цветом
                    r = material_box.row()
                    r.operator("object.cloner_create_material", text="Create Material from Color").cloner_name = mod.name
                    
                    # Выбор существующего материала
                    r = material_box.row()
                    r.prop_search(mod, f'["{material_item.identifier}"]', bpy.data, "materials", text="Material")
                
                # Показываем остальные параметры материала
                for item in material_params:
                    if item.name not in ["Material", "Color"]:
                        r = material_box.row()
                        r.context_pointer_set("modifier", mod)
                        r.prop(mod, f'["{item.identifier}"]', text=item.name)
            
            # Draw Random Parameters
            if random_params:
                random_box = box.box()
                random_box.label(text="Random:", icon='RNDCURVE')
                for item in random_params:
                    r = random_box.row()
                    r.context_pointer_set("modifier", mod)
                    r.prop(mod, f'["{item.identifier}"]', text=item.name)
            
            # Draw Collection Parameters
            if collection_params:
                collection_box = box.box()
                collection_box.label(text="Collection:", icon='OUTLINER_OB_GROUP_INSTANCE')
                for item in collection_params:
                    r = collection_box.row()
                    r.context_pointer_set("modifier", mod)
                    r.prop(mod, f'["{item.identifier}"]', text=item.name)
            
            # Draw Other Parameters
            if other_params:
                other_box = box.box()
                other_box.label(text="Other:", icon='SETTINGS')
                for item in other_params:
                    r = other_box.row()
                    r.context_pointer_set("modifier", mod)
                    r.prop(mod, f'["{item.identifier}"]', text=item.name)


# Вспомогательная функция для проверки наличия несвязанных эффекторов
def has_unlinked_effectors(obj, linked):
    for m in obj.modifiers:
        if not m.node_group:
            continue
        
        # Проверяем, что это эффектор
        is_effector = False
        for prefix in EFF_PREFIXES:
            if m.node_group.name.startswith(prefix):
                is_effector = True
                break
                
        if is_effector and m.name not in linked:
            return True
    return False

# регистрируем всё вместе
classes = (
    CLONER_OT_add_effector,
    CLONER_OT_remove_effector,
    CLONER_OT_create_material,
    CLONER_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
