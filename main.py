"""
The main loop; if you want to play, this is where you do it.
"""

# Schedule:
# 1. Redo the actions system.
# The idea is that each time you want the next monster to do something, you call
# curlev.next().  This then asks the current monster to do something.  Asking
# a monster to do something makes it do two things - decide what to do (which
# involves getting an Action) and doing it (which involves performing that
# Action).  There is also a dummy object (probably right behind the player, for
# now) which, when you ask it what to do, it does things that should be done
# once per turn.
# 2. Implement special attacks.
# 3. Implement decks.
# 4. Fix saving.

LOAD_FROM_SAVE = False
LOAD_FROM_RANDOM_DUNGEON = True
USE_PROFILER = False

from curses import wrapper

if USE_PROFILER:
    import cProfile

import tcod_display as display
import level
import dude
import config
import coordinates
import symbol
import fileio
import mapgen
import action
import exc

import log

def main(win = None):
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

    display.init()
    display.display_main_screen(curlev.getArray(),
                                curlev.getPlayer().coords,
                                curlev.messages.getArray(),
                                curlev.getPlayer().getSidebar().getArray())

    while 1:
        try:
            curlev.next()
        except exc.LevelChange:
            saved_player = curlev.player
            new_floor = curlev.floor + 1
            curlev = mapgen.randomLevel(new_floor, player, mainMonsterFactory)
            curlev.player.levelUp()
            curlev.messages.append("Welcome to the next floor!")

    raise NotImplementedError("You're not supposed to get here!")
    
    while 1:
        curlev.dudeLayer.generateQueue() #list of actors, in order of action
        
        for currentDude in curlev.dudeLayer.queue:
            
            if currentDude == curlev.player:
                curlev.messages.archive()
            
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
                curlev.messages.append("Welcome to the next floor!")
                # Restart the dude list.
                break
            elif dudeAction.getCode() == "STDATK":
                damage = action.damage(currentDude.attack, dudeAction.target.defense, currentDude.char_level, dudeAction.target.char_level)
                curlev.messages.append(dudeAction.message % {
                                "SOURCE_NAME": currentDude.getName(),
                                "DAMAGE": damage,
                                "TARGET_NAME": dudeAction.target.getName(),
                                })
                dudeAction.target.cur_HP -= damage
                dudeAction.target.checkDeath()
            elif dudeAction.getCode() == "WAIT":
                pass
            else:
                pass
        
        display.display_main_screen(curlev.getArray(),
                                    curlev.getPlayer().coords,
                                    curlev.messages.getArray(),
                                    curlev.getPlayer().getSidebar().getArray())

def entry():
    main()

def prof():
    cProfile.run('entry()', 'profile.pr')

if __name__ == "__main__":
    if USE_PROFILER:
        prof()
    else:
        entry()
