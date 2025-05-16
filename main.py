from game import CakeSortGame
from consoleview import ConsoleView

from sys import argv

def main():
    if len(argv) < 2:
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
