import math
import io
import base64
from PIL import Image, ImageDraw
import flet as ft
from game import CakeSortGame
from plate import Plate  
from constants import ROWS, COLS  
from constants import MAX_SLICES_PER_PLATE, CAKE_TYPE_COLORS

TEXTURE_FILES = [
    "textures/cereals.jpg",
    "textures/coliva.jpg",
    "textures/diabet.jpg",
    "textures/red.jpg",
    "textures/tiramisu.jpg",
    "textures/waffle.jpg"
]
TEXTURES = [Image.open(fname).convert("RGBA") for fname in TEXTURE_FILES]

def draw_plate_flet(plate, size=60):
    n = len(plate.slices)
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    cx, cy = size // 2, size // 2

    slices = list(plate.slices)
    while len(slices) < MAX_SLICES_PER_PLATE:
        slices.append(None)

    angle_per_slice = 360 / MAX_SLICES_PER_PLATE
    start_angle = 0
    for idx, slice_type in enumerate(slices):
        end_angle = start_angle + angle_per_slice
       
        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.pieslice([2, 2, size-2, size-2], start=start_angle, end=end_angle, fill=255)
        if slice_type is not None:
            texture_idx = int(slice_type) - 1
            if 0 <= texture_idx < len(TEXTURES):
                texture = TEXTURES[texture_idx].resize((size, size))
                img.paste(texture, (0, 0), mask)
            else:
                color = CAKE_TYPE_COLORS.get(int(slice_type), "#888888")
                color_img = Image.new("RGBA", (size, size), color)
                img.paste(color_img, (0, 0), mask)
        start_angle = end_angle

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = base64.b64encode(buf.getvalue()).decode()
    return ft.Image(src_base64=data, width=size, height=size)

def main(page: ft.Page):
    game = CakeSortGame()
    selected_plate_index = [0]
    score_text = ft.Text(f"Score: {game.score}", size=18)
    board_column = ft.Column()
    plates_row = ft.Row()

    def is_board_full():
        for r in range(ROWS):
            for c in range(COLS):
                if game.board.get_plate_number(r, c) == 0:
                    return False
        return True

    def update_board():
        board_column.controls.clear()
        def make_place_plate(r, c):
            return lambda e: place_plate(r, c)
        for r in range(ROWS):
            row_controls = []
            for c in range(COLS):
                plate_number = game.board.get_plate_number(r, c)
                if plate_number:
                    plate = game.placed_plates[plate_number]
                    label = draw_plate_flet(plate, size=100)  
                else:
                    label = ft.Container(width=120, height=120, bgcolor="#eee", border_radius=60)
                row_controls.append(
                    ft.Container(
                        content=label,
                        width=120,
                        height=120,
                        border=ft.border.all(2, "black"),
                        alignment=ft.alignment.center,
                        on_click=make_place_plate(r, c)
                    )
                )
            board_column.controls.append(ft.Row(row_controls))
        score_text.value = f"Score: {game.score}"
        page.update()

        if is_board_full() and len(game.current_plates) > 0:
            show_game_over()

    def update_plates():
        plates_row.controls.clear()
        def make_select_plate(i):
            return lambda e: select_plate(i)
        for idx, plate in enumerate(game.current_plates):
            plates_row.controls.append(
                ft.Container(
                    content=draw_plate_flet(plate, size=100),  
                    width=94,
                    height=94,
                    border=ft.border.all(3, "blue" if idx == selected_plate_index[0] else "grey"),
                    alignment=ft.alignment.center,
                    on_click=make_select_plate(idx)
                )
            )
        page.update()

    def select_plate(idx):
        selected_plate_index[0] = idx
        update_plates()

    def place_plate(row, col):
        if not game.current_plates:
            return
        if selected_plate_index[0] >= len(game.current_plates):
            return
        if is_board_full():
            show_game_over()
            return
        if game.board.get_plate_number(row, col) != 0:
            return
        success, moves = game.place_plate(selected_plate_index[0], row, col)
        print("Mutări efectuate:", moves)
        game.cleanup_empty_plates()
        if not game.current_plates:
            for _ in range(3):
                game.current_plates.append(Plate.generate_plate())
            selected_plate_index[0] = 0
        else:
            selected_plate_index[0] = min(selected_plate_index[0], len(game.current_plates) - 1)
        update_board()
        update_plates()
        if is_board_full() and len(game.current_plates) > 0:
            show_game_over()

    update_board()
    update_plates()

    while len(game.current_plates) < 3:
        game.current_plates.append(Plate.generate_plate())

    page.add(
        ft.Column([
            ft.Text("CakeSort Board", size=24),
            score_text,
            board_column,
            ft.Text("Plates available:", size=18),
            plates_row
        ])
    )


    def cleanup_empty_plates(self):
        for row in range(ROWS):
            for col in range(COLS):
                plate_number = self.board.get_plate_number(row, col)
                if plate_number:
                    plate = self.placed_plates.get(plate_number)
                    if plate and len(plate.slices) == 0:
                        self.board.remove_plate(row, col)
                        del self.placed_plates[plate_number]

    def show_game_over():
        page.clean()
        page.add(
            ft.Column([
                ft.Text("GAME OVER!", size=40, color="red"),
                ft.Text(f"Score: {game.score}", size=24),
                ft.ElevatedButton("Restart", on_click=lambda e: restart_game())
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def restart_game():
        page.clean()
        game.__init__()  
        selected_plate_index[0] = 0
        update_board()
        update_plates()
        page.add(
            ft.Column([
                ft.Text("CakeSort Board", size=24),
                score_text,
                board_column,
                ft.Text("Plates available:", size=18),
                plates_row
            ])
        )

ft.app(target=main)