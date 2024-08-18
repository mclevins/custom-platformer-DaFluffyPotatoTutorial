import os

import pygame

BASE_IMG_PATH = 'data/images/'


def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()         # .convert converts the internal representation of the image in pygame, making it more efficient for rendering, very important to use as default for everything
    img.set_colorkey((0, 0, 0))             # set black as transparent to get rid of png background of black
    return img


def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):           # listdir lists all things in directory
        images.append(load_image(path + '/' + img_name))        # already includes base image path
    return images


class Animation:
    def __init__(self, images, img_dur=5, loop=True, isPlayer=False):
        self.images = images
        self.isPlayer = isPlayer
        self.loop = loop
        self.img_duration = img_dur         # how many frames do we want each image in the animation to show for.
        self.done = False                   # keeps track if we're at the end, very primitive animation setup.
        self.frame = 0                      # frame of the game, not the animation.

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop, self.isPlayer)

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))      # modulo forces our frame to loop around.
        else:       # if we don't have a loop
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)     # - 1 is to account for indexing starting at 0, dont have to do above in self.frame because of how modulo works. Remainder of 3 % 3 is 0, because its the remainder.
            if self.frame >= self.img_duration * len(self.images) - 1:                  # we've reached the end of the animation
                self.done = True

    def img(self):      # gives us image for whatever frame we are on.
        # if self.isPlayer:
            # print(f'IMAGE: {int(self.frame / self.img_duration)} FRAME: {self.frame}')
        return self.images[int(self.frame / self.img_duration)]     # int truncates the float.