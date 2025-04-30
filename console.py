import numpy as np
import random

# Constante
ROWS, COLS = 5, 4
CAKE_SLICES = ["1", "2", "3", "4", "5", "6"]
MAX_SLICES = 6

# --- Clase de bază (folosite de logica jocului) ---

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
        self.grid = np.full((ROWS, COLS), 0, dtype=int)

    def place_plate(self, row, col, plate_number):
        if self.grid[row, col] != 0:
            return False
        self.grid[row, col] = plate_number
        return True

    def get_plate_number(self, row, col):
        return self.grid[row, col]

    def remove_plate(self, row, col):
        self.grid[row, col] = 0



# --- Clasa ce conține logica jocului ---

class CakeSortGame:
    def __init__(self):
        self.board = Board()
        self.plates = [self.generate_plate() for _ in range(3)]
        self.score = 0
        self.plate_counter = 0
        self.plate_contents = {}  # Mapează numărul farfuriei la obiectul Plate

    @staticmethod
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

    def refresh_plates(self):
        if not self.plates:
            self.plates = [self.generate_plate() for _ in range(3)]
    
    def cleanup_empty_plates(self):
        to_remove = []
        for r in range(ROWS):
            for c in range(COLS):
                plate_num = self.board.get_plate_number(r, c)
                if plate_num != 0:
                    plate = self.plate_contents.get(plate_num)
                    if plate and len(plate.slices) == 0:
                        self.board.remove_plate(r, c)
                        to_remove.append(plate_num)
                        print(f"Plate at ({r+1}, {c+1}) is empty and removed from board.")
        for plate_num in to_remove:
            del self.plate_contents[plate_num]


        

    def place_plate(self, plate_index, row, col):
        """
        Încearcă să plaseze farfuria selectată de utilizator pe poziția dată.
        Returnează True dacă plasarea este validă și actualizează starea jocului.
        """
        if plate_index < 0 or plate_index >= len(self.plates):
            return False

        if not (0 <= row < ROWS and 0 <= col < COLS):
            return False

        if self.board.get_plate_number(row, col) != 0:
            return False

        # Actualizează contorul pentru farfurii și folosește-l ca identificator unic.
        self.plate_counter += 1
        plate = self.plates.pop(plate_index)
        # Plasează farfuria pe tablă
        if not self.board.place_plate(row, col, self.plate_counter):
            # Dacă plasarea e invalidă, returnează farfuria în listă
            self.plates.insert(plate_index, plate)
            return False

        self.plate_contents[self.plate_counter] = plate
        # Aplică algoritmul de transfer între farfurii
        self._process_plate(row, col, self.plate_counter)
        return True

    def _process_plate(self, row, col, plate_number):
        plate = self.plate_contents[plate_number]
        # Mesaj de debug (acest print poate fi mutat în view dacă se dorește)
        print(f"Plate placed: {plate} (Number: {plate_number})")

        # Determină vecinii (plăcile adiacente pe tablă)
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if self.board.get_plate_number(nr, nc) != 0:
                    neighbor_num = int(self.board.get_plate_number(nr, nc))
                    neighbors.append((nr, nc, self.plate_contents[neighbor_num]))

        # Transferă felii între farfurii
        for slice_type in set(plate.slices):
            plate_count = plate.count_slice(slice_type)
            for nr, nc, neighbor_plate in neighbors:
                neighbor_count = neighbor_plate.count_slice(slice_type)
                transfer = min(MAX_SLICES - plate_count, neighbor_count)
                if transfer > 0:
                    neighbor_plate.remove_slices(slice_type, transfer)
                    plate.add_slices(slice_type, transfer)

        # Dacă farfuria are MAX_SLICES cu tipuri diferite, se face procesul de ajustare
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

        # Dacă farfuria poate fi "curățată" (toate feliile identice și numărul este MAX_SLICES),
        # se elimină de pe tablă și se acordă scor.
        if plate.is_clearable():
            self.board.remove_plate(row, col)
            self.score += 1
            print("Plate cleared! Score +1")


# --- Clasa de interfață (ConsoleView) ---

class ConsoleView:
    def __init__(self, game: CakeSortGame):
        self.game = game

    def display_board(self):
        # Afișează scorul și tabla de joc
        print(f"\nScore: {self.game.score}")
        self._print_board()
        self._print_plate_info()
        self._print_available_plates()

    def _print_board(self):
        # Metoda de afișare a tablei (se folosește metoda din clasa Board)
        print("\n    1   2   3   4")
        print("  +---+---+---+---+")
        for row in self.game.board.grid:
            print("  | " + " | ".join(str(cell) if cell != 0 else " " for cell in row) + " |")
            print("  +---+---+---+---+")

    def _print_plate_info(self):
        print("\nPlates on the board:")
        for r in range(ROWS):
            for c in range(COLS):
                if self.game.board.get_plate_number(r, c) != 0:
                    plate_number = int(self.game.board.get_plate_number(r, c))
                    plate = self.game.plate_contents[plate_number]
                    print(f"Plate at ({r + 1}, {c + 1}): Number {plate_number}, Content: {plate}")

    def _print_available_plates(self):
        print("\nAvailable plates:")
        for i, plate in enumerate(self.game.plates, 1):
            print(f"{i} -> {plate}")

    def prompt_move(self):
        try:
            choice = int(input(f"Choose a plate (1-{len(self.game.plates)}): ")) - 1
            row = int(input("Choose row (1-5): ")) - 1
            col = int(input("Choose column (1-4): ")) - 1
            return choice, row, col
        except ValueError:
            print("Invalid input! Please enter valid numbers.")
            return None

    def show_invalid_placement(self):
        print("Invalid placement. Try again.")

    def show_new_plates_generated(self):
        print("\nNew plates have been generated!")

    def run(self):
        # Bucla principală a jocului
        while True:
            self.game.cleanup_empty_plates()

            if not self.game.plates:
                self.game.refresh_plates()
                self.show_new_plates_generated()

            self.display_board()


            move = self.prompt_move()
            if move is None:
                continue

            choice, row, col = move

            if self.game.board.get_plate_number(row, col) != 0:
                print("The spot is already taken!")
                continue

            if choice < 0 or choice >= len(self.game.plates):
                print("Invalid choice!")
                continue

            success = self.game.place_plate(choice, row, col)
            if not success:
                self.show_invalid_placement()


# --- Execuția jocului ---

def main():
    game = CakeSortGame()
    view = ConsoleView(game)
    view.run()

if __name__ == "__main__":
    main()
