from abc import ABC, abstractmethod
import pygame


# DECORADOR: evita que un enemigo haga daño demasiadas veces seguidas.
def attack_cooldown(function):
    def wrapper(self, player, damage_function):
        current_time = pygame.time.get_ticks()

        if current_time - self.last_attack >= 800:
            self.last_attack = current_time
            return function(self, player, damage_function)

        return 0

    return wrapper


# ABSTRACCIÓN: clase general para todos los enemigos.
class Enemy(ABC):

    def _init_(self, x, y, width, height, health, damage, speed):
        if health <= 0:
            raise ValueError("La vida debe ser mayor que cero")

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed

        # ENCAPSULAMIENTO
        self.__health = health
        self.__damage = damage

        self.hitbox = pygame.Rect(x, y, width, height)
        self.last_attack = 0

        # CONJUNTO
        self.states = {"alive"}

    def get_health(self):
        return self.__health

    def get_damage(self):
        return self.__damage

    def receive_damage(self, damage):
        if damage < 0:
            raise ValueError("El daño no puede ser negativo")

        self.__health -= damage

        if self.__health <= 0:
            self.__health = 0
            self.states.discard("alive")
            self.states.add("defeated")

    def is_alive(self):
        return "alive" in self.states

    @attack_cooldown
    def attack(self, player, damage_function):
        if self.hitbox.colliderect(player.hitbox):

            # FUNCIÓN DELEGADA
            damage_function(self.__damage)
            return self.__damage

        return 0

    @abstractmethod
    def move(self, player):
        pass

    @abstractmethod
    def draw(self, screen):
        pass


# HERENCIA
class WalkingEnemy(Enemy):

    def _init_(self, x, y, left_limit, right_limit):
        super()._init_(
            x=x,
            y=y,
            width=40,
            height=60,
            health=40,
            damage=10,
            speed=2
        )

        # TUPLA
        self.limits = (left_limit, right_limit)
        self.direction = 1

    # POLIMORFISMO: movimiento del enemigo terrestre.
    def move(self, player):
        distance = player.hitbox.centerx - self.hitbox.centerx

        # Persigue a Lilie cuando se encuentra cerca.
        if abs(distance) < 200:
            if distance > 0:
                self.direction = 1
            else:
                self.direction = -1

        self.x += self.speed * self.direction

        left_limit, right_limit = self.limits

        if self.x <= left_limit:
            self.x = left_limit
            self.direction = 1

        if self.x + self.width >= right_limit:
            self.x = right_limit - self.width
            self.direction = -1

        self.hitbox.x = self.x
        self.hitbox.y = self.y

    def draw(self, screen):
        # Rectángulo provisional para representar al enemigo.
        pygame.draw.rect(screen, (135, 50, 145), self.hitbox)

        # Barra de vida.
        pygame.draw.rect(
            screen,
            (100, 0, 0),
            (self.x, self.y - 8, 40, 5)
        )

        pygame.draw.rect(
            screen,
            (0, 200, 0),
            (self.x, self.y - 8, self.get_health(), 5)
        )


# Segunda clase hija para demostrar herencia y polimorfismo.
class FlyingEnemy(Enemy):

    def _init_(self, x, y):
        super()._init_(
            x=x,
            y=y,
            width=45,
            height=35,
            health=30,
            damage=5,
            speed=1
        )

        self.start_y = y
        self.vertical_direction = 1

    # POLIMORFISMO: movimiento diferente al enemigo terrestre.
    def move(self, player):
        if player.hitbox.centerx > self.hitbox.centerx:
            self.x += self.speed
        else:
            self.x -= self.speed

        self.y += self.vertical_direction

        if self.y >= self.start_y + 30:
            self.vertical_direction = -1

        elif self.y <= self.start_y - 30:
            self.vertical_direction = 1

        self.hitbox.x = self.x
        self.hitbox.y = self.y

    def draw(self, screen):
        # Elipse provisional para representar al enemigo volador.
        pygame.draw.ellipse(screen, (70, 90, 170), self.hitbox)


# ITERADOR PERSONALIZADO
class EnemyIterator:

    def _init_(self, enemies):
        self.enemies = enemies
        self.position = 0

    def _iter_(self):
        return self

    def _next_(self):
        if self.position >= len(self.enemies):
            raise StopIteration

        enemy = self.enemies[self.position]
        self.position += 1

        return enemy


class EnemyManager:

    def _init_(self):

        # LISTA DE DICCIONARIOS CON TUPLAS
        self.enemy_data = [
            {
                "type": "walking",
                "position": (550, 538),
                "limits": (450, 750)
            },
            {
                "type": "walking",
                "position": (900, 538),
                "limits": (800, 1100)
            },
            {
                "type": "flying",
                "position": (700, 350)
            }
        ]

        self.enemies = []

        # Inicia la creación recursiva.
        self.create_recursive(0)

    # FUNCIÓN RECURSIVA
    def create_recursive(self, position):
        # Caso base: termina cuando no quedan datos.
        if position >= len(self.enemy_data):
            return

        data = self.enemy_data[position]

        try:
            if data["type"] == "walking":
                x, y = data["position"]
                left_limit, right_limit = data["limits"]

                enemy = WalkingEnemy(
                    x,
                    y,
                    left_limit,
                    right_limit
                )

                self.enemies.append(enemy)

            elif data["type"] == "flying":
                x, y = data["position"]

                enemy = FlyingEnemy(x, y)
                self.enemies.append(enemy)

        # MANEJO DE EXCEPCIONES
        except (KeyError, TypeError, ValueError) as error:
            print("No se pudo crear un enemigo:", error)

        # Se llama otra vez para crear el siguiente.
        self.create_recursive(position + 1)

    def _iter_(self):
        return EnemyIterator(self.enemies)

    # FUNCIÓN GENERADORA
    def living_enemies(self):
        for enemy in self.enemies:
            if enemy.is_alive():
                yield enemy

    def update(self, player, damage_function):
        try:
            for enemy in self.living_enemies():
                enemy.move(player)
                enemy.attack(player, damage_function)

        except (AttributeError, TypeError) as error:
            print("Error al actualizar los enemigos:", error)

    def draw(self, screen):
        for enemy in self.living_enemies():
            enemy.draw(screen)

    def player_attack(self, attack_hitbox, damage):
        for enemy in self.living_enemies():

            if attack_hitbox.colliderect(enemy.hitbox):
                enemy.receive_damage(damage)

        # FUNCIÓN LAMBDA
        self.enemies = list(
            filter(
                lambda enemy: enemy.is_alive(),
                self.enemies
            )
        )

    def order_by_position(self):
        # Ordena los enemigos de izquierda a derecha con lambda.
        self.enemies.sort(key=lambda enemy: enemy.x)