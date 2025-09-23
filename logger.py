class Color:
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    UNDERLINE = "\x1b[4m"
    BLINK = "\x1b[5m"
    REVERSE = "\x1b[7m"
    HIDDEN = "\x1b[8m"
    RESET = "\033[0m"

    BLACK = "\x1b[30m"
    RED = "\x1b[31m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    BLUE = "\x1b[34m"
    MAGENTA = "\x1b[35m"
    CYAN = "\x1b[36m"
    WHITE = "\x1b[37m"

    BRIGHT_BLACK = "\x1b[90m"
    BRIGHT_RED = "\x1b[91m"
    BRIGHT_GREEN = "\x1b[92m"
    BRIGHT_YELLOW = "\x1b[93m"
    BRIGHT_BLUE = "\x1b[94m"
    BRIGHT_MAGENTA = "\x1b[95m"
    BRIGHT_CYAN = "\x1b[96m"
    BRIGHT_WHITE = "\x1b[97m"

level_colors = {
    "LOG": Color.GREEN,
    "ERROR": Color.RED,
    "WARNING": Color.YELLOW,
    "": "" # For no coloring
}

def log(message: str, level: str, filename: str, allow_file: bool = True, allow_screen: bool = True) -> None:
    if (allow_file): log_to_file(message, level, filename)
    if (allow_screen): log_to_screen(message, level)

def log_to_file(message: str, level: str, filename: str) -> None:
    print(f"{level}: {message} [to {filename}]")
    
def log_to_screen(message: str, level: str) -> None:
    print(f"{level_colors[level]}{level}: {Color.RESET}{message}")