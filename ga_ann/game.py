from game_objects import *
# a simulation of a 3-player game of Andreas Seyfarth and Rio Grande Games' " Puerto Rico "
#
# Meant to be played with a board, where the user moves what the computer says is moved.
#
# Some assumptions that we're making here:
#
# 1. The players are placing their buildings in an efficient manner, such that
#    the number of spaces left in their city is enough to determine placement availability
#
# 2. The players take turns arranging their colonists in the mayor phase

# practical maxes

ROLE_MONEY_MAX = 8
VICTORY_POINT_MAX = 75
WEALTH_MAX = 30
BUILDING_MAX = 3
ABUNDANCE_MAX = 12
PRODUCTION_MAX = 12
PLANTATION_MAX = 12
AVAILABILITY_MAX = 6
COLONISTS_LEFT_MAX = 55 # also a good way of estimating the game progress
COLONISTS_MAX = 20
UNEMPLOYED_MAX = 10

NUM_ENV    = 10
ENV_OUTDIM = ( 59 ) 
ENV_INDIMS  = [6, 24, 6, 5, 5, 5, 30, 2, 2, 2] # see ai_controller.py


class Game:    
    def __init__(self, num_players, num_humans, ai):
        self.last_game_state = None
        self.winner = None
        self.runnerup = None
        self.num_players = num_players
        self.roles = [Role.none] * num_players
        self.gold = [2] * num_players
        self.victory_points = [0] * num_players
        self.victory_points_max = 75
        self.console = Console(num_humans, ai)
        self.role_gold = [0] * 7
        self.colonist_ship = self.num_players
        self.goods = []
        
        self.governor = 0 # 0th player starts first
        self.current_player = 0
        self.colonists_left = 55 # for 3 players, minus initial colonist ship
        self.trade_house = []
        self.ships = [None]*(3)  # ships[num players + 1] is for the player with the wharf
        self.cities = [City(), City(), City()]
        self.available_roles = [ Role.trader, Role.builder, Role.settler, Role.craftsman, Role.mayor, Role.captain ] # add and remove roles as players select them
        self.quarries = 8
        self.can_ship = [True, True, True]

        self.ships[0] = Ship(4)
        self.ships[1] = Ship(5)
        self.ships[2] = Ship(6)

        self.wharf_used = [0,0,0] # keep track if each player has used their wharf ship(s) yet each captain phase

        self.store = \
            { #[size, cost, workers, name], amount available, number of quarries which can be used to buy
              BID.none : [Building(0, 0, 0, "nothing", BID.none), 999, 1], \
              BID.small_indigo_plant : [Building(1, 1, 1, "Small Indigo Plant", BID.small_indigo_plant, Crop.indigo), 4, 1], \
              BID.small_market : [Building(1, 1, 1, "Small Market", BID.small_market), 2, 1], \
              BID.small_sugar_mill : [Building(1, 2, 1, "Small Sugar Mill", BID.small_sugar_mill, Crop.sugar), 4, 1], \
              BID.hacienda : [Building(1, 2, 1, "Hacienda", BID.hacienda), 2, 1], \
              BID.construction_hut : [Building(1, 2, 1, "Construction Hut", BID.construction_hut), 2, 1], \
              BID.small_warehouse : [Building(1, 3, 1, "Small Warehouse", BID.small_warehouse), 2, 1], \
              BID.indigo_plant : [Building(1, 3, 3, "Indigo Plant", BID.indigo_plant, Crop.indigo), 3, 2], \
              BID.sugar_mill : [Building(1, 4, 3, "Sugar Mill", BID.sugar_mill, Crop.indigo), 3, 2], \
              BID.hospice : [Building(1, 4, 1, "Hospice", BID.hospice), 2, 2], \
              BID.office : [Building(1, 5, 1, "Office", BID.office), 2, 2], \
              BID.large_market : [Building(1, 5, 1, "Large Market", BID.large_market), 2, 2],\
              BID.large_warehouse : [Building(1, 6, 1, "Large Warehouse", BID.large_warehouse), 2, 2], \
              BID.tobacco_storage : [Building(1, 5, 3, "Tobacco Storage", BID.tobacco_storage, Crop.tobacco), 3, 3], \
              BID.coffee_roaster : [Building(1, 6, 2, "Coffee Roaster", BID.coffee_roaster, Crop.coffee), 3, 3], \
              BID.factory : [Building(1, 7, 1, "Factory", BID.factory), 2, 3], \
              BID.university : [Building(1, 8, 1, "University", BID.university), 2, 3], \
              BID.harbor : [Building(1, 8, 1, "Harbor", BID.harbor), 2, 3], \
              BID.wharf : [Building(1, 9, 1, "Wharf", BID.wharf), 2, 3], \
              BID.guild_hall : [Building(2, 10, 1, "Guild Hall", BID.guild_hall), 1, 4], \
              BID.residence : [Building(2, 10, 1, "Residence", BID.residence), 1, 4], \
              BID.fortress : [Building(2, 10, 1, "Fortress", BID.fortress), 1, 4], \
              BID.customs_house : [Building(2, 10, 1, "Customs House", BID.customs_house), 1, 4], \
              BID.city_hall : [Building(2, 10, 1, "City Hall", BID.city_hall), 1, 4] \
            }
        # build the randomized plantation deck
        temp = []
        for i in range(0, 8):
            temp.append(Crop.coffee)
        for i in range(0, 9):
            temp.append(Crop.tobacco)
        for i in range(0, 10):
            temp.append(Crop.corn)
        for i in range(0, 11):
            temp.append(Crop.sugar)
        for i in range(0, 12):
            temp.append(Crop.indigo)            
        shuffle(temp)
        self.plantation_deck = [temp[0:11], temp[12:24], temp[25:37], temp[38:50]]
        
        # give the players their initial plantations and create the goods list
        self.cities[0].plantation.append([Crop.indigo, False])
        self.cities[1].plantation.append([Crop.indigo, False])
        self.cities[2].plantation.append([Crop.corn, False])
        for i in range(0, self.num_players):
            self.goods.append([])
            for j in range(0, 5):
                self.goods[i].append(0)
    
    def get_game_state(self, player):

        state = [log((min(VICTORY_POINT_MAX, self.victory_points[player])/VICTORY_POINT_MAX) * 9 + 1, 10)] # player victory points
        state.append(log((min(WEALTH_MAX, self.gold[player])/WEALTH_MAX) * 9 + 1, 10)) # player gold
        for i in range(1, 7): # money on each role
            state.append(log((min(ROLE_MONEY_MAX, self.role_gold[i])/ROLE_MONEY_MAX) * 9 + 1, 10))        
        for i in range(1, 24): # the number of buildings being worked of each type
            state.append(log((min(BUILDING_MAX, self.bonus(player, BID(i), True))/BUILDING_MAX) * 9 + 1, 10))
        for i in range(0, 5): # how much of each resource the player is holding on to
            state.append(log((min(ABUNDANCE_MAX, self.goods[player][i])/ABUNDANCE_MAX) * 9 + 1, 10))
        for i in range(1, 5): # amount of builfing production available per crop type
            state.append(log((min(PRODUCTION_MAX, sum(int(b.production == Crop(i) ) * b.assigned for b in self.cities[player].buildings))/PRODUCTION_MAX) * 9 + 1, 10))
        for i in range(-1, 5): # amount of plantation production available per crop type
            state.append(log((min(PLANTATION_MAX, sum((p[0] == Crop(i)) and p[1] for p in self.cities[player].plantation))/PLANTATION_MAX) * 9 + 1, 10))
        for i in range(0, 5): # possible amount of space available per crop type in all ships
            state.append(log((min(AVAILABILITY_MAX, max((s.capacity - s.cargo) * int(s.crop == Crop(i) or s.crop == Crop.none) for s in self.ships))/AVAILABILITY_MAX) * 9 + 1, 10))
        for i in range(0, 5): # whether each crop is or isn't in the trade house
            state.append(int(Crop(i) in self.trade_house))
        
        state.append(log((min(COLONISTS_LEFT_MAX, self.colonists_left)/COLONISTS_LEFT_MAX) * 9 + 1, 10)) # number of colonists left in the game
        state.append(log((min(COLONISTS_MAX, self.cities[player].get_total_colonists())/COLONISTS_MAX) * 9 + 1, 10)) # total number of colonists a player owns
        state.append(log((min(UNEMPLOYED_MAX, self.cities[player].unemployed)/UNEMPLOYED_MAX) * 9 + 1, 10)) # number of unemployed colonists a player has
        self.last_game_state = state
        return state
       
    
    def get_goods_list(self, player):    # return an expansion of the goods list
        return self.goods[player][0] * [Crop.corn] + self.goods[player][1] * [Crop.indigo] + self.goods[player][2] * [Crop.sugar] + \
                            self.goods[player][3] * [Crop.coffee] + self.goods[player][4] * [Crop.tobacco]


    def bonus(self, player, bid, ignore_assigned = False): # returns the number of a specified building a play has being worked        
        return sum((b.bid == bid) and ((b.assigned == b.workers) or ignore_assigned) for b in self.cities[player].buildings)



    def role_turn(self, role):
        role_player = self.roles.index(role)
        currentplayer = role_player

        # loop through each player's sub-turn
        while(True):
            if (role is Role.captain):
                self.captain_phase(currentplayer)
            elif (role is Role.trader):
                self.trader_phase(currentplayer)
            elif (role is Role.craftsman):
                self.craftsman_phase(currentplayer)
            elif (role is Role.builder):
                self.builder_phase(currentplayer)
            elif (role is Role.settler):
                self.settler_phase(currentplayer)
            elif (role is Role.mayor):
                if currentplayer is role_player:
                    my_colonists = self.colonist_ship // 3 # minimum colonists per player
                    leftovers = self.colonist_ship % 3
                self.mayor_phase(currentplayer, my_colonists + int(leftovers > 0) ) # take one of the lefotovers
                leftovers = max(0, leftovers - 1) # for correct colonist distribution
            else:
                print("\nError: " + role + " is not a valid role\n") #this shouldn't happen!
            currentplayer = (currentplayer + 1)%self.num_players

            # if the game is ending
            if (role != Role.captain and currentplayer is role_player) or (role == Role.captain and (not (True in self.can_ship))): # either one full turn or nobody can ship

                if (role == Role.mayor):            # put new colonists on the colonist ship
                    self.colonist_ship = max(self.num_players, \
                        self.cities[0].get_blank_spaces(True) + self.cities[1].get_blank_spaces(True) + self.cities[2].get_blank_spaces(True))
                    self.colonists_left -= self.colonist_ship
                    print("Loading " + str(self.colonist_ship) + " Colonists onto the Ship for the next mayor phase.")

                if (role == Role.settler):            # draw new plantations
                    for i in range(0, len(self.plantation_deck)):
                        if (len(self.plantation_deck[i]) > 1) and (self.plantation_deck[i][0] == Crop.none): # make sure it's been drawn and the stack isn't empty
                            del self.plantation_deck[i][0]

                if (role == Role.captain):
                    self.wharf_used = [0,0,0]
                    for p in range(0, 3):            # each player gets rid of crops
                        goods_list = self.get_goods_list(p)
                        if ( len(goods_list) == 0 ):
                            continue
                        print("Pick a barrel to keep")
                        keep = goods_list[self.console.get_crop(goods_list, p, 5, self.get_game_state(p))]    #choose crops to keep

                        # use warehouses
                        warehouses = self.bonus(p, BID.small_warehouse) + 2 * self.bonus(p, BID.large_warehouse)
                        if warehouses > 0:
                            goods_list = list(set(goods_list))
                            store = [0, 0, 0, 0, 0]
                            for w in range(0, warehouses):
                                print("Pick a type of good to store in a warehouse.")
                                temp = goods_list[self.console.get_crop(goods_list, p, 5, self.get_game_state(p))]
                                store[CropList.index(temp)] = self.goods[p][CropList.index(temp)] # note the amount of this crop to save
                            self.goods[p] = store
                            if store[CropList.index(keep)] == 0: # the additional barrel to keep
                                self.goods[p][CropList.index(keep)] += 1
                        else:
                            self.goods[p] = [0, 0, 0, 0, 0] # if the poor sap doesn't have a warehouse
                            self.goods[p][CropList.index(keep)] += 1

                                                    # full ships are sent home to Spain
                    for s in self.ships:
                        if s.is_full():
                            s.depart()

                if (role == Role.trader) and (len(self.trade_house) == 4):
                    self.trade_house = []            #empty the trade house
                    print("Trade house full!")
                return



    # Returns whether or not to end the game
    def game_end_condition(self):
        if ( self.roles[self.current_player] == Role.captain ) and (sum(self.victory_points) >= self.victory_points_max ):
            return True
        if ( self.colonists_left <= 0):
            return True
        if ( self.cities[0].used == self.cities[0].capacity or self.cities[1].used == self.cities[1].capacity or self.cities[2].used == self.cities[2].capacity):
            return True


    def get_end_game_vp_bonus( self, p ):
        extravp = 0
        # customs house needs to be calculated first because of its dependency on victory point chips
        if self.bonus(p, BID.customs_house) > 0:
            vp = self.victory_points[p] // 4
            print("Player " + str(p) + " gains " + str(vp) + " victory points from the Customs House.")
            extravp += vp

        if self.bonus(p, BID.guild_hall) > 0:
            vp = sum((b.production != Crop.none) and (b.workers == 1) for b in self.cities[p].buildings)
            vp += 2 * sum((b.production != Crop.none) and (b.workers != 1) for b in self.cities[p].buildings)
            print("Player " + str(p) + " gains " + str(vp) + " victory points from the Guild Hall.")
            extravp += vp
            
        if self.bonus(p, BID.residence) > 0:
            vp = max(4, len(self.cities[p].plantation) - 5)
            print("Player " + str(p) + " gains " + str(vp) + " victory points from the Residence.")
            extravp += vp
            
        if self.bonus(p, BID.fortress) > 0:
            vp = self.cities[p].get_total_colonists() // 3
            print("Player " + str(p) + " gains " + str(vp) + " victory points from the Fortress.")
            extravp += vp
            
        if self.bonus(p, BID.city_hall) > 0:
            vp = sum(b.production == Crop.none for b in self.cities[p].buildings)
            print("Player " + str(p) + " gains " + str(vp) + " victory points from the City Hall.")
            extravp += vp
        return extravp

        
    def end_game(self):

        # apply the large building bonuses
        for p in range(0, 3):
            self.victory_points[p] += self.get_end_game_vp_bonus( p )
            
        self.winner = self.victory_points.index(max(self.victory_points)) # we have a winner!
        winscore = max(self.victory_points)
        self.victory_points[self.winner] = 0
        self.runnerup = self.victory_points.index(max(self.victory_points))
        self.victory_points[self.winner] = winscore

        print("\n------------------\nGAME OVER!\n------------------\n\n First Place: Player " + str(self.winner + 1) + " with " + str(self.victory_points[self.winner]) + " victory points.")
        print("Second Place: Player " + str(self.runnerup + 1) + " with " + str(self.victory_points[self.runnerup]) + " victory points.")
        print("------------------\n\n")



    def end_game_turn(self):    # there's a new governor
        self.roles = [Role.none] * self.num_players
        self.governor = (self.governor + 1)%self.num_players
        self.current_player = self.governor
        


    # Returns whether or not to continue the game turn
    def end_player_turn(self):
        if self.game_end_condition():
            self.end_game()
            return False
        if(((self.governor == 0) and (self.current_player == (self.num_players -1))) or (self.current_player == (self.governor - 1))):
            self.end_game_turn()
            return False
        else:
            self.current_player = (self.current_player + 1) % self.num_players
            return True
    
    
    
    def game_turn(self):
        # do-while of role selection and role turns
        selector = self.governor
        self.roles[selector] = self.console.get_role(self.roles, selector, self.role_gold, self.get_game_state(selector))
        self.gold[selector] += self.role_gold[RoleList.index(self.roles[selector])]
        self.role_gold[RoleList.index(self.roles[selector])] = 0;
        selector = (selector + 1) % 3
        while selector != self.governor:
            self.roles[selector] = self.console.get_role(self.roles, selector, self.role_gold, self.get_game_state(selector))
            self.gold[selector] += self.role_gold[RoleList.index(self.roles[selector])]
            self.role_gold[RoleList.index(self.roles[selector])] = 0;            
            selector = (selector + 1) % 3

        # throw doubloons on all roles which were not chosen    
        for i in range(0, 7):
            if not (Role(i) in self.roles):
                self.role_gold[i] += 1        

        self.current_player = self.governor
        while True:
            # do the phase of the current player
            self.role_turn(self.roles[self.current_player])
            if ( not self.end_player_turn()):
                return
    
    
    
    def captain_phase(self, player):
        print("\nCAPTAIN PHASE for player " + str(player))
        # firstly, can the player actually ship anything? Build a crop list
        self.can_ship[player] = False
        goods_list = self.get_goods_list(player)
        crop_choices = []
        for s in self.ships:
            if s.crop == Crop.none:
                crop_choices += goods_list # we can ship whatever. purge doubles later
                self.can_ship[player] = True
                continue
            if s.crop in goods_list and not s.is_full():
                crop_choices.append(s.crop)
                self.can_ship[player] = True
        
        crop_choices = list(set(crop_choices)) # purge good doubles here
        
        for s in self.ships:  # can't ship goods which already fill a ship!
            if s.is_full() and s.crop in crop_choices:
                crop_choices.remove(s.crop)
        
        # the player can always use an empty wharf ship
        num_wharfs = self.bonus(player, BID.wharf) - self.wharf_used[player]
        if num_wharfs > 0:
            self.can_ship[player] = True
            crop_choices = goods_list[:] # I can ship everything I have
        
        # can we ship?
        if len(crop_choices) == 0:
            self.can_ship[player] = False
        
        if not self.can_ship[player]:
            print("Can't ship anything!")
            return

        # pick a crop to ship
        game_state = self.get_game_state(player)
        choice = self.console.get_crop(crop_choices, player, 4, game_state)
        if choice == None:
            return        
        crop_choice = crop_choices[choice]


        load_ship = None
        most_empty = None
        
        # determine which ship we need to load our goods on (or perhaps use a wharf ship...?)
        if (num_wharfs > 0) and self.console.get_wharf(player, game_state):
            self.wharf_used[player] += 1
            amount = self.goods[player][CropList.index(crop_choice)]
            load_ship = Ship(amount)    
        else:
            for s in self.ships:
                if s.crop == crop_choice: # we must load onto this ship!
                    load_ship = s
                    break
                if s.crop == Crop.none and (most_empty == None or s.capacity > most_empty.capacity):
                    most_empty = s
            if load_ship == None:
                load_ship = most_empty

            # now load the crop
            amount = min(load_ship.capacity - load_ship.cargo, self.goods[player][CropList.index(crop_choice)])

        # move cargo from the windrose to the ship
        self.goods[player][CropList.index(crop_choice)] -= amount
        load_ship.cargo += amount
        load_ship.crop = crop_choice
        print("Loaded " + str(amount) + " " + str(crop_choice) + " barrels onto cargo ship of size " + str(load_ship.capacity) + ".")

        # move VPs from the pile to the player, taking into account harbor
        amount += self.bonus(player, BID.harbor)
        print("Gained " + str(amount) + " victory points.")
        self.victory_points[player] += amount
        self.victory_points_max -= amount
        return



    def trader_phase(self, player):
        if len(self.trade_house) == 4:
            return
        print("\nTRADER PHASE for player " + str(player))
        possible_sales = self.get_goods_list(player)
        
        # get rid of goods already in the trade house, if the player doesn't have an office
        if self.bonus(player, BID.office) == 0:
            for good in self.trade_house:
                while good in possible_sales:
                    possible_sales.remove(good)

        # purge doubles from the list
        possible_sales = list(set(possible_sales))
                    
        # pick a good to trade
        if len(possible_sales) == 0:
            print("Cannot trade anything!")
        else:
            choice = self.console.get_crop(possible_sales, player, 3, self.get_game_state(player), True)
            if choice == None:
                return
            add_amount = CropList.index(possible_sales[choice]) + self.bonus(player, BID.small_market) + self.bonus(player, BID.large_market)
            if self.roles[player] == Role.trader:
                add_amount += 1 # trader privellege!
            self.trade_house.append(possible_sales[choice])
            print("Traded the " + str(possible_sales[choice]) + " for " + str(add_amount) + " doubloons.")
            self.gold[player] += add_amount
            self.goods[player][CropList.index(possible_sales[choice])] -= 1 # take one from the goods pile
        return
    
    
    
    def craftsman_phase(self, player):
        print("\nCRAFTSMAN PHASE for player " + str(player))
        crop_options = []
        # let's take a look at what goods the player gets.  can only produce what there's a plantation for.
        for i in range(0, 5):
            gather_crop = Crop(i)
            gather_count = sum((p[0] == gather_crop) and p[1] for p in self.cities[player].plantation) # count crops grown
            production_count = 0
            if gather_crop == Crop.corn:
                production_count = 12
            else:
                for b in self.cities[player].buildings:    # count possible production of this crop
                    if (b.production == gather_crop):
                        production_count += b.assigned
            self.goods[player][i] += min([production_count, gather_count])
            if min([production_count, gather_count]) > 0:
                print("Added " + str(min([production_count, gather_count])) + " " + str(gather_crop))
                if (not gather_crop in crop_options):    # for the craftsman player's extra crop or a factory owner's bonus doubloons
                    crop_options.append(gather_crop)
                    
        # factory owner gets doubloons! +0/1/2/3/5 per factory
        if self.bonus(player, BID.factory) > 0:
            cash = max(0, len(crop_options) - 1)
            if len(crop_options) == 5:
                cash += 1
            cash *= self.bonus(player, BID.factory)
            print("Earned " + str(cash) + " doubloons from factories.")            

        # get an extra crop if the player is the craftsman
        if (self.roles[player] == Role.craftsman) and (len(crop_options) > 0):
            print("Extra production for the craftsman")
            extra = self.console.get_crop(crop_options, player, 2, self.get_game_state(player)) # 2 because, I guess, "what could I use more of?"
            self.goods[player][CropList.index(crop_options[extra])] += 1
            print("Added 1 " + str(crop_options[extra]))
        return

    def builder_phase(self, player):
        # build up a list of overpriced stuff the AI might try to buy
        invalids = []
        game_state = self.get_game_state(player)
        print("\nBUILDER PHASE for player " + str(player) + ".  You have " + str(self.gold[player]) + " doubloons.")
        choice = self.console.get_building(self.store, player, self.cities[player].quarries(), invalids, game_state, self.gold[player], self.roles[player] == Role.builder)
        invalids.append(BIDList.index(choice))

        if choice == BID.none:
            return

        while ((self.gold[player] < (self.store[choice][0].cost - min(self.store[choice][2], self.cities[player].quarries())- int(self.roles[player] == Role.builder))) or \
            (self.cities[player].capacity - self.cities[player].used) < self.store[choice][0].size): # validate cost and size
            print("Cannot build " + self.store[choice][0].name + ".")
            choice = self.console.get_building(self.store, player, self.cities[player].quarries(), invalids, game_state, self.gold[player], self.roles[player] == Role.builder)
            invalids.append(BIDList.index(choice))

        new_building = self.store[choice][0].new()

        # use the university, if applicable
        if self.bonus(player, BID.university) and self.console.get_university(player, self.get_game_state(player)):
            new_building.assigned += 1

        self.cities[player].buildings.append(new_building)
        self.store[choice][1] -= 1
        self.gold[player] -= max(0, self.store[choice][0].cost - min(self.store[choice][2], self.cities[player].quarries()) - int(self.roles[player] == Role.builder))

        return



    def settler_phase(self, player):
        print("\nSETTLER PHASE for player " + str(player) + ". ")
        if len(self.cities[player].plantation) > 11:
            print("Not enough island space for new plantations")
            return

        # wanna use a hacienda?  pick blindly off of the top of the first pile
        if self.bonus(player, BID.hacienda) > 0:
            for i in range(0, self.console.get_haciendas(player, self.bonus(player, BID.hacienda), self.get_game_state(player))):
                choice = 0
                while (len(self.plantation_deck[choice]) == 0) or (self.plantation_deck[choice][0] == Crop.none): # get the first deck with an available plantation
                    if ( choice == 4 ):
                        print("No more plantations available!")
                        return
                    choice = choice + 1 
                if (len(self.cities[player].plantation) == 12):
                    return
                self.cities[player].plantation.append([self.plantation_deck[choice][0], False])
                print("Grabbed a " + str(self.plantation_deck[choice][0]) + " plantation with the hacienda.")
                del self.plantation_deck[choice][0]
            
        use_hospice = False
        # wanna use a hospice?
        if self.bonus(player, BID.hospice) > 0 and self.console.get_hospice(player):
            use_hospice = True

        choices = [Crop.none, Crop.none, Crop.none, Crop.none]
        
        # skim off the top of the plantation deck
        if len(self.plantation_deck[0]) > 0:
            choices[0] = self.plantation_deck[0][0]
        if len(self.plantation_deck[1]) > 0:
            choices[1] = self.plantation_deck[1][0]
        if len(self.plantation_deck[2]) > 0:
            choices[2] = self.plantation_deck[2][0]
        if len(self.plantation_deck[3]) > 0:
            choices[3] = self.plantation_deck[3][0]
        
        if (self.roles[player] == Role.settler or self.bonus(player, BID.construction_hut) > 0) and self.quarries > 0: 
            # the settler, or anyone with a construction hut, can build quarries
            choices.append(Crop.quarry)
        choice = self.console.get_crop(choices, player, 2, self.get_game_state(player), True)
        if choice == None:
            return
        self.cities[player].plantation.append([choices[choice], use_hospice]) # boolean says whether it's assigned to or not
        if choices[choice] == Crop.quarry:
            self.quarries -= 1
        else:
            self.plantation_deck[choice][0] = Crop.none
        return



    def mayor_phase(self, player, my_colonists):
        # how many colonists to take from the ship.  How to deal with non-divisible numbers?
        take = my_colonists
        if ((self.roles[player] == Role.mayor) and (self.colonists_left > 0)): # mayor gets free one, from the pile not the ship
            take +=1
            self.colonists_left -= 1
        print("\nMAYOR PHASE for player " + str(player) + ". You get " + str(take) + " from the ship.")

        # assign each new colonist to a chosen space        
        for i in range(0, take):
            if self.cities[player].get_blank_spaces() == 0: #quit if there are no more blank spots
                self.cities[player].unemployed += (take - i)
                return
            choice = self.console.get_worker_space(self.cities[player], player, self.get_game_state(player))
            self.cities[player].unemployed += 1 # because assign_worker decrements unemployed
            self.cities[player].assign_worker(choice)

        # now give them the opportunity to assign unemployed citizens
        if (self.cities[player].unemployed > 0):
            print("Player " + str(player) + " assign " + str(self.cities[player].unemployed) + " unemployed citizens")
        take = self.cities[player].unemployed
        for i in range(0, take):
            if self.cities[player].get_blank_spaces() == 0:
                return
            choice = self.console.get_worker_space(self.cities[player], player, self.get_game_state(player))
            self.cities[player].assign_worker(choice)
        return



if __name__ == "__main__":
    num_players = 3
    game = Game(3, num_players, None)
    
    while game.winner == None:
        game.game_turn()
