"""Convert the raw Board into what the snake can see."""
from srcs import config


def _cell_symbol(board, row, col):
    if not (0 <= row < board.size and 0 <= col < board.size):
        return config.SYMBOL_WALL
    cell = (row, col)
    if cell == board.snake[0]:
        return config.SYMBOL_HEAD
    if cell in board.snake[1:]:
        return config.SYMBOL_BODY
    if cell in board.green_apples:
        return config.SYMBOL_GREEN
    if cell == board.red_apple:
        return config.SYMBOL_RED
    return config.SYMBOL_EMPTY


def format_vision(board):
    head_row, head_col = board.snake[0]
    up_lines = [_cell_symbol(board, r, head_col)
                for r in range(-1, head_row)]
    row_line = "".join(_cell_symbol(board, head_row, c)
                       for c in range(-1, board.size + 1))
    down_lines = [_cell_symbol(board, r, head_col)
                  for r in range(head_row + 1, board.size + 1)]
    return "\n".join(up_lines + [row_line] + down_lines)


def _scan(board, drow, dcol):
    head_row, head_col = board.snake[0]
    row, col = head_row + drow, head_col + dcol
    symbol = _cell_symbol(board, row, col)
    while symbol == config.SYMBOL_EMPTY:
        row += drow
        col += dcol
        symbol = _cell_symbol(board, row, col)
    return symbol


def get_compact_state(board):
    return (
        _scan(board, -1, 0),
        _scan(board, 1, 0),
        _scan(board, 0, -1),
        _scan(board, 0, 1),
    )
