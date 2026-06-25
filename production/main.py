import board
import busio
import random

# KMK IMPORTS
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation
from kmk.modules.layers import Layers
from kmk.modules.tapdance import TapDance
from kmk.extensions.display import Display, TextEntry
from kmk.extensions.display.ssd1306 import SSD1306

keyboard = KMKKeyboard()

# MATRIX SETUP
keyboard.col_pins = (board.D8, board.D9, board.D10, board.D11)
keyboard.row_pins = (board.D13,)
keyboard.diode_orientation = DiodeOrientation.COL2ROW

# MODULES
layers = Layers()
tapdance = TapDance()
tapdance.tap_time = 300

keyboard.modules.append(layers)
keyboard.modules.append(tapdance)

# GAME ENGINE LOGIC
GRID_W = 21  
GRID_H = 6   

snake = [(GRID_W // 2, GRID_H // 2)]
food = (3, 3)
game_over = False
score = 0

def spawn_food():
    while True:
        f = (random.randint(0, GRID_W - 1), random.randint(0, GRID_H - 1))
        if f not in snake:
            return f

def tick_game(dx, dy):
    global game_over, food, score, snake
    
    if game_over:
        snake = [(GRID_W // 2, GRID_H // 2)]
        score = 0
        game_over = False
        food = spawn_food()
        return

    head_x, head_y = snake[0]
    new_head = (head_x + dx, head_y + dy)

    if new_head[0] < 0 or new_head[0] >= GRID_W or new_head[1] < 0 or new_head[1] >= GRID_H:
        game_over = True
        return

    if new_head in snake:
        game_over = True
        return

    snake.insert(0, new_head)

    if new_head == food:
        score += 1
        food = spawn_food() 
    else:
        snake.pop()         

def move_up(key, kb, *args, **kwargs): tick_game(0, -1)
def move_left(key, kb, *args, **kwargs): tick_game(-1, 0)
def move_down(key, kb, *args, **kwargs): tick_game(0, 1)
def move_right(key, kb, *args, **kwargs): tick_game(1, 0)

GAME_W = KC.make_key(on_press=move_up)
GAME_A = KC.make_key(on_press=move_left)
GAME_S = KC.make_key(on_press=move_down)
GAME_D = KC.make_key(on_press=move_right)

# OLED SETUP
i2c_bus = busio.I2C(board.D5, board.D4)
driver = SSD1306(i2c=i2c_bus, width=128, height=64)

def get_header():
    current_layer = keyboard.active_layers[0] if keyboard.active_layers else 0
    if current_layer == 0: return "Layer 0: Macropad"
    if current_layer == 1: return "Layer 1: Editing"
    if current_layer == 2: return f"SNAKE | Score: {score}"

def render_row(row_idx):
    current_layer = keyboard.active_layers[0] if keyboard.active_layers else 0
    if current_layer != 2:
        return "" 
        
    if game_over:
        if row_idx == 2: return "      GAME OVER     "
        if row_idx == 3: return "    Press Any Key   "
        return ""

    line = ""
    for x in range(GRID_W):
        pos = (x, row_idx)
        if pos == snake[0]:
            line += "@"
        elif pos in snake:
            line += "o"
        elif pos == food:
            line += "*"
        else:
            line += "."
    return line

display = Display(display=driver, width=128, height=64, entries=[
    TextEntry(text=get_header, x=0, y=0),
    TextEntry(text=lambda: render_row(0), x=0, y=10),
    TextEntry(text=lambda: render_row(1), x=0, y=19),
    TextEntry(text=lambda: render_row(2), x=0, y=28),
    TextEntry(text=lambda: render_row(3), x=0, y=37),
    TextEntry(text=lambda: render_row(4), x=0, y=46),
    TextEntry(text=lambda: render_row(5), x=0, y=55),
])
keyboard.extensions.append(display)

# KEYMAPS AND TAPDANCE
W_PAD  = KC.TD(KC.W, KC.W, KC.TO(1))                           
W_EDIT = KC.TD(KC.LCTL(KC.A), KC.LCTL(KC.A), KC.TO(2))         
W_PLAY = KC.TD(GAME_W, GAME_W, KC.TO(0))                       

keyboard.keymap = [
    # LAYER 0 (Triple tap W goes to Layer 1)
    [W_PAD, KC.A, KC.S, KC.D],                             
    
    # LAYER 1 (Triple tap W goes to Layer 2)
    [W_EDIT, KC.LCTL(KC.C), KC.LCTL(KC.X), KC.LCTL(KC.V)], 
    
    # LAYER 2 (Triple tap W goes back to Layer 0)
    [W_PLAY, GAME_A, GAME_S, GAME_D]                       
]

if __name__ == "__main__":
    keyboard.go()