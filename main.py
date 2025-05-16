from game import CakeSortGame
from consoleview import ConsoleView

def main():
    mode = input("Type 'gui' for graphical mode or press Enter for console mode: ").strip().lower()
    if mode == "gui":
        import tkinter as tk
        from gui import CakeSortGUI
        root = tk.Tk()
        app = CakeSortGUI(root)
        root.mainloop()
    else:
        game = CakeSortGame()
        view = ConsoleView(game)
        view.run()

if __name__ == "__main__":
    main()
