import curses
import random
from dataclasses import dataclass, field
from typing import List

import click


@dataclass
class Position:
    x: int
    y: int

    def __add__(self, other: "Position") -> "Position":
        return Position(self.x + other.x, self.y + other.y)

    def __le__(self, other: "Position") -> bool:
        return self.x <= other.x and self.y <= other.y


@dataclass
class Rectangle:
    start: Position
    end: Position

    @property
    def width(self) -> int:
        return self.end.x - self.start.x + 1

    @property
    def height(self) -> int:
        return self.end.y - self.start.y + 1

    def draw(self, stdscr: curses.window) -> None:
        stdscr.addstr(self.start.y - 1, self.start.x - 1, "┏" + "━" * self.width + "┓")
        stdscr.addstr(self.end.y + 1, self.start.x - 1, "┗" + "━" * self.width + "┛")
        for i in range(self.start.y, self.end.y + 1):
            stdscr.addch(i, self.start.x - 1, "┃")
            stdscr.addch(i, self.end.x + 1, "┃")


@dataclass
class Player:
    body: List[Position]
    length: int = 1
    direction: Position = field(default_factory=lambda: Position(0, 0))

    def draw(self, stdscr: curses.window) -> None:
        for part in self.body:
            stdscr.addch(part.y, part.x, "*", curses.color_pair(1))

        if self.direction == Position(0, -1):
            stdscr.addch(self.body[0].y, self.body[0].x, "^", curses.color_pair(1))
        elif self.direction == Position(0, 1):
            stdscr.addch(self.body[0].y, self.body[0].x, "v", curses.color_pair(1))
        elif self.direction == Position(-1, 0):
            stdscr.addch(self.body[0].y, self.body[0].x, "<", curses.color_pair(1))
        elif self.direction == Position(1, 0):
            stdscr.addch(self.body[0].y, self.body[0].x, ">", curses.color_pair(1))
        else:
            stdscr.addch(self.body[0].y, self.body[0].x, "X", curses.color_pair(1))

    def move(self, pellet_position: Position) -> None:
        head = self.body[0] + self.direction
        self.body.insert(0, head)
        if head != pellet_position:
            self.body.pop(-1)


@dataclass
class Pellet:
    position: Position = field(default_factory=lambda: Position(0, 0))

    def draw(self, stdscr: curses.window) -> None:
        stdscr.addch(self.position.y, self.position.x, "O", curses.color_pair(2))

    def generate(self, board: Rectangle, player: Player) -> None:
        position = Position(random.randint(board.start.x, board.end.x), random.randint(board.start.y, board.end.y))
        while position in player.body:
            position = Position(random.randint(board.start.x, board.end.x), random.randint(board.start.y, board.end.y))
        self.position = position


@dataclass
class GameState:
    board: Rectangle
    player: Player
    pellet: Pellet = field(default_factory=Pellet)
    score: int = 0
    game_over: bool = False


@dataclass
class GameSettings:
    board_height: int
    board_width: int
    game_speed: int


class Game:
    def __init__(self, stdscr: curses.window, settings: GameSettings) -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(settings.game_speed)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)

        screen_height, screen_width = stdscr.getmaxyx()

        board = Rectangle(
            Position((screen_width - settings.board_width) // 2, (screen_height - settings.board_height) // 2),
            Position((screen_width + settings.board_width) // 2 - 1, (screen_height + settings.board_height) // 2 - 1),
        )
        player = Player([board.start + Position(settings.board_width // 2, settings.board_height // 2)])

        self.state = GameState(board, player)
        self.state.pellet.generate(board, player)

    def is_game_over(self) -> bool:
        is_within_bounds: bool = (
            self.state.board.start <= self.state.player.body[0] and self.state.player.body[0] <= self.state.board.end
        )

        is_inside_self: bool = self.state.player.body[0] in self.state.player.body[1:]

        return not is_within_bounds or is_inside_self

    def draw(self, stdscr: curses.window) -> None:
        stdscr.clear()

        board = self.state.board
        board.draw(stdscr)
        self.state.pellet.draw(stdscr)
        self.state.player.draw(stdscr)

        stdscr.addstr(board.end.y + 2, board.start.x, "Score: " + str(self.state.score))
        if self.state.game_over:
            stdscr.addstr(board.end.y + 3, board.start.x, "Game Over")

        stdscr.refresh()

    def step(self, key: int) -> None:
        if key == curses.KEY_UP and self.state.player.direction != Position(0, 1):
            self.state.player.direction = Position(0, -1)
        elif key == curses.KEY_DOWN and self.state.player.direction != Position(0, -1):
            self.state.player.direction = Position(0, 1)
        elif key == curses.KEY_LEFT and self.state.player.direction != Position(1, 0):
            self.state.player.direction = Position(-1, 0)
        elif key == curses.KEY_RIGHT and self.state.player.direction != Position(-1, 0):
            self.state.player.direction = Position(1, 0)

        self.state.player.move(self.state.pellet.position)

        if self.state.player.body[0] == self.state.pellet.position:
            self.state.score += 1
            self.state.pellet.generate(self.state.board, self.state.player)

        if self.is_game_over():
            self.state.game_over = True
            self.state.player.direction = Position(0, 0)


def run_game(stdscr: curses.window, settings: GameSettings) -> None:
    game = Game(stdscr, settings)
    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        if game.state.game_over:
            if key == ord("r"):
                game = Game(stdscr, settings)
            continue

        game.step(key)
        game.draw(stdscr)


@click.command()
@click.option("-h", "--board-height", type=int, default=17, help="Height of the game board.")
@click.option("-w", "--board-width", type=int, default=71, help="Width of the game board.")
@click.option("-s", "--game-speed", type=int, default=100, help="Speed of the game in milliseconds per frame.")
def main(board_height, board_width, game_speed):
    """
    Snake game
    """
    game_settings = GameSettings(board_height, board_width, game_speed)
    curses.wrapper(lambda stdscr: run_game(stdscr, game_settings))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
