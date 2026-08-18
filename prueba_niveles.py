"""Prueba el encadenado de niveles sin abrir ventana.

    python prueba_niveles.py

Son dos pruebas distintas:

1. El mecanismo. Se lleva a Lilie al filo de cada nivel y se comprueba que
   pasa al que corresponde de `con.ORDEN_NIVELES`, que entra por el borde
   contrario, que queda parada sobre suelo y que en las puntas de la cadena no
   hay a dónde salir. Esto recorre los 7 niveles en los dos sentidos y es lo
   que decide si la prueba pasa o falla.

2. El paseo. Un autopiloto que camina hacia un costado y salta cuando se traba,
   para ver hasta dónde llega solo. Es sólo informativo: estos niveles piden
   plataformeo de verdad (repisas, muros que hay que saltar en dos tiempos) y
   un bot que sólo camina no los cruza. Que se quede corto no es un problema
   del encadenado.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

import Constantes as con

CAPTURAS = "capturas_mapa"
DT = 1000 // con.CLOCK_FPS


def asentar(lili, mapa, frames=90):
    """Deja caer al personaje unos cuadros para ver si el piso lo sostiene."""
    for _ in range(frames):
        lili.movements([])
        lili.update(DT, mapa.colisiones)
    return lili.on_ground


# --------------------------------------------------------------- mecanismo
def probar_mecanismo(niveles, lili, pantalla, lado):
    """Empuja a Lilie contra `lado` en cada nivel y sigue la cadena.

    Devuelve la lista de niveles visitados en orden."""
    paso = 1 if lado == "derecha" else -1
    inicio = 0 if lado == "derecha" else len(con.ORDEN_NIVELES) - 1
    niveles.cargar(inicio, lili)
    visitados = [os.path.basename(niveles.nombre)]
    problemas = []

    while True:
        mapa = niveles.mapa
        # Empujarla justo afuera del borde, como si hubiera caminado hasta ahí.
        lili.x = mapa.width if lado == "derecha" else -lili.width

        detectado = mapa.borde_alcanzado(lili)
        if detectado != lado:
            problemas.append(f"{os.path.basename(niveles.nombre)}: el borde "
                             f"{lado} no se detecta (dio {detectado})")
            break

        esperaba_salida = niveles.hay_salida(lado)
        if not niveles.cambiar(lili, lado, pantalla):
            if esperaba_salida:
                problemas.append(f"{os.path.basename(niveles.nombre)}: "
                                 f"deberia salir por {lado} y no salio")
            else:
                mapa.limitar(lili)
                dentro = 0 <= lili.x + lili.width / 2 <= mapa.width
                print(f"    punta de la cadena en {os.path.basename(niveles.nombre)}"
                      f"  {'frena bien' if dentro else 'SE VA DEL MUNDO'}")
                if not dentro:
                    problemas.append("la punta de la cadena no frena al personaje")
            break

        nombre = os.path.basename(niveles.nombre)
        mapa = niveles.mapa
        suelo = asentar(lili, mapa)
        # Al entrar por la izquierda tiene que aparecer del lado izquierdo, y
        # al revés: si no, volver sobre tus pasos te escupe en el otro extremo.
        entrada = "izquierda" if lado == "derecha" else "derecha"
        mitad_ok = (lili.x < mapa.width / 2 if entrada == "izquierda"
                    else lili.x > mapa.width / 2)

        print(f"    -> {nombre:26} entra x={lili.x:7.0f} y={lili.y:7.0f}"
              f"  mundo {mapa.width}x{mapa.height}"
              f"  {'pisa suelo' if suelo else 'NO PISA SUELO'}"
              f"  {'' if mitad_ok else ' ENTRA POR EL LADO EQUIVOCADO'}")
        if not suelo:
            problemas.append(f"{nombre}: entra sin piso abajo")
        if not mitad_ok:
            problemas.append(f"{nombre}: entra por el lado equivocado")

        niveles.dibujar(pantalla, lili)
        pygame.image.save(pantalla, f"{CAPTURAS}/cadena_{lado}_{len(visitados)}_{nombre}.png")
        visitados.append(nombre)

    return visitados, problemas


# ------------------------------------------------------------------ paseo
def probar_paseo(niveles, lili, direccion, max_frames=4000):
    """Autopiloto informativo: cuánto avanza caminando por cada nivel."""
    lado = "derecha" if direccion == "right" else "izquierda"
    inicio = 0 if lado == "derecha" else len(con.ORDEN_NIVELES) - 1
    niveles.cargar(inicio, lili)
    alcanzados = [os.path.basename(niveles.nombre)]

    while True:
        indice_antes = niveles.indice
        frames = trabada = 0
        x_previa = lili.x
        while niveles.indice == indice_antes and frames < max_frames:
            frames += 1
            trabada = trabada + 1 if abs(lili.x - x_previa) < 0.5 else 0
            x_previa = lili.x
            acciones = [direccion]
            if 10 <= trabada <= 12:
                acciones.append("jump")
            lili.movements(acciones)
            lili.update(DT, niveles.mapa.colisiones)
            if niveles.mapa.se_cayo(lili):
                niveles.mapa.colocar(lili)
            borde = niveles.mapa.borde_alcanzado(lili)
            if borde is None or not niveles.cambiar(lili, borde, None):
                niveles.mapa.limitar(lili)

        if niveles.indice == indice_antes:
            avance = lili.x / niveles.mapa.width * 100
            print(f"    se queda en {os.path.basename(niveles.nombre):26}"
                  f" x={lili.x:7.0f} ({avance:.0f}% del nivel)")
            return alcanzados
        alcanzados.append(os.path.basename(niveles.nombre))
        print(f"    cruza a {os.path.basename(niveles.nombre)}")


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((con.WIDTH, con.HEIGHT))
    os.makedirs(CAPTURAS, exist_ok=True)

    from Niveles import Niveles
    from Characters.Lilie.Lilie import Lilie

    esperado = [os.path.basename(r) for r in con.ORDEN_NIVELES]
    print(f"Cadena de {len(esperado)} niveles:")
    for i, nombre in enumerate(esperado):
        print(f"  {i}. {nombre}")

    niveles = Niveles()
    lili = Lilie(0, 0, 120, 120)

    print("\n  MECANISMO, saliendo por la derecha")
    ida, prob_ida = probar_mecanismo(niveles, lili, pantalla, "derecha")
    print("\n  MECANISMO, saliendo por la izquierda")
    vuelta, prob_vuelta = probar_mecanismo(niveles, lili, pantalla, "izquierda")

    problemas = prob_ida + prob_vuelta
    if ida != esperado:
        problemas.append(f"la ida no siguio el orden: {ida}")
    if vuelta != esperado[::-1]:
        problemas.append(f"la vuelta no siguio el orden al reves: {vuelta}")

    print(f"\n  ida    ({len(ida)}/{len(esperado)}): {' -> '.join(ida)}")
    print(f"  vuelta ({len(vuelta)}/{len(esperado)}): {' -> '.join(vuelta)}")

    print("\n  PASEO (informativo: hasta donde llega el autopiloto solo)")
    paseo = probar_paseo(niveles, lili, "right")
    print(f"    cruzo {len(paseo)}/{len(esperado)} niveles caminando: {' -> '.join(paseo)}")

    for p in problemas:
        print(f"  ERROR: {p}")
    print("\n" + ("FALLO" if problemas
                  else "OK: se pasa entre los 7 niveles en los dos sentidos."))
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
