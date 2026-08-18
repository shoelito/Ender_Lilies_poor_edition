"""Carga de niveles hechos en Tiled (.tmx).

Los niveles de este juego no son tilesets de verdad: cada .tmx es un fondo
pintado (un .jpeg de 1600px de ancho) que Tiled rebanó en cuadritos de 32x32,
más una capa de objetos con los rectángulos de colisión dibujados a mano
encima. Eso trae dos consecuencias que esta clase resuelve:

1. **El mundo nace diminuto.** Un nivel de 50x10 tiles mide 1600x320 píxeles;
   la ventana mide 1280x720. Sin escalar, el nivel entero ocupa menos de media
   pantalla y Lilie (120px) es más alta que el suelo y el techo juntos. Por eso
   `Mapa` calcula una escala para que el nivel llene el alto de la ventana y la
   aplica *tanto al dibujo como a las colisiones*, que es lo que las mantiene
   coincidiendo con lo que se ve.

2. **Redibujar tile por tile cuesta caro.** Son entre 200 y 700 blits por
   frame, siempre idénticos. Acá el nivel se arma una sola vez al cargarlo
   (`self.imagen`) y después cada frame es un único blit del pedazo visible.

Uso:

    mapa = Mapa("Assets/.../mapa_zona_1.tmx")
    camara = Camara(mapa.width, mapa.height)
    ...
    mapa.draw(camara.mundo, camara.vista)
    lili.update(dt, mapa.colisiones)

`mapa.width`/`mapa.height` ya vienen escalados: son el tamaño del mundo en
píxeles de pantalla, que es justo lo que espera `Camara`.
"""
import pygame
from pytmx.util_pygame import load_pygame

import Constantes as con

# Nombres de capa de objetos que se interpretan como colisiones. Se comparan en
# minúscula y sin acentos raros, así que "Colisiones", "colisiones" y
# "colision_suelo" entran todas.
_NOMBRES_COLISION = ("colision", "colisiones", "solido", "solidos", "wall")

# Nombres de objeto que marcan dónde aparece Lilie al entrar al nivel.
_NOMBRES_SPAWN = ("spawn", "inicio", "start", "player", "lilie")

# Marcadores en general: son puntos de referencia, no paredes, así que no
# entran en las colisiones aunque estén dibujados en la misma capa.
_NOMBRES_MARCADOR = _NOMBRES_SPAWN + ("entrada", "salida")

# Ancho del personaje en pantalla. Se usa para no dejarlo parado en un borde
# donde no entra y para separarlo del filo al cambiar de nivel.
ANCHO_PERSONAJE = 120


class Mapa:
    def __init__(self, filename, escala=None, suavizar=None):
        """Carga el .tmx, lo escala y deja listos dibujo y colisiones.

        escala:   None = automática (el nivel llena el alto de la ventana).
                  Un número fuerza esa escala (1.0 = tamaño original de Tiled).
        suavizar: interpolar al agrandar. Los fondos son .jpeg pintados, así
                  que suavizado se ven mejor que con vecino más cercano.
        """
        self.filename = filename
        self.tmxdata = load_pygame(filename)

        if suavizar is None:
            suavizar = getattr(con, "MAPA_SUAVIZAR", True)

        # ---------------------------------------------------------- tamaños
        # Tamaño tal cual salió de Tiled, antes de escalar.
        self.ancho_original = self.tmxdata.width * self.tmxdata.tilewidth
        self.alto_original = self.tmxdata.height * self.tmxdata.tileheight

        if escala is None:
            escala = getattr(con, "MAPA_ESCALA", None)
        if escala is None:
            # Automática: que el alto del nivel calce con el alto de la ventana.
            # Los niveles son tiras horizontales, así que la cámara sólo tendrá
            # que desplazarse en X y nunca quedan franjas negras arriba o abajo.
            escala = con.HEIGHT / self.alto_original if self.alto_original else 1.0
        self.escala = float(escala)

        # Tamaño del mundo en píxeles de pantalla. Es lo que consume `Camara`.
        self.width = max(1, round(self.ancho_original * self.escala))
        self.height = max(1, round(self.alto_original * self.escala))

        # ---------------------------------------------------------- dibujo
        self.imagen = self._prerenderizar(suavizar)

        # ------------------------------------------------------- colisiones
        self.colisiones = self._cargar_colisiones()
        self.spawn = self._buscar_spawn()

    # ------------------------------------------------------------- carga
    def _prerenderizar(self, suavizar):
        """Arma el nivel entero en una superficie, una sola vez.

        Se dibuja primero a tamaño original y recién después se escala el
        conjunto. Escalar tile por tile dejaría costuras de 1px entre cuadritos
        cuando la escala no es entera (2.25, 1.607...), que es justo el caso.
        """
        lienzo = pygame.Surface((self.ancho_original, self.alto_original),
                                pygame.SRCALPHA)

        tw, th = self.tmxdata.tilewidth, self.tmxdata.tileheight
        for layer in self.tmxdata.visible_layers:
            # Capas de tiles (las que tienen data). Las de objetos se saltean:
            # son las colisiones, que no se dibujan salvo en modo debug.
            if hasattr(layer, "data"):
                for x, y, gid in layer:
                    tile = self.tmxdata.get_tile_image_by_gid(gid)
                    if tile:
                        lienzo.blit(tile, (x * tw, y * th))
            # Capas de imagen: un .jpeg suelto puesto directo en Tiled.
            elif hasattr(layer, "image") and layer.image:
                lienzo.blit(layer.image,
                            (getattr(layer, "offsetx", 0) or 0,
                             getattr(layer, "offsety", 0) or 0))

        if (self.width, self.height) != (self.ancho_original, self.alto_original):
            escalar = pygame.transform.smoothscale if suavizar else pygame.transform.scale
            lienzo = escalar(lienzo, (self.width, self.height))

        return lienzo.convert_alpha()

    def _capas_de_colision(self):
        """Devuelve las capas de objetos que hay que tomar como colisión.

        Si alguna capa se llama "colisiones" (o parecido) se usan sólo ésas y
        el resto queda libre para marcadores, spawns o decoración. Si ninguna
        tiene ese nombre —como en `mapa_nivel_3.tmx`, donde la capa quedó con
        el nombre por defecto de Tiled— se usan todas, que es lo que el mapa
        quiso decir.
        """
        grupos = [l for l in self.tmxdata.layers if hasattr(l, "__iter__")
                  and not hasattr(l, "data")]
        nombradas = [l for l in grupos
                     if any(n in (l.name or "").lower() for n in _NOMBRES_COLISION)]
        return nombradas or grupos

    def _cargar_colisiones(self):
        """Convierte los objetos de Tiled en Rects ya escalados.

        Tiled guarda coordenadas con decimales (x=19.25, y=357.75). Si se
        escalan y se truncan por separado, dos plataformas pegadas pueden
        quedar con un hueco de 1px por el que Lilie se cuela. Por eso se
        redondean los cuatro bordes en vez de posición+tamaño: los bordes que
        coincidían en Tiled siguen coincidiendo después de escalar.
        """
        rects = []
        for capa in self._capas_de_colision():
            for obj in capa:
                if getattr(obj, "visible", True) is False:
                    continue
                if any(n in (obj.name or "").lower() for n in _NOMBRES_MARCADOR):
                    continue  # los marcadores no son pared

                x, y, w, h = obj.x, obj.y, obj.width, obj.height

                # Polígonos y polilíneas: se usa su caja envolvente. Ninguno de
                # los mapas actuales tiene, pero si alguien dibuja una rampa en
                # Tiled es mejor tener algo sólido que ignorarla en silencio.
                puntos = getattr(obj, "points", None)
                if puntos:
                    xs = [p[0] for p in puntos]
                    ys = [p[1] for p in puntos]
                    x, y = min(xs), min(ys)
                    w, h = max(xs) - x, max(ys) - y

                izq = round(x * self.escala)
                arr = round(y * self.escala)
                der = round((x + w) * self.escala)
                aba = round((y + h) * self.escala)

                if der - izq <= 0 or aba - arr <= 0:
                    continue  # puntos y objetos de área cero: no son colisión

                rects.append(pygame.Rect(izq, arr, der - izq, aba - arr))

        return self._abrir_bordes(self._absorber_contenidos(rects))

    def _abrir_bordes(self, rects):
        """Saca las paredes que sellan los costados del nivel.

        Cada captura del collage vino con su marco, así que el panel del
        extremo izquierdo y el del derecho tienen una pared vertical pegada al
        filo del mundo. Mientras cada .tmx era un nivel suelto no molestaba; al
        encadenarlos esa pared es la puerta cerrada entre un nivel y el
        siguiente, y Lilie se quedaba golpeándola a 270px de la salida.

        Se sacan sólo las verticales (más altas que anchas) que caen enteras
        dentro del margen de salida: los pisos y las plataformas de las puntas
        quedan intactos, así que no se abre ningún pozo. En los extremos de la
        cadena, donde no hay nivel al que pasar, `limitar` sigue frenándola.
        """
        margen = getattr(con, "NIVEL_MARGEN_SALIDA", 200)

        def es_tapon(r):
            if r.height <= r.width:
                return False        # piso o plataforma: no se toca
            return r.right <= margen or r.left >= self.width - margen

        return [r for r in rects if not es_tapon(r)]

    @staticmethod
    def _absorber_contenidos(rects):
        """Descarta los rects que ya están enteros dentro de otro.

        Los mapas se dibujaron a mano y tienen bastante solapamiento (en
        `mapa_zona_1` hay rectángulos apilados sobre la misma roca). Un rect
        contenido en otro no agrega colisión y sí agrega trabajo: la resolución
        de colisiones recorre la lista completa dos veces por frame.
        """
        ordenados = sorted(rects, key=lambda r: r.width * r.height, reverse=True)
        salida = []
        for r in ordenados:
            if not any(g.contains(r) for g in salida):
                salida.append(r)
        return salida

    def _objeto_marcador(self, nombres):
        """Busca en las capas de objetos un marcador con alguno de esos
        nombres y devuelve su posición ya escalada. None si no está."""
        for capa in self.tmxdata.layers:
            if not hasattr(capa, "__iter__") or hasattr(capa, "data"):
                continue
            for obj in capa:
                nombre = (obj.name or "").lower()
                tipo = (getattr(obj, "type", "") or "").lower()
                if any(n in nombre or n == tipo for n in nombres):
                    return (obj.x * self.escala, obj.y * self.escala)
        return None

    def _candidatos_suelo(self):
        """Plataformas donde tiene sentido dejar parado a un personaje.

        Se les piden tres cosas:
          - que estén en la mitad de abajo del nivel (arriba son techos),
          - que sean más anchas que Lilie, o no hay dónde pararse,
          - que tengan nivel dibujado encima.
        Lo último no es un capricho: estos mapas son un collage de capturas
        sobre fondo blanco, y en `mapa_zona_1` los objetos de más a la
        izquierda son paredes de borde plantadas en el vacío. Sin mirar el
        arte, Lilie aparecía parada en medio de una pantalla en blanco.
        """
        suelos = [r for r in self.colisiones if r.top > self.height * 0.4]
        anchos = [r for r in suelos if r.width >= ANCHO_PERSONAJE]
        con_arte = [r for r in anchos if self._hay_nivel_encima(r)]
        return con_arte or anchos or suelos or self.colisiones

    def _buscar_spawn(self):
        """Punto donde aparece Lilie, en coordenadas del mundo ya escaladas.

        Primero busca un objeto llamado "spawn" (o inicio/start) en cualquier
        capa de objetos de Tiled: esa es la forma correcta de fijarlo y no
        requiere tocar código. Si el mapa no lo trae, deduce un lugar seguro:
        parado sobre la plataforma jugable que esté más a la izquierda.
        """
        marcador = self._objeto_marcador(_NOMBRES_SPAWN)
        if marcador:
            return marcador

        if not self.colisiones:
            return (self.width * 0.1, self.height * 0.25)

        candidatos = self._candidatos_suelo()
        piso = min(candidatos, key=lambda r: (r.left, r.top))
        x = (piso.centerx if piso.width < ANCHO_PERSONAJE * 2
             else piso.left + ANCHO_PERSONAJE / 2)
        return (self._x_dentro(x), piso.top)

    def punto_entrada(self, lado):
        """Dónde aparece alguien que entra al nivel por un costado.

        Al pasar del nivel anterior se entra por la izquierda y al volver del
        siguiente por la derecha, así que el personaje tiene que aparecer
        pegado a ese borde y no en el spawn del nivel: si no, volver sobre tus
        pasos te teletransportaría al principio de la zona.

        Se puede fijar a mano poniendo en Tiled un objeto llamado
        "entrada_izquierda" o "entrada_derecha"; si no está, se toma la
        plataforma pisable más cercana a ese borde.
        """
        marcador = self._objeto_marcador((f"entrada_{lado}",))
        if marcador:
            return marcador
        if not self.colisiones:
            return self.spawn

        candidatos = self._candidatos_suelo()
        if lado == "izquierda":
            piso = min(candidatos, key=lambda r: (r.left, r.top))
            x = piso.left + ANCHO_PERSONAJE / 2
        else:
            piso = max(candidatos, key=lambda r: (r.right, -r.top))
            x = piso.right - ANCHO_PERSONAJE / 2
        return (self._x_dentro(x), piso.top)

    def _x_dentro(self, x):
        """Que el cuerpo entre entero en el nivel aunque la plataforma
        arranque justo sobre el borde."""
        return min(max(x, ANCHO_PERSONAJE / 2), self.width - ANCHO_PERSONAJE / 2)

    def _hay_nivel_encima(self, rect, alto=150, umbral=200):
        """True si arriba de `rect` hay dibujo y no fondo vacío.

        Muestrea unos puntos por encima del rectángulo: si todos salen
        transparentes o casi blancos, ahí no hay nivel, sólo el papel del
        collage."""
        imagen = self.imagen
        ancho_img, alto_img = imagen.get_size()
        for dx in (0.25, 0.5, 0.75):
            for dy in (0.2, 0.5, 0.9):
                x = int(rect.left + rect.width * dx)
                y = int(rect.top - alto * dy)
                if not (0 <= x < ancho_img and 0 <= y < alto_img):
                    continue
                r, g, b, a = imagen.get_at((x, y))
                if a > 10 and not (r > umbral and g > umbral and b > umbral):
                    return True
        return False

    def colocar(self, personaje, lado=None):
        """Deja al personaje de pie en el nivel.

        Sin `lado` va al spawn del mapa (empezar la partida, reaparecer tras
        caerse). Con "izquierda" o "derecha" entra por ese costado, que es lo
        que hace falta al encadenar niveles.

        El punto marca dónde van los pies, así que hay que subir al personaje
        su propia altura y centrarlo sobre él."""
        x, y = self.spawn if lado is None else self.punto_entrada(lado)
        personaje.x = x - personaje.width / 2
        personaje.y = y - personaje.height
        personaje.vel_y = 0
        return personaje

    def borde_alcanzado(self, personaje):
        """"izquierda"/"derecha" si el personaje llegó al filo del nivel.

        Es el disparador del cambio de nivel: se pregunta antes de `limitar`,
        con la posición sin recortar, para saber si quiso salirse."""
        if personaje.x + personaje.width * 0.75 >= self.width:
            return "derecha"
        if personaje.x + personaje.width * 0.25 <= 0:
            return "izquierda"
        return None

    def limitar(self, personaje):
        """Impide que el personaje camine fuera del nivel por los costados.

        Los .tmx no traen paredes en los extremos, así que sin esto Lilie sale
        del mundo caminando y queda dibujándose sobre el vacío. Se usa en las
        puntas de la cadena, donde no hay nivel al que pasar."""
        personaje.x = max(-personaje.width * 0.25,
                          min(self.width - personaje.width * 0.75, personaje.x))

    def se_cayo(self, personaje):
        """True si el personaje quedó por debajo del nivel (se fue por un pozo
        o por un hueco entre plataformas)."""
        return personaje.y > self.height + con.MAPA_MARGEN_CAIDA

    # ------------------------------------------------------------- dibujo
    def draw(self, surface, area=None):
        """Vuelca el nivel ya armado. `area` limita el blit a lo que se ve."""
        if area is None:
            surface.blit(self.imagen, (0, 0))
        else:
            recorte = self.imagen.get_rect().clip(area)
            if recorte.width and recorte.height:
                surface.blit(self.imagen, recorte.topleft, recorte)

    def draw_colisiones(self, surface, area=None, color=(255, 0, 0)):
        """Contornea las colisiones. Para ver si calzan con el dibujo."""
        for rect in self.colisiones:
            if area is None or area.colliderect(rect):
                pygame.draw.rect(surface, color, rect, 2)

    # ---------------------------------------------------------- utilidades
    def dentro(self, rect):
        """True si el rect todavía está dentro de los límites del nivel."""
        return rect.top < self.height

    def __repr__(self):
        return (f"<Mapa {self.filename} {self.width}x{self.height}px "
                f"escala={self.escala:.3f} colisiones={len(self.colisiones)}>")
