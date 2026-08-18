import pygame
from pytmx.util_pygame import load_pygame

import Constantes as con


class Mapa:
    """Un nivel: sus tiles ya compuestos, su tamaño en píxeles y sus colisiones.

    El .tmx viene a resolución de tile (el nivel 3 son 50x10 tiles de 32 px =
    1600x320 px), pero el juego trabaja en un espacio de 1280x720 con el piso
    en con.GROUND_Y. Dibujado tal cual, el mapa ocuparía la franja de arriba y
    Lilie y los jefes quedarían por debajo, fuera de la imagen.

    Por eso el mapa se escala al cargarlo. Con `alinear_suelo` la escala se
    deduce del propio nivel: la que hace que su piso caiga justo en GROUND_Y,
    así los personajes apoyan sobre el suelo dibujado sin tocar ninguna
    constante del juego.
    """

    def __init__(self, filename, escala=None, alinear_suelo=True):
        self.tmxdata = load_pygame(filename)
        t = self.tmxdata

        self.ancho_nativo = t.width * t.tilewidth
        self.alto_nativo = t.height * t.tileheight

        colisiones_nativas = [pygame.Rect(o.x, o.y, o.width, o.height) for o in t.objects]

        if escala is None:
            escala = self._escala_automatica(colisiones_nativas, alinear_suelo)
        self.escala = escala

        self.width = round(self.ancho_nativo * escala)
        self.height = round(self.alto_nativo * escala)

        self.colisiones = [pygame.Rect(round(r.x * escala), round(r.y * escala), round(r.width * escala), round(r.height * escala)) for r in colisiones_nativas]
        self.suelo_y = min((r.y for r in self.colisiones), default=self.height)

        # Los tiles se componen una sola vez en un lienzo. Antes se recorrían
        # las 500 casillas de cada capa en cada frame; ahora dibujar el nivel
        # es un solo blit.
        self.superficie = self._componer()

    def _escala_automatica(self, colisiones, alinear_suelo):
        """Escala del nivel. Con el piso identificado se usa la que lo deja en
        GROUND_Y; si el mapa no trae colisiones, se estira al alto de la
        ventana."""
        if alinear_suelo and colisiones:
            suelo = min(r.y for r in colisiones)
            if suelo > 0:
                return con.GROUND_Y / suelo
        return con.HEIGHT / self.alto_nativo

    def _componer(self):
        lienzo = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        t = self.tmxdata
        ancho = round(t.tilewidth * self.escala)
        alto = round(t.tileheight * self.escala)
        cache = {}

        for capa in t.visible_layers:
            if not hasattr(capa, "data"):
                continue
            for x, y, gid in capa:
                tile = t.get_tile_image_by_gid(gid)
                if not tile:
                    continue
                if gid not in cache:
                    cache[gid] = pygame.transform.scale(tile, (ancho, alto))
                lienzo.blit(cache[gid], (x * ancho, y * alto))
        return lienzo

    def draw(self, surface, origen=(0, 0)):
        surface.blit(self.superficie, origen)
