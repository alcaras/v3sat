#!/usr/bin/env python3
"""
Infamy Report for Victoria 3

Shows infamy levels by country in the format:
| Country | Infamy |
|---------|--------|
| FRA     | 74.0   |
| RUS     | 70.1   |
etc.
"""

import json
import os

def load_save_data(filepath):
    """Load JSON save data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def get_country_tag(countries, country_id):
    """Get country tag from country ID."""
    country = countries.get(str(country_id), {})
    if isinstance(country, dict):
        definition = country.get('definition', '')
        if definition:
            return definition
    return f"ID_{country_id}"

def get_country_infamy(countries, country_id):
    """Get infamy level for a country."""
    country = countries.get(str(country_id), {})
    if not isinstance(country, dict):
        return 0.0
        
    # Infamy is stored in the country's data
    infamy = country.get('infamy', 0.0)
    return float(infamy) if infamy else 0.0

def generate_infamy_report(save_data, humans_only=True):
    """Generate infamy report."""
    countries = save_data.get('country_manager', {}).get('database', {})
    
    # Load human countries if filtering
    human_countries = set()
    if humans_only and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Prepare report data
    report_data = []
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
            
        tag = get_country_tag(countries, country_id)
        
        # Filter by human countries if requested
        if humans_only and human_countries and tag not in human_countries:
            continue
            
        infamy = get_country_infamy(countries, country_id)
        report_data.append((tag, infamy))
    
    # Sort by infamy (highest first)
    report_data.sort(key=lambda x: -x[1])
    
    return report_data

def print_infamy_report(report_data):
    """Print infamy report in the requested format."""
    print("INFAMY LEVELS BY COUNTRY")
    print("=" * 30)
    print()
    print("| Country | Infamy |")
    print("|---------|--------|")
    
    for tag, infamy in report_data:
        print(f"| {tag:7} | {infamy:6.1f} |")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Victoria 3 infamy reports')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output', help='Output file for the report')
    parser.add_argument('--humans', action='store_true', default=True, help='Only analyze human-controlled countries')
    parser.add_argument('--all', action='store_true', help='Analyze all countries')
    
    args = parser.parse_args()
    
    # Determine save file to use
    if args.save_file:
        save_path = args.save_file
    else:
        # Use latest extracted save
        from pathlib import Path
        extracted_dir = Path('extracted-saves')
        if not extracted_dir.exists():
            print("Error: extracted-saves directory not found")
            return
        
        json_files = list(extracted_dir.glob('*_extracted.json'))
        if not json_files:
            print("Error: No extracted save files found")
            return
        
        # Get the most recent file
        save_path = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"Using latest save: {save_path.name}")
    
    # Load and analyze
    print(f"Loading save data...")
    save_data = load_save_data(save_path)
    
    humans_only = not args.all
    report_data = generate_infamy_report(save_data, humans_only)
    
    # Generate output
    if args.output:
        with open(args.output, 'w') as f:
            # Redirect print to file
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            print_infamy_report(report_data)
            sys.stdout = old_stdout
        print(f"Infamy report saved to: {args.output}")
    else:
        print_infamy_report(report_data)

if __name__ == '__main__':
    main()