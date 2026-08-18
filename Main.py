import Camara
import os
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
from Niveles import Niveles
from movements import handle_inputs

pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Mando detectado: {joystick.get_name()}")
else:
    print("No se detectó ningún mando. Usando teclado.")
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
# `Niveles` es dueño del mapa y de la cámara: los dos cambian juntos al pasar
# de un nivel al siguiente, así que se los usa siempre como niveles.mapa y
# niveles.camara en vez de guardarlos en variables que quedarían viejas.
niveles = Niveles()

# Lilie arranca parada en el spawn del primer nivel. Las coordenadas del save
# son de cuando el mundo medía una pantalla, así que no sirven para ubicarla
# dentro de un nivel de Tiled; el punto lo manda el .tmx (objeto "spawn" si lo
# hay, si no la primera plataforma pisable).
lili = Lilie(data["player"]["x"], data["player"]["y"], 120, 120)

# Cargar el primer nivel de la cadena: esto inicializa niveles.mapa y
# niveles.camara, y deja a Lilie parada en el spawn del .tmx.
niveles.cargar(0, lili)

# Jefes de prueba
jefes = [
    #Guardian_Siegrid(data["player"]["x"] + 300, con.GROUND_Y - 200),
    #Dark_Witch_Eleine(data["player"]["x"] + 600),
]

acciones_activas = []

video_pendiente = None
fundido_hasta = 0
vistos = set()

# Muerte de Lilie: suena su caida, se oscurece la pantalla y el juego arranca
# de cero. Se relanza el proceso entero en vez de rearmar el estado a mano
# porque la partida se monta a nivel de modulo (menu, mapa, jefes, videos):
# reiniciar el proceso es lo unico que garantiza dejarlo todo como al abrirlo.
muerte_hasta = None


def reiniciar_juego():
    pygame.mixer.music.stop()
    pygame.quit()
    os.execv(sys.executable, [sys.executable] + sys.argv)

while True:
    dt = reloj.tick(con.CLOCK_FPS)

    acciones_activas = handle_inputs(acciones_activas)

    if "quit" in acciones_activas:
        pygame.quit()
        sys.exit()

    if muerte_hasta is None and lili.is_dead:
        Sonidos.reproducir("player_muerte")
        Sonidos.parar_musica()
        muerte_hasta = pygame.time.get_ticks() + con.MUERTE_ESPERA_MS

    # Congelado cuando reproduce videos o mientras se muere Lilie
    congelado = video_pendiente is not None or muerte_hasta is not None

    if not congelado:
        lili.movements(acciones_activas, screen)
        lili.update(dt, niveles.mapa.colisiones)

        # Cambio de nivel: al llegar a un costado se pasa al nivel que sigue en
        # con.ORDEN_NIVELES, entrando por el borde contrario. En las puntas de
        # la cadena no hay a dónde ir, así que sólo topa contra el borde.
        lado = niveles.mapa.borde_alcanzado(lili)
        if lado is None or not niveles.cambiar(lili, lado, screen):
            niveles.mapa.limitar(lili)

        # Red de seguridad: si se cae por un agujero vuelve al spawn en vez de
        # seguir cayendo para siempre fuera del mundo.
        if niveles.mapa.se_cayo(lili):
            niveles.mapa.colocar(lili)

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
    
    jefes = jefes_vivos

    # Renderizado o Dibujo en el mundo de la cámara. `mapa` y `camara` salen de
    # `niveles` porque los dos cambian al pasar de nivel.
    screen.fill((20, 20, 30))
    niveles.camara.limpiar((20, 20, 30))

    # --- DIBUJO DEL MAPA ---
    # El nivel ya viene armado en una sola superficie; se vuelca nada más el
    # pedazo que la cámara está mirando.
    niveles.mapa.draw(niveles.camara.mundo, niveles.camara.vista)
    if con.MAPA_DEBUG_COLISIONES:
        niveles.mapa.draw_colisiones(niveles.camara.mundo, niveles.camara.vista)
    # --- FIN DIBUJO MAPA ---

    # 2. Dibujar a los jefes en el mundo
    for jefe in jefes:
        jefe.draw(niveles.camara.mundo)

    # 3. Dibujar a Lilie encima del mapa en el mundo
    if hasattr(lili, 'draw'):
        lili.draw(niveles.camara.mundo, jefes_vivos)

    # 4. Actualizar la cámara para que siga a Lilie (inmediato=False para suavizado)
    niveles.camara.seguir(lili.hitbox)

    # 5. Volcar lo que ve la cámara a la pantalla real
    niveles.camara.volcar(screen)

    # 6. Dibujar el HUD directamente sobre la pantalla (queda fijo)
    lili.draw_hud(screen)

    if muerte_hasta is not None:
        restante = muerte_hasta - pygame.time.get_ticks()
        avance = 1 - max(0, restante) / con.MUERTE_ESPERA_MS
        Video.superponer_oscurecido(screen, avance)
        pygame.display.flip()
        if restante <= 0:
            reiniciar_juego()
        continue

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