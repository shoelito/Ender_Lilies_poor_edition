import os
import pygame
import Constantes as con
_LILIE = {
    # Acciones
    "dash":               ("dash.wav", 0.7),
    "salto":              ("salto.wav", 0.6),
    "rezar":              ("rezar.wav", 0.8),
    
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

_ENEMIGOS = {
    "pre_ataque":         ("pre_ataque.wav", 0.7),          
}

CARPETAS = (("Lilie", _LILIE), ("Siegrid", _SIEGRID), ("Enemigos", _ENEMIGOS))

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
