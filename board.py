from constants import *
from plate import Plate

import numpy as np

class Board:
    def __init__(self):
        self.grid = [[Plate([])] * COLS for _ in range(ROWS)]
        self.plate_number_map = np.zeros((ROWS, COLS), dtype=int)

    def place_plate(self, row: int, column: int, plate_number: int, plate: np.array) -> bool:
        if not self.plate_number_map[row, column]:
            return False
        self.grid[row][column] = Plate(plate)
        self.plate_number_map[row, column] = plate_number
        return True

    def get_plate_number(self, row: int, column: int) -> int:
        return self.plate_number_map[row, column]

    def get_plate_slices(self, row: int, column: int) -> Plate:
        return self.grid[row][column]

    def remove_plate(self, row: int, column: int):
        self.grid[row][column] = Plate([])
        self.plate_number_map[row, column] = 0
