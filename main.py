"""
The main loop; if you want to play, this is where you do it.
"""

"""
To do:
# Replace the entire display class with an array-of-1-character-string-based
  class.
"""

LOAD_FROM_SAVE = False
LOAD_FROM_RANDOM_DUNGEON = True
USE_PROFILER = True

from curses import wrapper

if USE_PROFILER:
    import cProfile

import interface
import display
import level
import dude
import config
import coordinates
import symbol
import fileio
import mapgen
import action

import log

def main(win):
    interface.initialize(win)
    
    mainMonsterFactory = fileio.getMonsterFactory(
                         fileio.getFile("monsters.dat"))
    
    if LOAD_FROM_SAVE:
        save = fileio.restoreSave("save.dat", mainMonsterFactory, False)
        curlev = save[0]
    elif LOAD_FROM_RANDOM_DUNGEON:
        player = dude.Player("John Stenibeck", (40, 40))
        curlev = mapgen.randomLevel(1, player, mainMonsterFactory)
    else:
        floorlinelist = fileio.getFile("floors.dat")
        curlev = fileio.getFloor(floorlinelist, 0, mainMonsterFactory)
        
        player = dude.Player("John Stenibeck", (15, 4))
        curlev.addPlayer(player)
    
    UIDisplay = display.ScreenKing()
    UIDisplay.setCenteredMap(curlev)
    UIDisplay.playerStatus.getStatusFromPlayer(curlev.player)
    UIDisplay.updateScreenFromPrimaryDisplay()
    curlev.UI = UIDisplay
    
    while 1:
        curlev.dudeLayer.generateQueue() #list of actors, in order of action
        
        for currentDude in curlev.dudeLayer.queue:
            
            if currentDude == curlev.player:
                UIDisplay.messageBuffer.archive()
            
            dudeAction = currentDude.getAction()
            if dudeAction.getCode() == "QUIT":
                return
            elif dudeAction.getCode() == "MOVE":
                moveCoords = coordinates.addCoords(
                    dudeAction.getCoords(), currentDude.getCoords())

                curlev.moveDude(currentDude, moveCoords)
            elif dudeAction.getCode() == "UP":
                # Time to move up a level.
                saved_player = curlev.player
                new_floor = curlev.floor + 1
                curlev = mapgen.randomLevel(new_floor, player, mainMonsterFactory)
                curlev.player.levelUp()
                UIDisplay.messageBuffer.append("Welcome to the next floor!")
                # Restart the dude list.
                break
            elif dudeAction.getCode() == "STDATK":
                damage = action.damage(currentDude.attack, dudeAction.target.defense, currentDude.char_level, dudeAction.target.char_level)
                UIDisplay.messageBuffer.append(dudeAction.message % {
                                "SOURCE_NAME": currentDude.getName(),
                                "DAMAGE": damage,
                                "TARGET_NAME": dudeAction.target.getName(),
                                })
                dudeAction.target.curHP -= damage
                dudeAction.target.checkDeath()
            elif dudeAction.getCode() == "WAIT":
                pass
            else:
                pass
            
        UIDisplay.setCenteredMap(curlev)
        UIDisplay.playerStatus.getStatusFromPlayer(curlev.player)
        UIDisplay.updateScreenFromPrimaryDisplay()

def entry():
    wrapper(main)

def prof():
    cProfile.run('entry()', 'profile.pr')

if __name__ == "__main__":
    if USE_PROFILER:
        prof()
    else:
        entry()
