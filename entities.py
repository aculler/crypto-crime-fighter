import math
import random

import pygame as pg

PLAYERDEADEVENT = pg.USEREVENT + 1

class Entity(pg.sprite.Sprite):
    def __init__(self, game, image, rect, speed):
        super().__init__()

        self.game = game
        self.pos = (rect.x, rect.y)
        self.image = image
        self.rect = rect
        self.speed = speed

        self.game.entities.add(self)

    def draw(self):
        self.game.window.blit(self.image, self.rect)

    def move(self, x, y):
        # If this is a bullet we actually want it to collide and get destroyed 
        if isinstance(self, Bullet):
            self.rect.x += x * self.speed
            self.rect.y += y * self.speed
            return

        starting_x = self.rect.x
        starting_y = self.rect.y

        # Calculate our x position
        vx = x * self.speed
        self.rect.x += vx
        if pg.sprite.spritecollide(self, self.game.walls, False):
            self.rect.x = starting_x

        # Calculate our y position
        vy = y * self.speed
        self.rect.y += vy
        if pg.sprite.spritecollide(self, self.game.walls, False):
            self.rect.y = starting_y

    def remove(self):
        self.kill()
        del self


class Player(Entity):
    def __init__(self, game):
        img = game.load_image('Player.png')
        self.hit_img = game.load_image('PlayerHit.png')
        self.speed = 6
        super().__init__(
            game,
            img,
            img.get_bounding_rect(),
            self.speed
        )

        self.original_image = self.image
        self.can_shoot = True
        self.shot_timer = 0.2
        self.last_shot = -1
        self.score = 0

        self.max_health = 100
        self.health = self.max_health
        self.damage = 5

        self.hit_state = False
        self.hit_state_start = 0
        self.hit_state_duration = 500

    def _rotate(self):
        center_x = self.rect.center[0]
        center_y = self.rect.center[1]

        # Rotate the sprite to face the mouse
        mouse_x, mouse_y = pg.mouse.get_pos()
        rel_x = mouse_x - center_x
        rel_y = mouse_y - center_y
        rotation = ((180 / math.pi) * -math.atan2(rel_y, rel_x)) -90
        self.rotation = rotation

        original_center = self.rect.center
        if not self.hit_state:
            self.image = pg.transform.rotate(self.original_image, rotation)
        else:
            self.image = pg.transform.rotate(self.hit_img, rotation)
        self.rect = self.image.get_rect(center=original_center)

        # Calculate where bullets should spawn so that they appear to come out of the gun barrel
        # Accounting for sprite rotation

        # These are just offsets since we would translate back to the origin to do the rotation anyways
        gun_pos_x = 13
        gun_pos_y = -14
        
        gun_new_x = gun_pos_x * math.cos(rotation) - gun_pos_y * math.sin(rotation)
        gun_new_y = gun_pos_x * math.sin(rotation) + gun_pos_y * math.sin(rotation)

        self.gun_pos = (gun_new_x + center_x, gun_new_y + center_y)

    def _take_action(self):
        # Move the player
        keystate = pg.key.get_pressed()
        x_dir = keystate[pg.K_RIGHT] - keystate[pg.K_LEFT]
        y_dir = keystate[pg.K_DOWN] - keystate[pg.K_UP]

        self.move(x_dir, y_dir)

        # Shoot
        click, _, _ = pg.mouse.get_pressed()
        if click and self.can_shoot and not self.hit_state:
            self.can_shoot = False
            self.last_shot = pg.time.get_ticks()
            m_pos = pg.mouse.get_pos()
            #
            # TODO: I really need to fix the shooting because the bullets are all over the damn place
            #
            # At this point the bullets are consistently originating from the center of the player sprite,
            # which isn't super ideal, but is workable I guess. The frustrating part now is that they don't
            # actually go directly towards the mouse. However, I have been unable to figure this out
            # after spending hours trying, so I just need to move on.
            #
            p_vec = pg.Vector2(self.rect.center)
            m_vec = pg.Vector2(m_pos)


            b_vec = m_vec - p_vec
            b_vec.normalize_ip()
            print(f'b_vec: {b_vec}')

            Bullet(self.game, p_vec.x, p_vec.y, b_vec, Enemy, damage=self.damage)

    def take_hit(self, damage):
        # We don't take damage while we're in a hit state
        if self.hit_state:
            return

        self.health -= damage

        if self.health <= 0:
            pg.event.post(pg.event.Event(PLAYERDEADEVENT))
            return
        else:
            self.hit_state = True
            self.hit_state_start = pg.time.get_ticks()

    def heal(self, add_health):
        self.health = min(self.health + add_health, self.max_health)

    def update(self):
        if self.hit_state:
            if pg.time.get_ticks() >= self.hit_state_start + self.hit_state_duration:
                self.hit_state = False

        if not self.can_shoot:
            now = pg.time.get_ticks()
            if now - self.last_shot >= self.shot_timer * 1000:
                self.can_shoot = True
        self._rotate()

        self._take_action()


class Enemy(Entity):
    def __init__(self, game, x, y):
        img = game.load_image('Enemy.png')
        self.hit_img = game.load_image('EnemyHit.png')
        rect = img.get_bounding_rect()
        rect.x = x
        rect.y = y

        self.orig_img = img

        self.reward_chance = 0.25
        self.reward = Collectable

        self.health = 15
        self.melee_dmg = 5
        self.speed = 3

        self.hit_state = False
        self.hit_state_start = 0
        self.hit_state_duration = 500

        self.last_action = pg.time.get_ticks()
        self.action_timer = random.randint(750, 1500)
        self.rand_action_chance = 0.25
        self.rand_moving = False
        self.move_dir = (0, 0)
        self.attack_range = 300
        self.sight_range = 500

        super().__init__(game, img, rect, self.speed)
        self.game.enemies.add(self)

    def _player_in_range(self, distance):
        myvec = pg.Vector2(self.rect.center)
        playervec = pg.Vector2(self.game.player.rect.center)

        # This seems like a really expensive way to check if there's a wall between the enemy and the player, 
        # but I couldn't figure a better way to do it.
        distance_to_player = myvec.distance_to(playervec)
        if distance_to_player <= distance:
            walls = [w.rect for w in self.game.walls.sprites()]
            # Check every 10 pixels for a wall
            chk_count = int(distance_to_player / 10)
            interval = 1 / chk_count
            for itr in range(1, chk_count - 1):
                point = myvec.lerp(playervec, interval * itr)
                for wall in walls:
                    if wall.collidepoint(point.x, point.y):
                        print('line of sight blocked by wall')
                        return False
            return True
        return False

    def _vec_to_player(self):
        e_vec = pg.Vector2(self.rect.center)
        p_vec = pg.Vector2(self.game.player.rect.center)
        d_vec = p_vec - e_vec
        return d_vec.normalize()

    def update(self):
        if self.hit_state == True:
            self.image = self.hit_img

            if pg.time.get_ticks() >= self.hit_state_start + self.hit_state_duration:
                self.hit_state = False
                self.image = self.orig_img

            # If the enemy is currently hit, it will not take any actions.
            return

        now = pg.time.get_ticks()
        if now >= self.last_action + self.action_timer:
            self.last_action = now
            if self._player_in_range(self.attack_range):
                self.rand_moving = False
                print('player in attack range!')
                b_vec = self._vec_to_player()
                EnemyBullet(self.game, self.rect.center[0], self.rect.center[1], b_vec)

                self.last_action = now
            elif self._player_in_range(self.sight_range):
                self.rand_moving = True
                print('player in sight!')
                m_vec = self._vec_to_player()
                self.move_dir = (m_vec.x, m_vec.y)

                self.last_action = now
            else:
                # If we aren't moving and the player isn't in range, lets see about maybe moving randomly
                if not self.rand_moving:
                    if random.random() >= self.rand_action_chance:
                        self.rand_moving = True
                        newx = random.choice([-1, 0, 1])
                        newy = random.choice([-1, 0, 1])
                        self.move_dir = (newx, newy)

                # If we're already moving and our action timer is expired, lets see if we should stop moving for a bit
                elif self.rand_moving:
                    if random.random() < self.rand_action_chance:
                        self.rand_moving = False

        # If the enemy is already moving, keep on moving. We only change their movement behavior on the action timer
        if self.rand_moving:
            self.move(self.move_dir[0], self.move_dir[1])

    def take_hit(self, damage):
        # We don't take damage while we're in a hit state
        if self.hit_state:
            return
            
        self.health -= damage

        if self.health <= 0:
            self.drop_loot()
            self.remove()
        else:
            self.hit_state = True
            self.hit_state_start = pg.time.get_ticks()

    def drop_loot(self):
        if random.random() <= self.reward_chance:
            self.reward(self.game, self.rect.x, self.rect.y)


class Bullet(Entity):
    def __init__(self, game, x, y, direction, target, damage=5):
        img = game.load_image('Bullet.png')
        b_rect = img.get_bounding_rect()
        b_rect.x = x
        b_rect.y = y
        super().__init__(game, game.load_image('Bullet.png'), b_rect, 20)
        self.game.bullets.add(self)
        self.direction = direction
        self.damage = damage
        self.target = target

    def update(self):
        self.move(self.direction.x, self.direction.y)
        #raise Exception()

        if not self.game.screen_rect.contains(self.rect):
            self.remove()


class EnemyBullet(Bullet):
    def __init__(self, game, x, y, direction):
        super().__init__(game, x, y, direction, Player)

        self.speed = 5


class Wall(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()

        self.game = game
        self.image = game.load_image('BlueWall.png')
        self.rect = self.image.get_bounding_rect()
        self.rect.x = x
        self.rect.y = y

        self.game.walls.add(self)
        self.game.entities.add(self)


class Collectable(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()

        self.game = game
        self.image = game.load_image('Collectable.png')
        self.rect = self.image.get_bounding_rect()
        self.rect.x = x
        self.rect.y = y

        self.reward_health = 20
        self.reward_damage = random.choice([0, 1])

        self.game.collectables.add(self)
        self.game.entities.add(self)
