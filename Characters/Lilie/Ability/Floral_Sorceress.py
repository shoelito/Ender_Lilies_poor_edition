from Characters.Ability.Ability import Ability
import Constantes as con
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Floral_Sorceress(Ability):
    def __init__(self):
        super().__init__(
            name="Floral Sorceress",
            cooldown=4.0,
            uses=12,
            baseDamage=50,
            level=saved["abilities"][4]["level"],
            frames=[],
            animation_speed=5,
            scale=1.0, # los sprites del tornado ya vienen del tamaño de Lilie, no hace falta reducirlos
            offset_x=20, # Si es positivo, aparece más adelante (Y siempre toca el piso)
            anchor_once=True, # se queda donde se invocó, no sigue a Lilie
            duration_frames=5 * con.CLOCK_FPS, # dura ~5 segundos, repitiendo la secuencia
            damage_interval_frames=round(0.5 * con.CLOCK_FPS), # hace daño cada 0.5 segundos
            sound="ataque_floral")
        self.attack_zone = 5
        self._load_frames()

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Floral_Sorceress", "tornado", 6)