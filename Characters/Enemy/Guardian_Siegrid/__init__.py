"""Guardian Siegrid: la jefa y el descriptor de sus golpes.

Se reexportan acá para que el resto del juego siga escribiendo
    from Characters.Enemy.Guardian_Siegrid import Guardian_Siegrid
sin tener que repetir el nombre del paquete.
"""
from Characters.Enemy.Guardian_Siegrid.Move import Move
from Characters.Enemy.Guardian_Siegrid.Guardian_Siegrid import Guardian_Siegrid

__all__ = ["Guardian_Siegrid", "Move"]
