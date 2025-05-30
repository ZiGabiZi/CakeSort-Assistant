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

BOARD_HEIGHT_RATIO = 0.7

def main(page: ft.Page):
    page.window_full_screen = True
    page.window_frameless = True

    CELL_MARGIN = 10

    def get_cell_size():
        # Calculează dimensiunea maximă pentru celule, ținând cont de ROWS, COLS și margin
        w = (page.width - (COLS + 1) * CELL_MARGIN) // COLS
        h = (page.height * BOARD_HEIGHT_RATIO - (ROWS + 1) * CELL_MARGIN) // ROWS
        return int(min(w, h))

    def get_plate_size():
        # Plates-urile vor fi 60% din dimensiunea celulei board-ului, dar nu mai mari decât 18% din înălțime
        cell_size = get_cell_size()
        return int(min(cell_size * 0.9, page.height * 0.18))

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
        board_column.height = int(page.height * BOARD_HEIGHT_RATIO)
        board_column.controls.clear()
        cell_size = get_cell_size()
        for r in range(ROWS):
            row_controls = []
            for c in range(COLS):
                plate_number = game.board.get_plate_number(r, c)
                if plate_number:
                    plate = game.placed_plates[plate_number]
                    label = draw_plate_flet(plate, size=cell_size)  # <-- aici
                else:
                    label = ft.Container(width=cell_size, height=cell_size, bgcolor="#eee", border_radius=cell_size//2)
                cell = ft.Container(
                    content=label,
                    width=cell_size,
                    height=cell_size,
                    border=ft.border.all(2, "black"),
                    alignment=ft.alignment.center,
                    on_click=make_place_plate(r, c),
                    margin=CELL_MARGIN//2
                )
                board_cells[r][c] = cell
                row_controls.append(cell)
            board_column.controls.append(ft.Row(row_controls, spacing=0))
        score_text.value = f"Score: {game.score}"
        page.update()

        if is_board_full() and len(game.current_plates) > 0:
            show_game_over()

    def update_plates():
        plates_row.controls.clear()
        plate_cells.clear()
        plate_size = get_plate_size()
        for idx, plate in enumerate(game.current_plates):
            cell = ft.Container(
                content=draw_plate_flet(plate, size=plate_size),  # <-- aici
                width=plate_size,
                height=plate_size,
                border=ft.border.all(3, "blue" if idx == selected_plate_index[0] else "grey"),
                alignment=ft.alignment.center,
                on_click=make_select_plate(idx),
                margin=CELL_MARGIN//2
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
                score_text,
                board_column,
                plates_row
            ])
        )

    update_board()
    update_plates()

    while len(game.current_plates) < 3:
        game.current_plates.append(Plate.generate_plate())

    overlay = ft.Stack([
        ft.Row([
            ft.Column([
                score_text,
                board_column,
                ft.Container(height=page.height * 0.05),  # spațiu vertical între board și plates_row
                plates_row
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    ])
    page.add(overlay)

    def on_resize(e):
        update_board()
        update_plates()
    page.on_resize = on_resize

ft.app(target=main)