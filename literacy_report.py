#!/usr/bin/env python3
"""
Victoria 3 Literacy Report

Analyzes and reports literacy rates for tracked countries.
"""

import json
import os
import sys
import argparse
from pathlib import Path

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

def analyze_literacy(save_data, filter_humans=False):
    """Analyze literacy rates for countries."""
    countries = save_data.get('country_manager', {}).get('database', {})
    
    # Load human countries if filtering
    human_countries = set()
    if filter_humans and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Collect literacy data
    literacy_data = []
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        tag = get_country_tag(countries, country_id)
        
        # Filter by human countries if requested
        if filter_humans and human_countries and tag not in human_countries:
            continue
        
        # Get literacy rate
        literacy = country.get('literacy', 0)
        
        # Handle different data formats
        if isinstance(literacy, (int, float)):
            literacy_value = float(literacy)
        elif isinstance(literacy, dict):
            # Handle time series format (like GDP data)
            if 'channels' in literacy:
                channels = literacy.get('channels', {})
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
                            literacy_value = float(values[-1])
                        else:
                            literacy_value = 0.0
                    else:
                        literacy_value = 0.0
                else:
                    literacy_value = 0.0
            elif 'value' in literacy:
                literacy_value = float(literacy['value'])
            else:
                literacy_value = 0.0
        else:
            literacy_value = 0.0
        
        literacy_data.append({
            'tag': tag,
            'literacy': literacy_value
        })
    
    # Sort by literacy rate (highest first)
    literacy_data.sort(key=lambda x: x['literacy'], reverse=True)
    
    return literacy_data

def print_literacy_report(literacy_data, save_data):
    """Print the literacy report."""
    # Get current date
    meta_data = save_data.get('meta_data', {})
    game_date = meta_data.get('game_date', 'Unknown')
    
    print("=" * 60)
    print("VICTORIA 3 LITERACY REPORT")
    print("=" * 60)
    print(f"Date: {game_date}")
    print(f"Countries analyzed: {len(literacy_data)}")
    print()
    
    # Print table header
    print(f"{'Rank':<6} {'Country':<8} {'Literacy Rate':<15}")
    print("-" * 40)
    
    # Print each country
    for rank, country in enumerate(literacy_data, 1):
        literacy_pct = country['literacy'] * 100
        print(f"{rank:<6} {country['tag']:<8} {literacy_pct:>6.1f}%")
    
    # Calculate simple average literacy
    if literacy_data:
        print()
        print("-" * 40)
        simple_avg = sum(c['literacy'] for c in literacy_data) / len(literacy_data)
        print(f"Average literacy: {simple_avg*100:.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 literacy report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('--humans', action='store_true', help='Only analyze human-controlled countries')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Find save file if not specified
    if not args.save_file:
        extracted_dir = Path("extracted-saves")
        json_files = list(extracted_dir.glob("*_extracted.json"))
        if not json_files:
            print("No extracted save files found")
            sys.exit(1)
        args.save_file = str(max(json_files, key=lambda x: x.stat().st_mtime))
        print(f"Using latest save: {args.save_file}")
    
    # Load save data
    print(f"Loading save data: {args.save_file}")
    save_data = load_save_data(args.save_file)
    
    # Analyze literacy
    literacy_data = analyze_literacy(save_data, filter_humans=args.humans)
    
    # Output report
    if args.output:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_literacy_report(literacy_data, save_data)
        
        with open(args.output, 'w') as f:
            f.write(output.getvalue())
        print(f"Report saved to: {args.output}")
    else:
        print_literacy_report(literacy_data, save_data)

if __name__ == '__main__':
    main()