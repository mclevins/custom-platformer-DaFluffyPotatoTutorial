import json
import math

import pygame

# what tile variants should be used depending on neighbor locations
# running sorted makes the list the same order to accomodate the loop
# in autotile. list can't be used as a key, so it is made into a tuple.
AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]       # Surrounding tile coordinates, 9 tiles
PHYSICS_TILES = {'grass', 'stone', 'castle', 'pipe', 'yellowblock'}          # sets are faster than lists for accessing.
AUTOTILE_TYPES = {'grass', 'stone'}


class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}               # every single tile on a grid, handle all physics here to keep optimization easy.
        self.offgrid_tiles = []         # these are things placed all over the place but dont line up with the grid.

    def solid_check(self, pos):
        """
        for enemies, finding out if the tile is actually solid to walk on, so they don't walk off the edge.
        """
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    def extract(self, id_pairs, keep=False):        # tiles are in type and variance format, this is an 'id_pair'.
        """
        For particles
        """
        matches = []
        for tile in self.offgrid_tiles.copy():          # copying because we might want to delete from the list. removing offgrid tiles
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        notkeep = []
        for loc in self.tilemap:                        # for ongrid tiles.
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()      # we want to convert from tile coordinates to actual pixels.
                matches[-1]['pos'][0] *= self.tile_size             # ths gives us pixel coordinates. we are copying so we don't modify actual tile data on the map with this function.
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    notkeep.append(loc)
                    # del self.tilemap[loc]
        for loc in notkeep:
            del self.tilemap[loc]

        return matches

    def tiles_around(self, pos, entity_size):
        """tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))      # integer truncates decimal values, so use // not /, int() is used so we can use it later for indexing. Converts pixel position into grid position.
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])           # location to check if neighbors exist
            if check_loc in self.tilemap:          # tilemap can have a lot of empty spaces with no entries, so check if the tile is in the tilemap to begin with.
                tiles.append(self.tilemap[check_loc])
        return tiles
        """
        tiles = []
        bounding_box = []
        x, y = math.ceil(entity_size[0] / self.tile_size), math.ceil(entity_size[1]/ self.tile_size)    #finding out how tall and wide in tiles our entity is, tiles are 16x16, use ceiling for half tile values so they are included.
        # tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        top_left_x = int(round(pos[0] / self.tile_size))-1
        top_left_y = int(round(pos[1] / self.tile_size))-1
        for i in range(x+2):        # Trace outside tiles starting in top left going down and to right.
            bounding_box.append((top_left_x+i, top_left_y))                    # Top Row
            bounding_box.append((top_left_x+i, top_left_y+y+1))   # Bottom Row
        for i in range(1, y+1):
            bounding_box.append((top_left_x, top_left_y+i))                    # Left Side
            bounding_box.append((top_left_x+x+1, top_left_y+i))   # Right Side
        for tile in bounding_box:
            check_loc = str(tile[0]) + ';' + str(tile[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles

    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()

    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    def physics_rects_around(self, pos, size):
        """
        get physics tiles and return pygame.rects on them for collision
        """
        rects = []
        for tile in self.tiles_around(pos, size):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))        
        return rects

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:         # make sure tile is same type
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0)):
        # offgrid tiles, these are background, i.e. decoration, so render first. offset is for the camera and moves "everything else" to appear a camera is moving.
        for tile in self.offgrid_tiles:                             # just needs to be in pixels, because it is off the grid, so no multiply by tilesize. Offset is negative for camera because camera movement is technically opposite of where world is moving.
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

                        # this finds top left of camera, by adding surf.get_width, we find right side of screen, we add 1 because we're off by 1 with how the coordinates work.
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):     # y axis
                loc = str(x) + ';' + str(y)     # location in tilemap dictionary, this is a str for when we load into level editor as JSON cause JSON handles string better.
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))