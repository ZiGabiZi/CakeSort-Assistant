from itertools import product

import numpy as np

from utils import *
from constants import *
from plate import Plate
from board import Board

class CakeSortGame:
    def __init__(self):
        self.board = Board()
        self.current_plates = [Plate.generate_plate() for _ in range(3)]
        self.score = 0
        self.plate_counter = 1
        self.placed_plates = {}

    def reset_plates(self):
        self.current_plates = [Plate.generate_plate() for _ in range(3)]

    def cleanup_empty_plates(self):
        cleared_positions = []
        for row, column in product(range(ROWS),range(COLS)):
            plate_number = self.board.get_plate_number(row, column)
            if plate_number != 0:
                plate = self.placed_plates[plate_number]
                if plate.is_empty:
                    self.board.remove_plate(row, column)
                    del self.placed_plates[plate_number]
                    cleared_positions.append((row, column))
                    print(f"Plate at ({row + 1}, {column + 1}) is empty and removed from board.")
                if plate.is_clearable:
                    plate.slices = np.array([], dtype=int)
                    self.board.remove_plate(row, column)
                    del self.placed_plates[plate_number]
                    self.score += 1
        return cleared_positions

    def place_plate(self, plate_index, row_index, column_index):
        if self.board.get_plate_number(row_index, column_index):
            return False, []

        selected_plate = self.current_plates.pop(plate_index)
        if not self.board.place_plate(row_index, column_index, self.plate_counter, selected_plate):
            self.current_plates.insert(plate_index, selected_plate)
            return False, []

        self.placed_plates[self.plate_counter] = selected_plate
        moves = self.__process_new_plate(row_index, column_index, self.plate_counter)
        self.plate_counter += 1
        return True, moves

    def __process_new_plate(self, row, column, plate_number):
        plate = self.board.get_plate(row, column)
        moves = []
        # Pentru Costin:
        # Mută felii de la vecini spre farfuria NOUĂ (regula CakeSort corectă)
        for neighbor_row, neighbor_column in self.board.get_neighbors_indexes(row, column):
            neighbor = self.board.get_plate(neighbor_row, neighbor_column)
            common_types = np.intersect1d(plate.slices, neighbor.slices)
            for slice_type in common_types:
                need = plate.empty_spaces
                available = neighbor.count_slice(slice_type)
                to_move = min(need, available)
                if to_move > 0:
                    neighbor.remove_slices(slice_type, to_move)
                    plate.add_slices(slice_type, to_move)
                    moves.append(create_move(
                        neighbor_row, neighbor_column, row, column, slice_type, to_move
                    ))
        # Pentru Costin:
        # Clear dacă farfuria NOUĂ are 6 felii identice (regula CakeSort)
        if plate.is_clearable:
            plate.slices = np.array([], dtype=int)
            self.board.remove_plate(row, column)
            del self.placed_plates[plate_number]
            self.score += 1
        return moves
