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

        # Zona muerta: mientras el objetivo esté dentro de esta franja central
        # la cámara no se mueve. Evita que temblequee con cada pasito.
        self.zona_muerta_x = con.CAMARA_ZONA_MUERTA
        # 0 = no sigue, 1 = pega el salto instantáneo. Los valores bajos dan
        # ese arrastre suave típico de los metroidvania.
        self.suavizado = con.CAMARA_SUAVIZADO
        # Se ve en las franjas que el nivel no llega a cubrir.
        self.color_borde = (0, 0, 0)

    # ------------------------------------------------------------ seguimiento
    def _objetivo_x(self, foco):
        """Dónde debería estar el borde izquierdo de la vista."""
        deseado = self.vista.x
        limite_izq = self.vista.x + self.zona_muerta_x
        limite_der = self.vista.right - self.zona_muerta_x
        if foco.centerx < limite_izq:
            deseado = foco.centerx - self.zona_muerta_x
        elif foco.centerx > limite_der:
            deseado = foco.centerx - self.vista.width + self.zona_muerta_x
        return deseado

    def seguir(self, foco, inmediato=False):
        """Acerca la vista al objetivo (un Rect en coordenadas del mundo)."""
        destino_x = self._objetivo_x(foco)
        destino_y = foco.centery - self.vista.height // 2

        if inmediato:
            self.vista.x, self.vista.y = destino_x, destino_y
        else:
            self.vista.x += (destino_x - self.vista.x) * self.suavizado
            self.vista.y += (destino_y - self.vista.y) * self.suavizado

        self._encajar()

    def _encajar(self):
        """La vista nunca se sale del mundo. Si el mundo es más chico que la
        vista en algún eje, se centra en vez de dejar un borde negro."""
        if self.limite.width <= self.vista.width:
            self.vista.centerx = self.limite.centerx
        else:
            self.vista.x = max(0, min(self.limite.width - self.vista.width, self.vista.x))

        if self.limite.height <= self.vista.height:
            self.vista.centery = self.limite.centery
        else:
            self.vista.y = max(0, min(self.limite.height - self.vista.height, self.vista.y))

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
        self.mundo.fill(color)

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
