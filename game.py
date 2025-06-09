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
                    if ((neighbor:=self.board.get_plate(neighbor_row,neighbor_column)) & plate) is not None
        ]

        grouped = defaultdict(list)
        for neighbor,intersection,neighbor_row,neighbor_column in neighbors:
            for intersect in intersection:
                grouped[intersect].append((neighbor,neighbor_row,neighbor_column))

        print(grouped)

        for slice_type,group in grouped.items():
            print(f"{slice_type=}")
            if len(group) > 1:
                if plate.slices_types == 1:
                    # plate has a single type and all neighbors shares the same type with the plate
                    print("Case 0x111")
                    for neighbor,neighbor_row,neighbor_column in group:
                        CakeSortGame.__interchange_plates(
                            plate,neighbor,row,column,neighbor_row,neighbor_column,
                            slice_type,moves
                        )
                else:
                    print("B")
                    # otherwise the plate with more slices will be selected to have all slices
                    ordered_group = sorted(
                        group,
                        key=lambda x: x[0].count_slice(slice_type) if x[0].empty_spaces else 0
                    )
                    selected_plate,selected_row,selected_column = ordered_group.pop()
                    print(selected_row,selected_column)
                    for neighbor,neighbor_row,neighbor_column in ordered_group:
                        CakeSortGame.__interchange_plates(
                            plate,neighbor,row,column,neighbor_row,neighbor_column,
                            slice_type,moves
                        )

                    CakeSortGame.__interchange_plates(
                        selected_plate,plate,selected_row,selected_column,row,column,
                        slice_type,moves
                    )

                    # in the case, remaining slices are not moved
                    for neighbor,neighbor_row,neighbor_column in group:
                        if neighbor.count_slice(slice_type) not in [0,6] and plate.count_slice(slice_type):
                            CakeSortGame.__interchange_plates(
                                plate,neighbor,row,column,neighbor_row,neighbor_column,
                                slice_type,moves
                            )
                            CakeSortGame.__interchange_plates(
                                selected_plate,plate,selected_row,selected_column,row,column,
                                slice_type,moves
                            )

                continue

            neighbor,neighbor_row,neighbor_column = group.pop()
            
            if neighbor.slices_types == 1 and plate.slices_types != 1:
                print("Case 0x21")
                # when plate has more types and neighbor just one, go to neighbor
                CakeSortGame.__interchange_plates(
                    neighbor,plate,neighbor_row,neighbor_column,row,column,
                    slice_type,moves
                )
            elif neighbor.slices_types == plate.slices_types == 2 and plate ^ neighbor:
                # when plate and neighbor shares exactly same 2 types, interchange the slices
                print("Case 0x22")
                
                CakeSortGame.__interchange_plates(
                    plate,neighbor,row,column,neighbor_row,neighbor_column,
                    slice_type,moves
                )
                slice_type = (neighbor & plate)[0]
                CakeSortGame.__interchange_plates(
                    neighbor,plate,neighbor_row,neighbor_column,row,column,
                    slice_type,moves
                )
            else:
                # when plate shares a type with a neighbor, go to plate
                print("Case 0x11")
                CakeSortGame.__interchange_plates(
                    plate,neighbor,row,column,neighbor_row,neighbor_column,
                    slice_type,moves
                )

        return moves

    @staticmethod
    def __interchange_plates(
        plate1,
        plate2,
        plate1_row,
        plate1_column,
        plate2_row,
        plate2_column,
        slice_type,
        moves
    ):
        count = min(plate1.empty_spaces,plate2.count_slice(slice_type))
        plate2.remove_slices(slice_type,count)
        plate1.add_slices(slice_type,count)
        moves.append(create_move(
            plate2_row,plate2_column,plate1_row,plate1_column,slice_type,count
        ))
