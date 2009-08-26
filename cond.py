"""
Governs 'conditions', status effects that modify a Dude's movement in some way.
"""

import action

class Condition(object):
    """
    A condition.
    """

    def __init__(self, time, name):
        """
        Create a new Condition.

        time - the number of turns until the condition will wear off.
        name - a unique identifier for the condition, and the way it will be
               displayed to the player.
        """
        self.time = time
        self.name = name

    def passTurn(self):
        """
        Indicate to the condition that a turn has passed.
        """

        self.time -= 1

    def isOver(self):
        """
        Return True if the condition is over, False otherwise.
        """

        return self.time < 0

    def getAction(self, dude_):
        """
        Get an action, if this condition decides to control its dude's actions.
        
        Returns "None" if the condition allows the dude to choose its own
        actions.
        """
        return None

    def modifyAction(self, act):
        """
        Modify an action, if that action is not allowed under this condition.

        Returns: the new action that will be performed in place of the old.
        """
        return act

class Stuck(Condition):
    """
    A condition in which a dude cannot move.
    """
    
    def __init__(self):
        Condition.__init__(self, 8, "stuck")

    def modifyAction(self, act):
        """
        If a dude is Stuck, all of their moves become Wait actions.
        """

        if act.strcode == "MOVE":
            return action.Wait(act.source)
        else:
            return act

class Resting(Condition):
    """
    A condition in which a dude rests until it has full health.

    This condition is interrupted if there is a monster in sight.
    """

    def __init__(self):
        Condition.__init__(self, 200, "resting")

    def getAction(self, dude_):
        if len(dude_.fov.dudes) > 0 or dude_.cur_HP >= dude_.max_HP:
            self.time = -5
            return None
        else:
            return action.Wait(dude_)