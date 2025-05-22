from __future__ import annotations

from constants import *

from collections import Counter

import numpy as np

class Plate:
    def __init__(self, slices: np.array):
        self.slices = slices

    def set_plate(self, slices: np.array):
        self.slices = slices

    def add_slices(self, slice_type: int, number_of_slices: int) -> int:
        space_left = MAX_SLICES_PER_PLATE - len(self.slices)
        actual_added = min(space_left, number_of_slices)
        self.slices = np.sort(np.concatenate((self.slices,[slice_type] * actual_added)))
        return actual_added

    def remove_slices(self, slice_type: int , no_removes: int) -> int:
        removed_count = min(self.count_slice(slice_type),no_removes)
        indexes = np.where(self.slices == slice_type)[0]
        self.slices = np.delete(self.slices,indexes[:removed_count])

        return removed_count
    
    def count_slice(self, slice_type) -> int:
        return Counter(self.slices)[slice_type]

    @property
    def slices_types(self) -> int:
        return len(Counter(self.slices))
    
    @property
    def empty_spaces(self) -> int:
        return MAX_SLICES_PER_PLATE - len(self.slices)

    @property
    def is_clearable(self) -> bool:
        # Pentru Costin:
        # Returnează True dacă farfuria are exact 6 felii și toate sunt de același tip (regula CakeSort)
        return len(self.slices) == MAX_SLICES_PER_PLATE and self.slices_types == 1

    @property
    def is_empty(self) -> bool:
        # Pentru Costin:
        # Returnează True dacă farfuria nu mai are nicio felie (pentru cleanup pe tablă)
        return len(self.slices) == 0

    def __and__(self, other: Plate) -> int | None:
        common = np.intersect1d(self.slices, other.slices, assume_unique=False)
        return common[0] if common.size > 0 else None

    def __str__(self):
        return "".join(map(lambda x: str(int(x)),self.slices))
    
    @staticmethod
    def generate_plate():
        total_slices = np.random.randint(1, MAX_SLICES_PER_PLATE - 1)
        number_of_slice_types = np.random.randint(1, total_slices + 1)
        chosen_slice_types = np.random.choice(CAKE_SLICE_TYPES, size=number_of_slice_types, replace=False)

        base_distribution = np.full(number_of_slice_types, total_slices // number_of_slice_types)
        remaining = total_slices % number_of_slice_types

        if remaining > 0:
            indices = np.random.choice(number_of_slice_types, size=remaining, replace=False)
            base_distribution[indices] += 1

        generated_slices = np.repeat(chosen_slice_types, base_distribution)
        generated_slices.sort()

        return Plate(generated_slices)