"""Cámara que sigue a Lilie.

El juego dibujaba todo directamente sobre la ventana, así que el mundo medía
exactamente una pantalla. Para poder recorrer un nivel más grande hay dos
caminos: pasarle un desplazamiento a cada draw() —son una veintena repartidos
en ocho archivos— o dibujar el mundo entero en su propia superficie y volcar
solo el pedazo visible.

Acá se hace lo segundo: `camara.mundo` es un lienzo del tamaño del nivel y
todos los personajes siguen dibujando en coordenadas del mundo, sin enterarse
de que existe una cámara. Al final del frame, `volcar()` copia la ventana
visible a la pantalla.

    camara = Camara(con.WORLD_WIDTH, con.HEIGHT)
    ...
    camara.mundo.blit(fondo, (0, 0))
    jefe.draw(camara.mundo)
    lili.draw(camara.mundo, enemigos)
    camara.seguir(lili.hitbox)
    camara.volcar(pantalla)
    lili.draw_hud(pantalla)      # el HUD va sobre la pantalla, no se desplaza

Lo que se dibuje sobre `pantalla` después de volcar() queda fijo: HUD, fundidos
y cinemáticas.
"""
import pygame

import Constantes as con


class Camara:
    def __init__(self, ancho_mundo, alto_mundo,
                 ancho_vista=None, alto_vista=None):
        ancho_vista = ancho_vista or con.WIDTH
        alto_vista = alto_vista or con.HEIGHT

        self.mundo = pygame.Surface((ancho_mundo, alto_mundo)).convert()
        self.vista = pygame.Rect(0, 0, ancho_vista, alto_vista)
        self.limite = pygame.Rect(0, 0, ancho_mundo, alto_mundo)

        # Posición real de la vista. `self.vista` es un Rect y un Rect guarda
        # enteros: al interpolar, un avance de 0.9px se truncaba a 0 y la
        # cámara se quedaba clavada a unos píxeles del objetivo para siempre.
        # El decimal vive acá y se copia redondeado al Rect.
        self._x = 0.0
        self._y = 0.0

        # Zona muerta: mientras el objetivo esté dentro de esta franja central
        # la cámara no se mueve. Evita que temblequee con cada pasito.
        self.zona_muerta_x = con.CAMARA_ZONA_MUERTA
        # Lo mismo en vertical. Mientras el mundo medía una pantalla de alto no
        # hacía falta, pero con el mapa a escala real el nivel es más alto que
        # la ventana y sin franja muerta la cámara acompaña cada salto.
        self.zona_muerta_y = getattr(con, "CAMARA_ZONA_MUERTA_Y", 160)
        # 0 = no sigue, 1 = pega el salto instantáneo. Los valores bajos dan
        # ese arrastre suave típico de los metroidvania.
        self.suavizado = con.CAMARA_SUAVIZADO
        # Se ve en las franjas que el nivel no llega a cubrir.
        self.color_borde = (0, 0, 0)

    # ------------------------------------------------------------ seguimiento
    @staticmethod
    def _objetivo(centro, borde, largo, margen):
        """Borde de la vista para un eje: si el objetivo sigue dentro de la
        franja central no se mueve nada, y si se pasó, se corre lo justo para
        dejarlo de vuelta sobre el borde de esa franja."""
        if centro < borde + margen:
            return centro - margen
        if centro > borde + largo - margen:
            return centro - largo + margen
        return borde

    def seguir(self, foco, inmediato=False):
        """Acerca la vista al objetivo (un Rect en coordenadas del mundo)."""
        destino_x = self._objetivo(foco.centerx, self._x,
                                   self.vista.width, self.zona_muerta_x)
        destino_y = self._objetivo(foco.centery, self._y,
                                   self.vista.height, self.zona_muerta_y)

        if inmediato:
            self._x, self._y = destino_x, destino_y
        else:
            self._x += (destino_x - self._x) * self.suavizado
            self._y += (destino_y - self._y) * self.suavizado

        self._encajar()

    def _encajar(self):
        """La vista nunca se sale del mundo. Si el mundo es más chico que la
        vista en algún eje, se centra en vez de dejar un borde negro."""
        if self.limite.width <= self.vista.width:
            self._x = (self.limite.width - self.vista.width) / 2
        else:
            self._x = max(0, min(self.limite.width - self.vista.width, self._x))

        if self.limite.height <= self.vista.height:
            self._y = (self.limite.height - self.vista.height) / 2
        else:
            self._y = max(0, min(self.limite.height - self.vista.height, self._y))

        self.vista.topleft = (round(self._x), round(self._y))

    # ---------------------------------------------------------------- dibujo
    def volcar(self, pantalla):
        """Copia a la pantalla el pedazo de mundo que se ve ahora.

        Si el mundo es más chico que la vista en algún eje, el sobrante se
        rellena y el nivel queda centrado: sin esto la pantalla conservaría
        basura del frame anterior en las franjas que el mundo no cubre."""
        sobra_x = max(0, self.vista.width - self.limite.width)
        sobra_y = max(0, self.vista.height - self.limite.height)
        if sobra_x or sobra_y:
            pantalla.fill(self.color_borde)
        pantalla.blit(self.mundo, (sobra_x // 2, sobra_y // 2), self.vista)

    def limpiar(self, color=(20, 20, 30)):
        """Borra el frame anterior. Sólo la franja visible: el mundo puede
        medir varias pantallas de ancho y repintarlo entero es trabajo que
        nadie llega a ver."""
        self.mundo.fill(color, self.vista.clip(self.limite))

    def pintar_fondo(self, imagen):
        """Repite la imagen a lo ancho del mundo. Estirar un fondo de 16:9
        varias pantallas lo deformaría, así que se embaldosa."""
        ancho = imagen.get_width()
        if ancho <= 0:
            return
        for x in range(0, self.limite.width, ancho):
            self.mundo.blit(imagen, (x, 0))

    # ------------------------------------------------------------- utilidades
    def a_pantalla(self, x, y):
        """Convierte un punto del mundo a coordenadas de pantalla. Sirve para
        lo poco que necesite dibujarse fuera del lienzo del mundo."""
        return (x - self.vista.x, y - self.vista.y)

    def visible(self, rect):
        return self.vista.colliderect(rect)
