import numpy as np
import random

ROWS, COLS = 5, 4
CAKE_SLICES = ["1", "2", "3", "4", "5", "6"]

def create_board():
    return np.full((ROWS, COLS), " ", dtype=str)

def generate_plate():
    total_slices = random.randint(1, 7)
    num_types = random.randint(1, min(6, total_slices))
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
    return plate

def Alg_plasare_farfurii(board, plate, row, col, score, plate_number, plate_contents):
    if board[row, col] != " ":
        print("Locul este deja ocupat!")
        return score, plate_contents

    # Plasăm numărul farfuriei în matrice
    board[row, col] = str(plate_number)
    plate_contents[plate_number] = "".join(plate)  # Salvăm conținutul farfuriei
    print(f"Farfurie plasată: {''.join(plate)} (Numărul: {plate_number})")  # Confirmare plasare farfurie

    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS and board[nr, nc] != " ":
            neighbors.append((nr, nc, list(board[nr, nc])))

    for slice_type in set(plate):
        plate_count = plate.count(slice_type)

        sorted_neighbors = sorted(neighbors, key=lambda x: x[2].count(slice_type))
        for nr, nc, neighbor_plate in sorted_neighbors:
            neighbor_count = neighbor_plate.count(slice_type)

            if plate_count > neighbor_count:
                transfer = min(7 - plate_count, neighbor_count)
                if transfer > 0:
                    new_neighbor_plate = [s for s in neighbor_plate if s != slice_type][:len(neighbor_plate) - transfer]
                    board[nr, nc] = "".join(new_neighbor_plate)
                    plate.extend([slice_type] * transfer)
                    plate_count += transfer

                    if plate_count == 8 and len(set(plate)) == 1:
                        board[row, col] = " "
                        score += 1
                        print("Farfurie eliminată! Scor +1")
                        return score, plate_contents

    return score, plate_contents

def create_plates():
    return [generate_plate() for _ in range(3)]

def print_board(board):
    print("\n    1   2   3   4")
    print("  +---+---+---+---+")
    for row in board:
        print("  | " + " | ".join(row) + " |")
        print("  +---+---+---+---+")

def print_table_plates(board, plate_contents):
    print("\nFarfuriile de pe tablă:")
    for r in range(ROWS):
        for c in range(COLS):
            if board[r, c] != " ":
                plate_number = int(board[r, c])
                print(f"Farfuria la ({r + 1}, {c + 1}): Numărul {plate_number}, Conținut: {plate_contents[plate_number]}")

def print_plates(plates):
    print("\nFarfurii disponibile:")
    for i, plate in enumerate(plates, 1):
        print(f"{i} -> {''.join(plate)}")

def print_round_info(score, board, plate_contents):
    print(f"\nScor: {score}")
    print_table_plates(board, plate_contents)

def main():
    board = create_board()
    plates = create_plates()
    score = 0
    plate_counter = 0  # Contor pentru numărul farfuriilor plasate
    plate_contents = {}  # Dicționar pentru conținutul farfuriilor plasate

    while True:
        # Afișăm informațiile rundei la începutul unei noi runde
        print_round_info(score, board, plate_contents)
        print_board(board)
        print_plates(plates)

        if not plates:
            plates = create_plates()
            print("\nNoi farfurii au fost generate!")
            print_plates(plates)

        try:
            print(f"(Alege o farfurie 1 - {len(plates)})")  # Mesaj actualizat
            choice = int(input("Alege o farfurie: ")) - 1
            if choice not in range(len(plates)):
                print("Alegere invalidă!")
                continue

            row = int(input("Alege rândul (1-5): ")) - 1
            col = int(input("Alege coloana (1-4): ")) - 1

            if 0 <= row < ROWS and 0 <= col < COLS:
                plate_counter += 1  # Incrementăm contorul
                score, plate_contents = Alg_plasare_farfurii(board, plates.pop(choice), row, col, score, plate_counter, plate_contents)
            else:
                print("Poziție invalidă!")
        except ValueError:
            print("Intrare invalidă! Te rog introdu numere valide.")



if __name__ == "__main__":
    main()
