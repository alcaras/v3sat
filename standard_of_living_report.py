#!/usr/bin/env python3
"""
Standard of Living Report for Victoria 3

Shows current standard of living by country, sorted by SoL level.
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

def get_country_standard_of_living(country):
    """Get standard of living for a country from avgsoltrend data."""
    if not isinstance(country, dict) or 'avgsoltrend' not in country:
        return 0.0
    
    avgsoltrend = country['avgsoltrend']
    if not isinstance(avgsoltrend, dict):
        return 0.0
        
    # Get the latest SoL value from channels
    channels = avgsoltrend.get('channels', {})
    if channels:
        # Get the channel with the highest index (most recent)
        latest_channel = None
        max_index = -1
        for channel_id, channel_data in channels.items():
            if isinstance(channel_data, dict) and 'index' in channel_data:
                if channel_data['index'] > max_index:
                    max_index = channel_data['index']
                    latest_channel = channel_data
        
        if latest_channel and 'values' in latest_channel:
            values = latest_channel['values']
            if values and len(values) > 0:
                # The last value in the array is the most recent
                return float(values[-1])
    
    return 0.0

def generate_sol_report(save_data, humans_only=True):
    """Generate standard of living report."""
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
            
        sol = get_country_standard_of_living(country)
        
        if sol > 0:
            report_data.append((tag, sol))
    
    # Sort by standard of living (highest first)
    report_data.sort(key=lambda x: -x[1])
    
    return report_data

def print_sol_report(report_data):
    """Print standard of living report."""
    print("STANDARD OF LIVING BY COUNTRY")
    print("=" * 40)
    print()
    
    if not report_data:
        print("No standard of living data found.")
        return
    
    print("| Rank | Country |    SoL |")
    print("|------|---------|--------|")
    
    for i, (tag, sol) in enumerate(report_data, 1):
        print(f"| {i:4} | {tag:7} | {sol:6.1f} |")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Victoria 3 standard of living reports')
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
    report_data = generate_sol_report(save_data, humans_only)
    
    # Generate output
    if args.output:
        with open(args.output, 'w') as f:
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            print_sol_report(report_data)
            sys.stdout = old_stdout
        print(f"Standard of living report saved to: {args.output}")
    else:
        print_sol_report(report_data)

if __name__ == '__main__':
    main()