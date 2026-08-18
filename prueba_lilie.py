"""Comprueba que Lilie se apoya bien en el piso, en todos los mapas.

    python prueba_lilie.py

Mira dos cosas que se ven feo y son fáciles de reintroducir sin darse cuenta:

1. Que no tiemble. Estando apoyada, `y` tiene que quedar quieta. Si la gravedad
   la hunde medio píxel por frame y el choque la empuja de vuelta al siguiente,
   `y` alterna entre dos valores; al dibujar se trunca a entero y el sprite
   salta 1px arriba y abajo a 60fps, que se ve como si saltara sin parar.

2. Que no parpadee la animación. `on_ground` no puede depender de si este frame
   hubo choque o no, porque el estado es "jump" cuando está en el aire y el
   sprite alternaría entre salto y quieta varias veces por segundo.

Y de paso que el arreglo no haya roto lo obvio: que salte, que se caiga de las
plataformas y que en el aire no se crea apoyada.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

import Constantes as con

DT = 1000 // con.CLOCK_FPS
FRAMES = 600


def simular(mapa, Lilie, acciones_fn, frames=FRAMES):
    lili = Lilie(0, 0, 120, 120)
    mapa.colocar(lili)
    lili.update(0, mapa.colisiones)
    ys, estados, suelos = [], [], []
    for f in range(frames):
        lili.movements(acciones_fn(f))
        lili.update(DT, mapa.colisiones)
        ys.append(lili.y)
        estados.append(lili.state)
        suelos.append(lili.on_ground)
    return lili, ys, estados, suelos


def cambios(seq):
    return sum(1 for a, b in zip(seq, seq[1:]) if a != b)


def main():
    pygame.init()
    pygame.display.set_mode((con.WIDTH, con.HEIGHT))
    from Mapa import Mapa
    from Characters.Lilie.Lilie import Lilie

    problemas = []
    print(f"{'mapa':26} {'y tiembla':>11} {'estado cambia':>14}  animacion")
    print("-" * 74)

    for ruta in con.ORDEN_NIVELES:
        nombre = os.path.basename(ruta)
        mapa = Mapa(ruta)

        # Quieta sobre el piso: nada se puede mover.
        _, ys, estados, suelos = simular(mapa, Lilie, lambda f: [])
        tiembla = cambios(ys)
        cambia = cambios(estados)
        en_salto = estados.count("jump")
        print(f"{nombre:26} {tiembla:11} {cambia:14}  "
              f"{'idle' if en_salto == 0 else f'{en_salto} frames en jump!'}")
        if tiembla:
            problemas.append(f"{nombre}: parada quieta, y cambia {tiembla} veces "
                             f"(tiene que quedarse fija)")
        if en_salto:
            problemas.append(f"{nombre}: parada quieta, {en_salto} frames con la "
                             f"animacion de salto")
        del mapa

    # El resto se prueba en un mapa con relieve de sobra.
    mapa = Mapa(con.MAPAS_PATH + "mapa_zona_1.tmx")

    # Salta y vuelve al piso.
    lili, ys, _, _ = simular(mapa, Lilie,
                             lambda f: ["jump"] if f < 30 else [], frames=240)
    y0, pico = ys[0], min(ys)
    print(f"\n  salto: sube {y0 - pico:.0f}px y vuelve a y={lili.y:.0f} "
          f"(salio de {y0:.0f}) suelo={lili.on_ground}")
    if y0 - pico < 50:
        problemas.append("no salta")
    if not lili.on_ground:
        problemas.append("no aterriza despues de saltar")

    # Se cae al salirse de una plataforma: la sonda de suelo no la deja flotando.
    piso = max((r for r in mapa.colisiones
                if r.width > 200 and r.top > mapa.height * 0.4),
               key=lambda r: r.width)
    lili = Lilie(0, 0, 120, 120)
    lili.x, lili.y, lili.vel_y = piso.right - 100, piso.top - 120, 0
    lili.update(0, mapa.colisiones)
    y_antes = lili.y
    for _ in range(120):
        lili.movements(["right"])
        lili.update(DT, mapa.colisiones)
    caida = lili.y - y_antes
    print(f"  caida al salir de la plataforma: {caida:.0f}px")
    if caida < 20:
        problemas.append("no se cae al salirse de una plataforma: queda flotando")

    # En el aire no se cree apoyada.
    lili = Lilie(0, 0, 120, 120)
    lili.x, lili.y, lili.vel_y = piso.centerx, piso.top - 600, 0
    lili.update(DT, mapa.colisiones)
    print(f"  en el aire: suelo={lili.on_ground} vel_y={lili.vel_y:.2f}")
    if lili.on_ground:
        problemas.append("en pleno aire se cree apoyada")

    for p in problemas:
        print(f"  ERROR: {p}")
    print("\n" + ("FALLO" if problemas
                  else "OK: se apoya firme, sin temblor ni parpadeo, y salta y cae bien."))
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
