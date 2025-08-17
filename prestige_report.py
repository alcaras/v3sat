#!/usr/bin/env python3
"""
Victoria 3 Prestige Report

Analyzes and reports prestige levels for tracked countries.
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

def get_gdp_value(save_data, country_id):
    """Get the current GDP value for a country."""
    countries = save_data.get('country_manager', {}).get('database', {})
    country = countries.get(str(country_id), {})
    
    if isinstance(country, dict):
        gdp_data = country.get('gdp', {})
        if gdp_data:
            channels = gdp_data.get('channels', {})
            if channels:
                # Get latest GDP value
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
                        return float(values[-1])
    return 0.0

def analyze_prestige(save_data, filter_humans=False):
    """Analyze prestige levels for countries."""
    countries = save_data.get('country_manager', {}).get('database', {})
    
    # Load human countries if filtering
    human_countries = set()
    if filter_humans and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Collect prestige data
    prestige_data = []
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        tag = get_country_tag(countries, country_id)
        
        # Filter by human countries if requested
        if filter_humans and human_countries and tag not in human_countries:
            continue
        
        # Get prestige value
        prestige_raw = country.get('prestige', 0)
        
        # Handle different data formats
        if isinstance(prestige_raw, dict):
            # Time series format
            if 'channels' in prestige_raw:
                channels = prestige_raw.get('channels', {})
                if channels:
                    # Get channel 0 which typically has the current value
                    channel_0 = channels.get('0', {})
                    values = channel_0.get('values', [])
                    prestige_value = float(values[-1]) if values else 0.0
                else:
                    prestige_value = 0.0
            elif 'value' in prestige_raw:
                prestige_value = float(prestige_raw['value'])
            else:
                prestige_value = 0.0
        elif isinstance(prestige_raw, (int, float)):
            prestige_value = float(prestige_raw)
        else:
            prestige_value = 0.0
        
        # Get GDP value for additional context
        gdp = get_gdp_value(save_data, int(country_id))
        
        # Get prestige rank (if available)
        rank = country.get('prestige_rank', 0)
        
        # Get country power status based on prestige rank
        # Victoria 3 uses prestige thresholds for power status
        # Great Powers are top 8 by prestige
        # Major Powers are roughly 9-16
        # Regional Powers are roughly 17-32
        # Rest are Minor Powers
        
        # We'll determine this later based on ranking
        power_status = "TBD"
        
        prestige_data.append({
            'tag': tag,
            'prestige': prestige_value,
            'gdp': gdp,
            'rank': rank,
            'power_status': power_status
        })
    
    # Sort by prestige (highest first)
    prestige_data.sort(key=lambda x: x['prestige'], reverse=True)
    
    # Assign ranks and power status based on ranking
    for i, country in enumerate(prestige_data, 1):
        if country['rank'] == 0:
            country['rank'] = i
        
        # Determine power status based on rank
        if i <= 8:
            country['power_status'] = "Great Power"
        elif i <= 16:
            country['power_status'] = "Major Power"
        elif i <= 32:
            country['power_status'] = "Regional Power"
        else:
            country['power_status'] = "Minor Power"
    
    return prestige_data

def print_prestige_report(prestige_data, save_data):
    """Print the prestige report."""
    # Get current date
    meta_data = save_data.get('meta_data', {})
    game_date = meta_data.get('game_date', 'Unknown')
    
    print("=" * 70)
    print("VICTORIA 3 PRESTIGE REPORT")
    print("=" * 70)
    print(f"Date: {game_date}")
    print(f"Countries analyzed: {len(prestige_data)}")
    print()
    
    # Separate by power status
    great_powers = [c for c in prestige_data if c['power_status'] == "Great Power"]
    major_powers = [c for c in prestige_data if c['power_status'] == "Major Power"]
    regional_powers = [c for c in prestige_data if c['power_status'] == "Regional Power"]
    minor_powers = [c for c in prestige_data if c['power_status'] == "Minor Power"]
    
    # Print Great Powers
    if great_powers:
        print("GREAT POWERS")
        print("-" * 70)
        print(f"{'Rank':<6} {'Country':<8} {'Prestige':>10} {'Status':<15}")
        print("-" * 70)
        for country in great_powers[:8]:  # Top 8 are great powers
            print(f"{country['rank']:<6} {country['tag']:<8} {country['prestige']:>10.0f} {country['power_status']:<15}")
        print()
    
    # Print Major Powers
    if major_powers:
        print("MAJOR POWERS")
        print("-" * 70)
        print(f"{'Rank':<6} {'Country':<8} {'Prestige':>10} {'Status':<15}")
        print("-" * 70)
        for country in major_powers[:8]:
            print(f"{country['rank']:<6} {country['tag']:<8} {country['prestige']:>10.0f} {country['power_status']:<15}")
        print()
    
    # Print all countries in simple table
    print("ALL COUNTRIES BY PRESTIGE")
    print("-" * 70)
    print(f"{'Rank':<6} {'Country':<8} {'Prestige':>10} {'Power Status':<15}")
    print("-" * 70)
    
    for country in prestige_data:
        # Add visual indicator for top powers
        indicator = ""
        if country['rank'] <= 8:
            indicator = " ★"  # Great Power
        elif country['rank'] <= 16:
            indicator = " ☆"  # Major Power
        
        print(f"{country['rank']:<6} {country['tag']:<8} {country['prestige']:>10.0f} {country['power_status']:<15}{indicator}")
    
    # Print prestige and GDP table
    print()
    print("PRESTIGE AND GDP VALUES")
    print("-" * 70)
    print(f"{'Rank':<6} {'Country':<8} {'Prestige':>10} {'GDP (£M)':>12}")
    print("-" * 70)
    
    for country in prestige_data:
        gdp_millions = country['gdp'] / 1_000_000 if country['gdp'] > 0 else 0
        print(f"{country['rank']:<6} {country['tag']:<8} {country['prestige']:>10.0f} {gdp_millions:>12.1f}")
    
    # Calculate statistics
    if prestige_data:
        print()
        print("-" * 70)
        print("STATISTICS")
        print("-" * 70)
        
        total_prestige = sum(c['prestige'] for c in prestige_data)
        avg_prestige = total_prestige / len(prestige_data)
        max_prestige = max(c['prestige'] for c in prestige_data)
        min_prestige = min(c['prestige'] for c in prestige_data)
        
        print(f"Total prestige: {total_prestige:,.0f}")
        print(f"Average prestige: {avg_prestige:,.0f}")
        print(f"Highest prestige: {max_prestige:,.0f} ({prestige_data[0]['tag']})")
        print(f"Lowest prestige: {min_prestige:,.0f}")
        
        # Prestige distribution
        top_8_prestige = sum(c['prestige'] for c in prestige_data[:8])
        top_8_pct = (top_8_prestige / total_prestige * 100) if total_prestige > 0 else 0
        print(f"Top 8 countries control: {top_8_pct:.1f}% of world prestige")

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 prestige report')
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
    
    # Analyze prestige
    prestige_data = analyze_prestige(save_data, filter_humans=args.humans)
    
    # Output report
    if args.output:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_prestige_report(prestige_data, save_data)
        
        with open(args.output, 'w') as f:
            f.write(output.getvalue())
        print(f"Report saved to: {args.output}")
    else:
        print_prestige_report(prestige_data, save_data)

if __name__ == '__main__':
    main()