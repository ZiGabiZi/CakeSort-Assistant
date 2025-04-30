from game import CakeSortGame
from consoleview import ConsoleView

def main():
    game = CakeSortGame()
    view = ConsoleView(game)
    view.run()

if __name__ == "__main__":
    main()
