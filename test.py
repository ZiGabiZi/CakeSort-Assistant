import numpy as np
from game import CakeSortGame
from plate import Plate
from consoleview import ConsoleView



def test_caz_specific():
    print("=== TEST: Caz 112222 + plasare 2223 ===")
    game = CakeSortGame()
    # Pune farfuria cu 112222 pe (2,2)
    plate1 = Plate(np.array([1,1,2,2,2,2]))
    game.board.place_plate(2, 2, 1, plate1)
    game.placed_plates[1] = plate1

    view = ConsoleView(game)
    print("Tabla inițială (doar 112222):")
    view.display_board()

    # Acum plasezi farfuria cu 2223 pe (2,3)
    plate2 = Plate(np.array([2,2,2,3]))
    game.board.place_plate(2, 3, 2, plate2)
    game.placed_plates[2] = plate2

    print("Tabla după plasarea farfuriei 2223:")
    view.display_board()

    # Rulează algoritmul ca și cum ai pus farfuria cu 2223 pe (2,3)
    moves = game._process_plate_after_placement(2, 3, 2)
    print("Mutări efectuate:", moves)

    print("Tabla după mutare:")
    view.display_board()

    print("Score:", game.score)

if __name__ == "__main__":
    test_caz_specific()