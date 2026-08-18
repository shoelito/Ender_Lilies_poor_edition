WIDTH = 1280
HEIGHT = 720
GROUND_OFFSET = 50
GROUND_Y = HEIGHT - GROUND_OFFSET
ASSETS_PATH = "Assets/"
MUSIC_PATH = "Media/Music/"
SFX_PATH = "Assets/SFX/"
SFX_VOLUME = 0.7 # volumen efectos (0.0 - 1.0)
CLOCK_FPS = 60
SPEED = 5
GRAVITY = 0.5
# Píxeles que se le descuentan a Lilie por arriba al chocar con el mapa. Le dan
# aire para pasar por un hueco que mide justo su alto; los pies no se tocan.
HOLGURA_TECHO = 8
# Hasta cuántos píxeles por debajo de los pies se busca piso para considerarla
# apoyada. Cubre el hundimiento de un frame de gravedad y las juntas
# desparejas entre plataformas vecinas. Subirlo la deja "pisando" el aire.
SONDA_SUELO = 4
AXIS_DEADZONE = 0.5
SHOW_HITBOX = True
MAX_IMPURITY = 140
MAX_LVL = 100

# Salud y plegarias de Lilie 
MAX_HEALING_PRAYERS = 3         
PRAYER_HEAL_RATIO = 0.45         
PRAYER_CANCELLED_BY_DAMAGE = True
HURT_INVULN_MS = 700
HURT_FLASH_MS = 250
DASH_INVULN_GRACE_MS = 80
DASH_ALPHA = 170
HUD_MARGIN = 24

# Cinemáticas
VIDEO_PATH = "Assets/Videos/"
VIDEO_SKIP_MS = 1200
VIDEO_FUNDIDO_MS = 5000

# Cámara
CAMARA_ZONA_MUERTA = 300 # Pixeles desde el borde antes de que la cámara empiece a seguir
CAMARA_ZONA_MUERTA_Y = 160 # Igual pero en vertical: sin esto la cámara sube y
                           # baja con cada salto y marea
CAMARA_SUAVIZADO = 0.1   # Interpolación (0.1 es un seguimiento suave)

# Mapas (Tiled)
MAPAS_PATH = "Assets/Lilie/map/tileset_mapa/Mapas/"

# Orden en el que se encadenan los niveles. Saliendo por la derecha se pasa al
# siguiente de la lista y por la izquierda se vuelve al anterior; en las dos
# puntas de la cadena no se sale, sólo se topa contra el borde.
#
# OJO: mapa_nivel_1.tmx y mapa_nivel_2.tmx son idénticos y los dos muestran
# Nivel 2.jpeg. "Nivel 1.jpeg" tiene tileset (fondo_visual_1.1.tsx) pero
# ningún .tmx lo usa, así que el segundo nivel se va a ver igual que el
# tercero hasta que rehagas mapa_nivel_1.tmx en Tiled sobre ese tileset.
ORDEN_NIVELES = [
    MAPAS_PATH + "mapa_nivel_3.tmx",        # Nivel 3.jpeg
    MAPAS_PATH + "mapa_nivel_1.tmx",        # deberia ser Nivel 1.jpeg
    MAPAS_PATH + "mapa_nivel_2.tmx",        # Nivel 2.jpeg
    MAPAS_PATH + "mapa_zona_2.tmx",         # zona 2.jpeg
    MAPAS_PATH + "mapa_zona_1.tmx",         # Zona 1.jpeg
    MAPAS_PATH + "mapa_zona_finalboss.tmx", # zona_1_final_boss.jpeg
    MAPAS_PATH + "mapa_zona_3.tmx",         # zona 3_nivel2.jpeg
]
MAPA_INICIAL = ORDEN_NIVELES[0]
# Duración del fundido a negro con el que se tapa la carga del nivel nuevo.
NIVEL_TRANSICION_MS = 220
# Franja de cada costado que hace de puerta al nivel vecino. Las paredes
# verticales que caen enteras ahí adentro son el marco de la captura, no
# geometría del nivel, y se descartan para poder salir caminando.
NIVEL_MARGEN_SALIDA = 200
# Cuántos píxeles de pantalla mide una unidad de Tiled.
#
# Los .tmx no son tilesets dibujados: son capturas del juego original pegadas
# una al lado de la otra en una imagen de 1600px, y encima los rectángulos de
# colisión. Dentro de esas capturas el personaje mide unas 15 unidades de alto.
# Como el sprite de Lilie mide ~90px de cuerpo, para que quede del tamaño que
# el nivel supone hace falta 90/15 = 6 píxeles por unidad. Con menos, Lilie
# entra gigante y no pasa por los huecos (a escala 1.6 queda tapiada a los
# 650px de haber arrancado la zona 1).
#
# Subirlo agranda y desenfoca el nivel; bajarlo lo deja nítido pero Lilie no
# entra por los pasajes. None = automática (el mapa llena el alto de la
# ventana), útil sólo para mirar un nivel entero de un vistazo.
MAPA_ESCALA = 6.0
# Los fondos son .jpeg pintados, no pixel art: al agrandarlos conviene
# interpolar. Poner en False si algún día el arte pasa a ser pixel art.
MAPA_SUAVIZAR = True
# Dibuja los rectángulos de colisión del .tmx encima del nivel.
MAPA_DEBUG_COLISIONES = False
# Si Lilie cae por debajo del nivel, se la devuelve al spawn a esta distancia
# del borde de abajo del mundo.
MAPA_MARGEN_CAIDA = 400