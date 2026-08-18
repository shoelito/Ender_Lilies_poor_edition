"""Límites del nivel que se está jugando.

Antes el mundo medía exactamente una pantalla, así que quien necesitaba saber
dónde terminaba —los proyectiles para desaparecer, los jefes para no salirse—
usaba con.WIDTH. Con la cámara el nivel puede ser mucho más ancho, y ese
tamaño sale del .tmx recién al cargarlo, así que no puede vivir en Constantes.

Main lo fija una vez al entrar al nivel:

    import Mundo
    mapa = Mapa(...)
    Mundo.definir(mapa.width, mapa.height)

Mientras no se llame a definir(), vale una pantalla, que es como se comportaba
el juego antes y lo que necesitan los tests que no cargan un mapa.
"""
import Constantes as con

ancho = con.WIDTH
alto = con.HEIGHT


def definir(ancho_nivel, alto_nivel):
    global ancho, alto
    ancho = ancho_nivel
    alto = alto_nivel


def limitar_x(x, ancho_objeto=0):
    """Deja x dentro del nivel, contando el ancho del objeto."""
    return max(0, min(ancho - ancho_objeto, x))
