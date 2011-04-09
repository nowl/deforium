import astar
from map import Map, MapElement, MapView
from astar import AStar
from imagecache import ImageCache
from maputils import getCost, getHeuristicCost, setCost, isImpassable
from random import random, randint
from perlin import Perlin

import sys, pygame

per = Perlin()

def initMapElement(elem):
    #val = per.perlin2d(elem.x, elem.y, 0.15, 4)
    val = per.perlin2d(elem.x, elem.y, 40, 4)
    if int(val * 4) == 0:
        i = 'impassable-1'
        t = 'impassable'    
    else:
        i = 'normal'
        t = 'normal'
        
    elem.meta = {'image': i,
                 'type': t}

class MapSprite (pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.location = [0, 0]
        self.mapView = None

    def _modifyLocation(self, x, y):
        self.location[0] += x
        self.location[1] += y
        self.rect.left = self.location[0]
        self.rect.top = self.location[1]
        self.location[0] = self.rect.left
        self.location[1] = self.rect.top
        self.rect.move_ip(-self.mapView.offsetX, -self.mapView.offsetY)

    def setMapView(self, mapView):
        self.mapView = mapView
        self.mapView.addChangeListener(self._mapViewChangeListener)

    def _mapViewChangeListener(self, x, y):
        raise NotImplementedError

class PlayerSprite (pygame.sprite.Sprite):
    def __init__(self, img, x, y, imageCache, mobs):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.top = y
        self.location = [0, 0]
        self.dx, self.dy = 0, 0
        self.collideFunc = pygame.sprite.collide_rect_ratio(0.8)
        self.mapView = None
        self.imageCache = imageCache
        self.mobs = mobs
        self.mobsQueue = []

    def update(self, *args):
        maxSpeed = 25
        
        if self.dx != 0 or self.dy != 0:
            self.mapView.moveViewByPixels(self.dx, self.dy)

        if randint(0, 4) == 0:
            side = randint(0, 3)

            if side == 0:           # top
                x = randint(0, 31)
                mob = MobSprite(32 * x + self.mapView.offsetX,
                                0 + self.mapView.offsetY,
                                self.imageCache.getCachedSurface("mob"),
                                random() * maxSpeed/2 + maxSpeed/2,
                                self,
                                self.mapView)
            elif side == 1:           # bottom
                x = randint(0, 31)
                mob = MobSprite(32 * x + self.mapView.offsetX,
                                32 * 32 + self.mapView.offsetY,
                                self.imageCache.getCachedSurface("mob"),
                                random() * maxSpeed/2 + maxSpeed/2,
                                self,
                                self.mapView)
            elif side == 2:           # left
                y = randint(0, 31)
                mob = MobSprite(0 + self.mapView.offsetX,
                                32 * y + self.mapView.offsetY,
                                self.imageCache.getCachedSurface("mob"),
                                random() * maxSpeed/2 + maxSpeed/2,
                                self,
                                self.mapView)
            elif side == 3:           # right
                y = randint(0, 31)
                mob = MobSprite(32 * 32 + self.mapView.offsetX,
                                32 * y + self.mapView.offsetY,
                                self.imageCache.getCachedSurface("mob"),
                                random() * maxSpeed/2 + maxSpeed/2,
                                self,
                                self.mapView)

            self.mobs.add(mob)
            self.mobsQueue.append(mob)

        if len(self.mobs) > 20:
            self.mobs.empty()

class ActorSprite (MapSprite):
    def __init__(self, x, y, img, dx, dy):
        MapSprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.location = [x, y]
        self.rect.left = self.location[0]
        self.rect.top = self.location[1]
        self.rect.move_ip(-dx, -dy)
    
    def _mapViewChangeListener(self, x, y):
        self.rect.left = self.location[0]
        self.rect.top = self.location[1]
        self.rect.move_ip(-x, -y)

class MobSprite (ActorSprite):
    def __init__(self, x, y, img, speed, player, mapView):
        ActorSprite.__init__(self, x, y, img, 0, 0)
        self.dx = 0
        self.dy = 0
        self.dir = randint(0, 3)
        self.collideFunc = pygame.sprite.collide_rect_ratio(0.6)
        self.speed = speed
        self.player = player
        self.mapView = mapView

        self.setMapView(mapView)

    def update(self, *args):
        if self.dir == 0:
            self.dx = self.speed
            self.dy = 0
        elif self.dir == 1:
            self.dx = -self.speed
            self.dy = 0
        elif self.dir == 2:
            self.dy = self.speed
            self.dx = 0
        elif self.dir == 3:
            self.dy = -self.speed
            self.dx = 0

        if self.dy != 0:
            for sprite in self.mapView:
                if self.collideFunc(self, sprite) and isImpassable(sprite.mapElement):
                    self._modifyLocation(0, -self.dy)
                    self.dir = randint(0, 3)
        if self.dx != 0:
            for sprite in self.mapView:
                if self.collideFunc(self, sprite) and isImpassable(sprite.mapElement):
                    self._modifyLocation(0, -self.dx)
                    self.dir = randint(0, 3)
        
        self._modifyLocation(self.dx, self.dy)
            
class MineSprite (ActorSprite):
    def __init__(self, x, y, img, dx, dy):
        ActorSprite.__init__(self, x, y, img, dx, dy)
        self.collideFunc = pygame.sprite.collide_rect_ratio(0.8)

    def update(self, *args):
        pass


class GameLoop (object):
    def __init__(self, ticks_per_second, max_frame_skip):
        self.TicksPerSecond = ticks_per_second
        self.TimePerTick = 1000.0 / self.TicksPerSecond # MS per tick
        self.MaxFrameSkip = max_frame_skip
        
        pygame.init()

        try:
            self.font = pygame.font.Font('VeraMono.ttf', 16)
        except:
            print 'problem loading font'
            self.font = None

        self.fontSurf = None
        self._displayFPS = False
        
        size = width, height = 800, 600
        self.black = 0,0,0
        #self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        self.screen = pygame.display.set_mode(size)

        self.imageCache = ImageCache()
        self.imageCache.getSurface("units/Player1.png", "ball")
        self.imageCache.getSurface("units/Creature1.png", "mob")
        self.imageCache.getSurface("units/Mine1.png", "mine")
        self.imageCache.getSurface("terrains/Normal.jpg", "normal")
        self.imageCache.getSurface("terrains/Impassable5.jpg", "impassable-1")

        ball = self.imageCache.getCachedSurface("ball")
        self.mobs = pygame.sprite.Group()
        self.playerSprite = PlayerSprite(ball, width/2-16, height/2-16, self.imageCache, self.mobs)
        self.playerSpriteGroup = pygame.sprite.Group(self.playerSprite)
        self.mapView = None

    def _updateFPS(self, fps):
        self.fontSurf = self.font.render('FPS: %.3f' % fps, True, (0, 255, 0))

    def render(self):
        self.screen.fill(self.black)
        self.mapView.draw(self.screen)
        self.playerSpriteGroup.draw(self.screen)
        self.mobs.draw(self.screen)
        if self.fontSurf and self._displayFPS:
            self.screen.blit(self.fontSurf, (25, 25))
        pygame.display.flip()

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            
            speed = 15

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
                elif event.key == pygame.K_a:
                    self.playerSprite.dx -= speed
                elif event.key == pygame.K_d:
                    self.playerSprite.dx += speed
                elif event.key == pygame.K_w:
                    self.playerSprite.dy -= speed
                elif event.key == pygame.K_s:
                    self.playerSprite.dy += speed
                elif event.key == pygame.K_F1:
                    self._displayFPS = not self._displayFPS
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    self.playerSprite.dx += speed
                elif event.key == pygame.K_d:
                    self.playerSprite.dx -= speed
                elif event.key == pygame.K_w:
                    self.playerSprite.dy += speed
                elif event.key == pygame.K_s:
                    self.playerSprite.dy -= speed

        self.mapView.update()
        self.playerSpriteGroup.update()
        self.mobs.update()

    def loop(self):
        nextGameTick = pygame.time.get_ticks()

        renderClock = pygame.time.Clock()
        updateTick = 0

        self.levelMap = Map(mapElementCB = initMapElement)
        self.mapView = MapView(self.levelMap, self.imageCache, pygame.Rect(0, 0, 800, 600), 32, 32)
        self.playerSprite.mapView = self.mapView

        while 1:
            loops = 0

            while pygame.time.get_ticks() > nextGameTick and loops < self.MaxFrameSkip:
                self.update()
                nextGameTick += self.TimePerTick
                loops += 1
                updateTick += 1
                
                if updateTick % 10 == 0:
                    self._updateFPS(renderClock.get_fps())

            renderClock.tick()    
            self.render()

if __name__ == '__main__':
    game = GameLoop(10, 5)
    game.loop()
