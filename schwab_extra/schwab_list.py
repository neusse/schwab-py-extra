#!/usr/bin/env python3
"""
List all exported programs from setup.py
"""

import os
import sys
import ast
import re

def find_console_scripts_in_setup():
    """Extract console_scripts from setup.py file"""
    
    # Check if setup.py exists
    if not os.path.exists('setup.py'):
        print("Error: setup.py not found in current directory.")
        print("Please cd to the schwab-py-extra project root directory.")
        return None
    
    try:
        # Try different encodings to handle various file formats
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open('setup.py', 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print("Error: Unable to read setup.py with any supported encoding.")
            return None
        
        # Try to parse as AST first
        try:
            tree = ast.parse(content)
            scripts = extract_scripts_from_ast(tree)
            if scripts:
                return scripts
        except:
            pass
        
        # Fallback to regex parsing
        return extract_scripts_with_regex(content)
        
    except Exception as e:
        print(f"Error reading setup.py: {e}")
        return None

def extract_scripts_from_ast(tree):
    """Extract console_scripts using AST parsing"""
    scripts = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id == 'setup':
            for keyword in node.keywords:
                if keyword.arg == 'entry_points':
                    if isinstance(keyword.value, ast.Dict):
                        scripts.extend(parse_entry_points_dict(keyword.value))
                elif keyword.arg == 'console_scripts':
                    if isinstance(keyword.value, ast.List):
                        scripts.extend(parse_console_scripts_list(keyword.value))
    
    return scripts

def parse_entry_points_dict(dict_node):
    """Parse entry_points dictionary from AST"""
    scripts = []
    for key, value in zip(dict_node.keys, dict_node.values):
        # Handle both old ast.Str and new ast.Constant for compatibility
        key_value = None
        if isinstance(key, ast.Constant):
            key_value = key.value
        elif hasattr(ast, 'Str') and isinstance(key, ast.Str):  # Backwards compatibility
            key_value = key.s
            
        if key_value == 'console_scripts':
            if isinstance(value, ast.List):
                scripts.extend(parse_console_scripts_list(value))
    return scripts

def parse_console_scripts_list(list_node):
    """Parse console_scripts list from AST"""
    scripts = []
    for item in list_node.elts:
        script_def = None
        
        # Handle both old ast.Str and new ast.Constant for compatibility
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            script_def = item.value
        elif hasattr(ast, 'Str') and isinstance(item, ast.Str):  # Backwards compatibility
            script_def = item.s
        
        if script_def and '=' in script_def:
            script_name = script_def.split('=')[0].strip()
            scripts.append(script_name)
    
    return scripts

def extract_scripts_with_regex(content):
    """Fallback regex-based extraction"""
    scripts = []
    
    # Look for entry_points with console_scripts
    entry_points_pattern = r'entry_points\s*=\s*{[^}]*["\']console_scripts["\']\s*:\s*\[(.*?)\]'
    match = re.search(entry_points_pattern, content, re.DOTALL)
    
    if match:
        console_scripts_content = match.group(1)
        script_patterns = re.findall(r'["\']([^"\'=]+)\s*=', console_scripts_content)
        scripts.extend(script_patterns)
    
    # Also look for standalone console_scripts
    console_scripts_pattern = r'console_scripts\s*=\s*\[(.*?)\]'
    match = re.search(console_scripts_pattern, content, re.DOTALL)
    
    if match:
        console_scripts_content = match.group(1)
        script_patterns = re.findall(r'["\']([^"\'=]+)\s*=', console_scripts_content)
        scripts.extend(script_patterns)
    
    return scripts

def format_program_list(scripts):
    """Format the programs list for display"""
    if not scripts:
        print("No exported programs found in setup.py")
        return
    
    # Remove schwab-list from the list (this program itself)
    filtered_scripts = [script for script in scripts if script != 'schwab-list']
    
    if not filtered_scripts:
        print("No other exported programs found (only schwab-list)")
        return
    
    print("Available programs:")
    print("=" * 50)
    
    # Sort alphabetically for better presentation
    for script in sorted(filtered_scripts):
        print(f"  • {script}")
    
    print("=" * 50)
    print(f"Total: {len(filtered_scripts)} program(s)")

def main():
    """Main function"""
    scripts = find_console_scripts_in_setup()
    
    if scripts is not None:
        format_program_list(scripts)

if __name__ == "__main__":
    main()
