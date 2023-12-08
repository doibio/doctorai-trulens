import sys

def read_file(filename):
    """Reads the content of a file and returns it."""
    try:
        with open(filename, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "File not found."

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script.py <filename>")
    else:
        filename = sys.argv[1]
        content = read_file(filename)
        print(content)
