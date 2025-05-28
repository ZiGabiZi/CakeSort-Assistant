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
        for neighbor_row, neighbor_column in self.board.get_neighbors_indexes(row,column):
            neighbor = self.board.get_plate(neighbor_row,neighbor_column)
            slice_type = neighbor & plate
            if not slice_type:
                continue
            else:
                print(slice_type)
            if neighbor.slices_types == 1 and plate.slices_types != 1:
                count = min(neighbor.empty_spaces,plate.count_slice(slice_type))
                neighbor.add_slices(slice_type,count)
                plate.remove_slices(slice_type,count)
                moves.append(create_move(
                    row,column,neighbor_row,neighbor_column,slice_type,count
                ))
                
            else:
                count = min(plate.empty_spaces,neighbor.count_slice(slice_type))
                neighbor.remove_slices(slice_type,count)
                plate.add_slices(slice_type,count)
                moves.append(create_move(
                    neighbor_row,neighbor_column,row,column,slice_type,count
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
        - (2,1): [1,1]
        Nu trebuie să apară nicio mutare.
        """
        plate_neighbor = Plate(np.array([2, 2, 2], dtype=int))
        plate_new      = Plate(np.array([1, 1], dtype=int))

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
        - (2,1): [1, 2]     (nou, slices_types != 1)
        În acest caz, noua farfurie dă felii către vecin (ramura 'if').
        Sursa mutării: (2,1) -> Destinație: (2,0).
        """
        plate1 = Plate(np.array([1, 1, 1], dtype=int))
        plate2 = Plate(np.array([1, 2], dtype=int))

        success1, _     = self.game.place_plate(plate1, 2, 0)
        self.assertTrue(success1, "Nu s-a putut plasa plate1 la (2,0).")
        success2, moves = self.game.place_plate(plate2, 2, 1)
        self.assertTrue(success2, "Nu s-a putut plasa plate2 la (2,1).")

        self.assertEqual(len(moves), 1, f"Expected 1 move, got {len(moves)}")
        m = moves[0]
        self.assertEqual((m["source_row"], m["source_column"]), (2, 1),
                         f"Expected source (2,1), got {(m['source_row'], m['source_column'])}")
        self.assertEqual((m["destination_row"], m["destination_column"]), (2, 0),
                         f"Expected destination (2,0), got {(m['destination_row'], m['destination_column'])}")
        self.assertEqual(m["slice_type"], 1, f"Expected slice_type 1, got {m['slice_type']}")
        self.assertEqual(m["count"], 1, f"Expected count 1, got {m['count']}")

        self.assertEqual(plate1.count_slice(1), 4, "Vecinul (2,0) ar trebui să aibă 4 felii de tip 1.")
        self.assertEqual(plate2.count_slice(1), 0, "Farfuria nouă (2,1) nu mai trebuie să aibă felii de tip 1.")
        print("test_transfer_if_branch_after_placement: OK")

    def test_transfer_else_branch_after_placement(self):
        """
        Plasăm două farfurii într-o zonă liberă:
        - (3,0): [2, 3, 3]  (vecin, slices_types != 1)
        - (3,1): [2, 4]     (nou, slices_types != 1)
        Intersecția = 2 → noua (3,1) primește de la vecin (ramura 'else').
        Sursa mutării: (3,0) -> Destinație: (3,1).
        """
        neighbor   = Plate(np.array([2, 3, 3], dtype=int))
        new_plate  = Plate(np.array([2, 4], dtype=int))

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

        self.assertEqual(neighbor.count_slice(2), initial_neighbor_2 - expected_count,
                         "Vecinul ar trebui să fi pierdut slice-urile de tip 2 mutate.")
        self.assertEqual(new_plate.count_slice(2), expected_count + 1,
                         "Noua ar trebui să aibă slice-urile de tip 2 + cel inițial.")
        print("test_transfer_else_branch_after_placement: OK")

    def test_both_one_type(self):
        """
        Plasăm două farfurii cu EXACT un singur tip de felie:
        - (2,0): [4,4,4,4]
        - (2,1): [4,4,4,4]
        Ambele au același tip unic. Ramura 'else': noua primește de la vecin.
        """
        plate1 = Plate(np.array([4, 4, 4, 4], dtype=int))
        plate2 = Plate(np.array([4, 4, 4, 4], dtype=int))

        empty_space = MAX_SLICES_PER_PLATE - len(plate2.slices)
        count2_available = plate1.count_slice(4)
        expected_count = min(empty_space, count2_available)

        success1, _     = self.game.place_plate(plate1, 2, 0)
        self.assertTrue(success1)
        success2, moves = self.game.place_plate(plate2, 2, 1)
        self.assertTrue(success2)

        self.assertEqual(len(moves), 1)
        m = moves[0]
        self.assertEqual(m["slice_type"], 4)
        self.assertEqual(m["count"], expected_count)

        self.assertEqual(plate1.count_slice(4), count2_available - expected_count)
        self.assertEqual(plate2.count_slice(4), len([4, 4, 4, 4]) + expected_count)
        print("test_both_one_type: OK")

    def test_plate_new_no_space(self):
        """
        Plasăm farfuria nouă complet "plină" (fără spațiu liber):
        - (3,0): [5,5,5,5]  (NUMĂRUL egal cu MAX_SLICES_PER_PLATE)
        - (3,1): [5,3,3]
        Count = 0, deoarece empty_spaces(noua) == 0.
        """
        new_plate  = Plate(np.array([5] * MAX_SLICES_PER_PLATE, dtype=int))
        neighbor   = Plate(np.array([5, 3, 3], dtype=int))

        success1, _     = self.game.place_plate(new_plate, 3, 0)
        self.assertTrue(success1)
        success2, moves = self.game.place_plate(neighbor, 3, 1)
        self.assertTrue(success2)

        self.assertEqual(len(moves), 1)
        m = moves[0]
        self.assertEqual(m["slice_type"], 5)
        self.assertEqual(m["count"], 0)
        print("test_plate_new_no_space: OK")

    def test_neighbor_no_space(self):
        """
        Plasăm două farfurii astfel încât vecinul are empty_spaces == 0:
        - (3,2): [6,6,6,6] (vecin plin)
        - (3,3): [6,2]
        Ramura 'if', dar vecin empty_spaces == 0 → count = 0.
        """
        neighbor = Plate(np.array([6] * MAX_SLICES_PER_PLATE, dtype=int))
        new_plate = Plate(np.array([6, 2], dtype=int))

        success1, _     = self.game.place_plate(neighbor, 3, 2)
        self.assertTrue(success1)
        success2, moves = self.game.place_plate(new_plate, 3, 3)
        self.assertTrue(success2)

        self.assertEqual(len(moves), 1)
        m = moves[0]
        self.assertEqual(m["slice_type"], 6)
        self.assertEqual(m["count"], 0)
        print("test_neighbor_no_space: OK")

    def test_common_zero_ignored(self):
        """
        Plasăm două farfurii care folosesc '0' în slices:
        - (3,0): [0,2,2]
        - (3,1): [0,3,3]
        Intersecția produce slice_type = 0, dar e ignorat → nicio mutare.
        """
        plate1 = Plate(np.array([0, 2, 2], dtype=int))
        plate2 = Plate(np.array([0, 3, 3], dtype=int))

        success1, _     = self.game.place_plate(plate1, 3, 0)
        self.assertTrue(success1)
        success2, moves = self.game.place_plate(plate2, 3, 1)
        self.assertTrue(success2)

        self.assertEqual(len(moves), 0)
        print("test_common_zero_ignored: OK")

    def test_multiple_neighbors_same_type_limited_space(self):
        """
        Trei vecini în jurul (2,2):
        - (2,1): [7,7]
        - (2,3): [7,7]
        - (3,2): [7,7]
        Plasăm (2,2): [7]
        """
        coords = [(2, 1), (2, 3), (3, 2)]
        for r, c in coords:
            plate = Plate(np.array([7, 7], dtype=int))
            success, _ = self.game.place_plate(plate, r, c)
            self.assertTrue(success)

        empty_space = MAX_SLICES_PER_PLATE - 1
        new_plate = Plate(np.array([7], dtype=int))
        success_new, moves = self.game.place_plate(new_plate, 2, 2)
        self.assertTrue(success_new)

        # Ar trebui exact 3 mutări (în ordinea get_neighbors_indexes)
        self.assertEqual(len(moves), 3)
        first = min(empty_space, 2)
        second = min(empty_space - first, 2)
        third = min(empty_space - first - second, 2)
        counts = [m["count"] for m in moves]
        self.assertEqual(counts, [first, second, third])
        print("test_multiple_neighbors_same_type_limited_space: OK")

    def test_diagonal_ignored(self):
        """
        Plasăm o farfurie diagonală, fără vecini ortogonali:
        - (2,2): [8,8]
        - (3,3): [8,2]
        Diagonala (2,2) nu e considerată vecin, deci nicio mutare.
        """
        neighbor  = Plate(np.array([8, 8], dtype=int))
        new_plate = Plate(np.array([8, 2], dtype=int))

        success1, _     = self.game.place_plate(neighbor, 2, 2)
        self.assertTrue(success1)
        success2, moves = self.game.place_plate(new_plate, 3, 3)
        self.assertTrue(success2)

        self.assertEqual(len(moves), 0)
        print("test_diagonal_ignored: OK")

    def test_out_of_bounds_or_overlap(self):
        """
        Încercăm plasări invalide:
        - În afara limitelor: (-1,0), (0,-1), (ROWS,0), (0,COLS)
        - În poziție deja ocupată (0,0).
        Toate trebuie să returneze False.
        """
        invalid_positions = [(-1, 0), (0, -1), (ROWS, 0), (0, COLS)]
        plate = Plate(np.array([9, 9], dtype=int))
        for (r, c) in invalid_positions:
            success, _ = self.game.place_plate(plate, r, c)
            self.assertFalse(success, f"Should fail for out-of-bounds ({r},{c})")

        success_overlap, _ = self.game.place_plate(plate, 0, 0)
        self.assertFalse(success_overlap, "Should fail for overlap at (0,0)")
        print("test_out_of_bounds_or_overlap: OK")

    def test_chain_of_placements(self):
        """
        Plasăm 3 farfurii într-un șir orizontal în rândul 3:
        - A la (3,1): [3,3]
        - B la (3,2): [3,2]
        - C la (3,3): [3,4]
        B cedează un '3' lui A, apoi C cedează un '3' lui B.
        """
        plate_a = Plate(np.array([3, 3], dtype=int))
        plate_b = Plate(np.array([3, 2], dtype=int))
        plate_c = Plate(np.array([3, 4], dtype=int))

        success_a, _ = self.game.place_plate(plate_a, 3, 1)
        self.assertTrue(success_a)

        initial_a_3 = plate_a.count_slice(3)
        initial_b_3 = plate_b.count_slice(3)
        success_b, moves_b = self.game.place_plate(plate_b, 3, 2)
        self.assertTrue(success_b)
        self.assertEqual(len(moves_b), 1)
        m = moves_b[0]
        # B (3,2) cedează la A (3,1)
        self.assertEqual((m["source_row"], m["source_column"]), (3, 2))
        self.assertEqual((m["destination_row"], m["destination_column"]), (3, 1))
        self.assertEqual(m["slice_type"], 3)
        self.assertEqual(plate_b.count_slice(3), initial_b_3 - 1)
        self.assertEqual(plate_a.count_slice(3), initial_a_3 + 1)

        initial_b_3_after = plate_b.count_slice(3)
        initial_c_3       = plate_c.count_slice(3)
        success_c, moves_c = self.game.place_plate(plate_c, 3, 3)
        self.assertTrue(success_c)
        self.assertEqual(len(moves_c), 1)
        m2 = moves_c[0]
        # C (3,3) cedează la B (3,2)
        self.assertEqual((m2["source_row"], m2["source_column"]), (3, 3))
        self.assertEqual((m2["destination_row"], m2["destination_column"]), (3, 2))
        self.assertEqual(m2["slice_type"], 3)
        self.assertEqual(plate_c.count_slice(3), initial_c_3 - 1)
        self.assertEqual(plate_b.count_slice(3), initial_b_3_after + 1)
        print("test_chain_of_placements: OK")

    def test_cleanup_empty_and_clearable(self):
        """
        Plasăm o farfurie "clearable" la (3,0) și o farfurie goală la (3,1).
        După cleanup_empty_plates():
        - cea goală e ștearsă (is_empty).
        - cea clearable e ștearsă și score++.
        """
        plate_clearable = Plate(np.array([2] * MAX_SLICES_PER_PLATE, dtype=int))
        plate_empty     = Plate(np.array([], dtype=int))

        success1, _ = self.game.place_plate(plate_clearable, 3, 0)
        self.assertTrue(success1)
        success2, _ = self.game.place_plate(plate_empty, 3, 1)
        self.assertTrue(success2)

        num_initial = len(self.game.placed_plates)
        cleared = self.game.cleanup_empty_plates()

        # Numai poziția goală (3,1) apare în lista returned
        self.assertEqual(len(cleared), 1)
        self.assertIn((3, 1), cleared)
        # Score a fost incrementat cu 1 pentru clearable
        self.assertEqual(self.game.score, 1)
        self.assertEqual(len(self.game.placed_plates), num_initial - 2)
        print("test_cleanup_empty_and_clearable: OK")


if __name__ == '__main__':
    unittest.main()
