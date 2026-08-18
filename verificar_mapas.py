"""Comprueba que todos los .tmx cargan, escalan y traen colisiones usables.

    python verificar_mapas.py

Sirve como chequeo rápido después de tocar un mapa en Tiled: avisa si un
tileset apunta a una imagen que no existe, si un nivel se quedó sin capa de
colisiones o si quedó más bajo que la ventana.
"""
import glob
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

import Constantes as con


def main():
    pygame.init()
    pygame.display.set_mode((con.WIDTH, con.HEIGHT))
    from Mapa import Mapa

    fallos = 0
    for ruta in sorted(glob.glob(con.MAPAS_PATH + "*.tmx")):
        nombre = os.path.basename(ruta)
        try:
            mapa = Mapa(ruta)
        except Exception as e:
            print(f"  FALLA  {nombre}: {type(e).__name__}: {e}")
            fallos += 1
            continue

        pantallas = mapa.width / con.WIDTH
        aviso = ""
        if not mapa.colisiones:
            aviso = "  <-- sin colisiones: Lilie se cae del nivel"
            fallos += 1
        elif mapa.height < con.HEIGHT:
            aviso = "  <-- mas bajo que la ventana"

        print(f"  ok     {nombre:26} {mapa.ancho_original}x{mapa.alto_original}"
              f" -> {mapa.width}x{mapa.height}px"
              f"  escala {mapa.escala:.2f}"
              f"  {pantallas:.1f} pantallas"
              f"  colisiones {len(mapa.colisiones):3}"
              f"  spawn ({mapa.spawn[0]:.0f},{mapa.spawn[1]:.0f}){aviso}")

    print("\n" + ("FALLOS: %d" % fallos if fallos else "Todos los mapas cargan bien."))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
