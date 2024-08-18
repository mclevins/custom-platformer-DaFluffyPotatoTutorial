import random


class Cloud:
    def __init__(self, pos, img, speed, depth) -> None:
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth

    def update(self):
        self.pos[0] += self.speed

    def render(self, surf, offset=(0, 0)):
        # multiplying offest by depth to make a parsllax effect, so clouds further away move less quickly to make depth.
        render_pos = (self.pos[0] - offset[0] * self.depth, self.pos[1] - offset[1] * self.depth)
        # mod operater is used to make a 'loop' for the clouds so they just repeat, size of cloud is also included in making it loop, so that cloud is fully off screen.
        surf.blit(self.img, (render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(), render_pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height()))


class Clouds:
    def __init__(self, cloud_images, count=16) -> None:
        self.clouds = []

        for i in range(count):
            # Because we are looping clouds the 99999 number will just loop back around, size doesn't matter.
            self.clouds.append(Cloud((random.random() * 99999, random.random() * 99999), random.choice(cloud_images), random.random() * 0.05 + 0.05, random.random() * 0.6 + 0.2))

        # key determines how you sort things, we are sorting by depth with a lambda function, clouds that are closest to the camera will be pushed to the front, slowest will be in the back.
        self.clouds.sort(key=lambda x: x.depth)

    def update(self):
        for cloud in self.clouds:
            cloud.update()

    def render(self, surf, offset=(0, 0)):
        for cloud in self.clouds:
            cloud.render(surf, offset=offset)
