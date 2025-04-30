from constants import MAX_SLICES_PER_PLATE

class Plate:
    def __init__(self, slice_list):
        self.slices = slice_list

    def count_slice(self, slice_type):
        return self.slices.count(slice_type)

    def add_slices(self, slice_type, number_of_slices):
        self.slices.extend([slice_type] * number_of_slices)

    def remove_slices(self, slice_type, number_to_remove):
        removed_count = 0
        remaining_slices = []
        for current_slice in self.slices:
            if current_slice == slice_type and removed_count < number_to_remove:
                removed_count += 1
            else:
                remaining_slices.append(current_slice)
        self.slices = remaining_slices

    def is_clearable(self):
        return len(self.slices) == MAX_SLICES_PER_PLATE and len(set(self.slices)) == 1

    def __str__(self):
        return "".join(self.slices)
