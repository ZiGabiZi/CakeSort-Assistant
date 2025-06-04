from itertools import product
from collections import defaultdict

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
        neighbors = [
            (
                neighbor,
                neighbor & plate,
                neighbor_row,
                neighbor_column
            )
                for neighbor_row,neighbor_column in self.board.get_neighbors_indexes(row,column)
                    if (neighbor:=self.board.get_plate(neighbor_row,neighbor_column)) & plate
        ]

        grouped = defaultdict(list)
        for neighbor,intersection,neighbor_row,neighbor_column in neighbors:
            grouped[intersection].append((neighbor,neighbor_row,neighbor_column))

        print(grouped)
        for slice_type,group in grouped.items():
            if len(group) > 1:
                if all(map(lambda x: x[0].slices_types == 1,group)) and plate.slices_types == 1:
                    for neighbor,neighbor_row,neighbor_column in group:
                        count = min(plate.empty_spaces,neighbor.count_slice(slice_type))
                        neighbor.remove_slices(slice_type,count)
                        plate.add_slices(slice_type,count)
                        moves.append(create_move(
                            neighbor_row,neighbor_column,row,column,slice_type,count
                        ))
                else:
                    selected_plate,selected_row,selected_column = group.pop()
                    for neighbor,neighbor_row,neighbor_column in group:
                        count = min(plate.empty_spaces,neighbor.count_slice(slice_type))
                        neighbor.remove_slices(slice_type,count)
                        plate.add_slices(slice_type,count)
                        moves.append(create_move(
                            neighbor_row,neighbor_column,row,column,slice_type,count
                        ))

                    count = min(selected_plate.empty_spaces,plate.count_slice(slice_type))
                    selected_plate.add_slices(slice_type,count)
                    plate.remove_slices(slice_type,count)
                    moves.append(create_move(
                        row,column,selected_row,selected_column,slice_type,count
                    ))

                continue

            if neighbor.slices_types == 1 and plate.slices_types != 1:
                count = min(neighbor.empty_spaces,plate.count_slice(slice_type))
                neighbor.add_slices(slice_type,count)
                plate.remove_slices(slice_type,count)
                moves.append(create_move(
                    row,column,neighbor_row,neighbor_column,slice_type,count
                ))
            else:
                count = min(plate.empty_spaces,neighbor.count_slice(slice_type))
                neighbor.remove_slices(slice_type,count)
                plate.add_slices(slice_type,count)
                moves.append(create_move(
                    neighbor_row,neighbor_column,row,column,slice_type,count
                ))

        return moves
