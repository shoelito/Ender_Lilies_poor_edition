from abc import ABC, abstractmethod

class Ability(ABC):
    def __init__(self, name:str, cooldown:float = 0.0, Inmoving: bool = False, Inair: bool = False, uses:int = 0, baseDamage:int = 0, level:int = 1, frames:list[str] = [], spawn:tuple[int, int] = (0, 0)):
        self.name = name
        self.cooldown = cooldown
        self.Inmoving = Inmoving
        self.Inair = Inair
        self.uses = uses
        self.baseDamage = baseDamage
        self.damage = baseDamage * (1 + level / 4)
        self.level = level
        self.frames = frames
        self.spawn = spawn

    