import pygame as pg

from game import Game


def main():
    wind_width = 1680
    wind_height = 1088
    game_width = 1280
    game_height = wind_height
    tilesize = 32

    main_game = Game(wind_width, wind_height, game_width, game_height, tilesize)

    main_game.run_game()


if __name__ == '__main__':
    main()
