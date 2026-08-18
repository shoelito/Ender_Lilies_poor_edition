"""Bruja Oscura Eleine: la jefa y el descriptor de sus hechizos.

Se reexportan acá para que el resto del juego siga escribiendo
    from Characters.Enemy.Dark_Witch_Eleine import Dark_Witch_Eleine
sin tener que repetir el nombre del paquete.
"""
from Characters.Enemy.Dark_Witch_Eleine.Hechizo import Hechizo
from Characters.Enemy.Dark_Witch_Eleine.Dark_Witch_Eleine import Dark_Witch_Eleine

__all__ = ["Dark_Witch_Eleine", "Hechizo"]
