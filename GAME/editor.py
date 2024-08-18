import sys

import pygame

from scripts.utils import load_images
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0


class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('editor')

        # Create Game Window with resolution, display is to render onto smaller screen, then scale to the larger screen.
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))      # all black by default
        # Set game clock to run at 60fps, need to do
        # to prevent overtaxing processor, not using
        # delta time only using static time.
        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'yellowblock': load_images('tiles/yellowblock'),
            'stone': load_images('tiles/stone'),
            'castle': load_images('tiles/castle'),
            'pipe': load_images('tiles/pipe'),
            'spawners': load_images('tiles/spawners'),
        }

        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, tile_size=16)

        try:
            self.tilemap.load('data/maps/02.json')
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]        # "camera's" location

        self.tile_list = list(self.assets)      # running list on dictionary just gives you key
        self.tile_group = 0                     # grass, decor, etc
        self.tile_variant = 0                   # which type of grass?

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

    def run(self):

        while True:
            self.display.fill((0, 0, 0))        # draw screen to prevent trails of moving images.

            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2     
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)         # makes image partially transparent, 0 is fully transparent, 255 is fully opaque.

            mpos = pygame.mouse.get_pos()               # gives pixel coordinates of mouse with respect to the window.
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)         # SCALE DOWN mouse position to get correct coordinates since we are "two pixels" now.
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))           # gives us coordinates of our mouse in terms of the tile system.
                                                        # the division here aligns tiles with the grid

            if self.ongrid:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))     # we added scroll i.e. camera's position, in tile_pos so we need to remove it here...?
            # reason we are doing all of this is to align the tiles with the grid.
            else:
                self.display.blit(current_tile_img, mpos)       # off grid display            

            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos}      # place tile if clicking, formats into coordinate system of JSON format.
            if self.right_clicking:                          # delete tiles
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():                  # for deleting off-grid tiles, copy is because we are going to delete and we don't want to get the reference itself. This is poorly optimized code.
                    tile_img = self.assets[tile['type']][tile['variant']]       # computing hit box from the image for deletion
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())     # calculating the hitbox, we remove self.scroll because we are converting world space into display space because we're trying to collide with the mouse. tile_pos is calculated with self.scroll added to it, so we need to remove it.
                    if tile_r.collidepoint(mpos):           # this is for colliding rects with any point
                        self.tilemap.offgrid_tiles.remove(tile)

            self.display.blit(current_tile_img, (5, 5))

            # prevent computer from thinking program is not responding by constantly querying pygame.event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:           # pygame.QUIT is clicking X in the window.
                    pygame.quit()
                    sys.exit()                          # exit application.

                if event.type == pygame.MOUSEBUTTONDOWN:        # this is for any button activation on the mouse including scroll wheel, mouse buttons are assigned different numbers.
                    if event.button == 1:               # left clicking
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])}) # adding self.scroll converts from the display space to the world's space
                    if event.button == 3:               # right clicking, 2 is for pressing down on mouse wheel.
                        self.right_clicking = True
                    if self.shift:                      # hold shift to cycle through variants.
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])       # -1 for scrolling up mod is to loop through
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])       # +1 for scrolling down.
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)       # -1 for scrolling up mod is to loop through
                            self.tile_variant = 0                                               # to prevent indexing errors.
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)       # +1 for scrolling down.
                            self.tile_variant = 0                                               # to prevent indexing errors.
                if event.type == pygame.MOUSEBUTTONUP:                                          # clicking variables will be updated on current mouse state
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:        # pygame.KEYDOWN is for any key being pressed.
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:         # for the up arrow and 'w' key
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_o:
                        self.tilemap.save('02.json')
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))      # scale display and show it, 'blit' it, onto the screen.
            # For updating the display, without this, will just get a black screen
            pygame.display.update()
            # Run at 60fps, this function is a dynamic sleep to sleep as long as it
            # needs to maintain 60fps.
            self.clock.tick(60)


Editor().run()
