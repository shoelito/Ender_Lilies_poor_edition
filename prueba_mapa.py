"""Corre el bucle del juego sin ventana ni menú, para probar el mapa.

    python prueba_mapa.py [ruta.tmx]

Simula a Lilie caminando hacia la derecha por el nivel entero y comprueba que
pisa suelo, que no se va del mundo y que la cámara la sigue sin salirse de los
límites. Deja capturas en capturas_mapa/ para mirar el resultado.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

import Constantes as con

FRAMES = 900          # 15 segundos a 60fps
DT = 1000 // con.CLOCK_FPS
CAPTURAS = "capturas_mapa"


def main(ruta):
    pygame.init()
    pantalla = pygame.display.get_surface() or pygame.display.set_mode((con.WIDTH, con.HEIGHT))

    from Mapa import Mapa
    from Camara import Camara
    from Characters.Lilie.Lilie import Lilie

    mapa = Mapa(ruta)
    camara = Camara(mapa.width, mapa.height)
    lili = Lilie(0, 0, 120, 120)
    mapa.colocar(lili)
    lili.update(0, mapa.colisiones)
    camara.seguir(lili.hitbox, inmediato=True)

    print(mapa)
    print(f"  spawn      {mapa.spawn}")
    print(f"  Lilie en   ({lili.x:.0f}, {lili.y:.0f})  on_ground={lili.on_ground}")

    os.makedirs(CAPTURAS, exist_ok=True)
    frames_en_suelo = 0
    fuera_del_mundo = 0
    camara_fuera = 0
    y_maxima = lili.y
    x_final = lili.x

    for frame in range(FRAMES):
        # Caminar a la derecha. Cada 3 segundos un salto corto (dos frames de
        # botón, no mantenido) para comprobar que aterriza sobre el suelo del
        # mapa y no lo atraviesa.
        acciones = ["right"]
        if frame % 180 in (0, 1):
            acciones.append("jump")
        lili.movements(acciones)
        lili.update(DT, mapa.colisiones)
        mapa.limitar(lili)
        if mapa.se_cayo(lili):
            fuera_del_mundo += 1
            mapa.colocar(lili)

        camara.limpiar()
        mapa.draw(camara.mundo, camara.vista)
        if con.MAPA_DEBUG_COLISIONES:
            mapa.draw_colisiones(camara.mundo, camara.vista)
        lili.draw(camara.mundo)
        camara.seguir(lili.hitbox)
        camara.volcar(pantalla)
        lili.draw_hud(pantalla)

        if lili.on_ground:
            frames_en_suelo += 1
        y_maxima = max(y_maxima, lili.y)
        x_final = lili.x
        if (camara.vista.left < 0 or camara.vista.right > mapa.width
                or camara.vista.top < 0 or camara.vista.bottom > mapa.height):
            camara_fuera += 1

        if frame in (0, FRAMES // 3, 2 * FRAMES // 3, FRAMES - 1):
            nombre = os.path.basename(ruta).replace(".tmx", "")
            pygame.image.save(pantalla, f"{CAPTURAS}/{nombre}_{frame:04}.png")

    recorrido = x_final - mapa.spawn[0]
    print(f"\n  frames pisando suelo   {frames_en_suelo}/{FRAMES}"
          f"  ({100 * frames_en_suelo / FRAMES:.0f}%)")
    print(f"  recorrido horizontal   {recorrido:.0f}px de {mapa.width}px de nivel")
    print(f"  y maxima alcanzada     {y_maxima:.0f} (alto del mundo {mapa.height})")
    print(f"  caidas fuera del mundo {fuera_del_mundo}")
    print(f"  camara fuera de limite {camara_fuera}")
    print(f"  capturas en            {CAPTURAS}/")

    # El recorrido es sólo informativo: estos niveles tienen pasajes verticales
    # y nadie los cruza manteniendo "derecha" apretado.
    errores = []
    if frames_en_suelo < FRAMES * 0.25:
        errores.append("Lilie casi no toca suelo: las colisiones no la sostienen")
    if camara_fuera:
        errores.append("la camara se sale de los limites del mundo")
    if fuera_del_mundo > FRAMES * 0.05:
        errores.append("se cae del nivel todo el tiempo: revisar spawn y suelos")

    for e in errores:
        print(f"  ERROR: {e}")
    print("\n" + ("FALLO" if errores else "OK: el nivel se recorre bien."))
    return 1 if errores else 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        rutas = sys.argv[1:]
    else:
        import glob
        rutas = sorted(glob.glob(con.MAPAS_PATH + "*.tmx"))

    fallos = 0
    for ruta in rutas:
        print("\n" + "=" * 70)
        fallos += main(ruta)
    print("\n" + "=" * 70)
    print("FALLARON %d nivel(es)" % fallos if fallos else "Todos los niveles pasan.")
    sys.exit(1 if fallos else 0)
