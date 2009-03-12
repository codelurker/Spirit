"""
level.py includes the Level class, which stores a specific dungeon level.
"""

import config
# import display
import arrays
import coordinates
import numpy
import log
import msg

class Level(list):
    """
    A Level is an object that represents the current state of a dungeon level.
    
    A Level consists of a list of Layers, and a Dungeon at the bottom.
    
    Fields:
    dudeLayer - the Layer containing Dudes and, of course, the player.
    elements - an array of characters containing terrain features which
        exist on top of ordinary terrain, like stairs.
    dungeon - an array of characters representing walls and floors.
    """
    """
    __composite_map - an array of strings, representing a top-down view of
        the Level, with the Dudes on top and the dungeon on the bottom.
    __height_map - an array of integers, representing the height of each
        tile of the __composite_map, that is, which part of the Level each
        tile came from.
    __are_maps_correct - a boolean.  If True, the __composite_map and
        __height_map are correct, and don't need to be refreshed.  If
        False, then they are incorrect, and refresh_maps() must be called
        before they are used.
    __DUDE_HEIGHT - the height of dudes.
    __ELEMENT_HEIGHT - the height of elements.
    __DUNGEON_HEIGHT - the height of terrain.
    """

    __DUDE_HEIGHT = 2
    __ELEMENT_HEIGHT = 5
    __DUNGEON_HEIGHT = 8
    
    def __init__(self, 
        dimensions = (80, 24), floor = 1, layers = None, elements = None, dungeon = None):
        """
        Create a Level.

        dimensions - the actual dimensions of the Level, in (x, y) form.
        floor - the height of the Level in comparison to other Levels;
            an integer.
        layers - a list (or tuple, etc.) with only one element: a DudeLayer.
        elements - an array representing the elements of the Level: terrain
            features which are overlaid upon the regular terrain, but which
            cannot be picked up like items.
        dungeon - an array representing the dungeon: the walls, floors, and
            other terrain.
        """

        if layers is None:
            list.__init__(self)
        else:
            list.__init__(self, layers)
        
        if len(self) < 1:
            #No dudeLayer, create one.
            self.append(DudeLayer(None, dimensions))

        self.floor = floor
        self.dungeon = dungeon
        self.elements = elements
        self.dimensions = dimensions
        self.dudeLayer = self[0]
        self.player = None
        self.messages = msg.MessageBuffer(config.MESSAGES_DIMENSIONS)
        self.__composite_map = arrays.empty_str_array(dimensions)
        self.__height_map = numpy.zeros(dimensions, 'i')
        self.__are_maps_correct = False
    
    def __str__(self):
        return str(self.getArray())

    def __addCharacterToMap(self, character, coords, height):
        """
        Add a character to the composite and height maps.
        """

        if not self.__are_maps_correct: return
        # assert self.__are_maps_correct
        assert height != self.__height_map[coords], \
            "'%s' is blocked by '%s': attempted to place at same height, %d." \
            % (character, self.__composite_map, height)

# Remember that small height means being near the top.
        if height < self.__height_map[coords]:
            self.__composite_map[coords] = character
            self.__height_map[coords] = height

        return

    def __delCharacterFromMap(self, coords, height):
        """
        Delete the character specified from the composite and height maps,
        searching below it for a character to replace it.  If the character
        is below the character on the composite map, do nothing.
        """
        
        if not self.__are_maps_correct: return
        assert height >= self.__height_map[coords]

        if height == self.__height_map[coords]:
            (self.__composite_map[coords], self.__height_map[coords]) = \
                self.__getCharacterBelow(coords, height)

        return

    def __getCharacterBelow(self, coords, height):
        """
        Return the symbol and height of the highest non-transparent
        character at coords below height.  If no such character exists,
        return the transparent character and a very large height.

        coords - a tuple of integers representing the location of the
            character being searched for.
        height - an integer representing the (exclusive) lower limit
            of height for the character being looked for.
        
        Returns - a pair, containing a 1-character string (the character
            found) and an integer (its height).
        """

        if height < self.__DUDE_HEIGHT:
            char = self.dudeGlyph(coords)
            if char != config.TRANSPARENT_GLYPH:
                return (char, self.__DUDE_HEIGHT)
        if height < self.__ELEMENT_HEIGHT:
            char = self.elementGlyph(coords)
            if char != config.TRANSPARENT_GLYPH:
                return (char, self.__ELEMENT_HEIGHT)
        if height < self.__DUNGEON_HEIGHT:
            char = self.dungeonGlyph(coords)
            if char != config.TRANSPARENT_GLYPH:
                return (char, self.__DUNGEON_HEIGHT)

        return (config.TRANSPARENT_GLYPH, self.__DUNGEON_HEIGHT + 1)

    def getArray(self):
        """
        Get an array representing a top-down view of the Level.

        Returns: An array of characters.
        """

        if not self.__are_maps_correct:
            self.refreshMaps()
        return self.__composite_map

    def dudeGlyph(self, coords):
        """
        Get the symbol representing the spot on the dudeLayer at coords.
        """
        
        if coords in self.dudeLayer:
            return self.dudeLayer[coords].glyph
        else:
            return config.TRANSPARENT_GLYPH

    def elementGlyph(self, coords):
        """
        Get the symbol representing the spot on the element array at coords.
        """

        return self.elements[coords]

    def dungeonGlyph(self, coords):
        """
        Get the symbol representing the spot on the dungeon array at coords.
        """

        return self.dungeon[coords]

    def refreshMaps(self):
        maps = arrays.overlay((self.dudeLayer.getArray(), self.elements, 
            self.dungeon), (self.__DUDE_HEIGHT, self.__ELEMENT_HEIGHT,
            self.__DUNGEON_HEIGHT))
        self.__composite_map = maps[0]
        self.__height_map = maps[1]
        self.__are_maps_correct = True

        return
    
    def addDude(self, addedDude, coords = None):
        """
        Add a dude to the dudeLayer of this level, modifying all accordingly.
        
        If no coordinates are supplied, the current coordinates of the dude
        are used.
        """
        
        if coords is None:
            dudeCoords = addedDude.coords
            if dudeCoords is None:
                raise TypeError("Dude has no coordinates")
        else:
            dudeCoords = coords
        
        if dudeCoords in self.dudeLayer:
            raise AttributeError("A dude, %s, was already at %s." % (addedDude.getName("a"), dudeCoords))

        addedDude.setCurrentLevel(self)
        addedDude.setCoords(dudeCoords)
        self.dudeLayer.append(addedDude)
        self.__addCharacterToMap(addedDude.glyph, dudeCoords, self.__DUDE_HEIGHT)
    
    def addPlayer(self, addedPlayer, coords = None):
        """
        Add a dude to this Level, and set it as the current player here.
        """
        self.player = addedPlayer
        self.dudeLayer.player = addedPlayer
        self.addDude(addedPlayer, coords)
    
    def getPlayer(self):
        """Returns the player dude."""
        
        return self.player
    
    def removeDude(self, removedDude):
        """
        Remove a dude from this level, setting its current level to None.
        
        This will delete the dude entirely if no other references to it exist.
        """

        self.__delCharacterFromMap(removedDude.coords, self.__DUDE_HEIGHT)
        self.dudeLayer.remove(removedDude)
    
    def dungeonGlyph(self, coords):
        """
        Gets the particular glyph of a dungeon square.
        """
        
        return self.dungeon[coords]
    
    def canMove(self, movedDude, moveCoords):
        """
        Returns true if a move by movedDude to moveCoords is possible.
        
        Returns false otherwise.
        """
        
               #the given coordinates are legal
        return (self.legalCoordinates(moveCoords) and
               #the movedDude can move on the dungeon tile of moveCoords
                movedDude.canPass(self.dungeonGlyph(moveCoords)) and
               #either moveCoords is empty, or it's occupied by movedDude
                ((moveCoords not in self.dudeLayer)
                 or self.dudeLayer[moveCoords] == movedDude))
    
    def legalCoordinates(self, coords):
        """
        Returns True if coords is a set of coordinates inside this Level.
        
        Returns False otherwise.
        """
        
        legality = True
        
        for i in range(len(self.dimensions)):
            if coords[i] < 0:
                legality = False
            if coords[i] >= self.dimensions[i]:
                legality = False
        
        return legality
    
    def moveDude(self, movedDude, moveCoords):
        if not self.canMove(movedDude, moveCoords):
            return False

        self.__delCharacterFromMap(movedDude.coords, self.__DUDE_HEIGHT)
        self.dudeLayer.moveObject(movedDude, moveCoords)
        self.__addCharacterToMap(movedDude.glyph, movedDude.coords, self.__DUDE_HEIGHT)

        return True
    
    def getQueue(self):
        """
        Get the dudes who are moving this turn, in order.
        
        The following restrictions are in place here:
        1. The player, if he is moving, always moves first.
        2. The monsters move in a consistent order.
        """
        
        if self.player == self.dudeLayer[0]:
            return [presentDude for presentDude in self.dudeLayer]
        else:
            queue = [presentDude for presentDude in self.dudeLayer]
            del queue[queue.index(self.player)]
            queue.insert(0, self.player)
    
    def getPanel(self):
        raise NotImplementedError()
        totalDisplay = display.Display([layer.getPanel() 
                                        for layer in self])
        totalDisplay.append(self.elements.getPanel())
        totalDisplay.append(self.dungeon.getPanel())
        # at this point, you have a display of everything
        return totalDisplay.getFullPanel()
    
    def rectPanel(self, upperLeftCorner, lowerRightCorner):
        raise NotImplementedError()
        # Horribly inefficient.  Fix!
        
        return self.getPanel().subpanel(upperLeftCorner, lowerRightCorner)
    
    def centeredPanel(self, center, dimensions):
        raise NotImplementedError()
        """Return a panel centered around "center." """
        
        (upperLeftCorner, lowerRightCorner) = coordinates.centeredRect(center, dimensions)
        return self.rectPanel(upperLeftCorner, lowerRightCorner)
    
    def displayPanel(self, dimensions = None, center = None):
        raise NotImplementedError()
        realCenter = center if (center is not None) else self.player.coords
        
        if dimensions is None:
            totalPanel = self.getPanel()
        else:
            totalPanel = self.centeredPanel(realCenter, dimensions)
        totalPanel.update()
    

class Layer(list):
    """
    A Layer is a collection of FixedObjects, all on the same level.
    
    There can be a Trap Layer, a Dude Layer, etcetera.
    Note that the Layer dict's keys are the coords of said objects.
    Layers are intended for collections in which not every square is full.
    
    Note that the dudes should not normally be directly added to the DudeLayer;
    they should be added through a Level instead.
    """
    
    def __init__(self, dimensions):
        """
        Supply a tuple for dimensions.
        """
        
        #if initThing is None:
        list.__init__(self)
        #else:
        #    dict.__init__(self, initThing)
            
        self.dimensions = dimensions
        self.coordinateDict = {}
    
    def __getitem__(self, key):
        """Works with dictionary key as well."""
        try:
            k = key[0]
        except TypeError:
            #key is not a sequence; assumed to be a list key
            return list.__getitem__(self, key)
        else:
            #key is a sequence, assumed to be a coord key
            return self.coordinateDict[key]
    
    def __delitem__(self, key):
        """Deletes from dictionary as well."""
        try:
            k = key[0]
        except TypeError:
            #This will screw up silently if coords is wrong!
            del self.coordinateDict[self[key].coords]
            list.__delitem__(self, key)
        else:
            list.__delitem__(self, self.index(self[key]))
            del self.coordinateDict[key]
    
    def __contains__(self, item):
        """Returns true with an item in this Layer or coordinates of one."""
        try:
            item[0]
        except TypeError:
            return list.__contains__(self, item)
        else:
            return item in self.coordinateDict
    
    def __addCoords(self, item):
        """
        Add the coordinates of an item to the layer's coord dict.
        """
        self.coordinateDict[item.coords] = item
    
    def __changeCoords(self, item, newCoords):
        """
        Change the coordinates of an item in the coord dict to newCoords.
        
        changeCoords changes ONLY the coordinates in this Layer's coordinate
        dict, and, in fact, WILL NOT WORK if the FixedObject's coordinates in
        its coords attribute differ from its coordinates inside the coordinate
        dict of this layer.
        """
        del self.coordinateDict[item.getCoords()]
        self.coordinateDict[newCoords] = item
    
    def moveObject(self, movedDude, moveCoords):
        """
        Move an object from its current coordinates to moveCoords.
        
        This method changes both the coords inside the FixedObject and the
        coords inside this Layer's internal map.
        """
        
        dudeOriginalCoords = movedDude.getCoords()
        if dudeOriginalCoords != moveCoords:
            self.__changeCoords(movedDude, moveCoords)
            movedDude.setCoords(moveCoords)

    def getArray(self):
        array = arrays.empty_str_array(self.dimensions)
        for item in self:
            array[item.coords] = item.glyph
        return array
    
    def getPanel(self):
        panel = display.Panel(self.dimensions)
        for item in self:
            panel.putc(item.coords, item.glyph)
        return panel
    
    def rectPanel(self, upperLeftCorner, lowerRightCorner):
        """
        Returns a panel representation, in the rectangle specified.
        
        The current implementation is horribly inefficient, so fix it, dummy!
        """
        panel = display
    
    def append(self, item):
        """Adds to dictionary as well."""
        list.append(self, item)
        self.__addCoords(item)
        #self[obj.coords] = obj
        
    def extend(self, item):
        """Adds to dictionary as well."""
        for i in item:
            self.append(i)

class DudeLayer(Layer):
    """
    Just like a Layer, except that it has a nice, convenient queue.
    """
    
    def __init__(self, player = None, *args, **kwds):
        Layer.__init__(self, *args, **kwds)
        self.moveQueue = []
        self.player = player
    
    def generateQueue(self):
        """
        Set the dudes who are moving this turn, in order, to self.queue.
        
        The following restrictions are in place here:
        1. The player, if he is moving, always moves first.
        2. The monsters move in a consistent order.
        """
        
        if self.player == self[0]:
            self.queue = [presentDude for presentDude in self]
        else:
            queue = [presentDude for presentDude in self]
            del queue[queue.index(self.player)]
            queue.insert(0, self.player)
            self.queue = queue
    
    def remove(self, removed):
        """
        Remove something from this layer.
        """
        
        removed.setCurrentLevel(None)
        #These lines is horribly inefficient; there's got to be a better way.
        del self[self.index(removed)]
        if removed in self.queue:
            del self.queue[self.queue.index(removed)]

class Dungeon(object):
    """
    The Dungeon is the lowest layer of a level, the one with walls, floors, etc.
    
    The Dungeon is settable and gettable as a dictionary with coordinate tuples
    as keys.
    
    The Dungeon is terribly inefficient for setting, I think.  If there are
    speed issues with creating levels, etc., they're probably here.
    """
    
    def __init__(self, dimensions, initList = None):
        #dict.__init__(self)
        self.dimensions = dimensions
        if initList is None:
            self.panel = display.Panel(dimensions = self.dimensions, fillchar = ' ', transparentchar = ' ')
        else:
            self.panel = display.Panel(dimensions = self.dimensions, existingList = initList)
    
    def __str__(self):
        return str(self.panel)
    
    def __getitem__(self, key):
        if key[0] >= self.dimensions[0] or key[1] >= self.dimensions[1]:
            raise ValueError("Coordinate value out of bounds")
        return self.panel.getc(key)
    
    def __setitem__(self, key, item):
        if not ((0 <= key[0] < self.dimensions[0]) or (0 <= key[1] < self.dimensions[1])):
            try:
                unnecessaryVariable = key[0] + key[1] + 3
            except TypeError:
                raise TypeError("Key supplied should be a sequence of ints")
            else:
                raise ValueError("Coordinate value out of bounds")
        self.panel.putc(key, item)
    
    def isPassable(self, coords):
        """
        This is not actually implemented yet, makes no sense, and, thus, probably never will be.
        """
        return True
    
    def getPanel(self):
        return self.panel
    
    def rectPanel(self, upperLeftCorner, lowerRightCorner):
        return self.panel.subpanel(upperLeftCorner, lowerRightCorner)
    
    def find(self, glyph):
        """
        Returns coordinates for the glyph provided if it is present.
        
        Raises a ValueError otherwise.
        """
        for y in range(self.dimensions[1]):
            x = self.panel[y].find(glyph)
            if x != -1:
                return (x, y)
        
        raise ValueError("Dungeon.find(glyph): glyph not in Dungeon")

def empty_dungeon(dimensions):
    """
    Return an empty dungeon with the dimensions specified.
    """

    return arrays.empty_str_array(dimensions)

def empty_elements(dimensions):
    """
    Return an empty container of terrain elements with the dimensions given.
    """

    return arrays.empty_str_array(dimensions)

if __name__ == "__main__":
    import dude
    import symbol
    import fileio
    
    fullPanelDim = (7, 6)
    subPanelUpLeft = (-2, -1)
    subPanelDownRight = (7, 8)
    
    linelist = fileio.getFile("tinytest.txt")
    dungeon = fileio.getDungeon(linelist, fullPanelDim, 0)
    print dungeon
    print "\nrectPanel"
    print dungeon.rectPanel(subPanelUpLeft, subPanelDownRight)