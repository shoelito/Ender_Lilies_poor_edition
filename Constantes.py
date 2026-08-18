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
MAPA_INICIAL = MAPAS_PATH + "mapa_zona_1.tmx"
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