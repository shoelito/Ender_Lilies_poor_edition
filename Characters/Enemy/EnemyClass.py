import pygame
import Sonidos
from Characters.CharacterClass import Character


class Enemy(Character):
    """Base de jefe/enemigo. Sin sprites todavía: se dibuja como un
    rectángulo de color (mismo criterio que el fallback de Character) para
    poder probar vida/daño/muerte antes de tener arte."""

    # Nombre lógico (de Video.VIDEOS) de la cinemática que se dispara al
    # morir este enemigo. None = no tiene.
    VIDEO_MUERTE = None

    def __init__(self, x, y, width, height, max_health, color=(150, 40, 40)):
        super().__init__(x, y, width, height)
        self.max_health = max_health
        self.health = max_health
        self.color = color
        self.state = "idle"  # idle | hurt | dead

        self.hurt_flash_duration = 150  # ms que se ve "golpeado" (blanco)
        self.hurt_timer = 0
        self.invuln_duration = 250  # ms de invulnerabilidad tras cada golpe
        self.invuln_timer = 0

    def avisar_ataque(self):
        """Aviso sonoro al empezar la preparación de un ataque, para que el
        jugador tenga con qué anticiparlo. Lo llama cualquier enemigo al
        arrancar un movimiento que hace daño."""
        Sonidos.reproducir("pre_ataque")

    def take_damage(self, amount):
        if self.state == "dead" or self.invuln_timer > 0:
            return
        self.health = max(0, self.health - amount)
        self.invuln_timer = self.invuln_duration
        if self.health <= 0:
            self.state = "dead"
        else:
            self.state = "hurt"
            self.hurt_timer = self.hurt_flash_duration

    def update(self, dt, target=None):
        if self.state == "dead":
            return

        if self.invuln_timer > 0:
            self.invuln_timer -= dt

        if self.state == "hurt":
            self.hurt_timer -= dt
            if self.hurt_timer <= 0:
                self.state = "idle"

        self.hitbox.x = self.x
        self.hitbox.y = self.y

    def draw(self, screen):
        if self.state == "dead":
            return

        color = (255, 255, 255) if self.state == "hurt" else self.color
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))

        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 0, 0), self.hitbox, 2)

        self._draw_health_bar(screen)

    def _draw_health_bar(self, screen):
        bar_width = self.width
        bar_height = 6
        bar_x = self.x
        bar_y = self.y - bar_height - 6

        pygame.draw.rect(screen, (40, 10, 10), (bar_x, bar_y, bar_width, bar_height))
        ratio = self.health / self.max_health if self.max_health else 0
        pygame.draw.rect(screen, (200, 40, 40), (bar_x, bar_y, int(bar_width * ratio), bar_height))
