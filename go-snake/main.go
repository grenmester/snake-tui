package main

import (
	"math/rand"
	"time"

	"github.com/gdamore/tcell/v2"
)

type Position struct {
	x int
	y int
}

func (p Position) Add(other Position) Position {
	return Position{p.x + other.x, p.y + other.y}
}

func (p Position) Equal(other Position) bool {
	return p.x == other.x && p.y == other.y
}

type Rectangle struct {
	start Position
	end   Position
}

func (r Rectangle) Width() int {
	return r.end.x - r.start.x + 1
}

func (r Rectangle) Height() int {
	return r.end.y - r.start.y + 1
}

type Player struct {
	body      []Position
	length    int
	direction Position
}

func (p *Player) Move(pelletPos Position) {
	head := p.body[0].Add(p.direction)
	p.body = append([]Position{head}, p.body...)
	if !head.Equal(pelletPos) {
		p.body = p.body[:len(p.body)-1]
	}
}

func (p *Player) Draw(screen tcell.Screen) {
	style := tcell.StyleDefault.Foreground(tcell.ColorGreen)
	for _, part := range p.body {
		screen.SetContent(part.x, part.y, '*', nil, style)
	}

	head := p.body[0]
	var char rune
	switch {
	case p.direction.Equal(Position{0, -1}):
		char = '^'
	case p.direction.Equal(Position{0, 1}):
		char = 'v'
	case p.direction.Equal(Position{-1, 0}):
		char = '<'
	case p.direction.Equal(Position{1, 0}):
		char = '>'
	default:
		char = 'X'
	}
	screen.SetContent(head.x, head.y, char, nil, style)
}

type Pellet struct {
	position Position
}

func (p *Pellet) Draw(screen tcell.Screen) {
	style := tcell.StyleDefault.Foreground(tcell.ColorRed)
	screen.SetContent(p.position.x, p.position.y, 'O', nil, style)
}

func (p *Pellet) Generate(board Rectangle, player Player) {
	rand.Seed(time.Now().UnixNano())
	pos := Position{
		x: rand.Intn(board.Width()) + board.start.x,
		y: rand.Intn(board.Height()) + board.start.y,
	}
	for containsPosition(player.body, pos) {
		pos = Position{
			x: rand.Intn(board.Width()) + board.start.x,
			y: rand.Intn(board.Height()) + board.start.y,
		}
	}
	p.position = pos
}

type GameState struct {
	board    Rectangle
	player   Player
	pellet   Pellet
	score    int
	gameOver bool
}

func (g *GameState) isGameOver() bool {
	head := g.player.body[0]
	isWithinBounds := head.x >= g.board.start.x && head.x <= g.board.end.x &&
		head.y >= g.board.start.y && head.y <= g.board.end.y
	isInsideSelf := containsPosition(g.player.body[1:], head)
	return !isWithinBounds || isInsideSelf
}

func containsPosition(body []Position, pos Position) bool {
	for _, part := range body {
		if part.Equal(pos) {
			return true
		}
	}
	return false
}

func drawBox(screen tcell.Screen, board Rectangle) {
	horizontalStyle := tcell.StyleDefault.Foreground(tcell.ColorWhite)

	// Draw top and bottom borders
	for x := board.start.x; x <= board.end.x; x++ {
		screen.SetContent(x, board.start.y-1, '-', nil, horizontalStyle)
		screen.SetContent(x, board.end.y+1, '-', nil, horizontalStyle)
	}

	// Draw left and right borders
	for y := board.start.y; y <= board.end.y; y++ {
		screen.SetContent(board.start.x-1, y, '|', nil, horizontalStyle)
		screen.SetContent(board.end.x+1, y, '|', nil, horizontalStyle)
	}
}

func gameLoop(screen tcell.Screen, settings GameSettings) {
	screen.Clear()

	width, height := screen.Size()
	board := Rectangle{
		start: Position{x: (width - settings.boardWidth) / 2, y: (height - settings.boardHeight) / 2},
		end:   Position{x: (width + settings.boardWidth) / 2, y: (height + settings.boardHeight) / 2},
	}
	player := Player{
		body:      []Position{{x: board.start.x + settings.boardWidth/2, y: board.start.y + settings.boardHeight/2}},
		direction: Position{0, 0},
	}
	pellet := Pellet{}
	pellet.Generate(board, player)

	state := GameState{
		board:  board,
		player: player,
		pellet: pellet,
	}

	for !state.gameOver {
		drawBox(screen, state.board)
		state.player.Draw(screen)
		state.pellet.Draw(screen)

		screen.Show()
		ev := screen.PollEvent()
		switch ev := ev.(type) {
		case *tcell.EventKey:
			switch ev.Key() {
			case tcell.KeyEscape:
				return
			case tcell.KeyUp:
				if state.player.direction != (Position{0, 1}) {
					state.player.direction = Position{0, -1}
				}
			case tcell.KeyDown:
				if state.player.direction != (Position{0, -1}) {
					state.player.direction = Position{0, 1}
				}
			case tcell.KeyLeft:
				if state.player.direction != (Position{1, 0}) {
					state.player.direction = Position{-1, 0}
				}
			case tcell.KeyRight:
				if state.player.direction != (Position{-1, 0}) {
					state.player.direction = Position{1, 0}
				}
			case tcell.KeyRune:
				if ev.Rune() == 'q' {
					return
				}
			}
		}

		state.player.Move(state.pellet.position)
		if state.player.body[0].Equal(state.pellet.position) {
			state.score++
			state.pellet.Generate(state.board, state.player)
		}

		if state.isGameOver() {
			state.gameOver = true
		}

		time.Sleep(time.Duration(settings.gameSpeed) * time.Millisecond)
	}
}

type GameSettings struct {
	boardHeight int
	boardWidth  int
	gameSpeed   int
}

func main() {
	settings := GameSettings{
		boardHeight: 17,
		boardWidth:  71,
		gameSpeed:   100,
	}

	screen, err := tcell.NewScreen()
	if err != nil {
		panic(err)
	}
	defer screen.Fini()

	err = screen.Init()
	if err != nil {
		panic(err)
	}

	screen.SetStyle(tcell.StyleDefault.Foreground(tcell.ColorWhite).Background(tcell.ColorBlack))
	screen.Clear()

	gameLoop(screen, settings)
}
