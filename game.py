import numpy as np
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
        plate_numbers_to_remove = []
        cleared_positions = []
        for row_index in range(ROWS):
            for column_index in range(COLS):
                plate_number = self.board.get_plate_number(row_index, column_index)
                if plate_number != 0:
                    plate = self.placed_plates.get(plate_number)
                    if plate and len(plate.slices) == 0:
                        self.board.remove_plate(row_index, column_index)
                        plate_numbers_to_remove.append(plate_number)
                        cleared_positions.append((row_index, column_index))
                        print(f"Plate at ({row_index + 1}, {column_index + 1}) is empty and removed from board.")
        for plate_number in plate_numbers_to_remove:
            del self.placed_plates[plate_number]
        return cleared_positions

    def place_plate(self, plate_index, row_index, column_index):
        if plate_index < 0 or plate_index >= len(self.current_plates):
            return False, []
        if not (0 <= row_index < ROWS and 0 <= column_index < COLS):
            return False, []
        if self.board.get_plate_number(row_index, column_index) != 0:
            return False, []

        selected_plate = self.current_plates.pop(plate_index)

        if not self.board.place_plate(row_index, column_index, self.plate_counter, selected_plate):
            self.current_plates.insert(plate_index, selected_plate)
            return False, []

        self.placed_plates[self.plate_counter] = selected_plate
        moves = self._process_plate_after_placement(row_index, column_index, self.plate_counter)
        self.plate_counter += 1
        return True, moves

    def _process_plate_after_placement(self, row, col, plate_number):
        current = self.placed_plates[plate_number]
        moves = []
        neighbors = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            r, c = row+dr, col+dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                pn = self.board.get_plate_number(r, c)
                if pn:
                    neighbors.append((r, c, self.placed_plates[pn]))

        for nr, nc, neighbor in neighbors:
            common_types = set(current.slices) & set(neighbor.slices)
            for slice_type in common_types:
                cnt_cur = current.count_slice(slice_type)
                cnt_nb  = neighbor.count_slice(slice_type)
                total   = cnt_cur + cnt_nb
                # Înregistrează mutarea pentru animație
                if cnt_nb > 0:
                    moves.append((nr, nc, row, col, slice_type, cnt_nb))
                current.remove_slices(slice_type, cnt_cur)
                neighbor.remove_slices(slice_type, cnt_nb)
                if total > MAX_SLICES_PER_PLATE:
                    remaining = total - MAX_SLICES_PER_PLATE
                else:
                    remaining = total
                if remaining > 0:
                    current.add_slices(slice_type, remaining)
                if current.is_clearable():
                    self.board.remove_plate(row, col)
                    self.score += 1
                    return moves
        return moves
