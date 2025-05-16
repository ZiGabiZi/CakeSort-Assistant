import tkinter as tk
from tkinter import messagebox
from game import CakeSortGame
from constants import ROWS, COLS, CAKE_TYPE_COLORS, MAX_SLICES_PER_PLATE
import time

def draw_plate_canvas(parent, plate, size=60):
    canvas = tk.Canvas(parent, width=size, height=size, bg="white", highlightthickness=0)
    angle_per_slice = 360 / MAX_SLICES_PER_PLATE
    start_angle = 0
    for slice_type in plate.slices:
        color = CAKE_TYPE_COLORS.get(slice_type, "gray")
        canvas.create_arc(
            2, 2, size-2, size-2,
            start=start_angle,
            extent=angle_per_slice,
            fill=color,
            outline="black"
        )
        start_angle += angle_per_slice
    return canvas

class CakeSortGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CakeSort")
        self.game = CakeSortGame()
        self.selected_plate_index = None

        self.board_buttons = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.plate_buttons = []

        self.score_label = tk.Label(root, text="Score: 0")
        self.score_label.pack()

        self.board_frame = tk.Frame(root)
        self.board_frame.pack()

        self.plates_frame = tk.Frame(root)
        self.plates_frame.pack()

        self.draw_board()
        self.draw_plates()

    def draw_board(self):
        for c in range(COLS):
            label = tk.Label(self.board_frame, text=str(c), width=6, height=1, bg="lightgray")
            label.grid(row=0, column=c+1)
        for r in range(ROWS):
            row_label = tk.Label(self.board_frame, text=str(r), width=2, height=3, bg="lightgray")
            row_label.grid(row=r+1, column=0)
            for c in range(COLS):
                frame = tk.Frame(self.board_frame, width=60, height=60)
                frame.grid(row=r+1, column=c+1, padx=2, pady=2)
                canvas = tk.Canvas(frame, width=60, height=60, bg="white", highlightthickness=0)
                canvas.pack()
                canvas.bind("<Button-1>", lambda e, r=r, c=c: self.place_plate(r, c))
                self.board_buttons[r][c] = canvas

    def draw_plates(self):
        for widget in self.plates_frame.winfo_children():
            widget.destroy()
        self.plate_canvases = []
        self.plate_buttons = []
        for idx, plate in enumerate(self.game.plates):
            frame = tk.Frame(self.plates_frame)
            frame.grid(row=0, column=idx, padx=5)
            canvas = draw_plate_canvas(frame, plate)
            canvas.pack()
            btn = tk.Button(frame, text="Select", command=lambda idx=idx: self.select_plate(idx))
            btn.pack()
            self.plate_canvases.append((canvas, btn))
            self.plate_buttons.append(btn)

    def select_plate(self, idx):
        self.selected_plate_index = idx
        for i, btn in enumerate(self.plate_buttons):
            btn.config(relief=tk.SUNKEN if i == idx else tk.RAISED)

    def place_plate(self, row, col):
        if self.selected_plate_index is None:
            messagebox.showinfo("Info", "Select a plate first!")
            return
        if self.game.board.get_plate_number(row, col) != 0:
            messagebox.showerror("Error", "Spot already taken!")
            return
        success = self.game.place_plate(self.selected_plate_index, row, col)
        if not success:
            messagebox.showerror("Error", "Invalid move!")
            return
        self.selected_plate_index = None
        self.update_gui()
        self.print_placed_plates()

    def update_gui(self):
        cleared_positions = self.game.cleanup_empty_plates()
        if not self.game.plates:
            self.game.refresh_plates()
        self.score_label.config(text=f"Score: {self.game.score}")
        for r in range(ROWS):
            for c in range(COLS):
                canvas = self.board_buttons[r][c]
                canvas.delete("all")
                plate_number = self.game.board.get_plate_number(r, c)
                if plate_number != 0:
                    plate = self.game.plate_contents_by_number.get(plate_number)
                    if plate:
                        angle_per_slice = 360 / MAX_SLICES_PER_PLATE
                        start_angle = 0
                        for slice_type in plate.slices:
                            color = CAKE_TYPE_COLORS.get(slice_type, "gray")
                            canvas.create_arc(
                                2, 2, 58, 58,
                                start=start_angle,
                                extent=angle_per_slice,
                                fill=color,
                                outline="black"
                            )
                            start_angle += angle_per_slice
        for r, c in cleared_positions:
            self.flash_red_tile(r, c)
        self.draw_plates()

    def animate_slice_move(self, src_row, src_col, dst_row, dst_col, slice_type):
        src_canvas = self.board_buttons[src_row][src_col]
        dst_canvas = self.board_buttons[dst_row][dst_col]
        color = CAKE_TYPE_COLORS.get(slice_type, "gray")
        src_x = src_canvas.winfo_rootx() - self.root.winfo_rootx() + 30
        src_y = src_canvas.winfo_rooty() - self.root.winfo_rooty() + 30
        dst_x = dst_canvas.winfo_rootx() - self.root.winfo_rootx() + 30
        dst_y = dst_canvas.winfo_rooty() - self.root.winfo_rooty() + 30
        float_win = tk.Toplevel(self.root)
        float_win.overrideredirect(True)
        float_win.attributes('-topmost', True)
        float_win.geometry(f"40x40+{int(src_x-20+self.root.winfo_rootx())}+{int(src_y-20+self.root.winfo_rooty())}")
        float_canvas = tk.Canvas(float_win, width=40, height=40, highlightthickness=0, bg='white')
        float_canvas.pack()
        arc = float_canvas.create_arc(0, 0, 40, 40, start=0, extent=60, fill=color, outline="black")
        steps = 20
        for i in range(steps):
            nx = src_x + (dst_x - src_x) * (i+1) / steps
            ny = src_y + (dst_y - src_y) * (i+1) / steps
            float_win.geometry(f"40x40+{int(nx-20+self.root.winfo_rootx())}+{int(ny-20+self.root.winfo_rooty())}")
            self.root.update_idletasks()
            self.root.update()
            time.sleep(0.015)
        float_win.destroy()

    def flash_red_tile(self, row, col, duration=200):
        canvas = self.board_buttons[row][col]
        rect = canvas.create_rectangle(2, 2, 58, 58, fill="red", outline="")
        self.root.update_idletasks()
        self.root.after(duration, lambda: canvas.delete(rect))

    def print_placed_plates(self):
        print("\nPlates currently on the board:")
        for row in range(ROWS):
            for col in range(COLS):
                plate_number = self.game.board.get_plate_number(row, col)
                if plate_number != 0:
                    plate = self.game.plate_contents_by_number.get(plate_number)
                    print(f"At ({row},{col}): Plate #{plate_number} -> {plate}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CakeSortGUI(root)
    root.mainloop()