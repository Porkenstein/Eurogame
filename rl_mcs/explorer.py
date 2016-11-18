# Wrapper for PyBrain meant for Puerto Rico simulation
# http://pybrain.org/docs/tutorial/reinforcement-learning.html
#
# Based on examples from:
# http://simontechblog.blogspot.com/2010/08/pybrain-reinforcement-learning-tutorial_15.html
# and the given simons_blackjack_example.py
#
# actionvaluenetwork
#
from pybrain.rl import *
from pybrain.rl.environments import *
from pybrain.rl.environments.task import *
from numpy import *
from scipy import *
import sys

NUM_STATES = 22
GAME_STATES_LENGTH = ( 2 ** NUM_STATES ) # the number of possible states
ENV_INDIMS  = [6, 24, 7, 6, 5, 5, 30, 2, 2, 2] # see ai_controller.py
DBGOUT = sys.stdout


class PlayerState():
    #contains all scoring data for a player
    
    def __init__(self, playernum):
        self.playernum = playernum
    
        # in order to calculate the reward, we need to store parts of the board state which are desireable
        self.last_goods = 0 # the combined values of all goods owned by the player from the last reward
        self.last_vp    = 0 # the last held amount of victory points from the last reward
        self.last_gold  = 2 # the last held amount of doubloons from the last reward
        self.last_pvp   = 0 # the last held amount of potential victory points from the last reward (vp giving buildings)
        self.last_disc  = 0 # the last amount of goods discarded in the captain phase
        
        self.cur_goods = 0 # from the last observation
        self.cur_vp    = 0
        self.cur_gold  = 2
        self.cur_pvp   = 0
        self.cur_disc  = 0
        
        # only update these if the game has ended:
        self.firstplace = 0
        self.lastplace = 0
        
    def updatePlayerstate(self, boardstate):
        # given the player's board state, update its scoring state
        self.last_goods = self.cur_goods # the combined values of all goods owned by the player from the last reward
        self.last_vp    = self.cur_vp # the last held amount of victory points from the last reward
        self.last_gold  = self.cur_gold # the last held amount of doubloons from the last reward
        self.last_pvp   = self.cur_pvp # the last held amount of potential victory points from the last reward (vp giving buildings)
        self.last_disc  = self.cur_disc # the last amount of goods discarded in the captain phase
        
        [ self.cur_goods, self.cur_vp, self.cur_gold, self.cur_pvp, self.cur_disc, self.firstplace, self.lastplace ] = boardstate
        
    def getReward(self):
        # Rewards:
        # +1 for new goods
        # +1 for new doubloons
        # +1 for new VP
        # +1 for new potential VP
        # -1 for throwing away crops
        # +5 for game ended, and in first place
        # -5 for game ended, and in last place
        
        max_reward = 10
        
        new_goods = max(0, self.cur_goods - self.last_goods)
        new_vp    = max(0, self.cur_vp - self.last_vp)
        new_gold  = max(0, self.cur_gold - self.last_gold)
        new_pvp   = max(0, self.cur_pvp - self.last_pvp)
        new_disc  = max(0, self.cur_disc - self.last_disc)
        
        reward = (new_goods + new_gold + new_vp + new_pvp + (5 * self.firstplace) - (new_disc + (5 * self.lastplace)))
        reward = reward / max_reward  # magnitude reduction
        return reward
        
class PuertoRicoTask(Task):
    """Represents as single transaction between an agent and the board, affecting
    the board state and changing the agent's gameplay policy by returning a reward."""

    def __init__(self, environment):
        """ Create the task and couple it to the puerto rico board. """
        self.env = environment
        self.playerstate = None
        
        self.last_reward = 0

    def setPlayerState(self, playerstate):
        # sets the reference to the object which holds all of the current player's scoring data
        self.playerstate = playerstate
        
    def performAction(self, action):
        """ A filtered mapping towards performAction on the board. """                
        self.env.performAction(action)
        
    def getObservation(self):
        """ A filtered mapping to getSample of the board. """
        rewardstate = []
        rewardstate.append(sum(self.env.game.goods[self.playerstate.playernum])) # the number of goods
        rewardstate.append(self.env.game.victory_points[self.playerstate.playernum]) # the number of victory points
        rewardstate.append(self.env.game.gold[self.playerstate.playernum]) # the amount of gold
        rewardstate.append(self.env.game.get_end_game_vp_bonus( self.playerstate.playernum )) # the current potential vp (in level 4 buildings)
        rewardstate.append(self.env.game.discards[self.playerstate.playernum]) # the number of discarded goods
        rewardstate.append(int(self.env.game.winner == self.playerstate.playernum))
        rewardstate.append(int(self.env.game.loser == self.playerstate.playernum))
        
        self.playerstate.updatePlayerstate(rewardstate)
        sensors = self.env.getSensors()
        return sensors

    def getReward(self):
        """ Compute and return the "current" reward, corresponding to the last action performed """
        
        reward = self.playerstate.getReward()
        # retrieve last reward, and save current given reward
        cur_reward = self.last_reward
        self.last_reward = reward
    
        return cur_reward

    @property
    def indim(self):
        return self.env.indim
    
    @property
    def outdim(self):
        return self.env.outdim

    
    
class PuertoRicoEnvironment(Environment):
    """ An implementation of the Puerto Rico Board. """       

    # the number of action values the environment accepts.
    # should be changed with setIndim to reflect the possible
    # choices which can be taken. varies with each decision.
    indim = None
    
    # the dimensionality of the board state
    outdim = 2147483648 # same for all decisions
    
    # the associated game
    game = None
    
    # which player I am
    playernum = None
    
    # which choices am I making
    choice_idx = None
    
    # the last decision I made
    lastdecision = None
    
    def setIndim( self, indim ):
        """
            :key indim: the number of action values the environment accepts.
            :type indim: an unsigned int
        """    
        self.indim = indim
        return
    
    def setGame(self, game):
        """ couple an initialized game to this environment.  The game is the underlying environment
            which unifies all Pybrain RL Environments in the simulation.
            :key game: a game simulation of puerto rico to associate with the environment.
            :type game: a Game object from game.py
        """
        self.game = game
        return
    
    def setPlayer(self, idx):
        self.playernum = idx
    
    def setChoiceIdx(self, idx):  # this environment makes this choice
        self.choice_idx = idx
    
    def getSensors(self):
        """ return the board state. 
            :rtype: a numpy array of doubles corresponding to get_game_state in game.py
        """
        game_state = self.game.get_game_state(self.playernum)
        game_state_value = 0
        for i in range(0, len(game_state)): # use the state values as bits
            game_state_value += (2 ** i)
        return [game_state_value,] # returned as a double array
        #return game_state # returned as a double array
                    
    def performAction(self, action):
        """ perform a move on the board that changes the board state.
            :key action: the move performed up the board.  The board will modify itself as a side-affect.
        """
        self.lastdecision = int(action[0]) # so the Player object knows how to affect the board state
        return

    def reset(self):
        """ Most environments will implement this optional method that allows for reinitialization. 
        """
        # which choices am I making
        choice_idx = None
        
        # the last decision I made
        lastdecision = None

        return