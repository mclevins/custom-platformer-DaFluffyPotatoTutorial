import math
import random

import pygame

from scripts.particle import Particle
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type          # type is builtin function, so using e_type
        self.pos = list(pos)        # converting to list, make sure each entity has its own list, not just a reference to a list, cant use tuple, cant change individual values in tuple.
        self.size = size
        self.velocity = [0, 0]      # derivative of position is velocity, rate of change in position
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        self.action = ''
        self.anim_offset = (-3, -3)           # create space around your animation, our players dimensions are smaller than the images of them, this accounts for the overflow
        self.flip = False                       # player should be able to look right or left
        self.set_action('idle')             # set which animation we are currently using.

        self.last_movement = [0, 0]

    def rect(self):
        """
        For collisions, in pygame, two rects can make a collision
        will be constantly updated.
        """
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:           # check if action should change from what is currently our action.
            self.action = action
            # This line actually calls the Animation class.
            self.animation = self.game.assets[self.type + '/' + self.action].copy()        # entity type is type.

    def update(self, tilemap, movement=(0, 0)):
        """
        Updating position and the physics of collision,
        a Rect is not used in place of position because
        Rects only handle integers, they truncate floats.
        There is an updated version of pygame CE which
        has something where Rects can have floats, but for this
        we are trying to be compatible with all versions
        of pygame, so we are using our own position instead.
        """
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}           # Reset collisions each frame
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        tiles = tilemap.tiles_around(self.pos, self.size)
        rects = tilemap.physics_rects_around(self.pos, self.size)
        # Actual movement right here !!!
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        top_left_x = int(self.pos[0] // tilemap.tile_size)-1
        top_left_y = int(self.pos[1] // tilemap.tile_size)-1
        # tiles = tilemap.tiles_around(self.pos, self.size)
        # rects = tilemap.physics_rects_around(self.pos, self.size)
        # if self.size == (12, 29):
            # print(f'PHYSICS RECTS {rects} -------> PLAYER POS {entity_rect.top // 16}, {entity_rect.left // 16} ({entity_rect})')
            # for tile in tiles:
                # print(tile)
        for rect in rects:
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:       # moving right
                    entity_rect.right = rect.left       # move to left edge of the tile, i.e. the collision
                    self.collisions['right'] = True
                if frame_movement[0] < 0:       # moving left
                    entity_rect.left = rect.right       # move to right edge of the tile, i.e. the collision
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x    # update the player's position as well on x-axis

        # print(f'BEFORE self.pos[1]: {self.pos[1]}, entity_rect.y: {entity_rect.y}')
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()

        for rect in tilemap.physics_rects_around(self.pos, self.size):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:       # moving down
                    entity_rect.bottom = rect.top       # move to top edge of the tile, i.e. the collision, rect.top is a single integer
                    self.collisions['down'] = True

                if frame_movement[1] < 0:       # moving up
                    entity_rect.top = rect.bottom       # move to bottom edge of the tile, i.e. the collision
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y     # update the player's position as well on y-axis
                # print(f'AFTER self.pos[1]: {self.pos[1]}, entity_rect.y: {entity_rect.y}')

        if movement[0] > 0:     # flip the player to face right or left. if we're going right, we're already facing right, so don't flip, if going left, then flip.
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement
                            # 5 represents downward velocity as positive y means down.
        self.velocity[1] = min(5, self.velocity[1] + 0.1)           # represents acceleration, but caps it using the min function so we dont accelerate until infinity.

        if self.collisions['down'] or self.collisions['up']:        # if you're going down, it should stop you, if you're going up it should stop you
            self.velocity[1] = 0

        self.animation.update()
        #if self.size == (12, 29):
            #print(f'FRAME: {self.animation.frame}')

    def render(self, surf, offset=(0, 0)):                      # x-axis, y-axis               camera offset   anim offset 
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))            # pygame transform can flip the image.


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):        # we're looking 7 pixels to left or right, also looking 23 pixels into the ground
                if (self.collisions['right'] or self.collisions['left']):       # if you run into something you turn around, otherwise just walk
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])   # if self.flip is positive, facing left?
            else:
                self.flip = not self.flip               # flip if there is nothing to walk on, enemy will go back and forth alot if on only one solid tile.
            self.walking = max(0, self.walking - 1)         # bring it down to zero over time.
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1]) < 32):       # if the y axis offset is less than 16 pixels.
                    if (self.flip and dis[0] < 0):      # if the player is towards the left and we're looking left, dis should be negative for left facing
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random())) # facing left
                    if (not self.flip and dis[0] > 0):
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random())) # facing right

        elif random.random() < 0.01:            # random.random() generates a num between 0 and 1, so 1% chance of occuring, if we're not walking, 1 in every 1.67 seconds at 60fps if we're not walking.
            self.walking = random.randint(30, 120)      #between half a second (30) to two seconds (120)

        super().update(tilemap, movement=movement)  # calls parent function Physics Entity's update function

        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.game.player.dashing) >= 50:         # if in frames where you're actually dashing
            if self.rect().colliderect(self.game.player.rect()):        # the player hit an enemy with a dash.
                self.game.screenshake = max(16, self.game.screenshake)
                for i in range(30):     # spawning 30 sparks
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                return True


"""
    def render(self, surf, offset=(0, 0)):

        for rendering guns

        super().render(surf, offset=offset)

        # for flipping guns.
        if self.flip:                                                               # for placing the gun in a specific spot and accounting for gun width, play with the number. Also need to account for the camera.
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 9 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))
"""


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.air_time += 1

        if self.air_time > 120:     # three seconds is 180, 60fps
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1

        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1      # you have 1 jump when hitting the floor.

        self.wall_slide = False     # this variable will act as a single frame switch
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:      # in air and touching wall
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)       # capping downward velocity at 0.5
            if self.collisions['right']:
                self.flip = False           # base images for player are facing right, so False means use the base images
            else:
                self.flip = True            # flips the image to left
            self.set_action('wall_slide')

        if not self.wall_slide:     # if wallsliding, dont show any other animations.
            # this top if statement makes it the highest priority to check for first.
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        if abs(self.dashing) in {60, 50}:       # if we're at the start or the end of our dash, order of where this block matters if you want a burst at the beginning and end of a dash.
            for i in range(20):                 # create 20 particles
                # For burst of particles
                # why not just pick random numbers for all of this, why the trigonometry? Problem is scaling, if you just did (1, 1) for a vector in one direction, it makes an explosion at twice the speed, in the shape of a square, not a circle. To spread something out in the circle is to pick a random angle, with polar coordinates, then convert it to cartesian coordinates for velocity. This is for the burst of particles not the stream of particles in a dash.
                angle = random.random() * math.pi * 2       # this is the full circle of angles in radians, picking a random angle in the circle
                speed = random.random() * 0.5 + 0.5         # random speed between 0.5 and 1
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]      # cos is for x axis, sin is for y axis, generates a velocity based on the angle. based on trigonometry. take angle of what you want to move times the speed you want to move. This covers most trigonometry for games. arctangent turns x and y coordinates into angles, which would be another thing you may need.
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)     # manage dashing so it goes towards zero but not below it
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:          # if we're in the first 10 frames of the dash, if you divide the absolute by its own value, you get the direction of the scalar.
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:     # at the end of the first 10 frames of dash, we will severely cut down on velocity, to suddenly stop, the reason its 50 frames left, is because this serves a dual purpose, not just to finish the animation but to be a cooldown for the dash so you cant dash as much as you want.
                self.velocity[0] *= 0.1
            # streaming particles.
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]        # player velocity, abs divided by self is giving the direction, random number from 1 - 3 int he direction we are dashing, so the stream of particles moves in the direction of the movement. Only in x axis not y axis
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))

        # making sure velocity is zero'd out after jumping
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:     # facing left and movement to the left
                self.velocity[0] = 3.5      # velocity pushing to right, jumping away from wall
                self.velocity[1] = -2.5     # forces you off, but not as high as horizontally
                self.air_time = 5           # to update animation
                self.jumps = max(0, self.jumps - 1)     # jump to be consumed, make sure jumps cant go below 0.
                return True                 # if event actually occurs, return True.
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5      # velocity pushing to left, jumping away from wall
                self.velocity[1] = -2.5     # forces you off, but not as high as horizontally
                self.air_time = 5           # to update animation
                self.jumps = max(0, self.jumps - 1)     # jump to be consumed, make sure jumps cant go below 0.
                return True

        elif self.jumps:          # if jumps are 0 will evaluate to False
            self.velocity[1] = -3.5   # slows velocity
            self.jumps -= 1
            self.air_time = 5       # automatically forces it to go to jump animation since its > 4.

    def render(self, surf, offset=(0, 0)):       # for adding dashing to player with new render animation.
        if abs(self.dashing) <= 50:     # this is accounting for both directions with abs(), if we're in the first ten frames of the dash.
            super().render(surf, offset=offset)     # we're gating the rendering function of PhysicsEntity

    def dash(self):
        if not self.dashing:
            if self.flip:       # if facing left
                self.dashing = -60  # negative is for direction, velocity is not just a speed but a direction.
            else:
                self.dashing = 60   # how long we're dashing for


class Matt(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'matt', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.angry = False

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.air_time += 1

        if self.air_time > 240:     # three seconds is 180, 60fps
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1

        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1      # you have 1 jump when hitting the floor.

        if self.air_time > 4:
            self.set_action('jump')
        elif movement[0] != 0:
            self.set_action('walk')
        elif self.angry:
            self.set_action('angry')
        else:
            self.set_action('idle')

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def jump(self):
        if self.jumps:          # if jumps are 0 will evaluate to False
            self.velocity[1] = -3   # slows velocity
            self.jumps -= 1
            self.air_time = 5       # automatically forces it to go to jump animation since its > 4.

    def render(self, surf, offset=(0, 0)):       # for adding dashing to player with new render animation.
        super().render(surf, offset=offset)     # we're gating the rendering function of PhysicsEntity


class Potts(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'potts', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.milk = False
        self.surprised = False

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.air_time += 1

        if self.air_time > 120:     # three seconds is 180, 60fps
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1

        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1      # you have 1 jump when hitting the floor.

        if self.air_time > 4:
            self.set_action('jump')
        elif movement[0] != 0:
            self.set_action('walk')
        elif self.milk:
            self.set_action('milk')
        elif self.surprised:
            self.set_action('surprised')
        else:
            self.set_action('idle')

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def jump(self):
        if self.jumps:          # if jumps are 0 will evaluate to False
            self.velocity[1] = -3   # slows velocity
            self.jumps -= 1
            self.air_time = 5       # automatically forces it to go to jump animation since its > 4.

    def render(self, surf, offset=(0, 0)):       # for adding dashing to player with new render animation.
        super().render(surf, offset=offset)     # we're gating the rendering function of PhysicsEntity
