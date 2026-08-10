from ..Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Cliffside_Hamlet_Youth(Ability):
    def __init__(self):
        super().__init__(
            name="Cliffside Hamlet Youth",
            cooldown=2.4,
            uses=18,
            baseDamage=50,
            level=saved["abilities"][2]["level"],
            frames=[])

    def Attack(self, screen):
        pass

    def Update(self):
        pass

    def ResetUses(self):
        pass