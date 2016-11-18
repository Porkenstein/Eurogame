# policy-building tree search for Puerto Rico simulation

from pybrain.rl import *
from explorer import *
from pybrain.rl.learners.valuebased import ActionValueTable
from pybrain.rl.agents import LearningAgent
from pybrain.rl.learners import Q
from pybrain.rl.experiments import Experiment
from pybrain.rl.explorers import EpsilonGreedyExplorer
from math import *
from random import *
from game import *
import operator
import os
import sys
import pickle
import numpy

# settings

DOUBLOON_THRESHOLD  = 30 # after this many doubloons are on the mayor, end the game as a deadlock
NUMBER_OF_ITERATIONS = 5000
DEBUG_GAME_CONSOLE = False
LOADFILE = ""

PICK_ROLE = 0
PICK_BUILDING = 1
PICK_PLANTATION = 2
PICK_TRADE = 3
PICK_CAPTAIN = 4
PICK_SAVE = 5
PICK_WORKERS = 6
PICK_HACIENDA = 7
PICK_UNIVERSITY = 8
PICK_WHARF = 9

# Q-learning parameters
ALPHA = 0.5 # learning rate

# MCTS parameters
EPSILONS = [1.0, 0.0, 0.001, 0.01, 0.1]

class Player():

    def __init__(self, playernum, game, epsilon):
        
        self.epsilon = epsilon
        self.playernum = playernum
        self.game = game
        self.playerstate = PlayerState(self.playernum)
        
        self.environments = []
        #self.game.av_tables = []
        self.agents = []
        self.tasks = []
        self.experiments = []
        self.learners = []
        
        # create each experiment - one per decision to make
        for i in range(0, len(ENV_INDIMS)):
            self.environments.append( PuertoRicoEnvironment() )
            self.environments[i].setIndim(ENV_INDIMS[i])
            self.environments[i].setGame(game)
            self.environments[i].setPlayer(self.playernum)
            self.learners.append( Q( ALPHA ) )
            self.learners[i]._setExplorer( EpsilonGreedyExplorer( self.epsilon ) )
            self.agents.append( LearningAgent( self.game.av_tables[i], self.learners[i] ) )
            self.tasks.append( PuertoRicoTask( self.environments[i] ) )
            self.tasks[i].setPlayerState( self.playerstate )
            self.experiments.append(Experiment(self.tasks[i], self.agents[i]))
    
    def reset(self): # learn, then forget all previous interactions
        for i in range(0, len(ENV_INDIMS)):
            self.agents[i].learn()
            self.agents[i].reset()
    
    
    def end_game(self):
        # rewards for winning or losing. consider backpropogation here
        for i in range(0, len(ENV_INDIMS)):
            self.agents[i].learn()
            self.experiments[i].doInteractions(1)
        
    def pick_role(self, game_state, invalids):
        self.agents[0].learn() # learn from the last decision made
        self.experiments[0].stepid += 1
        self.experiments[0].agent.integrateObservation(self.experiments[0].task.getObservation())
        self.experiments[0].task.performAction(self.experiments[0].agent.getAction())
        if self.environments[0].lastdecision in invalids:
            self.learners[0]._setExplorer( EpsilonGreedyExplorer( 1.0 ) )
            while self.environments[0].lastdecision in invalids:
                self.experiments[0].agent.lastaction = None
                self.experiments[0].task.performAction(self.experiments[0].agent.getAction())  # try again
            self.learners[0]._setExplorer( EpsilonGreedyExplorer( self.epsilon ) )
        reward = self.experiments[0].task.getReward()
        self.experiments[0].agent.giveReward(reward)
        return self.environments[0].lastdecision
    
    def pick_building(self, game_state, invalids):
        self.agents[1].learn() # learn from the last decision made
        self.experiments[1].stepid += 1
        self.experiments[1].agent.integrateObservation(self.experiments[1].task.getObservation())
        self.experiments[1].task.performAction(self.experiments[1].agent.getAction())
        if self.environments[1].lastdecision in invalids:
            self.learners[1]._setExplorer( EpsilonGreedyExplorer( 1.0 ) )
            while self.environments[1].lastdecision in invalids:
                self.experiments[1].agent.lastaction = None
                self.experiments[1].task.performAction(self.experiments[1].agent.getAction())  # try again
            self.learners[1]._setExplorer( EpsilonGreedyExplorer( self.epsilon ) )
        reward = self.experiments[1].task.getReward()
        self.experiments[1].agent.giveReward(reward)
        return self.environments[1].lastdecision

    def pick_plantation(self, game_state, invalids):
        self.agents[2].learn() # learn from the last decision made
        self.experiments[2].stepid += 1
        self.experiments[2].agent.integrateObservation(self.experiments[2].task.getObservation())
        self.experiments[2].task.performAction(self.experiments[2].agent.getAction())
        if self.environments[2].lastdecision in invalids:
            self.learners[2]._setExplorer( EpsilonGreedyExplorer( 1.0 ) )
            while self.environments[2].lastdecision in invalids:
                self.experiments[2].agent.lastaction = None
                self.experiments[2].task.performAction(self.experiments[2].agent.getAction())  # try again
            self.learners[2]._setExplorer( EpsilonGreedyExplorer( self.epsilon ) )
        reward = self.experiments[2].task.getReward()
        self.experiments[2].agent.giveReward(reward)
        return self.environments[2].lastdecision

    def pick_trade(self, game_state, invalids):
        self.agents[3].learn() # learn from the last decision made
        self.experiments[3].stepid += 1
        self.experiments[3].agent.integrateObservation(self.experiments[3].task.getObservation())
        self.experiments[3].task.performAction(self.experiments[3].agent.getAction())
        if (self.environments[3].lastdecision + 1) in invalids:
            self.learners[3]._setExplorer( EpsilonGreedyExplorer( 1.0 ) )
            while (self.environments[3].lastdecision + 1) in invalids:
                self.experiments[3].agent.lastaction = None
                self.experiments[3].task.performAction(self.experiments[3].agent.getAction())  # try again
            self.learners[3]._setExplorer( EpsilonGreedyExplorer( self.epsilon ) )
        reward = self.experiments[3].task.getReward()
        self.experiments[3].agent.giveReward(reward)
        return self.environments[3].lastdecision

    def pick_captain(self, game_state, invalids):
        self.agents[4].learn() # learn from the last decision made
        self.experiments[4].stepid += 1
        self.experiments[4].agent.integrateObservation(self.experiments[4].task.getObservation())
        self.experiments[4].task.performAction(self.experiments[4].agent.getAction())
        if (self.environments[4].lastdecision + 1) in invalids:
            self.learners[4]._setExplorer( EpsilonGreedyExplorer( 1.0 ) )
            while (self.environments[4].lastdecision + 1) in invalids:
                self.experiments[4].agent.lastaction = None
                self.experiments[4].task.performAction(self.experiments[4].agent.getAction())  # try again
            self.learners[4]._setExplorer( EpsilonGreedyExplorer( self.epsilon ) )
        reward = self.experiments[4].task.getReward()
        self.experiments[4].agent.giveReward(reward)
        return self.environments[4].lastdecision
        
    def pick_save(self, game_state, invalids):
        self.agents[5].learn() # learn from the last decision made
        self.experiments[5].stepid += 1
        self.experiments[5].agent.integrateObservation(self.experiments[5].task.getObservation())
        self.experiments[5].task.performAction(self.experiments[5].agent.getAction())
        if (self.environments[5].lastdecision + 1) in invalids:
            self.learners[5]._setExplorer( EpsilonGreedyExplorer( 1.0 ) )
            while (self.environments[5].lastdecision + 1) in invalids:
                self.experiments[5].agent.lastaction = None
                self.experiments[5].task.performAction(self.experiments[5].agent.getAction())  # try again
            self.learners[5]._setExplorer( EpsilonGreedyExplorer( self.epsilon ) )
        reward = self.experiments[5].task.getReward()
        self.experiments[5].agent.giveReward(reward)
        return self.environments[5].lastdecision
        
    def pick_workers(self, game_state, invalids):
        self.agents[6].learn() # learn from the last decision made
        self.experiments[6].stepid += 1
        self.experiments[6].agent.integrateObservation(self.experiments[6].task.getObservation())
        self.experiments[6].task.performAction(self.experiments[6].agent.getAction())
        if self.environments[6].lastdecision in invalids:
            self.learners[6]._setExplorer( EpsilonGreedyExplorer( 1.0 ) )
            while self.environments[6].lastdecision in invalids:
                self.experiments[6].agent.lastaction = None
                self.experiments[6].task.performAction(self.experiments[6].agent.getAction())  # try again
            self.learners[6]._setExplorer( EpsilonGreedyExplorer( self.epsilon ) )
        reward = self.experiments[6].task.getReward()
        self.experiments[6].agent.giveReward(reward)
        return self.environments[6].lastdecision
        
    def use_hacienda(self, game_state):
        self.agents[7].learn() # learn from the last decision made
        self.experiments[7].doInteractions(1)
        if self.environments[7].lastdecision == 0:
            return 'y'
        return 'n'

    def use_university(self, game_state):
        self.agents[8].learn() # learn from the last decision made
        self.experiments[8].doInteractions(1)
        if self.environments[8].lastdecision == 0:
            return 'y'
        return 'n'

    def use_wharf(self, game_state):
        self.agents[9].learn() # learn from the last decision made
        self.experiments[9].doInteractions(1)
        if self.environments[9].lastdecision == 0:
            return 'y'
        return 'n'


if __name__ == "__main__":

    seed()
    
    epsilon = EPSILONS[0]
    
    for n_t in range(0, len(EPSILONS)):
        epsilon = EPSILONS[n_t]
        # create game
        game = Game(3, 0, None) # player objects are passed down to the game's console's selector object
        stdo = sys.stdout
        winscores = []
        
        # create actionvalue tables
        stdo.write("Initializing AV Tables:\n")
        stdo.flush()
        if not (LOADFILE is ""):
            with open(LOADFILE, 'rb') as pickle_file:
                print("Loading AV Table File...")
                game.av_tables = pickle.load(pickle_file)
                print("Loaded File!")

        for i in range(0, len(ENV_INDIMS)):
            stdo.write(str(i)+".")
            stdo.flush()
            if LOADFILE is "":
                game.av_tables.append( ActionValueTable(GAME_STATES_LENGTH, ENV_INDIMS[i]) )
                game.av_tables[i].initialize(0.)

        # create players
        competitors = []
        for i in range(0, 3):
            competitors.append(Player(i, game, epsilon))
        
        # set the ais in the game and create the Console
        game.set_ais( 0, competitors )
        
        print("\n\nWinning Scores: ")
        
        # play games until done
        iteration = 0
        stdo.flush()
        devnul = open(os.devnull, 'w')
        if not DEBUG_GAME_CONSOLE:
            sys.stdout = devnul
        
        while iteration < NUMBER_OF_ITERATIONS:
            while ((game.winner is None) and not (game.role_gold[Role.mayor.value] > DOUBLOON_THRESHOLD)):
                game.game_turn()
                stdo.write(".")
                stdo.flush()
            
            for c in competitors:
                c.reset()
            
            winner_score = max([game.victory_points[0], game.victory_points[1], game.victory_points[2]])
            winscores.append(winner_score)
            stdo.write(" " + str(winner_score) + " ")
            stdo.flush()
            game.game_reset() # ready for new game
            iteration = iteration + 1
        
        # export final best Q-value ActionValueTable    
        sys.stdout = stdo
        filename = ("file" + str(n_t))
        print("Saving...")
        pickle.dump( game.av_tables, open(filename,'wb'))
        
        
        file = open("performanceovertime_" + str(n_t) + ".csv", "w")
        file.write(str(epsilon) + ",")
        for i in range(0, len(winscores)-1):
            file.write(str(winscores[i]) + ",")
        file.write(str(winscores[len(winscores)-1]) + str("\n"))
        
        total = 0
        for i in range(0, len(ENV_INDIMS)):
            sys.stdout.write(str(i)+".")
            sys.stdout.flush()
            for j in range(0, len(game.av_tables[i].params)):
                total += sum(numpy.absolute(game.av_tables[i].params[j]))
        print("\nTotal weights: " + str(total))
        file.close()