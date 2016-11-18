from game import *
from phase_ann2 import *

GAME_STATE_LENGTH = 27
# 
# Note - each value representing an unbound amount is scaled logarithmically, with a practical max determined beforehand
#
# wealth - 1
# has_ for each building - 24
# abundance_ for each crop - 5
# production_strength_ for each crop - 5
# plantation_amount_ for each crop and quarry - 6
# ship availability (to me, for each crop. stronger = more spots.  0 = not available) - 5
# colonists_left - 1
# in_trade_house for each crop - 5
# colonists - 1
# unemployed - 1

class AI:
    # decisions: pick role, pick building, pick plantation, pick trade crop, pick captain crop, prioritize crops to save, 
    #             prioritize new workers, use hacienda, use university, use wharf
    def __init__(self, hidden_layers, weights = None):

        self.hidden_layers = hidden_layers
        self.fitness = 0 # for evolution
        if weights == None:
            self.init_weights_random()
            return

        self.ann_pick_role = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 6)
        self.ann_pick_role.weights = weights[0]

        self.ann_pick_building = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 24)
        self.ann_pick_building.weights = weights[1]

        self.ann_pick_plantation = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 6) # 7 is none
        self.ann_pick_plantation.weights = weights[2]

        self.ann_pick_trade = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 5) # 6 is none 
        self.ann_pick_trade.weights = weights[3]

        self.ann_pick_captain = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 5)
        self.ann_pick_captain.weights = weights[4]

        self.ann_pick_save = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 5)
        self.ann_pick_save.weights = weights[5]

        self.ann_pick_workers = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 30) #24 buildings plus six crop types
        self.ann_pick_workers.weights = weights[6]

        self.ann_use_hacienda = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 2)
        self.ann_use_hacienda.weights = weights[7]

        self.ann_use_university = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 2)
        self.ann_use_university.weights = weights[8]

        self.ann_use_wharf = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, GAME_STATE_LENGTH, 2)
        self.ann_use_wharf.weights = weights[9]
    
    # create random set of weights
    def init_weights_random(self):
        self.ann_pick_role = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 6, 6)
        self.ann_pick_building = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 24, 24)
        self.ann_pick_plantation = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 6, 6)
        self.ann_pick_trade = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 5, 5)
        self.ann_pick_captain = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 5, 5)
        self.ann_pick_save = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 5, 5)
        self.ann_pick_workers = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 30, 30) #24 buildings plus six crop types
        self.ann_use_hacienda = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 2, 2)
        self.ann_use_university = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 2, 2)
        self.ann_use_wharf = phase_ann( 2 + self.hidden_layers, GAME_STATE_LENGTH, 2, 2)
        
    def crossover_weights( self, other1, other2, alpha ):
        self.ann_pick_role.crossover_weights(other1.ann_pick_role, other2.ann_pick_role, alpha)
        self.ann_pick_building.crossover_weights(other1.ann_pick_building, other2.ann_pick_building, alpha)
        self.ann_pick_plantation.crossover_weights(other1.ann_pick_plantation, other2.ann_pick_plantation, alpha)
        self.ann_pick_trade.crossover_weights(other1.ann_pick_trade, other2.ann_pick_trade, alpha)
        self.ann_pick_captain.crossover_weights(other1.ann_pick_captain, other2.ann_pick_captain, alpha)
        self.ann_pick_save.crossover_weights(other1.ann_pick_save, other2.ann_pick_save, alpha)
        self.ann_pick_workers.crossover_weights(other1.ann_pick_workers, other2.ann_pick_workers, alpha)
        self.ann_use_hacienda.crossover_weights(other1.ann_use_hacienda, other2.ann_use_hacienda, alpha)
        self.ann_use_university.crossover_weights(other1.ann_use_university, other2.ann_use_university, alpha)
        self.ann_use_wharf.crossover_weights(other1.ann_use_wharf, other2.ann_use_wharf, alpha)
    
    def mutate_weights(self, num_weights):
        for i in range(0, num_weights):
            mutant = random.randint(0,9)
            if mutant is 0:
                self.ann_pick_role.mutate_weights(1)
            elif mutant is 1:
                self.ann_pick_building.mutate_weights(1)
            elif mutant is 2:
                self.ann_pick_plantation.mutate_weights(1)
            elif mutant is 3:
                self.ann_pick_trade.mutate_weights(1)
            elif mutant is 4:
                self.ann_pick_captain.mutate_weights(1)
            elif mutant is 5:
                self.ann_pick_save.mutate_weights(1)
            elif mutant is 6:
                self.ann_pick_workers.mutate_weights(1)
            elif mutant is 7:
                self.ann_use_hacienda.mutate_weights(1)
            elif mutant is 8:
                self.ann_use_university.mutate_weights(1)
            elif mutant is 9:
                self.ann_use_wharf.mutate_weights(1)
    
    def pick_role(self, game_state, invalids):
        out = [0] * 6
        self.ann_pick_role.evaluate(game_state, out)
        out = [i[0] for i in sorted(enumerate(out), key=lambda x:x[1])]
        for i in invalids:
            out.remove(i)
        return out[0]
        
    def pick_building(self, game_state, invalids):
        out = [0] * 24
        self.ann_pick_building.evaluate(game_state, out)
        out = [i[0] for i in sorted(enumerate(out), key=lambda x:x[1])]
        for i in invalids:
            if i in out:
                out.remove(i)
        return out[0]

    def pick_plantation(self, game_state, invalids):
        out = [0] * 7
        self.ann_pick_plantation.evaluate(game_state, out)
        out = [i[0] for i in sorted(enumerate(out), key=lambda x:x[1])]
        for i in invalids:
            if i in out: # 0 here is quarry
                out.remove(i)
        return out[0]

    def pick_trade(self, game_state, invalids):
        out = [0] * 6
        self.ann_pick_trade.evaluate(game_state, out)
        out = [i[0] for i in sorted(enumerate(out), key=lambda x:x[1])]
        for i in invalids:
            if (i-1) in out: # i-1 because 0 is corn here
                out.remove(i-1)
        return out[0]

    def pick_captain(self, game_state, invalids):
        out = [0] * 5
        self.ann_pick_captain.evaluate(game_state, out)
        out = [i[0] for i in sorted(enumerate(out), key=lambda x:x[1])]
        for i in invalids:
            if (i-1) in out:  # i-1 because 0 is corn here
                out.remove(i-1)
        if len(out) > 0:
            return out[0]
        else:
            return None

    def pick_save(self, game_state, invalids):
        out = [0] * 5
        self.ann_pick_save.evaluate(game_state, out)
        out = [i[0] for i in sorted(enumerate(out), key=lambda x:x[1])]
        for i in invalids:
            if (i-1) in out: # i-1 because 0 is corn here
                out.remove(i-1)
        return out[0]

    def pick_workers(self, game_state, invalids):
        out = [0] * 30
        self.ann_pick_workers.evaluate(game_state, out)
        out = [i[0] for i in sorted(enumerate(out), key=lambda x:x[1])]
        for i in invalids:
            out.remove(i)
        return out[0]

    def use_hacienda(self, game_state):
        out = [0] * 2
        self.ann_use_hacienda.evaluate(game_state, out)
        if out.index(max(out)) == 0:
            return 'y'
        return 'n'

    def use_university(self, game_state):
        out = [0] * 2
        self.ann_use_university.evaluate(game_state, out)
        if out.index(max(out)) == 0:
            return 'y'
        return 'n'

    def use_wharf(self, game_state):
        out = [0] * 2
        self.ann_use_wharf.evaluate(game_state, out)
        if out.index(max(out)) == 0:
            return 'y'
        return 'n'
        
    def save_weights(self, filename):
        weights = [self.ann_pick_role.weights, self.ann_pick_building.weights, self.ann_pick_plantation.weights, self.ann_pick_trade.weights,\
        self.ann_pick_captain.weights, self.ann_pick_save.weights, self.ann_pick_workers.weights, self.ann_use_hacienda.weights,\
        self.ann_use_university.weights, self.ann_use_university.weights]
        
        pickle.dump( weights, open(filename,'wb'))
