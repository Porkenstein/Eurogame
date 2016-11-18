from math import *
from random import *
from ai_controller import *
import operator
import os
import sys

# This file is used to generate the AI file through tournament selection
# and an evolutionary program.

# levels of debug detail

DEBUG = True # output generation jumps
DEBUG_1 = True # wins/ties
DEBUG_2 = False # progression of tournament selection
DEBUG_3 = False # print game outputs

DOUBLOON_THRESHOLD  = 50 # after this many doubloons are on the mayor, end the game as a deadlock
DEADLOCK_PENALTY    = 2
KEEP_RANKS          = 2 # the number to keep off of the top at the end of every iteration
SELECTION_RATE      = 0.5 # the amount to breed in the current population
POPULATION_SIZE     = 20
NUMBER_OF_ITERATIONS= 200
MUTATION_SEVERITY   = 18 # the max possible mutations per mutant
TOURNAMENT_ROUNDS   = 1 # number of times to iterate through entire population per generation
ALPHA               = 0.05 # alpha for BLX-Alpha Crossover
SA_START_TEMP       = 1.0 # percentage
SA_COOL_RATE        = 0.01 # reduction in mutation rate per generation
SA_MIN_TEMP         = 0.01 # this is the smallest allowed mutation rate
HIDDEN_LAYERS       = 1  # create AIs with this many hidden layers
USE_START_POP       = False # load a starting population
NUM_TRIALS          = 10

# possible improvements:
#   backpropogation learning, for faster reinforcement of winning strategies
#   non-monotonic cooling schedule, for chances at moving the population out of a local max in later generations
#   better, simpler symbolic representations of the board state, for faster results and more meaningful strategeis
#   dynamic sub-populations, where two evolve in isolation and then are thrown together.  Would definitely help reduce stagnation
#   parallel processing, optimizations, and translation into compiled C for more power.  This might allow the use of a more rigorous fitness function

# starting population weightset files
START_POP = ["ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7", "ail4_7" ]

def create_ann():
    return AI(HIDDEN_LAYERS)

# starts running random tournament selection.  the fitness of each ann (AI) is
# set equal to an amount reflectant to how many games they've won
def run_tournament_selection(anns, max_iterations):
    #done = []
    #used = [0] * len(anns)
    #max_used = (max_iterations // len(anns)) + 1
    #wincounts = [0] * len(anns)
    #runnerupcounts = [0] * len(anns) # use for tie breaking
    competitor_indecies = [0, 0, 0]
    for i in (0, max_iterations):
        for j in range(0, len(anns)):
            competitor_indecies[0] = j
            # select two random anns to face this one
            for k in range(1,3):
                competitor_indecies[k] = randrange(0, len(anns))
            while competitor_indecies[0] == competitor_indecies[1] or competitor_indecies[0] == competitor_indecies[2] or competitor_indecies[1] == competitor_indecies[2]:
                for m in range(1,3):
                    competitor_indecies[m] = randrange(0, len(anns))
            competitors = [anns[competitor_indecies[0]], anns[competitor_indecies[1]], anns[competitor_indecies[2]]]
            
            # run a single 3-AI game and record the scores.
            
            # turn off output
            stdo = sys.stdout
            devnul = open(os.devnull, 'w')
            if not DEBUG_3:
                sys.stdout = devnul
            game = Game(3, 0, competitors)
            curr_gamestate = []
            prev_gamestate = None
            while (game.winner == None) and not ( curr_gamestate == prev_gamestate ) and not (game.role_gold[Role.mayor.value] > DOUBLOON_THRESHOLD): # so games don't get caught in an infinite loop
                if DEBUG_2:
                    stdo.write(".")
                    stdo.flush()
                game.game_turn()
                prev_gamestate = curr_gamestate
                curr_gamestate = game.last_game_state
            sys.stdout = stdo

            # we have a winner!
            if not (game.winner == None):            

                winner_score = game.victory_points[game.winner]
                runnerup_score = game.victory_points[game.runnerup]
                
                # update fitness
                for i in range(0, 3):
                    if anns[competitor_indecies[i]].fitness < game.victory_points[i]:
                        anns[competitor_indecies[i]].fitness = game.victory_points[i]
                
                if DEBUG_1:
                    stdo.write("-") # winning game 
                    stdo.flush()
            else:
                for i in range(0, 3):
                    anns[competitor_indecies[i]].fitness -= DEADLOCK_PENALTY  # deadlocking is discouraged.  AIs should be able to at least make the game move along.
                if DEBUG_1:
                    stdo.write("|") # deadlock 
                    stdo.flush()


# fills a new population with mates, fits, mutates and returns it
def mate_population(population, n, mutation_rate, mutation_severity, alpha):
    children = []
    for i in range(0, n):
        a = randrange(0, len(population))
        b = randrange(0, len(population))        
        while a == b:  # make sure that a dude doesn't breed with itself 
            b = randrange(0, len(population))
        child = create_ann()
        child.crossover_weights(population[a], population[b], alpha )
        if(random.random() < mutation_rate):
            child.mutate_weights(int(random.randint(1, mutation_severity)))
        children.append(child)
    return children

if __name__ == "__main__":

    seed()
    
    file = open("performanceovertime_2.csv", "w")
    
    for n_t in range(0, NUM_TRIALS):
        
        max_score = 0
        population = []
        breeding_population = []
        keep_ranks = KEEP_RANKS
        selection_rate = SELECTION_RATE
        population_size = POPULATION_SIZE
        number_of_iterations = NUMBER_OF_ITERATIONS
        mutation_severity = MUTATION_SEVERITY
        tournament_rounds = TOURNAMENT_ROUNDS
        alpha = ALPHA
        
        winscores = []
        
        simulated_annealing = True # slowly reduce mutation rate
        sa_start_temp = SA_START_TEMP
        sa_cool_rate = SA_COOL_RATE
        sa_min_temp = SA_MIN_TEMP
        

        if(len(sys.argv)>4):
            selection_rate = float(sys.argv[4])
        if(len(sys.argv)>3):
            sa_start_temp = float(sys.argv[3])
        if(len(sys.argv)>2):
            number_of_iterations = int(sys.argv[2])
        if(len(sys.argv)>1):
            population_size = int(sys.argv[1])
            
        # generate  (or load) initial population
        if USE_START_POP:
            weights = []
            for i in range(0, len(START_POP)):
                s = START_POP[i]
                with open(s, 'rb') as pickle_file:
                    weights.append(pickle.load(pickle_file))
                # create the AI
                population.append(AI(HIDDEN_LAYERS, [weights[i][0], weights[i][1], weights[i][2], weights[i][3], weights[i][4], weights[i][5], weights[i][6], weights[i][7], weights[i][8], weights[i][9]]))
                
        for i in range(len(population), population_size):
            population.append(create_ann())

        print("BEGINNING NEW TRIAL WITH POPULATION SIZE " + str(population_size) + ", " + str(number_of_iterations) + " GENERATIONS, AND " + str(tournament_rounds) + " TOURNAMENT ROUNDS PER GENERATION." )
            
        run_tournament_selection(population, tournament_rounds)
        best = population[0]

        population.sort(key=lambda x: x.fitness, reverse=True)
        best = population[0]
        
        mutation_rate = sa_start_temp
        
        print("\n-- Initial best: " + str(best.fitness) + "\n")
        winscores.append(best.fitness)
        
        # begin generations
        sys.stdout.flush()
        for i in range(1, number_of_iterations):
                
            #sort by fitness and remove the bottom half
            population.sort(key=lambda x: x.fitness, reverse=True)
            if DEBUG:
                sys.stdout.write("\nFitnesses: ")
                for p in population:
                    sys.stdout.write(str(p.fitness) + ", ")
                sys.stdout.write("\n")
            population = population[0:int(population_size * selection_rate)]
            keepers = population[0:keep_ranks]
            best = population[0]
                
            new_population = mate_population(population, population_size - len(keepers), mutation_rate, mutation_severity, alpha)
            population = keepers + new_population # replace with offspring and keepers
            run_tournament_selection(population, tournament_rounds)
            print("\n-- Best score in iteration " + str(i) + ": " + str(best.fitness) + "\n")
            winscores.append(best.fitness)
            
            if best.fitness > max_score:
                max_score = best.fitness
            
            # cool down the population
            
            if ( simulated_annealing and ( ( mutation_rate - sa_cool_rate ) >= sa_min_temp ) ):
                mutation_rate = mutation_rate - sa_cool_rate
                
        print("\n----------------------------------------\n Final best score = " + str(best.fitness)+ "\n" )
        print("\n----------------------------------------\n Max best score = " + str(max_score)+ "\n" )

        
        filename = ("autoai" + str(n_t))   
        best.save_weights(filename)

        
        for i in range(0, len(winscores)-1):
            file.write(str(winscores[i]) + ",")
        file.write(str(winscores[len(winscores)-1]) + str("\n"))
    file.close()