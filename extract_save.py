#!/usr/bin/env python3
"""
Victoria 3 Save File Extractor
Converts compressed Victoria 3 save files to JSON format using Rakaly
"""

import sys
import os
import subprocess
from pathlib import Path
import argparse

def extract_save(save_name):
    """
    Convert a Victoria 3 save file to JSON using Rakaly
    
    Args:
        save_name: Name of the save file (without path)
    
    Returns:
        True if successful, False otherwise
    """
    # Define paths
    base_dir = Path(__file__).parent
    rakaly_path = base_dir / "rakaly" / "rakaly"
    save_dir = base_dir / "save-files"
    output_dir = base_dir / "extracted-saves"
    
    # Construct full paths
    input_file = save_dir / save_name
    
    # Handle output filename - remove .v3 extension if present and add .json
    if save_name.endswith('.v3'):
        output_name = save_name[:-3] + '_extracted.json'
    else:
        output_name = save_name + '_extracted.json'
    
    output_file = output_dir / output_name
    
    # Check if input file exists
    if not input_file.exists():
        print(f"Error: Save file '{input_file}' not found")
        return False
    
    # Check if rakaly exists
    if not rakaly_path.exists():
        print(f"Error: Rakaly binary not found at '{rakaly_path}'")
        return False
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run rakaly to extract the save file
    try:
        print(f"Extracting '{save_name}'...")
        
        # Rakaly command for Victoria 3 saves
        # Using 'json' command to convert to JSON
        result = subprocess.run(
            [str(rakaly_path), "json", 
             str(input_file)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"Error extracting save file: {result.stderr}")
            return False
        
        # Write the JSON output to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        print(f"Successfully extracted to: {output_file}")
        
        # Print file size info
        input_size = input_file.stat().st_size
        output_size = output_file.stat().st_size
        print(f"Input size: {input_size:,} bytes")
        print(f"Output size: {output_size:,} bytes")
        if output_size > 0:
            print(f"Compression ratio: {input_size/output_size:.2f}x")
        else:
            print("Warning: Output file is empty")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error running rakaly: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def list_save_files():
    """List all available save files"""
    save_dir = Path(__file__).parent / "save-files"
    
    if not save_dir.exists():
        print("No save-files directory found")
        return []
    
    saves = list(save_dir.glob("*.v3"))
    
    if not saves:
        # Try without extension filter
        saves = [f for f in save_dir.iterdir() if f.is_file()]
    
    return saves

def main():
    parser = argparse.ArgumentParser(
        description="Convert Victoria 3 save files to JSON using Rakaly"
    )
    parser.add_argument(
        "save_file",
        nargs='?',
        help="Name of the save file to extract (in save-files directory)"
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available save files"
    )
    
    args = parser.parse_args()
    
    # List saves if requested
    if args.list or not args.save_file:
        saves = list_save_files()
        if saves:
            print("Available save files:")
            for save in saves:
                print(f"  - {save.name}")
        else:
            print("No save files found in save-files directory")
        
        if not args.save_file:
            sys.exit(0)
    
    # Extract the specified save
    if args.save_file:
        success = extract_save(args.save_file)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()