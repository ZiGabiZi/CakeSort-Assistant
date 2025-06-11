import pickle
import io
import base64
from PIL import Image, ImageDraw
import flet as ft
from env import Env
from game import CakeSortGame
from plate import Plate  
from constants import ROWS, COLS  
from constants import MAX_SLICES_PER_PLATE, CAKE_TYPE_COLORS
import asyncio
import numpy as np
import os
from tensorflow.keras.models import load_model

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
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    model = load_model("cake_sort_model.h5")
    try:
        for fname in os.listdir(temp_dir):
            fpath = os.path.join(temp_dir, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
    except Exception as ex:
        print("Eroare la ștergerea fișierelor temp la pornire:", ex)

    page.window_on_close = True 
    page.window_full_screen = True
    page.window_frameless = True

    CELL_MARGIN = 10

    def get_cell_size():
        w = (page.width - (COLS + 1) * CELL_MARGIN) // COLS
        h = (page.height * BOARD_HEIGHT_RATIO - (ROWS + 1) * CELL_MARGIN) // ROWS
        return int(min(w, h))

    def get_plate_size():
        cell_size = get_cell_size()
        return int(min(cell_size * 0.9, page.height * 0.18))

    game = CakeSortGame()
    while len(game.current_plates) < 3:
        game.current_plates.append(Plate.generate_plate())

    autosave_counter = [1]  

    def autosave_game():
        for i in range(len(game.current_plates)):
            print(f"Plate{i}")
            env = Env(game)
            env.set_plate_index(i)
            action = np.argmax((model.predict(env.get_state()[np.newaxis], verbose=0)[0]))
            score = np.max((model.predict(env.get_state()[np.newaxis], verbose=0)[0]))
            row,column = divmod(action,COLS)
            print(f"{row=},{column=},{score=}")
        filename = os.path.join(temp_dir, f"autosave_{autosave_counter[0]}.pkl")
        with open(filename, "wb") as f:
            pickle.dump(game, f)
        autosave_counter[0] += 1

    # Autosave la începutul jocului
    autosave_game()
    print("Initial game state saved.")  # Mesaj opțional pentru claritate

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
                    label = draw_plate_flet(plate, size=cell_size)  
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
                content=draw_plate_flet(plate, size=plate_size),  
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
                        return get_board_cell_position(r, c)
            for i, cell in enumerate(plate_cells):
                if cell is widget:
                    plate_size = get_plate_size()
                    plates_row_width = len(plate_cells) * plate_size + (len(plate_cells) + 1) * CELL_MARGIN
                    offset_x = (page.width - plates_row_width) // 2 + CELL_MARGIN + i * (plate_size + CELL_MARGIN)
                    board_height = ROWS * get_cell_size() + (ROWS + 1) * CELL_MARGIN
                    offset_y = (page.height - board_height) // 2 + board_height + int(page.height * 0.05) + CELL_MARGIN
                    return offset_x, offset_y
            return (0, 0)

        src_left, src_top = get_cell_pos(src_widget)
        dst_left, dst_top = get_cell_pos(dst_widget)

        img = draw_plate_flet(Plate(np.array([slice_type])), size=get_cell_size())
        anim = ft.Container(content=img, left=src_left, top=src_top, width=get_cell_size(), height=get_cell_size())
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

        moves = game.place_plate(selected_plate_index[0], row, col)
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
        autosave_game()
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
                score_row,
                board_column,
                ft.Container(height=page.height * 0.05),
                plates_row
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

    def save_game(e):
        with open("cakesort_save.pkl", "wb") as f:
            pickle.dump(game, f)

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def load_game_from_path(path):
        try:
            with open(path, "rb") as f:
                loaded_game = pickle.load(f)
                game.__dict__.update(loaded_game.__dict__)
                update_board()
                update_plates()
        except Exception as ex:
            print("Eroare la load:", ex)

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            load_game_from_path(e.files[0].path)

    file_picker.on_result = on_file_picked

    def load_game(e):
        file_picker.pick_files(
            dialog_title="Alege fișierul de autosave",
            allowed_extensions=["pkl"],
            initial_directory=temp_dir
        )

    def get_last_autosave_file():
        files = [f for f in os.listdir(temp_dir) if f.startswith("autosave_") and f.endswith(".pkl")]
        if not files:
            return None
        files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
        return os.path.join(temp_dir, files[-2]) if len(files) > 1 else os.path.join(temp_dir, files[-1])

    def undo_game(e):
        last_file = get_last_autosave_file()
        if last_file and os.path.exists(last_file):
            try:
                with open(last_file, "rb") as f:
                    loaded_game = pickle.load(f)
                    game.__dict__.update(loaded_game.__dict__)
                    update_board()
                    update_plates()
            except Exception as ex:
                print("Eroare la undo:", ex)
    
    save_button = ft.ElevatedButton("Save", on_click=save_game)
    load_button = ft.ElevatedButton("Load", on_click=load_game)
    undo_button = ft.ElevatedButton("Undo", on_click=undo_game)
    score_row = ft.Row([save_button, load_button, undo_button, score_text], alignment=ft.MainAxisAlignment.START)

    update_board()
    update_plates()

    while len(game.current_plates) < 3:
        game.current_plates.append(Plate.generate_plate())

    overlay = ft.Stack([
        ft.Row([
            ft.Column([
                score_row,
                board_column,
                ft.Container(height=page.height * 0.05),  
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

    def get_board_cell_position(row, col):
        cell_size = get_cell_size()
        board_width = COLS * cell_size + (COLS + 1) * CELL_MARGIN
        board_height = ROWS * cell_size + (ROWS + 1) * CELL_MARGIN
        offset_x = (page.width - board_width) // 2 + CELL_MARGIN + col * (cell_size + CELL_MARGIN)-20
        offset_y = (page.height * 0.078) + CELL_MARGIN + row * (cell_size + CELL_MARGIN) 
        return offset_x, offset_y


    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(temp_dir, exist_ok=True)

    

    

ft.app(target=main)