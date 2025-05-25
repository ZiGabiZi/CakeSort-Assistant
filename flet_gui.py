import math
import io
import base64
from PIL import Image, ImageDraw
import flet as ft
from game import CakeSortGame
from plate import Plate  
from constants import ROWS, COLS  
from constants import MAX_SLICES_PER_PLATE, CAKE_TYPE_COLORS
import asyncio
import numpy as np

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

    board_cells = [[None for _ in range(COLS)] for _ in range(ROWS)]
    plate_cells = []

    def is_board_full():
        for r in range(ROWS):
            for c in range(COLS):
                if game.board.get_plate_number(r, c) == 0:
                    return False
        return True

    def make_place_plate(row, col):
        return lambda e: place_plate(row, col)

    def make_select_plate(idx):
        return lambda e: select_plate(idx)

    def update_board():
        board_column.controls.clear()
        for r in range(ROWS):
            row_controls = []
            for c in range(COLS):
                plate_number = game.board.get_plate_number(r, c)
                if plate_number:
                    plate = game.placed_plates[plate_number]
                    label = draw_plate_flet(plate, size=100)  
                else:
                    label = ft.Container(width=120, height=120, bgcolor="#eee", border_radius=60)
                cell = ft.Container(
                    content=label,
                    width=120,
                    height=120,
                    border=ft.border.all(2, "black"),
                    alignment=ft.alignment.center,
                    on_click=make_place_plate(r, c)
                )
                board_cells[r][c] = cell
                row_controls.append(cell)
            board_column.controls.append(ft.Row(row_controls))
        score_text.value = f"Score: {game.score}"
        page.update()

        if is_board_full() and len(game.current_plates) > 0:
            show_game_over()

    def update_plates():
        plates_row.controls.clear()
        plate_cells.clear()
        for idx, plate in enumerate(game.current_plates):
            cell = ft.Container(
                content=draw_plate_flet(plate, size=100),
                width=94,
                height=94,
                border=ft.border.all(3, "blue" if idx == selected_plate_index[0] else "grey"),
                alignment=ft.alignment.center,
                on_click=make_select_plate(idx)
            )
            plate_cells.append(cell)
            plates_row.controls.append(cell)
        page.update()

    def select_plate(idx):
        selected_plate_index[0] = idx
        update_plates()

    async def animate_slice_move(src_widget, dst_widget, slice_type):
        def get_cell_pos(widget):
            for r in range(ROWS):
                for c in range(COLS):
                    if board_cells[r][c] is widget:
                        return (c * 120 + 60, 60 + r * 120 + 60)
            for i, cell in enumerate(plate_cells):
                if cell is widget:
                    return (i * 94 + 47, 60 + ROWS * 120 + 40 + 47)
            return (0, 0)  

        src_left, src_top = get_cell_pos(src_widget)
        dst_left, dst_top = get_cell_pos(dst_widget)

        img = draw_plate_flet(Plate(np.array([slice_type])), size=60)
        anim = ft.Container(content=img, left=src_left, top=src_top, width=60, height=60)
        overlay.controls.append(anim)
        page.update()

        steps = 20
        for i in range(steps + 1):
            t = i / steps
            anim.left = src_left + (dst_left - src_left) * t
            anim.top = src_top + (dst_top - src_top) * t
            page.update()
            await asyncio.sleep(0.01)

        overlay.controls.remove(anim)
        page.update()

    async def do_animations(moves):
        for move in moves:
            count = move.get("count", 1)
            for _ in range(count):
                if move["source_row"] == -1:  
                    src_widget = plate_cells[selected_plate_index[0]]
                else:
                    src_widget = board_cells[move["source_row"]][move["source_column"]]
                dst_widget = board_cells[move["destination_row"]][move["destination_column"]]
                await animate_slice_move(src_widget, dst_widget, move["slice_type"])

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
        if moves:
            asyncio.run(do_animations(moves))
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

    update_board()
    update_plates()

    while len(game.current_plates) < 3:
        game.current_plates.append(Plate.generate_plate())

    overlay = ft.Stack([
        ft.Column([
            ft.Text("CakeSort Board", size=24),
            score_text,
            board_column,
            ft.Text("Plates available:", size=18),
            plates_row
        ]),
    ])
    page.add(overlay)

ft.app(target=main)