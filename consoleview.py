from constants import ROWS, COLS
from game import CakeSortGame

class ConsoleView:
    def __init__(self, game_instance):
        self.game = game_instance

    def display_board(self):
        print(f"\nScore: {self.game.score}")
        self._print_board()
        self._print_plate_info()
        self._print_available_plates()

    def _print_board(self):
        print("\n    1   2   3   4")
        print("  +-----+-----+-----+-----+")
        for row_index in range(ROWS):
            row_display = []
            for column_index in range(COLS):
                plate_number = self.game.board.get_plate_number(row_index, column_index)
                if plate_number != 0:
                    plate = self.game.plate_contents_by_number[plate_number]
                    cell = str(plate)[:5].ljust(5)
                else:
                    cell = "     "
                row_display.append(cell)
            print(f"{row_index + 1} |" + "|".join(row_display) + "|")
            print("  +-----+-----+-----+-----+")

    def _print_plate_info(self):
        print("\nPlates on the board:")
        for row_index in range(ROWS):
            for column_index in range(COLS):
                plate_number = self.game.board.get_plate_number(row_index, column_index)
                if plate_number != 0:
                    plate = self.game.plate_contents_by_number[plate_number]
                    print(f"Plate at ({row_index + 1}, {column_index + 1}): Number {plate_number}, Content: {plate}")

    def _print_available_plates(self):
        print("\nAvailable plates:")
        for index, plate in enumerate(self.game.plates, 1):
            print(f"{index} -> {plate}")

    def prompt_move(self):
        try:
            selected_plate_index = int(input(f"Choose a plate (1-{len(self.game.plates)}): ")) - 1
            target_row_index = int(input("Choose row (1-5): ")) - 1
            target_column_index = int(input("Choose column (1-4): ")) - 1
            return selected_plate_index, target_row_index, target_column_index
        except ValueError:
            print("Invalid input! Please enter valid numbers.")
            return None

    def show_invalid_placement(self):
        print("Invalid placement. Try again.")

    def show_new_plates_generated(self):
        print("\nNew plates have been generated!")

    def run(self):
        while True:
            self.game.cleanup_empty_plates()

            if not self.game.plates:
                self.game.refresh_plates()
                self.show_new_plates_generated()

            self.display_board()

            move = self.prompt_move()
            if move is None:
                continue

            selected_plate_index, target_row_index, target_column_index = move

            if self.game.board.get_plate_number(target_row_index, target_column_index) != 0:
                print("The spot is already taken!")
                continue

            if selected_plate_index < 0 or selected_plate_index >= len(self.game.plates):
                print("Invalid choice!")
                continue

            placement_success = self.game.place_plate(
                selected_plate_index,
                target_row_index,
                target_column_index
            )
            if not placement_success:
                self.show_invalid_placement()