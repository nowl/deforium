from pygame.sprite import Sprite, Group, Rect

class MapElement (object):
    def __init__(self, x, y, mapElementCB = None):
        self.x = x
        self.y = y

        if mapElementCB:
            mapElementCB(self)

    def __eq__(self, elem):
        return self.x == elem.x and self.y == elem.y

    def __repr__(self):
        return '(%d, %d)' % (self.x, self.y)
        
class Map (object):
    def __init__(self, mapElementCB = None):
        self.meta = {}
        self.mapElementCB = mapElementCB

    def getMapElement(self, x, y):
        return MapElement(x, y, self.mapElementCB)

    def getDiagonalAdjacencies(self, elem):
        x = elem.x
        y = elem.y
        
        results = []

        minX = max(x-1, 0)
        maxX = min(self.width-1, x+1)
        minY = max(y-1, 0)
        maxY = min(self.height-1, y+1)

        for j in range(minX, maxX + 1):
            for i in range(minY, maxY + 1):
                if j == x and i == y:
                    continue
                results.append(self.getMapElement(j, i))

        return results

    def getSquareAdjacencies(self, elem):
        x = elem.x
        y = elem.y
        
        squaresToCheck = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
        results = []

        minX = max(x-1, 0)
        maxX = min(self.width-1, x+1)
        minY = max(y-1, 0)
        maxY = min(self.height-1, y+1)

        for point in squaresToCheck:
            if point[0] >= minX and point[0] <= maxX and point[1] >= minY and point[1] <= maxY:
                results.append(self.getMapElement(point[0], point[1]))

        return results

class MapElementSprite (Sprite):
    def __init__(self, mapElement, imageCache):
        Sprite.__init__(self)
        self.mapElement = mapElement
        self.image = imageCache.getCachedSurface(self.mapElement.meta['image'])
        self.rect = self.image.get_rect()
        pixelLocation = self.mapElement.meta['screenLocation']
        self.rect.move_ip(*pixelLocation)

    def update(self, *args):
        pass

class MapView (Group):
    def __init__(self, map, imageCache, rectPixelView, imWidth, imHeight):
        Group.__init__(self)
        self._changeListeners = []
        self.upperLeft = [0, 0]
        self.numTiles = (int(rectPixelView.width / imWidth), int(rectPixelView.height / imHeight))
        self.map = map
        self.imageCache = imageCache
        self.imageSize = (imWidth, imHeight)
        self.offsetX = 0
        self.offsetY = 0
        self.setView(rectPixelView)

    def _updateView(self):
        self.offsetX = self.view.left
        self.offsetY = self.view.top
        
        self._updateContainer()
        self._updateChangeListeners(self.offsetX, self.offsetY)

    def setView(self, rect):
        self.view = rect
        self._updateView()

    def moveViewByPixels(self, x, y):
        self.view.move_ip(x, y)
        self._updateView()

    def _updateContainer(self):
        self.empty()

        sprites = []
        w = self.imageSize[0]
        h = self.imageSize[1]
        for xi in range(self.numTiles[0] + 1):
            x = xi + int(self.offsetX/32)
            for yi in range(self.numTiles[1] + 2):
                y = yi + int(self.offsetY/32)
                elem = self.map.getMapElement(x, y)
                elem.meta['screenLocation'] = elem.x * w - self.offsetX, elem.y * h - self.offsetY
                sprites.append(MapElementSprite(elem, self.imageCache))
        self.add(sprites)

    def addChangeListener(self, listener):
        self._changeListeners.append(listener)

    def _updateChangeListeners(self, *args):
        for listener in self._changeListeners:
            listener(*args)


                
