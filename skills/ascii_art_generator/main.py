import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from justdoit import render

def run_skill():
    if len(sys.argv) < 2:
        print('Usage: openclaw run skills/ascii_art_generator main.py --text <your_text> --output /path/to/output.txt')
        return

    text = ''
    output_file = ''

    for arg in sys.argv[1:]:
        if arg.startswith('--text='):
            text = arg.split('=')[1]
        elif arg.startswith('--output='):
            output_file = arg.split('=')[1]

    if not text or not output_file:
        print('Error: Missing required arguments.')
        return

    ascii_art = render(text)

    with open(output_file, 'w') as file:
        file.write(ascii_art)

if __name__ == '__main__':
    run_skill()