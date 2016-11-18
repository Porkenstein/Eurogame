#/**********************************************************************/
#/*                                                                    */
#/*  Copyright (c) 1994                                                */
#/*  Larry D. Pyeatt                                                   */
#/*  Computer Science Department                                       */
#/*  Colorado State University                                         */
#/*                                                                    */
#/*  Permission is hereby granted to copy all or any part of           */
#/*  this program for free distribution.   The author's name           */
#/*  and this copyright notice must be included in any copy.           */
#/*                                                                    */
#/*  Contact the author for commercial licensing.                      */

import random
from math import exp
import pickle
class phase_ann:
    #Takes two lists of weights and randomly chooses between the two weight to pick
    def combine_weights( self, weights1, weights2 ):
         for i in range( 0, self.numlayers-1 ):  #(i = 0 ; i < (numlayers - 1) ; i++)
            for j in range( 0, self.size[i+1] ):     #(j = 0 ; j < size[i+1] ; j++)
                for k in range( 0, self.size[i]+1 ):   #(k = 0 ; k < size[i]+1 ; k++)  // +1 for the bias input 
                    tmp = random.random()
                    if( tmp < 0.5 ):
                        self.weights[i][j][k] = weights1[i][j][k]
                    else:
                        self.weights[i][j][k] = weights2[i][j][k]
    
    #Takes two lists of weights and applies BLX-alpha crossover, selecting between a range cenetered around the two weights
    # interval is [x_min - (alpha * difference), x_max + (alpha * difference)
    def crossover_weights( self, other1, other2, alpha ):
         for i in range( 0, self.numlayers-1 ):  #(i = 0 ; i < (numlayers - 1) ; i++)
            for j in range( 0, self.size[i+1] ):     #(j = 0 ; j < size[i+1] ; j++)
                for k in range( 0, self.size[i]+1 ):   #(k = 0 ; k < size[i]+1 ; k++)  // +1 for the bias input 
                    min_x = min( other1.weights[i][j][k], other2.weights[i][j][k] )
                    max_x = max( other1.weights[i][j][k], other2.weights[i][j][k] )
                    dif_x = max_x - min_x
                    self.weights[i][j][k] = random.uniform(min_x - (alpha * dif_x), max_x + (alpha * dif_x))

    def mutate_weights( self, num_weights ):
        for i in range( 0, num_weights ):
            j = random.randint(0, self.numlayers-2)
            k = random.randint(0, self.size[j+1]-1 )
            l = random.randint(0, self.size[j])
            self.weights[j][k][l] = random.random()
            



#/* define the activation (transfer) function and its derivative */

    def xferfunc(self, x, theta):
        return 1.0 / (1.0 + exp(-(theta*x)));

    def xferfuncprime( self, xprime, theta):
        return theta * (xprime * (1.0 - xprime));

#/* Methods for scaling the input and output data                */
    def scale( self, x ):
        return ((x - self.xfermin) / (self.xfermax - self.xfermin) * (self.outmax-self.outmin)) + self.outmin;

    def unscale( self, x ):
        return ((x / (self.outmax - self.outmin)) * (self.xfermax - self.xfermin)); 

    #/* Allocate storage for the bpnet                               */
    def new_all(self):
        #/* allocate storage for the layers */
        self.activation = [0 for i in range(self.numlayers)] #new
        self.dotprod = [0 for i in range(self.numlayers)]         #new double*[numlayers];
        self.weights = [0 for i in range(self.numlayers-1)]       #new double**[numlayers-1];
        self.sigma =   [0 for i in range(self.numlayers)]         #new double*[numlayers];
        self.delta =   [0 for i in range(self.numlayers-1)]         #new double**[numlayers-1];     
        for i in range( self.numlayers ):
            self.activation[i] = [0 for k in range( self.size[i] ) ]  #new double[size[i]];
            self.dotprod[i] = [0 for k in range( self.size[i] ) ]     #new double[size[i]];

            self.sigma[i] = [0 for k in range( self.size[i] ) ]   #new double[size[i]];

            if( i < ( self.numlayers - 1 ) ):
                self.weights[i] = [0 for k in range( self.size[i+1] ) ]  #new double*[size[i+1]];
                self.delta[i] =   [0 for k in range( self.size[i+1] ) ]  #new double*[size[i+1]];
                for j in range( self.size[i+1] ):   #(j = 0 ; j < size[i+1] ; j++)
                    #// add one for the bias input
                    self.weights[i][j] = [ 0 for k in range( self.size[i] + 1 ) ] #new double[size[i]+1];
                    self.delta[i][j] =   [ 0 for k in range( self.size[i] + 1 ) ] #new double[size[i]+1];  

#/****************************************************************/
#/* Constructor for the backpropagation networks                 */
#/* arguments:                                                   */
#/*    number of layers,                                         */
#/*    size of input layer,                                      */
#/*    size of hidden layers,                                    */
#/*    ...                                                       */
#/*    size of output layer                                      */
    def __init__(self, layers, *args):
        self.set_defaults();
        self.numlayers = layers;  
        self.weights = []
        self.size = [ 0.0 for i in range(self.numlayers) ]
        j = 0
        self.size[0] = args[0] # input layer lengths
        for i in range(1, layers - 1): # hidden layer lengths
            self.size[i] = args[1];
        self.size[layers - 1] = args[2] # output layer lengths
        self.new_all();
  #/* randomize the weights and set deltas to zero */
        for i in range( 0, self.numlayers-1 ):  #(i = 0 ; i < (numlayers - 1) ; i++)
            for j in range( 0, self.size[i+1] ):     #(j = 0 ; j < size[i+1] ; j++)
                for k in range( 0, self.size[i]+1 ):   #(k = 0 ; k < size[i]+1 ; k++)  // +1 for the bias input 
                    self.weights[i][j][k] = random.random()
                    self.delta[i][j][k] = 0.0;

    def set_defaults(self):
        self.fitness = -1.0;
        self.THETA = 1.0;
        self.STEP = 0.01;
        self.MOMENTUM = 0.0;
        self.outmax = 1.0; 
        self.outmin = -1.0; 
        self.xfermin = 0;
        self.xfermax = 1;
        self.LINEAR_OUTPUT = 0;

#/* evaluate the network from inputs to outputs                  */
    def evaluate( self, input_vector, output_vector):
  #/* Don't copy input vector.  Just set the pointer  */
        self.activation[0] = input_vector;
  
        for i in range ( self.numlayers - 1):       #(i = 0 ; i < numlayers - 1 ; i++)      // i = layer number
            for j in range( self.size[i+1] ):       #(j = 0 ; j < self.size[i+1] ; j++)    #// j = to node
                self.dotprod[i+1][j] = 0.0;
                for k in range( self.size[i] ):          #(k = 0 ; k < size[i] ; k++)      #// k = from node
                    self.dotprod[i+1][j] += (self.weights[i][j][k] * self.activation[i][k]);
                self.dotprod[i+1][j] += self.weights[i][j][self.size[i]] * 1.0;                  #// bias input 
                if( ( i < self.numlayers-2 ) or ( not self.LINEAR_OUTPUT )):
                    self.activation[i+1][j] = self.xferfunc(self.dotprod[i+1][j],self.THETA);
                else:
                    self.activation[i+1][j] = self.dotprod[i+1][j] * self.THETA;         
  
        for i in range( self.size[self.numlayers - 1] ):   #(i = 0 ; i < size[numlayers-1] ; i++)
            output_vector[i] = self.scale( self.activation[self.numlayers-1][i] );
    def write_weights(self, filename):
        pickle.dump( self.weights, open(filename,'wb'))
        pickle.dump( self.size, open(filename + '_size.pickle','wb'))

def get_ann(filename):
    rfile = open(filename, 'r')
    weights = pickle.load(rfile)
    size = pickle.load(open(filename+'_size.pickle','r'));
    layers = len(size)
    player = phase_ann( layers, *size )
    player.weights = weights
    return player
def main():
    layers = 4
    layer1 = 4
    layer2 = 4
    layer3 = 7
    layer4 = 7
    input_vector = [0 for i in range(layer4) ]
    input_vector[0] = [ 0, 0, 0, 0]
    input_vector[1] = [ 0, 0, 0, 1]
    input_vector[2] = [ 0, 0, 1, 0]
    input_vector[3] = [ 0, 0, 1, 1]
    input_vector[4] = [ 0, 1, 0, 0]
    input_vector[5] = [ 0, 1, 0, 1]
    input_vector[6] = [ 0, 1, 1, 0]
    ans = [0 for i in range(layer4)]
    for i in range( layer4 ):
        ans[i] = input_vector[i][0]*2 + input_vector[i][1] + input_vector[i][2]*2 + input_vector[i][3]
    results = [ -1 for i in range(layer4)]
    test = phase_ann(layers, layer1, layer2, layer3, layer4 )
    test.write_weights('my_test')
    new_test = get_ann('my_test')
    new_test.write_weights('test2')
    while( min(results) == -1 ):
        results = [ -1 for i in range(layer4)]
        for i in range(layer4):
            output_vector = [0 for k in range(layer4)]
            test.evaluate(input_vector[i], output_vector)
            test.mutate_weights(1)
            if( output_vector[ans[i]] == max(output_vector)):
                results[i] = 1
        print(results)
    test.write_weights('my_test')
    new_test = get_ann('my_test')
    new_test.write_weights('test2')
if __name__ == "__main__":
    main()

