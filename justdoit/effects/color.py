COLORS = {
    'red':     '\033[91m',
    'green':   '\033[92m',
    'yellow':  '\033[93m',
    'blue':    '\033[94m',
    'magenta': '\033[95m',
    'cyan':    '\033[96m',
    'white':   '\033[97m',
    'reset':   '\033[0m',
    'bold':    '\033[1m',
    'rainbow': None,  # special case
}

RAINBOW_CYCLE = ['\033[91m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m']


def colorize(text: str, color: str, rainbow_index: int = 0) -> str:
    if color == 'rainbow':
        c = RAINBOW_CYCLE[rainbow_index % len(RAINBOW_CYCLE)]
        return f"{c}{text}{COLORS['reset']}"
    if color in COLORS and COLORS[color]:
        return f"{COLORS['bold']}{COLORS[color]}{text}{COLORS['reset']}"
    return text
