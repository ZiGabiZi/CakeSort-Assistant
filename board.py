import numpy as np
from constants import ROWS, COLS, MAX_SLICES_PER_PLATE

class Board:
    def __init__(self):
        self.grid = np.zeros((ROWS, COLS, MAX_SLICES_PER_PLATE), dtype=int)
        self.plate_number_map = np.zeros((ROWS, COLS), dtype=int)

    def place_plate(self, row_index, column_index, plate_number, slice_array):
        if self.plate_number_map[row_index, column_index] != 0:
            return False
        self.grid[row_index, column_index] = slice_array
        self.plate_number_map[row_index, column_index] = plate_number
        return True

    def get_plate_number(self, row_index, column_index):
        return self.plate_number_map[row_index, column_index]

    def get_plate_slices(self, row_index, column_index):
        return self.grid[row_index, column_index]

    def remove_plate(self, row_index, column_index):
        self.grid[row_index, column_index] = 0
        self.plate_number_map[row_index, column_index] = 0
