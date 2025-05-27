import unittest
from itertools import product
import numpy as np

from utils import *
from constants import ROWS, COLS, MAX_SLICES_PER_PLATE
from plate import Plate
from board import Board

class CakeSortGame:
    def __init__(self):
        self.board = Board()
        self.score = 0
        self.plate_counter = 1
        self.placed_plates = {}

        plates_data = [
            ((0, 0), [1, 1, 3, 5]),
            ((0, 1), [3, 3]),
            ((0, 2), [5]),
            ((1, 0), [2, 2]),
            ((1, 1), [3, 5]),
            ((1, 2), [1, 1, 1])
        ]

        for (r, c), slices in plates_data:
            plate = Plate(np.array(slices, dtype=int))
            nr = self.plate_counter
            assert self.board.place_plate(r, c, nr, plate), f"Nu s-a putut plasa farfuria la ({r},{c})"
            self.placed_plates[nr] = plate
            self.__process_new_plate(r, c, nr)
            self.plate_counter += 1

        self.current_plates = []

    def reset_plates(self):
        self.current_plates = []

    def cleanup_empty_plates(self):
        cleared_positions = []
        for row, column in product(range(ROWS), range(COLS)):
            plate_number = self.board.get_plate_number(row, column)
            if plate_number != 0:
                plate = self.placed_plates[plate_number]
                if plate.is_empty:
                    self.board.remove_plate(row, column)
                    del self.placed_plates[plate_number]
                    cleared_positions.append((row, column))
                    print(f"Plate la ({row + 1}, {column + 1}) a fost ștearsă deoarece e goală.")
                elif plate.is_clearable:
                    plate.slices = np.array([], dtype=int)
                    self.board.remove_plate(row, column)
                    del self.placed_plates[plate_number]
                    self.score += 1
        return cleared_positions

    def place_plate(self, plate_index, row_index, column_index):
        if plate_index < 0 or plate_index >= len(self.current_plates):
            return False, []
        if self.board.get_plate_number(row_index, column_index):
            return False, []

        selected_plate = self.current_plates.pop(plate_index)
        if not self.board.place_plate(row_index, column_index, self.plate_counter, selected_plate):
            self.current_plates.insert(plate_index, selected_plate)
            return False, []

        self.placed_plates[self.plate_counter] = selected_plate
        moves = self.__process_new_plate(row_index, column_index, self.plate_counter)
        self.plate_counter += 1
        return True, moves

    def __process_new_plate(self, row, column, plate_number):
        plate = self.board.get_plate(row, column)
        moves = []
        for neighbor_row, neighbor_column in self.board.get_neighbors_indexes(row, column):
            neighbor = self.board.get_plate(neighbor_row, neighbor_column)
            slice_type = neighbor & plate
            if not slice_type:
                continue

            if neighbor.slices_types == 1 and plate.slices_types != 1:
                count = min(neighbor.empty_spaces, plate.count_slice(slice_type))
                neighbor.add_slices(slice_type, count)
                plate.remove_slices(slice_type, count)
                moves.append(create_move(
                    row, column,
                    neighbor_row, neighbor_column,
                    slice_type, count
                ))
            else:
                count = min(plate.empty_spaces, neighbor.count_slice(slice_type))
                neighbor.remove_slices(slice_type, count)
                plate.add_slices(slice_type, count)
                moves.append(create_move(
                    neighbor_row, neighbor_column,
                    row, column,
                    slice_type, count
                ))
        return moves


class TestProcessNewPlate(unittest.TestCase):

    def setUp(self):
        """
        Vom folosi CakeSortGame așa cum e definit mai sus. Constructorul plasează cele șase farfurii
        și aplică deja __process_new_plate pentru fiecare plasare succesiv, deci pornim de la starea
        finală a tablei inițiale.
        """
        self.game = CakeSortGame()

    def test_initial_board_state(self):
        """
        Verificăm că cele șase farfurii au fost plasate și contorizate corect.
        """
        # Au fost plasate 6 farfurii în constructor
        self.assertEqual(len(self.game.placed_plates), 6)
        # După 6 plasări, plate_counter trebuie să fie 7
        self.assertEqual(self.game.plate_counter, 7)
        # Exact 6 poziții sunt ocupate pe tablă
        occupied = sum(
            1
            for r in range(ROWS) for c in range(COLS)
            if self.game.board.get_plate_number(r, c) != 0
        )
        self.assertEqual(occupied, 6)

    def test_no_common_slices_on_initial_neighbors(self):
        """
        Verificăm că doi vecini din configurația inițială fără felii comune nu au generat mutări
        adiționale dacă reapelăm __process_new_plate. De exemplu (0,0) și (1,0) n-au feliile comune.
        """
        # Identificăm id-ul la (1,0)
        plate_id = self.game.board.get_plate_number(1, 0)
        moves = self.game._CakeSortGame__process_new_plate(1, 0, plate_id)
        self.assertEqual(len(moves), 0, "Nu așteptăm mutări între (0,0) și (1,0)")

    def test_transfer_between_specific_plates(self):
        """
        Alegem două poziții din configurația inițială care știm că au cel puțin un slice comun
        după plasările inițiale. Reapelăm __process_new_plate și verificăm o mutare validă.
        """
        # De exemplu: pozițiile (0,1) și (1,1)
        id_01 = self.game.board.get_plate_number(0, 1)
        id_11 = self.game.board.get_plate_number(1, 1)
        plate_01 = self.game.placed_plates[id_01]
        plate_11 = self.game.placed_plates[id_11]

        # Verificăm că există slice comun
        common = np.intersect1d(plate_01.slices, plate_11.slices)
        self.assertTrue(common.size > 0, "Trebuie slice comun între (0,1) și (1,1).")

        # Re-apelăm procesarea farfuriei de la (1,1)
        moves = self.game._CakeSortGame__process_new_plate(1, 1, id_11)
        self.assertTrue(len(moves) >= 1, "Trebuie cel puțin o mutare între (0,1) și (1,1).")
        m = moves[0]
        src = (m["source_row"], m["source_column"])
        dst = (m["destination_row"], m["destination_column"])
        self.assertIn(src, [(0, 1), (1, 1)])
        self.assertIn(dst, [(0, 1), (1, 1)])
        self.assertIn(m["slice_type"], common.tolist())

    def test_multiple_neighbors_simultaneous(self):
        """
        Plasăm o farfurie nouă la o poziție cu patru vecini (de ex. (1,1)), care există deja.
        Verificăm că apar între 1 și 4 mutări, câte una per vecin cu slice comun.
        """
        # Coordonatele (1,1) deja conțin un plate inițial; mutăm temporar pentru test
        # Extragem vecinii din configurația inițială (după constructor)
        neighbors = self.game.board.get_neighbors_indexes(1, 1)
        slices_neighbors = set()
        for (nr, nc) in neighbors:
            plate_id = self.game.board.get_plate_number(nr, nc)
            plate_obj = self.game.placed_plates[plate_id]
            for t in np.unique(plate_obj.slices):
                slices_neighbors.add(int(t))

        self.assertTrue(len(slices_neighbors) > 0, "Vecinii lui (1,1) trebuie să aibă felii.")

        chosen_slice = slices_neighbors.pop()

        # Creăm farfuria nouă cu acel slice și rest '0' pentru spații libere
        new_slices = [chosen_slice] + [0] * (MAX_SLICES_PER_PLATE - 1)
        farfurie_noua = Plate(np.array(new_slices, dtype=int))

        # Plasăm temporar farfuria la (1,1) cu id 99
        self.game.board.place_plate(1, 1, 99, farfurie_noua)
        self.game.placed_plates[99] = farfurie_noua

        moves = self.game._CakeSortGame__process_new_plate(1, 1, 99)
        self.assertTrue(1 <= len(moves) <= 4, f"Aștept între 1 și 4 mutări, am primit {len(moves)}.")

        for m in moves:
            src = (m["source_row"], m["source_column"])
            dst = (m["destination_row"], m["destination_column"])
            self.assertIn(src, neighbors + [(1, 1)])
            self.assertIn(dst, neighbors + [(1, 1)])
            self.assertEqual(m["slice_type"], chosen_slice)

    def test_no_invalid_states_after_processing(self):
        """
        După ce constructorul a rulat, ne asigurăm că nicio farfurie nu are empty_spaces negativ
        și că len(slices) + empty_spaces == MAX_SLICES_PER_PLATE.
        """
        for plate_id, plate_obj in self.game.placed_plates.items():
            length = len(plate_obj.slices)
            empty = plate_obj.empty_spaces
            self.assertTrue(0 <= length <= MAX_SLICES_PER_PLATE)
            self.assertTrue(0 <= empty <= MAX_SLICES_PER_PLATE)
            self.assertEqual(length + empty, MAX_SLICES_PER_PLATE)

if __name__ == '__main__':
    unittest.main()
