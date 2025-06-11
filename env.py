from itertools import product

import numpy as np

from constants import *

class Env:
    def __init__(self,game=None):
        from game import CakeSortGame
        self.game = CakeSortGame() if game is None else game
        self.plate_index = 0

    def set_plate_index(self,index):
        self.plate_index = index

    def reset(self):
        from game import CakeSortGame
        self.game = CakeSortGame()
        return self.get_state()

    def step(self,action):
        score = self.game.score
        row,column = divmod(action,COLS)
        
        if self.game.board.get_plate_number(row,column):
            return self.get_state(),-10 if self.get_empty_spaces() else 0,True
  
        self.game.place_plate(self.plate_index,row,column)
        self.game.cleanup_empty_plates()
        
        return self.get_state(),self.game.score-score,False

    def get_state(self):
        state = []
        for i,j in product(range(ROWS),range(COLS)):
            slices = self.game.board.grid[i][j].slices
            state.append(list(slices)+[0]*(MAX_SLICES_PER_PLATE-len(slices)))

        if not self.game.current_plates:
            self.game.reset_plates()
            
        plate = self.game.current_plates[0]
        state.append(list(plate.slices)+[0]*(MAX_SLICES_PER_PLATE-len(plate.slices)-1))

        return np.concatenate(state)
    
    def get_empty_spaces(self):
        return sum(self.game.board.plate_number_map.flatten() == 0)
