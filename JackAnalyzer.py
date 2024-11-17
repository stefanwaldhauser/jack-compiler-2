import os
import sys
from pathlib import Path
import CompilationEngine
from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine
from SymbolTable import SymbolTable


def parse_file(input_path):
    output_path = input_path.with_suffix(".xml")
    tokens = []
    with open(output_path, 'w', encoding='UTF-8') as output_file:
        with open(input_path, 'r', encoding="utf-8") as input_file:
            tokenizer = JackTokenizer(input_file)
            symbol_table = SymbolTable()
            compilation_engine = CompilationEngine(tokenizer, output_file, symbol_table)
            compilation_engine.compile_class()
            input_file.close()
        output_file.close()
    return tokens

def parse_directory(path):
    for file_path in path.glob('*.jack'):
        parse_file(file_path)

def main():
    if len(sys.argv) == 1:
        path = Path(os.getcwd())
    else:
        path = Path(sys.argv[1])

    if path.is_file():
        parse_file(path)
    else:
        parse_directory(path)


if __name__ == "__main__":
    main()
