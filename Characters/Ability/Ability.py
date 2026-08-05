from abc import ABC, abstractmethod

class Ability(ABC):
    def __init__(self, name:str, cooldown:float = 0.0, uses:int = 0, baseDamage:int = 0, level:int = 1, frames:list[str] = []):
        self.name = name
        self.cooldown = cooldown
        self.uses = uses
        self.baseDamage = baseDamage
        self.damage = baseDamage * (1 + level / 4)
        self.level = level
        self.frames = frames


    @abstractmethod
    def Attack(self, screen):
        pass

    @abstractmethod
    def Update(self):
        pass

    @abstractmethod
    def ResetUses(self):
        pass