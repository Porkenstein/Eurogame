from ai_controller import *



#  This is the main which should be run for the
#  Puerto Rico AI
if __name__ == "__main__":
    print("Puerto Rico - a game by Andreas Seyfarth.  Simulation by Derek Stotz.")
    print("------------------------------------------------------------------------------------\n")

    weights = []
    ai = []

    # ask for number of human players (0 - 3)
    print("How many human players?")
    num_players = input(">>")
    while (not num_players.isdigit()) or (int(num_players) > 3) or (int(num_players) < 0):
        num_players = input(">>")
    num_players = int(num_players) 

    # load weights from file
    for i in range(0, 3 - num_players):
        weights = []
        print("Enter filename for AI " + str(i))
        filename = input(">>")
        print("Hidden Layers?")
        hidden_layers = int(input(">>"))
        with open(filename, 'rb') as pickle_file:
            weights.append(pickle.load(pickle_file))

        # create the AIs
        ai.append(AI(hidden_layers, [weights[i][0], weights[i][1], weights[i][2], weights[i][3], weights[i][4], weights[i][5], weights[i][6], weights[i][7], weights[i][8], weights[i][9]]))

    # begin the game
    game = Game(3, num_players, ai)
    
    while game.winner == None:
        game.game_turn()