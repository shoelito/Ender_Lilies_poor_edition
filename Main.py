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
from Camara import Camara
from Mapa import Mapa
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

# --- INTEGRACIÓN DEL MAPA Y CÁMARA ---
# 1. Cargar el mapa Tiled (.tmx). Mapa lo escala para que llene la ventana:
#    mapa.width/height ya vienen en píxeles de pantalla.
mapa = Mapa(con.MAPA_INICIAL)

# 2. La cámara se dimensiona con el mundo ya escalado.
camara = Camara(mapa.width, mapa.height)

# 3. Lilie arranca parada en el spawn del mapa. Las coordenadas del save son de
#    cuando el mundo medía una pantalla, así que no sirven para ubicarla dentro
#    de un nivel de Tiled; el punto lo manda el .tmx (objeto "spawn" si lo hay,
#    si no la primera plataforma pisable del nivel).
lili = Lilie(data["player"]["x"], data["player"]["y"], 120, 120)
mapa.colocar(lili)
lili.update(0, mapa.colisiones)             # la asienta sobre el suelo
camara.seguir(lili.hitbox, inmediato=True)  # arranca ya encuadrada, sin barrido
# --- FIN INTEGRACIÓN MAPA Y CÁMARA ---

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
        lili.update(dt, mapa.colisiones)
        mapa.limitar(lili)      # no se sale del nivel por los costados

        # Red de seguridad: si se cae por un agujero vuelve al spawn en vez de
        # seguir cayendo para siempre fuera del mundo.
        if mapa.se_cayo(lili):
            mapa.colocar(lili)

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

    # Renderizado o Dibujo en el mundo de la cámara
    camara.limpiar((20, 20, 30))

    # --- DIBUJO DEL MAPA ---
    # El nivel ya viene armado en una sola superficie; se vuelca nada más el
    # pedazo que la cámara está mirando.
    mapa.draw(camara.mundo, camara.vista)
    if con.MAPA_DEBUG_COLISIONES:
        mapa.draw_colisiones(camara.mundo, camara.vista)
    # --- FIN DIBUJO MAPA ---

    # 2. Dibujar a los jefes en el mundo
    for jefe in jefes:
        jefe.draw(camara.mundo)

    # 3. Dibujar a Lilie encima del mapa en el mundo
    if hasattr(lili, 'draw'):
        lili.draw(camara.mundo, jefes_vivos)

    # 4. Actualizar la cámara para que siga a Lilie (inmediato=False para suavizado)
    camara.seguir(lili.hitbox)

    # 5. Volcar lo que ve la cámara a la pantalla real
    camara.volcar(screen)

    # 6. Dibujar el HUD directamente sobre la pantalla (queda fijo)
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