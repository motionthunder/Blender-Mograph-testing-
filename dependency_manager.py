import bpy

class DependencyManager:
    """Manages relationships between cloners, effectors and fields"""
    
    def __init__(self):
        self.cloner_effector_map = {}  # Maps cloner modifiers to effectors
        self.effector_field_map = {}   # Maps effectors to fields
    
    def link_effector_to_cloner(self, cloner_mod, effector_mod):
        """Link an effector to a cloner"""
        if cloner_mod.name not in self.cloner_effector_map:
            self.cloner_effector_map[cloner_mod.name] = []
        
        if effector_mod.name not in self.cloner_effector_map[cloner_mod.name]:
            self.cloner_effector_map[cloner_mod.name].append(effector_mod.name)
            return True
        return False
    
    def unlink_effector_from_cloner(self, cloner_mod, effector_mod):
        """Unlink an effector from a cloner"""
        if cloner_mod.name in self.cloner_effector_map:
            if effector_mod.name in self.cloner_effector_map[cloner_mod.name]:
                self.cloner_effector_map[cloner_mod.name].remove(effector_mod.name)
                return True
        return False
    
    def link_field_to_effector(self, effector_mod, field_mod):
        """Link a field to an effector"""
        if effector_mod.name not in self.effector_field_map:
            self.effector_field_map[effector_mod.name] = []
        
        if field_mod.name not in self.effector_field_map[effector_mod.name]:
            self.effector_field_map[effector_mod.name].append(field_mod.name)
            return True
        return False
    
    def unlink_field_from_effector(self, effector_mod, field_mod):
        """Unlink a field from an effector"""
        if effector_mod.name in self.effector_field_map:
            if field_mod.name in self.effector_field_map[effector_mod.name]:
                self.effector_field_map[effector_mod.name].remove(field_mod.name)
                return True
        return False
    
    def get_effectors_for_cloner(self, cloner_mod):
        """Get all effectors linked to a cloner"""
        if cloner_mod.name in self.cloner_effector_map:
            return [bpy.context.object.modifiers.get(name) for name in self.cloner_effector_map[cloner_mod.name] 
                   if name in bpy.context.object.modifiers]
        return []
    
    def get_fields_for_effector(self, effector_mod):
        """Get all fields linked to an effector"""
        if effector_mod.name in self.effector_field_map:
            return [bpy.context.object.modifiers.get(name) for name in self.effector_field_map[effector_mod.name] 
                   if name in bpy.context.object.modifiers]
        return []

# Create a global instance
dependency_manager = DependencyManager()