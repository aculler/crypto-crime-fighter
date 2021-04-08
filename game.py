import csv
import os
import sys
from enum import Enum

import pygame as pg
import pygame_gui as pgui

from entities import Player, Enemy, Wall, Bullet, Collectable, PLAYERDEADEVENT
from levels import LevelManager


class GameState(Enum):
    TITLE = 1
    PAUSE = 2
    PLAYING = 3
    EXIT = 4
    NEWGAME = 5
    GAMEOVER = 6
    INTROSTORY = 7
    WIN = 8


class LevelText(pg.sprite.Sprite):
    def __init__(self, game, x, y, name):
        super().__init__()

        self.game = game

        self.font = pg.font.Font(None, 40)
        self.f_color = pg.Color('#FFFFFF')
        self.name = name
        self.image = self.font.render(f'Level: {self.name}', True, self.f_color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.game.entities.add(self)

    def draw(self):
        self.game.window.blit(self.image, self.rect)

    def update(self):
        self.image = self.font.render(f'Level: {self.name}', True, self.f_color)


class StatsHeaderText(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()

        self.game = game

        self.font = pg.font.Font(None, 40)
        self.f_color = pg.Color('#FFFFFF')
        self.image = self.font.render('Stats:', True, self.f_color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.game.entities.add(self)

    def draw(self):
        self.game.window.blit(self.image, self.rect)

    def update(self):
        self.image = self.font.render('Stats:', True, self.f_color)


class StatsHealthText(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()

        self.game = game

        self.font = pg.font.Font(None, 40)
        self.f_color = pg.Color('#058c0d')
        self.image = self.font.render(f'Health: {self.game.player.health}/{self.game.player.max_health}', True, self.f_color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.game.entities.add(self)

    def draw(self):
        self.game.window.blit(self.image, self.rect)

    def update(self): 
        self.image = self.font.render(f'Health: {self.game.player.health}/{self.game.player.max_health}', True, self.f_color)


class StatsDamageText(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()

        self.game = game

        self.font = pg.font.Font(None, 40)
        self.f_color = pg.Color('#7d0909')
        self.image = self.font.render(f'Damage: {self.game.player.damage}', True, self.f_color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.game.entities.add(self)

    def draw(self):
        self.game.window.blit(self.image, self.rect)

    def update(self):
        self.image = self.font.render(f'Damage: {self.game.player.damage}', True, self.f_color)


# TODO: finish implementing the game window specific stuff and get some game UI done
class Game(object):
    def __init__(self, wind_width, wind_height, game_width, game_height, tile_size):
        pg.init()
        self.state = GameState.TITLE
        self.fps = 30
        # Overall window size
        self.wind_width = wind_width
        self.wind_height = wind_height
        self.screen_rect = pg.Rect(0, 0, self.wind_width, self.wind_height)

        self.game_width = game_width
        self.game_height = game_height
        self.game_rect = pg.Rect(0, 0, self.game_width, self.game_height)

        self.sidebar_rect = pg.Rect(self.game_width, 0, (self.wind_width - self.game_width), (self.wind_height - self.game_height))
        self.sidebar_surface = pg.Surface(self.sidebar_rect.size)
        self.sidebar_surface.fill((255, 0, 0))

        self.level_manager = LevelManager()

        self._init_groups()

        # Size of the gameplay area
        self.game_width = game_width
        self.game_height = game_height

        self.tile_size = tile_size
        self.window = pg.display.set_mode((self.wind_width, self.wind_height))
        pg.display.set_caption('Crypto Crime Fighter')

    def _init_groups(self):
        # Set up game clock and groups
        self.game_clock = pg.time.Clock()
        self.entities = pg.sprite.RenderUpdates()
        self.bullets = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.collectables = pg.sprite.Group()

    def new_game(self):
        # Initialize the player
        self.player = Player(self)
        self.level_manager = LevelManager()

        self.play_level()

    def play_level(self):
        self._init_groups()
        self.entities.add(self.player)

        level = self.level_manager.get_level()

        # Set up stats text
        x_offset = self.game_width + 10
        y_offset = 10

        self.level_text = LevelText(self, x_offset, y_offset, level.name)
        y_offset += self.level_text.rect.height + 30

        self.stat_header = StatsHeaderText(self, x_offset, y_offset)
        y_offset += self.stat_header.rect.height + 10
        
        self.stat_text_health = StatsHealthText(self, x_offset, y_offset)
        y_offset += self.stat_text_health.rect.height + 10

        self.stat_text_dmg = StatsDamageText(self, x_offset, y_offset)
        

        level_grid = level.load()

        # Set up the background tiles
        background_tile = self.load_image('BlueTileFloor.png')
        self.background = pg.Surface(self.screen_rect.size)
        for x in range(0, self.game_width, self.tile_size):
            for y in range(0, self.game_height, self.tile_size):
                grid_x = int(x / self.tile_size)
                grid_y = int(y / self.tile_size)

                if level_grid[grid_y][grid_x] == 'W':
                    Wall(self, x, y)
                elif level_grid[grid_y][grid_x] == 'E':
                    Enemy(self, x, y)
                elif level_grid[grid_y][grid_x] == 'P':
                    # todo: change the player around so that we can initialize it with a position
                    self.player.rect.x = x
                    self.player.rect.y = y
                elif level_grid[grid_y][grid_x] == 'C':
                    Collectable(self, x, y)
                
                self.background.blit(background_tile, (x, y))

        self.window.blit(self.background, (0, 0))
        self.window.blit(self.sidebar_surface, (self.game_width, 0))
        pg.display.flip()

        self.state = GameState.PLAYING

    def title_menu(self):
        manager = pgui.UIManager(self.screen_rect.size)
        bg = pg.Surface(self.screen_rect.size)
        bg.fill(pg.Color('#000000'))

        font = pg.font.Font(None, 150)
        title_text = font.render('Crypto Crime Fighter', True, pg.Color('#FF0000'))
        tt_rect = title_text.get_rect()
        title_x = (self.wind_width / 2) - (tt_rect.width / 2)
        title_y = 400

        # Buttons
        btn_width = 200
        btn_height = 50
        btn_x = (self.wind_width / 2) - (btn_width / 2)
        # Starting y-coordinate for the buttons so that there is room for the header
        btn_y_buffer = title_y + tt_rect.height + 200
        btn_new_game = pgui.elements.UIButton(
            relative_rect=pg.Rect(
                (btn_x, btn_y_buffer), 
                (btn_width, btn_height)
            ),
            text='New Game',
            manager=manager
        )
        btn_y_buffer += btn_height + 10

        btn_exit = pgui.elements.UIButton(
            relative_rect=pg.Rect(
                (btn_x, btn_y_buffer),
                (btn_width, btn_height)
            ),
            text='Exit Game',
            manager=manager
        )

        ui_clock = pg.time.Clock()
        while True:
            time_delta = ui_clock.tick(self.fps)/1000.0
            # Event loop
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.state = GameState.EXIT
                    return
                if event.type == pg.USEREVENT:
                    if event.user_type == pgui.UI_BUTTON_PRESSED:
                        if event.ui_element == btn_new_game:
                            self.state = GameState.INTROSTORY
                            return
                        elif event.ui_element == btn_exit:
                            self.state = GameState.EXIT
                            return

                manager.process_events(event)
            manager.update(time_delta)

            # Screen updates
            self.window.blit(bg, (0, 0))
            self.window.blit(title_text, (title_x, title_y))

            manager.draw_ui(self.window)

            pg.display.update()

    def intro_story(self):
        manager = pgui.UIManager(self.screen_rect.size)
        bg = pg.Surface(self.screen_rect.size)
        bg.fill(pg.Color('#000000'))

        nar = r'<b><font color="#115622">Narrator:</font></b>'
        frank = r'<b><font color="#d78f00">Frank:</font></b>'
        robyn = r'<b><font color="#af0500">Robyn:</font></b>'

        text1_time = 17
        text1 = f"""{nar} Monday. The worst day of the week. As Frank rolled out of bed and brewed a cup of coffee he had no idea what would be in store for him when he logged in to work.
{nar} Steaming cup of Joe in hand, Frank walked into his home office, sat down at his desk, and pulled on his headset. In 2341 most people only commuted to their VR headset. And while Frank was not like most people, in this regard he was the same.
{frank} <i>Yawning.</i> Morning folks. How we lookin'?
{robyn} Morning sunshine. If you had shown up 10 minutes ago I would've said "lookin' good", but we just started getting some weird telemetry from the data cluster in Seattle. I need you to check it out ASAP.
{nar} "Just great" thought Frank. "I should've stayed in bed and let someone else be the first one in...."
{frank} Yea, no problem boss. I'll take a look. Probably just a misconfiguration. Not many people have access to that cluster, so there can't be too much wrong.
{nar} Boy did Frank regret that last statement.
 
<b>[ Space to Continue ]</b>"""

        text2_time = 13
        text2 = f"""{nar} As a seasoned cyber warrior, it only took Frank a few minutes of digging to realize that he had been horribly wrong. This was no misconfiguration. Somehow ransomware had been installed in the cluster and was now trying to encrypt all of the data!
{frank} ...Robyn we have a problem. That cluster is completely infested with a particularly nasty flavor of Ransomware. The automated defenses aren't going to cut it this time...I have to go in.
{robyn} Ahh shit. Well, I'm glad it was you who arrived first today then. You're the best we've got, so go kick some ass out there!
{nar} Frank did not respond, but simply proceeded to load himself into the cluster. This is why he got paid the big bucks. It was time to do battle with the malware - man to byte.
 
<b>[ Space to Continue ]</b>"""

        text3_time = 3
        instruction_text = f"""<b>Move:</b> Arrow keys
 
<b>Aim:</b> Move the mouse

<b>Shoot:</b> Left click
 
<b>Collect dropped computer chips</b> to power up your character.
 
<b>Defeat all the viruses</b> to win the game!
 
<b>[ Space to Start ]</b>"""

        text_list = [text1, text2, instruction_text]
        time_list = [text1_time, text2_time, text3_time]
        text_itr = 0

        current_text = text_list[text_itr]
        current_timer = time_list[text_itr] * 1000

        box_width = 800
        box_height = 600
        box_x = (self.wind_width / 2) - (box_width / 2)
        box_y = (self.wind_height / 2) - (box_height / 2)
        textbox = pgui.elements.UITextBox(
            relative_rect=pg.Rect((box_x, box_y), (box_width, box_height)),
            html_text=current_text.replace('\n', '<br>'),
            manager=manager
        )
        textbox.set_active_effect('typing_appear')

        ui_clock = pg.time.Clock()
        text_finished = False
        text_timer = pg.time.get_ticks()
        while True:
            time_delta = ui_clock.tick(60)/1000.0
            textbox.update(0.5)

            if not text_finished and pg.time.get_ticks() >= text_timer + current_timer:
                text_finished = True

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.state = GameState.EXIT
                    return

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE:
                        if not text_finished:
                            textbox.set_active_effect(None)
                            textbox.rebuild()
                            text_finished = True
                        else:
                            if text_itr == len(text_list) - 1:
                                self.state = GameState.NEWGAME
                                return
                            else:
                                text_finished = False
                                text_itr += 1
                                textbox.html_text = text_list[text_itr].replace('\n', '<br>')
                                current_timer = time_list[text_itr] * 1000
                                textbox.set_active_effect('typing_appear')
                                textbox.rebuild()
                                text_timer = pg.time.get_ticks()

                manager.process_events(event)

            manager.update(time_delta)

            self.window.blit(bg, (0, 0))
            manager.draw_ui(self.window)

            pg.display.update()

    def pause_menu(self):
        manager = pgui.UIManager(self.screen_rect.size)
        bg = pg.Surface(self.screen_rect.size)
        bg.fill(pg.Color('#000000'))

        font = pg.font.Font(None, 150)
        pause_text = font.render("Game Paused", True, pg.Color('#FF0000'))
        pt_rect = pause_text.get_rect()
        text_x = (self.wind_width / 2) - (pt_rect.width / 2)
        text_y = 400

        # Buttons
        btn_width = 200
        btn_height = 50
        btn_x = (self.wind_width / 2) - (btn_width / 2)
        # Starting y-coordinate for the buttons so that there is room for the header
        btn_y_buffer = text_y + pt_rect.height + 200

        btn_continue = pgui.elements.UIButton(
            relative_rect=pg.Rect(
                (btn_x, btn_y_buffer),
                (btn_width, btn_height)
            ),
            text='Continue',
            manager=manager
        )
        btn_y_buffer += btn_height + 10

        btn_main_menu = pgui.elements.UIButton(
            relative_rect=pg.Rect(
                (btn_x, btn_y_buffer),
                (btn_width, btn_height)
            ),
            text='Main Menu',
            manager=manager
        )
        btn_y_buffer += btn_height + 10

        btn_quit = pgui.elements.UIButton(
            relative_rect=pg.Rect(
                (btn_x, btn_y_buffer),
                (btn_width, btn_height)
            ),
            text='Quit Game',
            manager=manager
        )

        ui_clock = pg.time.Clock()
        while True:
            time_delta = ui_clock.tick(self.fps)/1000.0
            # Event loop
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.state = GameState.EXIT
                    return
                if event.type == pg.USEREVENT:
                    if event.user_type == pgui.UI_BUTTON_PRESSED:
                        if event.ui_element == btn_continue:
                            self.state = GameState.PLAYING
                            return
                        elif event.ui_element == btn_main_menu:
                            self.state = GameState.TITLE
                            return
                        elif event.ui_element == btn_quit:
                            self.state = GameState.EXIT
                            return
                manager.process_events(event)
            manager.update(time_delta)

            # Screen updates
            self.window.blit(bg, (0, 0))
            self.window.blit(pause_text, (text_x, text_y))

            manager.draw_ui(self.window)

            pg.display.update()

    def win_menu(self):
        manager = pgui.UIManager(self.screen_rect.size)
        bg = pg.Surface(self.screen_rect.size)
        bg.fill(pg.Color('#000000'))

        nar = r'<b><font color="#115622">Narrator:</font></b>'
        frank = r'<b><font color="#d78f00">Frank:</font></b>'
        robyn = r'<b><font color="#af0500">Robyn:</font></b>'

        text1_time = 9
        text1 = f"""{nar} After several hours of hard fighting, Frank had finally cleared the ransomware from the cluster.
{robyn} Great work, Frank! You really saved our ass on this one. Why don't you take the rest of the day off and go relax a bit.
{frank} Thanks boss. That was one of the more challenging and buggy infections I've seen. Taking the afternoon off would be a welcome change.
{nar} With that, Frank pulled off his headset and headed outside to take a walk. Just another day in the life of a cyber warrior....
 
<b>[ Space to Continue ]</b>"""

        thank_time = 4
        thank_text = f"""Thank you <i>so much</i> for taking the time to play my entry for the <font color="#e167cf"><b>Pygame Community Easter Jam 2021</b></font>. I know it has some rough edges, but I'm generally happy with how it turned out.
 
Thanks for playing.
Andy
 
<b>[ Space to Main Menu ]</b>"""

        text_list = [text1, thank_text]
        time_list = [text1_time, thank_time]
        text_itr = 0

        current_text = text_list[text_itr]
        current_timer = time_list[text_itr] * 1000

        box_width = 800
        box_height = 600
        box_x = (self.wind_width / 2) - (box_width / 2)
        box_y = (self.wind_height / 2) - (box_height / 2)
        textbox = pgui.elements.UITextBox(
            relative_rect=pg.Rect((box_x, box_y), (box_width, box_height)),
            html_text=current_text.replace('\n', '<br>'),
            manager=manager
        )
        textbox.set_active_effect('typing_appear')

        ui_clock = pg.time.Clock()
        text_finished = False
        text_timer = pg.time.get_ticks()
        while True:
            time_delta = ui_clock.tick(60)/1000.0
            textbox.update(0.5)

            if not text_finished and pg.time.get_ticks() >= text_timer + current_timer:
                text_finished = True

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.state = GameState.EXIT
                    return

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE:
                        if not text_finished:
                            textbox.set_active_effect(None)
                            textbox.rebuild()
                            text_finished = True
                        else:
                            if text_itr == len(text_list) - 1:
                                self.state = GameState.TITLE
                                return
                            else:
                                text_finished = False
                                text_itr += 1
                                textbox.html_text = text_list[text_itr].replace('\n', '<br>')
                                current_timer = time_list[text_itr] * 1000
                                textbox.set_active_effect('typing_appear')
                                textbox.rebuild()
                                text_timer = pg.time.get_ticks()

                manager.process_events(event)

            manager.update(time_delta)

            self.window.blit(bg, (0, 0))
            manager.draw_ui(self.window)

            pg.display.update()

    def game_over(self):
        manager = pgui.UIManager(self.screen_rect.size)
        bg = pg.Surface(self.screen_rect.size)
        bg.fill(pg.Color('#000000'))
        bg.set_alpha(100)

        font = pg.font.Font(None, 150)
        over_text = font.render('Game Over', True, pg.Color('#FF0000'))
        ot_rect = over_text.get_rect()
        text_x = (self.wind_width / 2) - (ot_rect.width / 2)
        text_y = 400

        # Buttons
        btn_width = 200
        btn_height = 50
        btn_x = (self.wind_width / 2) - (btn_width / 2)
        # Starting y-coordinate for the buttons so that there is room for the header
        btn_y_buffer = text_y + ot_rect.height + 200

        btn_play_again = pgui.elements.UIButton(
            relative_rect=pg.Rect(
                (btn_x, btn_y_buffer),
                (btn_width, btn_height)
            ),
            text='Play Again?',
            manager=manager
        )
        btn_y_buffer += btn_height + 10

        btn_exit = pgui.elements.UIButton(
            relative_rect=pg.Rect(
                (btn_x, btn_y_buffer),
                (btn_width, btn_height)
            ),
            text='Main Menu',
            manager=manager
        )

        self.window.blit(bg, (0, 0))
        self.window.blit(over_text, (text_x, text_y))

        ui_clock = pg.time.Clock()
        while True:
            time_delta = ui_clock.tick(self.fps)/1000.0
            # Event loop
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.state = GameState.EXIT
                    return
                if event.type == pg.USEREVENT:
                    if event.user_type == pgui.UI_BUTTON_PRESSED:
                        if event.ui_element == btn_play_again:
                            self.state = GameState.NEWGAME
                            return
                        elif event.ui_element == btn_exit:
                            self.state = GameState.TITLE
                            return
                manager.process_events(event)
            manager.update(time_delta)

            # Screen updates
            manager.draw_ui(self.window)

            pg.display.update()

    def exit_game(self):
        pg.quit()
        sys.exit()

    def run_game(self):
        while True:
            if self.state == GameState.TITLE:
                self.title_menu()
            elif self.state == GameState.PAUSE:
                self.pause_menu()
            elif self.state == GameState.INTROSTORY:
                self.intro_story()
            elif self.state == GameState.NEWGAME:
                self.new_game()
            elif self.state == GameState.PLAYING:
                self.game_loop()
            elif self.state == GameState.WIN:
                self.win_menu()
            elif self.state == GameState.GAMEOVER:
                self.game_over()
            elif self.state == GameState.EXIT:
                self.exit_game()

    def game_loop(self):
        self.window.blit(self.background, (0, 0))
        self.window.blit(self.sidebar_surface, (self.game_width, 0))
        
        pg.display.flip()
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.state = GameState.EXIT
                    return
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        self.state = GameState.PAUSE
                        return
                    if event.key == pg.K_F4:
                        for enemy in self.enemies:
                            enemy.remove()
                if event.type == PLAYERDEADEVENT:
                    self.state = GameState.GAMEOVER
                    return

            if len(self.enemies) == 0:
                if self.level_manager.is_final_level():
                    self.state = GameState.WIN
                    return
                self.level_manager.next_level()
                self.play_level()

            self.entities.clear(self.window, self.background)
            self.entities.update()

            self.check_collisions()

            changes = self.entities.draw(self.window)
            pg.display.update(changes)

    def load_image(self, filename):
        fullpath = os.path.join('.', 'assets', 'images', filename)
        try:
            surface = pg.image.load(fullpath)
        except pg.error:
            raise RuntimeError(f'Unable to load image "{fullpath}". error: {pg.get_error()}')
        return surface.convert_alpha()

    def load_level(self, filename):
        level = []
        fullpath = os.path.join('.', 'assets', 'levels', filename)

        with open(fullpath, 'r') as fh:
            reader = csv.reader(fh, delimiter=',')
            for row in reader:
                level.append(row)
        return level

    def check_collisions(self):
        # Check for bullet collisions
        for bullet in self.bullets:
            if bullet.target == Enemy:
                for enemy in pg.sprite.spritecollide(bullet, self.enemies, False):
                    enemy.take_hit(bullet.damage)
                    bullet.remove()

            for _ in pg.sprite.spritecollide(bullet, self.walls, False):
                bullet.remove()

        # Check for player on enemy collisions
        for enemy in pg.sprite.spritecollide(self.player, self.enemies, False):
            self.player.take_hit(enemy.melee_dmg)

        # Check for player on enemy bullet collisions
        for bullet in pg.sprite.spritecollide(self.player, self.bullets, False):
            if bullet.target == Player:
                self.player.take_hit(bullet.damage)
                bullet.remove()

        # Check for player on collectable collisions
        for item in pg.sprite.spritecollide(self.player, self.collectables, True):
            self.player.heal(item.reward_health)
            self.player.damage += item.reward_damage
