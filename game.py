import random
import numpy as np
from constants import CAKE_SLICE_TYPES, ROWS, COLS, MAX_SLICES_PER_PLATE
from plate import Plate
from board import Board

class CakeSortGame:
    def __init__(self):
        self.board = Board()
        self.plates = [self.generate_plate() for _ in range(3)]
        self.score = 0
        self.plate_counter = 0
        self.plate_contents_by_number = {}

    @staticmethod
    def generate_plate():
        total_slices = random.randint(1, 5)
        number_of_slice_types = random.randint(1, total_slices)
        chosen_slice_types = random.sample(CAKE_SLICE_TYPES, number_of_slice_types)

        slice_distribution = [total_slices // number_of_slice_types] * number_of_slice_types
        remaining_slices = total_slices % number_of_slice_types

        while remaining_slices > 0:
            random_index = random.randint(0, number_of_slice_types - 1)
            slice_distribution[random_index] += 1
            remaining_slices -= 1

        generated_slices = []
        for index in range(number_of_slice_types):
            generated_slices.extend([chosen_slice_types[index]] * slice_distribution[index])
        generated_slices.sort()
        return Plate(generated_slices)

    def refresh_plates(self):
        if not self.plates:
            self.plates = [self.generate_plate() for _ in range(3)]

    def cleanup_empty_plates(self):
        plate_numbers_to_remove = []
        for row_index in range(ROWS):
            for column_index in range(COLS):
                plate_number = self.board.get_plate_number(row_index, column_index)
                if plate_number != 0:
                    plate = self.plate_contents_by_number.get(plate_number)
                    if plate and len(plate.slices) == 0:
                        self.board.remove_plate(row_index, column_index)
                        plate_numbers_to_remove.append(plate_number)
                        print(f"Plate at ({row_index + 1}, {column_index + 1}) is empty and removed from board.")
        for plate_number in plate_numbers_to_remove:
            del self.plate_contents_by_number[plate_number]

    def place_plate(self, plate_index, row_index, column_index):
        if plate_index < 0 or plate_index >= len(self.plates):
            return False
        if not (0 <= row_index < ROWS and 0 <= column_index < COLS):
            return False
        if self.board.get_plate_number(row_index, column_index) != 0:
            return False

        self.plate_counter += 1
        selected_plate = self.plates.pop(plate_index)
        plate_slices_array = np.zeros(MAX_SLICES_PER_PLATE, dtype=int)
        for i, slice_value in enumerate(selected_plate.slices):
            plate_slices_array[i] = int(slice_value)

        if not self.board.place_plate(row_index, column_index, self.plate_counter, plate_slices_array):
            self.plates.insert(plate_index, selected_plate)
            return False

        self.plate_contents_by_number[self.plate_counter] = selected_plate
        self._process_plate_after_placement(row_index, column_index, self.plate_counter)
        return True

    def _process_plate_after_placement(self, row, col, plate_number):
        current = self.plate_contents_by_number[plate_number]

        neighbors = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            r, c = row+dr, col+dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                pn = self.board.get_plate_number(r, c)
                if pn:
                    neighbors.append(self.plate_contents_by_number[pn])

        for neighbor in neighbors:
            common_types = set(current.slices) & set(neighbor.slices)
            for slice_type in common_types:
                cnt_cur = current.count_slice(slice_type)
                cnt_nb  = neighbor.count_slice(slice_type)
                total   = cnt_cur + cnt_nb
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
                    return
