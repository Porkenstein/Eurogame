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
    av_tables = []
    for i in range(0, 3 - num_players):
        weights = []
        print("Enter filename for AI " + str(i))
        filename = input(">>")
        with open(filename, 'rb') as pickle_file:
            av_tables = pickle.load(pickle_file)

    # begin the game
    game = Game(3, num_players, ai)
    game.av_tables = av_tables
    
    while game.winner == None:
        game.game_turn()