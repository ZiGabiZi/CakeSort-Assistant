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
        self.current_plates = []

        # === Tabla inițială cu farfuriile predefinite ===
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

    def place_plate(self, plate: Plate, row_index: int, column_index: int):
        """
        Plasează o farfurie nouă la (row_index, column_index)
        și aplică transferurile de felii. Returnează (succes, moves).
        """
        if not (0 <= row_index < ROWS and 0 <= column_index < COLS):
            return False, []
        if self.board.get_plate_number(row_index, column_index):
            return False, []

        nr = self.plate_counter
        if not self.board.place_plate(row_index, column_index, nr, plate):
            return False, []

        self.placed_plates[nr] = plate
        moves = self.__process_new_plate(row_index, column_index, nr)
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

            # Vecin cu un singur tip și farfurie nouă cu multiple tipuri: noua dă felii
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
                # În rest, farfuria nouă primește de la vecin
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
        Înainte de fiecare test, instanțiem CakeSortGame,
        care își populează automat tabla cu farfuriile predefinite.
        """
        self.game = CakeSortGame()

    def test_no_common_slices_after_placement(self):
        """
        Plasăm două farfurii într-o zonă liberă, fără felii comune:
        - (2,0): [2,2,2]
        - (2,1): [1,1,0]
        Nu trebuie să apară nicio mutare.
        """
        plate_neighbor = Plate(np.array([2, 2, 2], dtype=int))
        plate_new      = Plate(np.array([1, 1, 0], dtype=int))

        success1, _     = self.game.place_plate(plate_neighbor, 2, 0)
        self.assertTrue(success1, "Nu s-a putut plasa plate_neighbor la (2,0).")
        success2, moves = self.game.place_plate(plate_new, 2, 1)
        self.assertTrue(success2, "Nu s-a putut plasa plate_new la (2,1).")

        self.assertEqual(len(moves), 0, "Expected no moves if no common slices exist.")
        print("test_no_common_slices_after_placement: OK")

    def test_transfer_if_branch_after_placement(self):
        """
        Plasăm două farfurii într-o zonă liberă:
        - (2,0): [1, 1, 1]  (vecin, slices_types == 1)
        - (2,1): [1, 2, 0]  (nou, slices_types != 1)
        În acest caz, noua farfurie dă felii către vecin (ramura 'if').
        Sursa mutării: (2,1) -> Destinație: (2,0).
        """
        plate1 = Plate(np.array([1, 1, 1], dtype=int))
        plate2 = Plate(np.array([1, 2, 0], dtype=int))

        success1, _     = self.game.place_plate(plate1, 2, 0)
        self.assertTrue(success1, "Nu s-a putut plasa plate1 la (2,0).")
        success2, moves = self.game.place_plate(plate2, 2, 1)
        self.assertTrue(success2, "Nu s-a putut plasa plate2 la (2,1).")

        self.assertEqual(len(moves), 1, f"Expected 1 move, got {len(moves)}")
        m = moves[0]
        # Sursa trebuie să fie (2,1), destinația (2,0)
        self.assertEqual((m["source_row"], m["source_column"]), (2, 1),
                         f"Expected source (2, 1), got {(m['source_row'], m['source_column'])}")
        self.assertEqual((m["destination_row"], m["destination_column"]), (2, 0),
                         f"Expected destination (2, 0), got {(m['destination_row'], m['destination_column'])}")
        self.assertEqual(m["slice_type"], 1, f"Expected slice_type 1, got {m['slice_type']}")
        self.assertEqual(m["count"], 1, f"Expected count 1, got {m['count']}")

        # Verificăm starea farfuriilor după mutare:
        # Vecinul (2,0) primește un slice 1 și ajunge la 4 felii de tip 1
        self.assertEqual(plate1.count_slice(1), 4, "Vecinul (2,0) ar trebui să aibă 4 felii de tip 1.")
        # Noua (2,1) a cedat 1 felie de tip 1 și rămâne fără felii de tip 1
        self.assertEqual(plate2.count_slice(1), 0, "Farfuria nouă (2,1) nu mai trebuie să aibă felii de tip 1.")
        print("test_transfer_if_branch_after_placement: OK")

    def test_transfer_else_branch_after_placement(self):
        """
        Plasăm două farfurii într-o zonă liberă:
        - (3,0): [2, 3, 3]  (vecin, slices_types != 1)
        - (3,1): [2, 4, 0]  (nou, slices_types != 1)
        Intersecția = 2 → noua (3,1) primește de la (3,0).
        Sursa mutării: (3,0) -> Destinație: (3,1).
        """
        neighbor   = Plate(np.array([2, 3, 3], dtype=int))
        new_plate  = Plate(np.array([2, 4, 0], dtype=int))

        initial_empty      = new_plate.empty_spaces
        initial_neighbor_2 = neighbor.count_slice(2)
        expected_count     = min(initial_empty, initial_neighbor_2)

        success1, _     = self.game.place_plate(neighbor, 3, 0)
        self.assertTrue(success1, "Nu s-a putut plasa neighbor la (3,0).")
        success2, moves = self.game.place_plate(new_plate, 3, 1)
        self.assertTrue(success2, "Nu s-a putut plasa new_plate la (3,1).")

        self.assertEqual(len(moves), 1, f"Expected 1 move, got {len(moves)}")
        m = moves[0]
        self.assertEqual((m["source_row"], m["source_column"]), (3, 0),
                         f"Expected source (3,0), got {(m['source_row'], m['source_column'])}")
        self.assertEqual((m["destination_row"], m["destination_column"]), (3, 1),
                         f"Expected destination (3,1), got {(m['destination_row'], m['destination_column'])}")
        self.assertEqual(m["slice_type"], 2, f"Expected slice_type 2, got {m['slice_type']}")
        self.assertEqual(m["count"], expected_count,
                         f"Expected count {expected_count}, got {m['count']}")

        # Verificăm starea farfuriilor după mutare:
        self.assertEqual(neighbor.count_slice(2), initial_neighbor_2 - expected_count,
                         "Vecinul ar trebui să fi pierdut slice-urile de tip 2 mutate.")
        self.assertEqual(new_plate.count_slice(2), expected_count + 1,
                         "Noua ar trebui să aibă slice-urile de tip 2 + cel inițial.")
        print("test_transfer_else_branch_after_placement: OK")

    def test_multiple_neighbors_simultaneous_after_placement(self):
        """
        Plasăm mai mulți vecini dinamic în jurul centrului (2,2), apoi plasăm farfurie nouă la (2,2)
        și verificăm mutările multiple simultane.
        """
        # Vecin inițial la (1,2) există, apoi adăugăm încă trei:
        coords_plates = [
            ((2, 1), [4, 4]),
            ((2, 3), [4, 5]),
            ((3, 2), [5, 5])
        ]
        valid_neighbors = [(1, 2)]
        for (r, c), slices in coords_plates:
            plate_obj = Plate(np.array(slices, dtype=int))
            success, _ = self.game.place_plate(plate_obj, r, c)
            self.assertTrue(success, f"Nu s-a putut plasa vecin la ({r},{c}).")
            valid_neighbors.append((r, c))

        # Colectăm toate tipurile de felii comune printre acești vecini:
        slices_neighbors = set()
        for (nr, nc) in valid_neighbors:
            pid = self.game.board.get_plate_number(nr, nc)
            plate_obj = self.game.placed_plates[pid]
            for t in np.unique(plate_obj.slices):
                slices_neighbors.add(int(t))

        self.assertTrue(len(slices_neighbors) > 0,
                        "Trebuie cel puțin un tip de felie comun printre vecini.")

        chosen_slice = slices_neighbors.pop()
        new_slices = [chosen_slice] + [0] * (MAX_SLICES_PER_PLATE - 1)
        farfurie_noua = Plate(np.array(new_slices, dtype=int))

        success_new, moves = self.game.place_plate(farfurie_noua, 2, 2)
        self.assertTrue(success_new, "Nu s-a putut plasa farfurie nouă la (2,2).")

        # Așteptăm un număr de mutări între 1 și len(valid_neighbors)
        self.assertTrue(1 <= len(moves) <= len(valid_neighbors),
                        f"Aștept între 1 și {len(valid_neighbors)} mutări, am primit {len(moves)}.")

        for m in moves:
            src = (m["source_row"], m["source_column"])
            dst = (m["destination_row"], m["destination_column"])
            self.assertIn(src, valid_neighbors + [(2, 2)])
            self.assertIn(dst, valid_neighbors + [(2, 2)])
            self.assertEqual(m["slice_type"], chosen_slice)
        print("test_multiple_neighbors_simultaneous_after_placement: OK")

    def test_no_invalid_states_after_placement(self):
        """
        Verificăm invariants pentru toate farfuriile deja plasate (inclusiv inițiale),
        plus câteva plasări adiționale făcute aici, în poziții fără vecini pentru a nu modifica
        conținutul inițial. Pentru fiecare farfurie:
        - 0 <= len(slices) <= MAX_SLICES_PER_PLATE
        - 0 <= empty_spaces <= MAX_SLICES_PER_PLATE
        - len(slices) + empty_spaces == MAX_SLICES_PER_PLATE
        """
        # Plasăm 3 farfurii noi în poziții fără vecini existenți:
        plate_x = Plate(np.array([6, 6], dtype=int))
        plate_y = Plate(np.array([7, 7], dtype=int))
        plate_z = Plate(np.array([8, 8], dtype=int))

        success_x, _ = self.game.place_plate(plate_x, 3, 0)
        self.assertTrue(success_x, "Nu s-a putut plasa plate_x la (3,0).")
        success_y, _ = self.game.place_plate(plate_y, 3, 3)
        self.assertTrue(success_y, "Nu s-a putut plasa plate_y la (3,3).")
        success_z, _ = self.game.place_plate(plate_z, 4, 2)
        self.assertTrue(success_z, "Nu s-a putut plasa plate_z la (4,2).")

        for plate_id, plate_obj in self.game.placed_plates.items():
            length = len(plate_obj.slices)
            empty = plate_obj.empty_spaces
            self.assertTrue(0 <= length <= MAX_SLICES_PER_PLATE)
            self.assertTrue(0 <= empty <= MAX_SLICES_PER_PLATE)
            self.assertEqual(length + empty, MAX_SLICES_PER_PLATE)
        print("test_no_invalid_states_after_placement: OK")


if __name__ == '__main__':
    unittest.main()
