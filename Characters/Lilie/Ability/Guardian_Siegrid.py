from Characters.Ability.Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Guardian_Siegrid(Ability):
    def __init__(self):
        super().__init__(
            name="Guardian Siegrid",
            cooldown=4.5,
            uses=13,
            baseDamage=50,
            level=saved["abilities"][1]["level"],
            frames=[])

    def Attack(self, screen):
        pass

    def Update(self):
        pass

    def ResetUses(self):
        pass

    def name(self):
        return self.name