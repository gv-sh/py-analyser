import ast
import os
import argparse

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description='Analyze Python code structure with tree-like pretty print.')
    parser.add_argument('directory', help='Directory to analyze')
    parser.add_argument('--exclude-imports', action='store_true', help='Exclude import statements from the output')
    parser.add_argument('--output', choices=['print', 'dot'], default='print', help='Output format: text (default) or dot file')
    parser.add_argument('--func-symbol', default='ƒ', help='Symbol to prepend to function names (default: ƒ)')
    parser.add_argument('--class-symbol', default='ℂ', help='Symbol to prepend to class names (default: ℂ)')
    return parser.parse_args()

def analyze_python_file(file_path, exclude_imports):
    """Returns a nested dictionary representing the structure of a Python file."""
    structure = {'imports': [], 'functions': [], 'classes': {}}
    try:
        with open(file_path, "r") as source:
            tree = ast.parse(source.read(), filename=file_path)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return structure  # Continue with the initialized (empty) structure for this file

    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and not exclude_imports:
            for alias in node.names:
                structure['imports'].append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and not exclude_imports:
            structure['imports'].append(f"from {node.module} import {', '.join(alias.name for alias in node.names)}")
        elif isinstance(node, ast.FunctionDef):
            structure['functions'].append(node.name)
        elif isinstance(node, ast.ClassDef):
            class_methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            structure['classes'][node.name] = class_methods
    if exclude_imports:
        del structure['imports']
    return structure

def print_structure(structure, indent='', func_symbol='ƒ', class_symbol='ℂ'):
    if not structure:  # Debugging line
        print("No structure to print.")
        return

    for file_path, contents in structure.items():
        print(f"{file_path}:")  # Prints the relative file path
        if contents.get('imports') and not args.exclude_imports:
            print(f"{indent}Imports:")
            for imp in contents['imports']:
                print(f"{indent}  - {imp}")
        if contents.get('functions'):
            for func in contents['functions']:
                print(f"{indent}{func_symbol} {func}()")
        if contents.get('classes'):
            for cls, methods in contents['classes'].items():
                print(f"{indent}{class_symbol} {cls}")
                for method in methods:
                    print(f"{indent}  - {method}()")
        print()  # Adds a newline for better readability between files


def analyze_directory(directory, exclude_imports):
    """Analyzes each Python file in the directory and subdirectories."""
    structure = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, file), directory)
                structure[rel_path] = analyze_python_file(os.path.join(root, file), exclude_imports)
    return structure

def generate_dot(structure):
    """Generates a dot representation with a tree-like structure and improved legibility."""
    lines = [
        'digraph G {',
        '    rankdir=LR;',  # Left to Right, change to TB for Top to Bottom
        '    node [style=filled, fontname="Helvetica"];',
        '    edge [arrowhead=none];'  # Remove arrowheads for a tree-like appearance
    ]
    
    file_attrs = 'fillcolor="lightblue", shape=box'
    class_attrs = 'fillcolor="lightgreen", shape=ellipse'
    function_attrs = 'fillcolor="lightyellow", shape=note'

    for file, content in structure.items():
        file_node_name = file.replace('.', '_').replace('/', '_')
        lines.append(f'    {file_node_name} [{file_attrs}, label="{file}"];')

        for func in content.get('functions', []):
            func_node = f"{file_node_name}_func_{func}"
            lines.append(f'    {func_node} [{function_attrs}, label="{func}()"];')
            lines.append(f'    {file_node_name} -> {func_node};')

        for cls, methods in content.get('classes', {}).items():
            class_node = f"{file_node_name}_cls_{cls}"
            lines.append(f'    {class_node} [{class_attrs}, label="{cls}"];')
            lines.append(f'    {file_node_name} -> {class_node};')

            for method in methods:
                method_node = f"{class_node}_meth_{method}"
                lines.append(f'    {method_node} [{function_attrs}, label="{method}()"];')
                lines.append(f'    {class_node} -> {method_node};')

    lines.append('}')
    return '\n'.join(lines)

if __name__ == "__main__":
    args = parse_args()
    module_structure = analyze_directory(args.directory, args.exclude_imports)
    
    if args.output == 'print':
        print(f"{args.directory}/")
        print_structure(module_structure, indent='    ', func_symbol=args.func_symbol, class_symbol=args.class_symbol)
    elif args.output == 'dot':
        dot_content = generate_dot(module_structure)
        dot_filename = os.path.join(args.directory, "structure.dot")
        with open(dot_filename, 'w') as f:
            f.write(dot_content)
        print(f"Dot file created at {dot_filename}")
