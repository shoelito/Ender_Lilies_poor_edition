import os
import pygame
import Constantes as con
_LILIE = {
    # Acciones
    "dash":               ("dash.wav", 0.7),
    "salto":              ("salto.wav", 0.6),
    "rezar":              ("rezar.wav", 0.8),
    "player_muerte":      ("player_muerte.wav", 0.95),   # Lilie cae
    
    # Habilidades
    "golpe_caballero":    ("golpe_caballero.wav", 0.9),     
    "ataque_floral":      ("ataque_floral.wav", 0.8),       
    "ataque_veneno":      ("ataque_veneno.wav", 0.8),       
    "lanzamiento_gusano": ("lanzamiento_gusano.wav", 0.9),  
    "impacto_gusano":     ("impacto_gusano.wav", 0.9),      
    "tiro_magia":         ("tiro_magia.wav", 0.8),          
}

_SIEGRID = {
    "siegrid_mangual":       ("siegrid_mangual.wav", 0.85),
    "siegrid_mangual_suelo": ("siegrid_mangual_suelo.wav", 0.9),   
    "siegrid_zarpazo":       ("siegrid_zarpazo.wav", 0.85),        
    "siegrid_embestida":     ("siegrid_embestida.wav", 0.8),       
    "siegrid_barrido":       ("siegrid_barrido.wav", 0.85),        
    "siegrid_aplastar":      ("siegrid_aplastar.wav", 1.0),        
    "siegrid_rugido":        ("siegrid_rugido.wav", 1.0),          
    "siegrid_muerte":        ("siegrid_muerte.wav", 0.9),
    "siegrid_golpeada":      ("siegrid_golpeada_1.wav", 0.65),     
}

_ELEINE = {
    "cambio_eleine":      ("cambio_eleine.wav", 0.9),    # cada cambio de fase
}

_ENEMIGOS = {
    "pre_ataque":         ("pre_ataque.wav", 0.7),          
}

CARPETAS = (("Lilie", _LILIE), ("Siegrid", _SIEGRID),
            ("Eleine", _ELEINE), ("Enemigos", _ENEMIGOS))

SONIDOS = {nombre: (os.path.join(carpeta, archivo), volumen) 
           for carpeta, grupo in CARPETAS 
           for nombre, (archivo, volumen) in grupo.items()}

_cache = {}
_faltantes = set()


def _disponible():
    return pygame.mixer.get_init() is not None


def obtener(nombre):
    if nombre in _cache:
        return _cache[nombre]
    if not _disponible():
        return None

    entrada = SONIDOS.get(nombre)
    if entrada is None:
        if nombre not in _faltantes:
            _faltantes.add(nombre)
            print(f"Sonido desconocido: '{nombre}' (no está en Sonidos.SONIDOS)")
        return None

    archivo, volumen = entrada
    ruta = os.path.join(con.SFX_PATH, archivo)
    try:
        sonido = pygame.mixer.Sound(ruta)
    except (pygame.error, FileNotFoundError):
        if nombre not in _faltantes:
            _faltantes.add(nombre)
            print(f"No se pudo cargar el sonido '{ruta}'")
        _cache[nombre] = None
        return None

    sonido.set_volume(volumen * con.SFX_VOLUME)
    _cache[nombre] = sonido
    return sonido


def reproducir(nombre):
    sonido = obtener(nombre)
    if sonido is None:
        return None
    return sonido.play()


def reiniciar():
    _cache.clear()
    _faltantes.clear()


def precargar():
    if not _disponible():
        return 0
    return sum(1 for nombre in SONIDOS if obtener(nombre) is not None)


# ---------------------------------------------------------------- musica
# La musica no pasa por el cache de arriba: son archivos largos (el tema de la
# fase I son 54 MB) y pygame.mixer.music los transmite desde disco en vez de
# cargarlos enteros en memoria. Solo puede sonar un tema a la vez, que es
# justo lo que hace falta para un combate por fases.
MUSICA = {
    "siegrid_fase1": ("music_siegrid_01.wav", 0.55),
    "siegrid_fase2": ("music_siegrid_02.wav", 0.55),
    "eleine_fase1": ("music_eleine_01.wav", 0.55),
    "eleine_fase2": ("music_eleine_02.wav", 0.55),
    "eleine_fase3": ("music_eleine_03.wav", 0.55),
}

_tema_actual = None


def musica(nombre, fundido_ms=600, repetir=True):
    """Pone un tema de fondo. Si ya esta sonando ese, no lo reinicia.

    Devuelve True si quedo sonando. El tema anterior se corta: mixer.music
    tiene un solo canal, asi que no hay mezcla entre dos.
    """
    global _tema_actual
    if not _disponible():
        return False
    if nombre == _tema_actual and pygame.mixer.music.get_busy():
        return True

    entrada = MUSICA.get(nombre)
    if entrada is None:
        if nombre not in _faltantes:
            _faltantes.add(nombre)
            print(f"Tema desconocido: '{nombre}' (no esta en Sonidos.MUSICA)")
        return False

    archivo, volumen = entrada
    ruta = os.path.join(con.MUSIC_PATH, archivo)
    try:
        pygame.mixer.music.load(ruta)
    except (pygame.error, FileNotFoundError):
        if nombre not in _faltantes:
            _faltantes.add(nombre)
            print(f"No se pudo cargar la musica '{ruta}'")
        return False

    pygame.mixer.music.set_volume(volumen * con.SFX_VOLUME)
    pygame.mixer.music.play(-1 if repetir else 0, fade_ms=fundido_ms)
    _tema_actual = nombre
    return True


def parar_musica():
    """Corta el tema de fondo.

    Se usa stop() y no fadeout(): fadeout() bloquea hasta terminar de bajar el
    volumen, o sea que congelaria el juego ese tiempo. Para un apagado suave
    habria que bajar el volumen a lo largo de varios frames.
    """
    global _tema_actual
    _tema_actual = None
    if _disponible():
        pygame.mixer.music.stop()


def tema_actual():
    return _tema_actual
