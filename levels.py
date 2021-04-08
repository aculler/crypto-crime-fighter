import csv
import os

class Level(object):
    def __init__(self, name, filename):
        self.name = name
        self.filename = filename

    def load(self):
        level = []
        fullpath = os.path.join('.', 'assets', 'levels', self.filename)

        with open(fullpath, 'r') as fh:
            reader = csv.reader(fh, delimiter=',')
            for row in reader:
                level.append(row)
        return level

class LevelManager(object):
    def __init__(self):
        self.current_level = 0
        self.levels = [
            Level('Network', 'level1 - network.level'),
            Level('Harddrive', 'level2 - harddrive.level'),
            Level('CPU', 'level3 - cpu.level')
        ]

    def is_final_level(self):
        return self.current_level == len(self.levels) - 1

    def get_level(self):
        return self.levels[self.current_level]

    def next_level(self):
        self.current_level += 1
