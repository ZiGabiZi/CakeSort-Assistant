import numpy as np
import random

# Constants
ROWS, COLS = 5, 4
CAKE_SLICES = ["1", "2", "3", "4", "5", "6"]
MAX_SLICES = 6

class Plate:
    def __init__(self, slices):
        self.slices = slices

    def count_slice(self, slice_type):
        return self.slices.count(slice_type)

    def add_slices(self, slice_type, count):
        self.slices.extend([slice_type] * count)

    def remove_slices(self, slice_type, count):
        removed = 0
        new_slices = []
        for s in self.slices:
            if s == slice_type and removed < count:
                removed += 1
            else:
                new_slices.append(s)
        self.slices = new_slices

    def is_clearable(self):
        return len(self.slices) == MAX_SLICES and len(set(self.slices)) == 1

    def __str__(self):
        return "".join(self.slices)

class Board:
    def __init__(self):
        self.grid = np.full((ROWS, COLS), " ", dtype=str)

    def place_plate(self, row, col, plate_number):
        if self.grid[row, col] != " ":
            print("The spot is already taken!")
            return False
        self.grid[row, col] = str(plate_number)
        return True

    def get_plate_number(self, row, col):
        return self.grid[row, col]

    def remove_plate(self, row, col):
        self.grid[row, col] = " "

    def print_board(self):
        print("\n    1   2   3   4")
        print("  +---+---+---+---+")
        for row in self.grid:
            print("  | " + " | ".join(row) + " |")
            print("  +---+---+---+---+")

    def print_plate_info(self, plate_contents):
        print("\nPlates on the board:")
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r, c] != " ":
                    plate_number = int(self.grid[r, c])
                    print(f"Plate at ({r + 1}, {c + 1}): Number {plate_number}, Content: {plate_contents[plate_number]}")

def generate_plate():
    total_slices = random.randint(1, 5)
    num_types = random.randint(1, total_slices)
    available_slices = random.sample(CAKE_SLICES, num_types)

    distribution = [total_slices // num_types] * num_types
    remaining_slices = total_slices % num_types

    while remaining_slices > 0:
        index = random.randint(0, num_types - 1)
        distribution[index] += 1
        remaining_slices -= 1

    plate = []
    for i in range(num_types):
        plate.extend([available_slices[i]] * distribution[i])
    
    plate.sort()
    return Plate(plate)

def print_plates(plates):
    print("\nAvailable plates:")
    for i, plate in enumerate(plates, 1):
        print(f"{i} -> {plate}")

def cleanup_empty_plates(board, plate_contents):
    """
    Elimină farfuriile care au devenit goale de pe tablă.
    Acestea sunt setate ca " " în grilă, iar corespondența din plate_contents rămâne pentru rezervă.
    """
    for r in range(ROWS):
        for c in range(COLS):
            if board.get_plate_number(r, c) != " ":
                plate_num = int(board.get_plate_number(r, c))
                # Dacă farfuria este goală, elimina-o de pe tablă
                if len(plate_contents[plate_num].slices) == 0:
                    board.remove_plate(r, c)
                    print(f"Plate at ({r+1}, {c+1}) is empty and removed from board.")

def place_plate_algorithm(board, plate, row, col, score, plate_number, plate_contents):
    if not board.place_plate(row, col, plate_number):
        return score, plate_contents

    plate_contents[plate_number] = plate  # Save the placed plate
    print(f"Plate placed: {plate} (Number: {plate_number})")

    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS and board.get_plate_number(nr, nc) != " ":
            neighbor_plate_number = int(board.get_plate_number(nr, nc))
            neighbors.append((nr, nc, plate_contents[neighbor_plate_number]))

    for slice_type in set(plate.slices):
        plate_count = plate.count_slice(slice_type)
        for nr, nc, neighbor_plate in neighbors:
            neighbor_count = neighbor_plate.count_slice(slice_type)
            transfer = min(MAX_SLICES - plate_count, neighbor_count)
            if transfer > 0:
                neighbor_plate.remove_slices(slice_type, transfer)
                plate.add_slices(slice_type, transfer)

    # If the plate has 6 slices but includes multiple types,
    # evolve it toward the dominant type.
    if len(plate.slices) == MAX_SLICES and len(set(plate.slices)) > 1:
        dominant_slice = max(set(plate.slices), key=plate.count_slice)
        for useless_slice in set(plate.slices):
            if useless_slice != dominant_slice:
                count_to_give = plate.count_slice(useless_slice)
                for nr, nc, neighbor_plate in neighbors:
                    neighbor_capacity = MAX_SLICES - len(neighbor_plate.slices)
                    transfer = min(count_to_give, neighbor_capacity)
                    if transfer > 0:
                        plate.remove_slices(useless_slice, transfer)
                        neighbor_plate.add_slices(useless_slice, transfer)
                        count_to_give -= transfer
                        if count_to_give == 0:
                            break

    # Check if the plate can be cleared.
    if plate.is_clearable():
        board.remove_plate(row, col)
        score += 1
        print("Plate cleared! Score +1")
        return score, plate_contents

    return score, plate_contents

def main():
    board = Board()
    plates = [generate_plate() for _ in range(3)]
    score = 0
    plate_counter = 0
    plate_contents = {}

    while True:
        print(f"\nScore: {score}")
        board.print_board()
        board.print_plate_info(plate_contents)
        print_plates(plates)

        # Curățăm farfuriile goale, dacă există
        cleanup_empty_plates(board, plate_contents)

        if not plates:
            plates = [generate_plate() for _ in range(3)]
            print("\nNew plates have been generated!")
            print_plates(plates)

        try:
            choice = int(input(f"Choose a plate (1-{len(plates)}): ")) - 1
            if choice not in range(len(plates)):
                print("Invalid choice!")
                continue

            row = int(input("Choose row (1-5): ")) - 1
            col = int(input("Choose column (1-4): ")) - 1

            if 0 <= row < ROWS and 0 <= col < COLS:
                if board.get_plate_number(row, col) != " ":
                    print("The spot is already taken!")
                    continue
                plate_counter += 1
                score, plate_contents = place_plate_algorithm(
                    board, plates.pop(choice), row, col, score, plate_counter, plate_contents
                )
            else:
                print("Invalid position!")
        except ValueError:
            print("Invalid input! Please enter valid numbers.")

if __name__ == "__main__":
    main()
