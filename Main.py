import pygame
import sys
import Constantes as con
import Sonidos
import Video
from Menu import Menu
from Characters.Lilie.Lilie import Lilie
from Characters.Enemy.Guardian_Siegrid import Guardian_Siegrid
from Characters.Enemy.Dark_Witch_Eleine import Dark_Witch_Eleine
import json
from movements import handle_inputs

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.set_num_channels(32)
Sonidos.precargar()

screen = pygame.display.set_mode((con.WIDTH, con.HEIGHT))
pygame.display.set_caption("Ender Lilies: Quietus of the Knights - Poor Edition")
reloj = pygame.time.Clock()

Video.reproducir(screen, "intro")

# Ejecutamos el Menú Principal
menu_principal = Menu(screen)
slot_seleccionado = menu_principal.ejecutar()

NumeroDePartida = slot_seleccionado + 1

with open(f"SavedCampaing/PreSaved{NumeroDePartida}.json", "r") as f:
    data = json.load(f)

Video.reproducir(screen, "partida")
reloj.tick(con.CLOCK_FPS)

lili = Lilie(data["player"]["x"], data["player"]["y"], 120, 120)

# Cargar la imagen del Nivel 3 desde la ruta exacta de tus assets
imagen_mapa = pygame.image.load("Assets/Lilie/map/tileset_mapa/Fondos/Nivel 3.jpeg").convert()

# Jefes de prueba
jefes = [
    #Guardian_Siegrid(data["player"]["x"] + 300, con.GROUND_Y - 200),
    #Dark_Witch_Eleine(data["player"]["x"] + 600),
]

acciones_activas = []

video_pendiente = None
fundido_hasta = 0
vistos = set()

while True:
    dt = reloj.tick(con.CLOCK_FPS)

    acciones_activas = handle_inputs(acciones_activas)

    if "quit" in acciones_activas:
        pygame.quit()
        sys.exit()

    # Congelado cuando reproduce videos
    congelado = video_pendiente is not None

    if not congelado:
        lili.movements(acciones_activas, screen)
        lili.update(dt)

    jefes_vivos = []
    for jefe in jefes:
        if not congelado:
            jefe.update(dt, lili)
        if jefe.state != "dead":
            jefes_vivos.append(jefe)
        elif (video_pendiente is None and jefe.VIDEO_MUERTE and jefe.VIDEO_MUERTE not in vistos):
            vistos.add(jefe.VIDEO_MUERTE)
            video_pendiente = jefe.VIDEO_MUERTE
            fundido_hasta = pygame.time.get_ticks() + con.VIDEO_FUNDIDO_MS

    # Renderizado o Dibujo en pantalla
    screen.fill((20, 20, 30))

    # 1. Dibujar el mapa del Nivel 3 como fondo primero
    screen.blit(imagen_mapa, (0, 0))

    # 2. Dibujar a los jefes
    for jefe in jefes:
        jefe.draw(screen)

    # 3. Dibujar a Lilie encima del mapa
    if hasattr(lili, 'draw'):
        lili.draw(screen, jefes_vivos)

    # 4. Dibujar el HUD
    lili.draw_hud(screen)

    if video_pendiente is not None:
        restante = fundido_hasta - pygame.time.get_ticks()
        avance = 1 - max(0, restante) / con.VIDEO_FUNDIDO_MS
        Video.superponer_oscurecido(screen, avance)
        pygame.display.flip()
        if restante <= 0:
            Video.reproducir(screen, video_pendiente)
            video_pendiente = None
            reloj.tick(con.CLOCK_FPS)
        continue

    pygame.display.flip()