import astar
from map import Map, MapElement, MapView
from astar import AStar
from imagecache import ImageCache
from maputils import getCost, getHeuristicCost, setCost, isImpassable
from random import random, randint

import sys, pygame

def initMapElement(elem):
    if random() > 0.1:
        i = 'normal'
        t = 'normal'
    else:
        i = 'impassable-1'
        t = 'impassable'
        
    elem.meta = {'image': i,
                 'type': t,
                 'cost': 10}

class MapSprite (pygame.sprite.Sprite):
    def __init__(self, screenRect):
        pygame.sprite.Sprite.__init__(self)
        self.location = [0, 0]
        self.mapView = None
        self.screenRect = screenRect

    def _modifyLocation(self, x, y):
        self.location[0] += x
        self.location[1] += y
        self.rect.left = self.location[0]
        self.rect.top = self.location[1]
        self.rect.clamp_ip(self.mapView.worldRect)
        self.location[0] = self.rect.left
        self.location[1] = self.rect.top
        self.rect.move_ip(-self.mapView.offsetX, -self.mapView.offsetY)

    def setMapView(self, mapView):
        self.mapView = mapView
        self.mapView.addChangeListener(self._mapViewChangeListener)

    def _mapViewChangeListener(self, x, y):
        raise NotImplementedError

class PlayerSprite (MapSprite):
    def __init__(self, img, screenRect):
        MapSprite.__init__(self, screenRect)
        self.image = img
        self.rect = self.image.get_rect()
        self.dx = 0
        self.dy = 0
        self.collideFunc = pygame.sprite.collide_rect_ratio(0.8)

    def update(self, *args):
        needsUpdate = False
        
        if self.dx != 0:
            needsUpdate = True
            self._modifyLocation(self.dx, 0)
            
            for sprite in self.mapView:
                if self.collideFunc(self, sprite) and isImpassable(sprite.mapElement):
                    self._modifyLocation(-self.dx, 0)

        if self.dy != 0:
            needsUpdate = True
            self._modifyLocation(0, self.dy)
            
            for sprite in self.mapView:
                if self.collideFunc(self, sprite) and isImpassable(sprite.mapElement):
                    self._modifyLocation(0, -self.dy)
            
        if needsUpdate:
            imWidth, imHeight = self.mapView.imageSize
            if self.mapView.view.right < self.mapView.map.width * imWidth and self.rect.right > self.screenRect.width-100:
                self.mapView.moveView(imWidth * 6, 0)
            if self.mapView.view.bottom < self.mapView.map.height * imHeight and self.rect.bottom > self.screenRect.height-100:
                self.mapView.moveView(0, imHeight * 4)
            if self.mapView.offsetX > 0 and self.rect.left < 100:
                self.mapView.moveView(-imWidth * 6, 0)
            if self.mapView.offsetY > 0 and self.rect.top < 100:
                self.mapView.moveView(0, -imHeight * 4)

    def getAdjacency(self, dir):
        adj = None
        
        if dir == pygame.K_RIGHT:
            self._modifyLocation(self.rect.width / 2, 0)
            
            for sprite in self.mapView:
                if self.collideFunc(self, sprite) and isImpassable(sprite.mapElement):
                    adj = sprite
                    break

            self._modifyLocation(-self.rect.width / 2, 0)

        elif dir == pygame.K_LEFT:
            self._modifyLocation(-self.rect.width / 2, 0)
            
            for sprite in self.mapView:
                if self.collideFunc(self, sprite) and isImpassable(sprite.mapElement):
                    adj = sprite
                    break

            self._modifyLocation(self.rect.width / 2, 0)

        elif dir == pygame.K_UP:
            self._modifyLocation(0, -self.rect.height / 2)
            
            for sprite in self.mapView:
                if self.collideFunc(self, sprite) and isImpassable(sprite.mapElement):
                    adj = sprite
                    break

            self._modifyLocation(0, self.rect.height / 2)

        elif dir == pygame.K_DOWN:
            self._modifyLocation(0, self.rect.height / 2)
            
            for sprite in self.mapView:
                if self.collideFunc(self, sprite) and isImpassable(sprite.mapElement):
                    adj = sprite
                    break

            self._modifyLocation(0, -self.rect.height / 2)

        return adj

    def _mapViewChangeListener(self, x, y):
        self.rect.move_ip(x, y)

class ActorSprite (MapSprite):
    def __init__(self, x, y, screenRect, img, dx, dy):
        MapSprite.__init__(self, screenRect)
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
    def __init__(self, x, y, img, screenRect, speed, player, mapView):
        ActorSprite.__init__(self, x, y, screenRect, img, 0, 0)
        self.dx = 0
        self.dy = 0
        self.dir = randint(0, 4)
        self.collideFunc = pygame.sprite.collide_rect_ratio(0.6)
        self.speed = speed
        self.player = player
        self.mapView = mapView

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
                    self.dir = randint(0, 4)
        if self.dx != 0:
            for sprite in self.mapView:
                if self.collideFunc(self, sprite) and isImpassable(sprite.mapElement):
                    self._modifyLocation(0, -self.dx)
                    self.dir = randint(0, 4)
        
        self._modifyLocation(self.dx, self.dy)
            
class MineSprite (ActorSprite):
    def __init__(self, x, y, img, screenRect, dx, dy):
        ActorSprite.__init__(self, x, y, screenRect, img, dx, dy)
        self.collideFunc = pygame.sprite.collide_rect_ratio(0.8)

    def update(self, *args):
        pass

def sprinkleMobs(num, maxSpeed, sprites, mapView, imageCache, screenRect, player):
    imWidth, imHeight = mapView.imageSize
    for x in xrange(num):
        mob = MobSprite(randint(0, mapView.map.width * imWidth),
                        randint(0, mapView.map.height * imHeight),
                        imageCache.getCachedSurface("mob"),
                        screenRect,
                        random() * maxSpeed/2 + maxSpeed/2,
                        player,
                        mapView)

        mob.setMapView(mapView)
    
        sprites.add(mob)    


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
        self.screenRect = pygame.Rect(0, 0, width, height)
        self.playerSprite = PlayerSprite(ball, self.screenRect)
        self.sprites = pygame.sprite.Group(self.playerSprite)
        self.mapView = None

    def _updateFPS(self, fps):
        self.fontSurf = self.font.render('FPS: %.3f' % fps, True, (0, 255, 0))

    def render(self):
        self.screen.fill(self.black)
        self.mapView.draw(self.screen)
        self.sprites.draw(self.screen)
        if self.fontSurf and self._displayFPS:
            self.screen.blit(self.fontSurf, (25, 25))
        pygame.display.flip()

    def _swapAux(self, key, xi, yi):
        adj = self.playerSprite.getAdjacency(key)
        if adj:
            x = adj.mapElement.x
            y = adj.mapElement.y
            self.levelMap.swap(x, y, x+xi, y+yi)
            self.mapView.moveView(0, 0)
            rect = self.playerSprite.rect
            self.playerSprite._modifyLocation(-xi * rect.width, -yi * rect.height)
            self.playerSprite.needsUpdate = True
        else:
            x = self.playerSprite.location[0] - xi * self.mapView.imageSize[0]
            y = self.playerSprite.location[1] - yi * self.mapView.imageSize[1]
            imWidth, imHeight = self.mapView.imageSize
            mine = MineSprite(x, y, self.imageCache.getCachedSurface("mine"), self.screenRect, self.mapView.offsetX, self.mapView.offsetY)
                
            mine.setMapView(self.mapView)
                
            self.sprites.add(mine)

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            
            speed = 5

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
                elif event.key == pygame.K_RIGHT:
                    self._swapAux(event.key, -1, 0)
                elif event.key == pygame.K_LEFT:
                    self._swapAux(event.key, 1, 0)
                elif event.key == pygame.K_UP:
                    self._swapAux(event.key, 0, 1)
                elif event.key == pygame.K_DOWN:
                    self._swapAux(event.key, 0, -1)
                    
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
        self.sprites.update()

    def loop(self):
        nextGameTick = pygame.time.get_ticks()

        renderClock = pygame.time.Clock()
        updateTick = 0

        self.levelMap = Map(50, 50, mapElementCB = initMapElement)
        self.mapView = MapView(self.levelMap, self.imageCache, pygame.Rect(0, 0, 800, 600), 32, 32)
        self.playerSprite.setMapView(self.mapView)

        sprinkleMobs(10, 4, self.sprites, self.mapView, self.imageCache, self.screenRect, self.playerSprite)

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
    game = GameLoop(30, 5)
    game.loop()
