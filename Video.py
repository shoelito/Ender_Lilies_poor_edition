import os
import pygame
import Constantes as con
import Sonidos

try:
    from ffpyplayer.player import MediaPlayer
except ImportError:
    MediaPlayer = None

VIDEOS = {
    "intro":     "intro.mp4",
    "partida":   "primervid.mp4",
    "siegrid":   "siegrid.mp4",
    "eleine":    "eleine.mp4",
}

_avisado = set()


def _ruta(nombre):
    archivo = VIDEOS.get(nombre)
    if archivo is None:
        return None
    return os.path.join(con.VIDEO_PATH, archivo)


def disponible(nombre):
    ruta = _ruta(nombre)
    return MediaPlayer is not None and ruta is not None and os.path.isfile(ruta)


def _silenciar_juego():
    if pygame.mixer.get_init() is None:
        return False
    pygame.mixer.music.pause()
    pygame.mixer.pause()
    return True


def _restaurar_juego(activo):
    if not activo:
        return
    if pygame.mixer.get_init() is None:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(32)
            Sonidos.reiniciar()
        except pygame.error:
            print("No se pudo recuperar el audio después de la cinemática")
        return
    pygame.mixer.unpause()
    pygame.mixer.music.unpause()


def superponer_oscurecido(pantalla, progreso):
    progreso = max(0.0, min(1.0, progreso))
    if progreso <= 0:
        return
    velo = pygame.Surface(pantalla.get_size())
    velo.fill((0, 0, 0))
    velo.set_alpha(int(255 * progreso))
    pantalla.blit(velo, (0, 0))


def _dibujar_aviso(pantalla):
    fuente = pygame.font.Font(None, 30)
    texto = fuente.render("ESC de nuevo para saltar", True, (225, 220, 210))
    fondo = pygame.Surface((texto.get_width() + 24, texto.get_height() + 14))
    fondo.fill((0, 0, 0))
    fondo.set_alpha(150)
    x = pantalla.get_width() - fondo.get_width() - con.HUD_MARGIN
    y = pantalla.get_height() - fondo.get_height() - con.HUD_MARGIN
    pantalla.blit(fondo, (x, y))
    pantalla.blit(texto, (x + 12, y + 7))


def reproducir(pantalla, nombre):
    ruta = _ruta(nombre)
    if MediaPlayer is None:
        if "lib" not in _avisado:
            _avisado.add("lib")
            print("Sin ffpyplayer: no se reproducen cinemáticas (pip install ffpyplayer)")
        return False
    if ruta is None or not os.path.isfile(ruta):
        if nombre not in _avisado:
            _avisado.add(nombre)
            print(f"No se encontró el video '{nombre}' ({ruta})")
        return False

    audio_activo = _silenciar_juego()
    ancho, alto = pantalla.get_size()
    reproductor = MediaPlayer(ruta, ff_opts={"out_fmt": "rgb24"})
    reproductor.set_size(ancho, alto)

    reloj = pygame.time.Clock()
    ultimo_esc = -10_000
    aviso_hasta = 0
    completo = True

    try:
        while True:
            ahora = pygame.time.get_ticks()
            saltar = False
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    reproductor.close_player()
                    _restaurar_juego(audio_activo)
                    pygame.quit()
                    raise SystemExit
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    if ahora - ultimo_esc <= con.VIDEO_SKIP_MS:
                        saltar = True
                    else:
                        ultimo_esc = ahora
                        aviso_hasta = ahora + con.VIDEO_SKIP_MS
            if saltar:
                completo = False
                break

            frame, estado = reproductor.get_frame()
            if estado == "eof":
                break
            if frame is not None:
                imagen, _ = frame
                w, h = imagen.get_size()
                superficie = pygame.image.frombuffer(
                    imagen.to_bytearray()[0], (w, h), "RGB")
                if (w, h) != (ancho, alto):
                    superficie = pygame.transform.smoothscale(superficie, (ancho, alto))
                pantalla.blit(superficie, (0, 0))
                if ahora < aviso_hasta:
                    _dibujar_aviso(pantalla)
                pygame.display.flip()
            reloj.tick(60)
    finally:
        reproductor.close_player()
        _restaurar_juego(audio_activo)

    pantalla.fill((0, 0, 0))
    pygame.display.flip()
    return completo
