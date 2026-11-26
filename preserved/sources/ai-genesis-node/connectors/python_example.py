"""Run from the app folder: python connectors/python_example.py"""
from genesis_connector import GenesisConnector


def handle_message(text):
    # Replace this function with your program's supported operations.
    # Never eval/exec raw AI output or incoming messages.
    return f"Python received: {text}\nCharacters: {len(text)}\nStatus: ready"


if __name__ == "__main__":
    connector = GenesisConnector("Python example", handle_message)
    try:
        connector.serve_forever()
    except KeyboardInterrupt:
        connector.stop()
