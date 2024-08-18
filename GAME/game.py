import sys
import random
import math

import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy, Matt, Potts
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('ninja game')

        # Create Game Window with resolution, display is to render onto smaller screen, then scale to the larger screen.
        self.screen = pygame.display.set_mode((1920, 1080))
        self.display = pygame.Surface((455, 270))      # all black by default
        # Set game clock to run at 60fps, need to do
        # to prevent overtaxing processor, not using
        # delta time only using static time.
        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.mattmovement = [False, False]

        self.pottsmovement = [False, False]

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'castle': load_images('tiles/castle'),
            'pipe': load_images('tiles/pipe'),
            'yellowblock': load_images('tiles/yellowblock'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'matt/idle': Animation(load_images('entities/matt/idle'), img_dur=6),
            'matt/walk': Animation(load_images('entities/matt/walk'), img_dur=6),
            'matt/angry': Animation(load_images('entities/matt/angry'), img_dur=6, loop=False),
            'matt/jump': Animation(load_images('entities/matt/jump'), img_dur=5, loop=False),
            'potts/idle': Animation(load_images('entities/potts/idle'), img_dur=5),
            'potts/walk': Animation(load_images('entities/potts/walk'), img_dur=5),
            'potts/surprised': Animation(load_images('entities/potts/surprised'), img_dur=5, loop=False),
            'potts/jump': Animation(load_images('entities/potts/jump'), img_dur=5, loop=False),
            'potts/milk': Animation(load_images('entities/potts/milk'), img_dur=5, loop=False),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6, isPlayer=True),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4, isPlayer=True),
            'player/jump': Animation(load_images('entities/player/jump'), img_dur=5),
            'player/slide': Animation(load_images('entities/player/slide'), img_dur=5),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide'), img_dur=5),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),

        }

        self.clouds = Clouds(self.assets['clouds'], count=16)
        self.matt = False
        self.potts = False
        self.starting_level = '02'

        self.player = Player(self, (50, 50), (12, 29))

        self.tilemap = Tilemap(self, tile_size=16)

        self.load_level(self.starting_level)

        self.screenshake = 0

    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))      # takes position of the tree and makes it based off of the tree's size.

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2), ('spawners', 3)]):     #we're not using keep, because keep is used to keep the tilemap in the tilemap or to showup on the tilemap, we don't want the spawners to show, we just want the locations.
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0        # reset air time to not trigger multiple times.
            elif spawner['variant'] == 2:
                self.matt = Matt(self, (100, 100), (12, 29))
                self.matt.pos = spawner['pos']
                self.matt.air_time = 0
            elif spawner['variant'] == 3:
                if self.starting_level == '0':
                    self.assets['potts/idle'] = Animation(load_images('entities/potts/normalidle'), img_dur=5)
                    self.assets['potts/walk'] = Animation(load_images('entities/potts/normalwalk'), img_dur=5)
                    self.assets['potts/surprised'] = Animation(load_images('entities/potts/normalsurprised'), img_dur=5, loop=False)
                self.potts = Potts(self, (100, 100), (12, 29))
                self.potts.pos = spawner['pos']
                self.potts.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 12)))

        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0, 0]        # "camera's" location
        self.dead = 0

    def run(self):

        while True:
            self.display.blit(self.assets['background'], (0, 0))        # draw screen to prevent trails of moving images.

            self.screenshake = max(0, self.screenshake - 1)     # timer that goes down to zero.

            if self.dead:
                self.dead += 1
                if self.dead > 40:  # once dead, wait 40 frames, timer is above with the += 1
                    self.load_level(1)

            # camera position is changed based on the player's center of rect, technically camera position is in top left of screen so to center player, we need to remove half of the screen. We also subtract our current position, and add to the scroll.
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30 # dividing the increment by 30, it now takes 1/30 of the distance to center and applies that so the result is the further away the player is the faster the camera moves since we're using a ratio.
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))      # this is to remove 1 pixel jitter in player entity because of sub pixel calculations for camera offset since it is a float.
            # camera will still move closer to target in pixels not sub-pixels so it will jitter when moving close to character, but the character itself won't.

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:          # the 49999 is to control the rate of the spawn, it will make it so we're not spawning every frame. This is a random odd chance line of code, make sure its smaller than the hitbox
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)       # pos is spawn position of leaf, gives us any number within the bounds of the rect.
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            self.clouds.update()
            self.clouds.render(self.display, offset=render_scroll)

            self.tilemap.render(self.display, offset=render_scroll)

            # ENEMIES SECTION

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if self.matt:
                self.matt.update(self.tilemap, (self.mattmovement[1] - self.mattmovement[0], 0)) ############################
                self.matt.render(self.display, offset=render_scroll)

            if self.potts:
                self.potts.update(self.tilemap, (self.pottsmovement[1] - self.pottsmovement[0], 0)) ############################
                self.potts.render(self.display, offset=render_scroll)

            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0)) ############################
                self.player.render(self.display, offset=render_scroll)

            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():      # copy cause we're removing them later
                projectile[0][0] += projectile[1]
                projectile[2] += 1  # timer
                img = self.assets['projectile']         # often times when adding something new, if you can't see it, its often because you got the camera stuff wrong, like offsets, think about how the camera should apply to whatever you are working on.
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))    # subtracting half the width gets center
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:     # if you're not in the moving fast part of the dash animation, dashing is invincible
                    if self.player.rect().collidepoint(projectile[0]):  # if player hit by projectile.
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.screenshake = max(16, self.screenshake)
                        for i in range(30):     # spawning 30 sparks
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3         # helps particle move back and forth in a smooth pattern, the 0.035 is to make sure you don't go through the loop of the sin function too fast. It always gives a number between -1 and 1.
                if kill:
                    self.particles.remove(particle)

            # prevent computer from thinking program is not responding by constantly querying pygame.event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:           # pygame.QUIT is clicking X in the window.
                    pygame.quit()
                    sys.exit()                          # exit application.

                if event.type == pygame.KEYDOWN:        # pygame.KEYDOWN is for any key being pressed.
                    if event.key == pygame.K_LEFT:
                        self.mattmovement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.mattmovement[1] = True
                    if event.key == pygame.K_UP:
                        self.matt.jump()
                    if event.key == pygame.K_DOWN:
                        self.matt.angry = True
                    if event.key == pygame.K_j:
                        self.pottsmovement[0] = True
                    if event.key == pygame.K_l:
                        self.pottsmovement[1] = True
                    if event.key == pygame.K_i:
                        self.potts.jump()
                    if event.key == pygame.K_m:
                        self.potts.milk = True
                    if event.key == pygame.K_k:
                        self.potts.surprised = True
                    if event.key == pygame.K_a:         # for the up arrow and 'w' key
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_SPACE:
                        self.player.jump()       # overrides vertical velocity to move player upwards, gravity will move them downwards again.
                    if event.key == pygame.K_x:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.mattmovement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.mattmovement[1] = False
                    if event.key == pygame.K_DOWN:
                        self.matt.angry = False
                    if event.key == pygame.K_j:
                        self.pottsmovement[0] = False
                    if event.key == pygame.K_l:
                        self.pottsmovement[1] = False
                    if event.key == pygame.K_m:
                        self.potts.milk = False
                    if event.key == pygame.K_k:
                        self.potts.surprised = False
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)      # scale display and show it, 'blit' it, onto the screen.
            # For updating the display, without this, will just get a black screen
            pygame.display.update()
            # Run at 60fps, this function is a dynamic sleep to sleep as long as it
            # needs to maintain 60fps.
            self.clock.tick(60)


Game().run()
