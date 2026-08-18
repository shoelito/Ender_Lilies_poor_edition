"""Encadena los niveles y hace el cambio de uno a otro.

El juego tenía un solo `.tmx` cargado a mano en `Main.py`. Acá vive la lista
ordenada (`con.ORDEN_NIVELES`) y la lógica de pasar de uno al siguiente:
saliendo por la derecha se avanza y por la izquierda se retrocede, entrando
siempre por el borde contrario para que volver sobre tus pasos te deje donde
estabas y no al principio de la zona.

`Niveles` es dueño del mapa *y* de la cámara, porque los dos cambian juntos:
cada nivel tiene su propio tamaño de mundo y la cámara se dimensiona con él.
Por eso `Main` los usa como `niveles.mapa` y `niveles.camara` en vez de tener
variables sueltas que quedarían viejas al cambiar de nivel.

    niveles = Niveles()
    niveles.cargar(0, lili)
    ...
    lado = niveles.mapa.borde_alcanzado(lili)
    if lado and not niveles.cambiar(lili, lado, pantalla):
        niveles.mapa.limitar(lili)      # punta de la cadena: no hay a dónde ir

Los mapas se cargan de a uno. A escala 6 cada nivel ocupa ~100MB entre la
imagen y el lienzo del mundo, así que tener los siete en memoria serían casi
1.5GB: se suelta el anterior antes de armar el nuevo y se tapa el medio
segundo de carga con un fundido a negro.
"""
import gc

import pygame

import Constantes as con
from Camara import Camara
from Mapa import Mapa


class Niveles:
    def __init__(self, orden=None):
        self.orden = list(orden if orden is not None else con.ORDEN_NIVELES)
        self.indice = -1
        self.mapa = None
        self.camara = None

    # ------------------------------------------------------------ consultas
    @property
    def nombre(self):
        """Ruta del nivel actual, para logs y para guardar la partida."""
        return self.orden[self.indice] if 0 <= self.indice < len(self.orden) else None

    def _destino(self, lado):
        """Índice del nivel al que lleva ese borde, o None si es la punta."""
        destino = self.indice + (1 if lado == "derecha" else -1)
        return destino if 0 <= destino < len(self.orden) else None

    def hay_salida(self, lado):
        return self._destino(lado) is not None

    # -------------------------------------------------------------- cambios
    def cargar(self, indice, personaje=None, entrada=None):
        """Deja montado el nivel `indice` y ubica al personaje.

        `entrada` es el costado por el que llega ("izquierda" al avanzar,
        "derecha" al volver). Sin costado se usa el spawn del mapa.
        """
        # Soltar el nivel viejo ANTES de armar el nuevo: si no, durante la
        # carga conviven dos mundos completos en memoria.
        self.mapa = None
        self.camara = None
        gc.collect()

        self.indice = indice
        self.mapa = Mapa(self.orden[indice])
        self.camara = Camara(self.mapa.width, self.mapa.height)

        if personaje is not None:
            self.mapa.colocar(personaje, entrada)
            # Un update con dt=0 la asienta sobre el suelo y sincroniza el
            # hitbox, que es lo que la cámara sigue.
            personaje.update(0, self.mapa.colisiones)
            self.camara.seguir(personaje.hitbox, inmediato=True)
        return self.mapa

    def cambiar(self, personaje, lado, pantalla=None):
        """Pasa al nivel que sigue por ese borde. False si no hay ninguno."""
        destino = self._destino(lado)
        if destino is None:
            return False

        # Entra por el borde opuesto al que usó para salir.
        entrada = "izquierda" if lado == "derecha" else "derecha"

        if pantalla is not None:
            self._fundido(pantalla, entrando=False)
        self.cargar(destino, personaje, entrada)
        if pantalla is not None:
            self.dibujar(pantalla, personaje)
            self._fundido(pantalla, entrando=True)
        return True

    # --------------------------------------------------------------- dibujo
    def dibujar(self, pantalla, personaje=None, enemigos=()):
        """Un frame completo del mundo sobre la pantalla, sin HUD.

        Lo usa el fundido para tener algo abajo del velo, y sirve de resumen
        del orden de dibujo que hace `Main`."""
        self.camara.limpiar()
        self.mapa.draw(self.camara.mundo, self.camara.vista)
        if con.MAPA_DEBUG_COLISIONES:
            self.mapa.draw_colisiones(self.camara.mundo, self.camara.vista)
        for enemigo in enemigos:
            enemigo.draw(self.camara.mundo)
        if personaje is not None:
            personaje.draw(self.camara.mundo)
        self.camara.volcar(pantalla)

    def _fundido(self, pantalla, entrando):
        """Funde a negro (o desde negro) sobre lo que ya está en pantalla.

        Bloquea el bucle unos cuadros a propósito: el cambio de nivel para el
        juego igual mientras carga, y así la carga queda escondida detrás del
        negro en vez de aparecer como un tirón."""
        duracion = con.NIVEL_TRANSICION_MS
        if duracion <= 0:
            return
        base = pantalla.copy()
        reloj = pygame.time.Clock()
        transcurrido = 0
        while transcurrido < duracion:
            # Sin bombear eventos Windows marca la ventana como colgada.
            pygame.event.pump()
            avance = transcurrido / duracion
            pantalla.blit(base, (0, 0))
            Niveles._velo(pantalla, avance if not entrando else 1 - avance)
            pygame.display.flip()
            transcurrido += reloj.tick(con.CLOCK_FPS)

        if not entrando:
            pantalla.fill((0, 0, 0))
            pygame.display.flip()

    @staticmethod
    def _velo(pantalla, opacidad):
        opacidad = max(0.0, min(1.0, opacidad))
        if opacidad <= 0:
            return
        velo = pygame.Surface(pantalla.get_size())
        velo.fill((0, 0, 0))
        velo.set_alpha(int(255 * opacidad))
        pantalla.blit(velo, (0, 0))
