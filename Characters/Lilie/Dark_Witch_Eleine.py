from ..Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Dark_Witch_Eleine(Ability):
    def __init__(self):
        super().__init__(
            name="Dark Witch Eleine",
            cooldown=0.0,
            uses=70,
            baseDamage=50,
            level=saved["abilities"][5]["level"],
            frames=[])

    def Attack(self, screen):
        pass

    def Update(self):
        pass

    def ResetUses(self):
        pass