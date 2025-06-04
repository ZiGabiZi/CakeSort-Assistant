from constants import *
from plate import Plate

import numpy as np

class Board:
    def __init__(self):
        self.grid = [[Plate(np.array([]))] * COLS for _ in range(ROWS)]
        self.plate_number_map = np.zeros((ROWS, COLS), dtype=int)

    def place_plate(self, row: int, column: int, plate_number: int, plate: Plate) -> bool:
        if self.plate_number_map[row, column]:
            return False
        self.grid[row][column] = plate
        self.plate_number_map[row, column] = plate_number
        return True

    def get_plate_number(self, row: int, column: int) -> int:
        return self.plate_number_map[row, column]

    def get_plate(self, row: int, column: int) -> Plate:
        return self.grid[row][column]

    def remove_plate(self, row, col):
        self.grid[row][col] = Plate(np.array([]))
        self.plate_number_map[row, col] = 0
    
    @staticmethod
    def get_neighbors_indexes(row: int, column: int) -> list[tuple[int,int]]:
        neighbors = []
        if row < ROWS - 1:
            neighbors.append((row + 1, column))
        if row > 0:
            neighbors.append((row - 1, column))
        if column > 0:
            neighbors.append((row, column - 1))
        if column < COLS - 1:
            neighbors.append((row, column + 1))
        return neighbors
