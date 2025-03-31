import numpy as np
import random

ROWS, COLS = 5, 4

CAKE_SLICES = ["1", "2", "3", "4", "5", "6"]

def create_board():
    return np.full((ROWS, COLS), " ", dtype=str)

def generate_plate():
    total_slices = random.randint(1, 7)  # Total felii pe farfurie
    num_types = random.randint(1, min(6, total_slices))  # Tipuri de felii
    available_slices = random.sample(CAKE_SLICES, num_types)  # Se aleg tipurile
    
    # Distribui felii pt ca fiecare tip sa aiba cel putin o felie
    distribution = [1] * num_types  
    remaining_slices = total_slices - num_types  # Rest felii de distribuit
    
    while remaining_slices > 0:
        index = random.randint(0, num_types - 1)
        distribution[index] += 1
        remaining_slices -= 1
    
    plate = []
    for i in range(num_types):
        plate.extend([available_slices[i]] * distribution[i])
    
    plate.sort()
    return plate




def Alg_Plasare_Felii():
    return






def create_plates():
    return [generate_plate() for _ in range(3)]

def print_board(board):
    print("\n    1   2   3   4")
    print("  +---+---+---+---+")
    for row in board:
        print("  | " + " | ".join(row) + " |")
        print("  +---+---+---+---+")


def print_plates(plates):
    print("\nFarfurii inițiale:")
    for i, plate in enumerate(plates, 1):
        print(f"Farfuria {i}: {''.join(plate)}")

def main():
    board = create_board()
    plates = create_plates()
    print_board(board)
    print_plates(plates)

if __name__ == "__main__":
    main()
