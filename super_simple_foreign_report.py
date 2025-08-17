#!/usr/bin/env python3
"""
Super Simple Foreign Ownership Report

Shows just the totals:
1. Building levels each country owns abroad
2. Building levels owned by foreigners in each country
"""

import json
import os
from collections import defaultdict

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

def analyze_simple_foreign_ownership(save_data):
    """Analyze foreign building ownership - simple totals only."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    ownership_data = save_data.get('building_ownership_manager', {}).get('database', {})
    
    # Load human countries
    human_countries = set()
    if os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Track: country -> levels_owned_abroad
    levels_owned_abroad = defaultdict(int)
    
    # Track: country -> levels_foreign_owned_within
    levels_foreign_owned_within = defaultdict(int)
    
    for ownership_id, ownership in ownership_data.items():
        if not isinstance(ownership, dict):
            continue
        
        identity = ownership.get('identity', {})
        owned_building_id = str(ownership.get('building'))
        levels = ownership.get('levels', 0)
        
        if not (owned_building_id and levels > 0):
            continue
        
        # Get the owned building's location
        building = buildings.get(owned_building_id)
        if not building:
            continue
        
        state_id = str(building.get('state'))
        if not state_id:
            continue
        
        state = states.get(state_id)
        if not state:
            continue
        
        target_country = state.get('country')
        if not target_country:
            continue
        
        # Determine the owner's country
        owner_country = None
        
        if 'country' in identity:
            # Direct country ownership
            owner_country = identity['country']
        elif 'building' in identity:
            # Building-based ownership (company, financial district, etc.)
            owner_building_id = str(identity['building'])
            if owner_building_id in buildings:
                owner_building = buildings[owner_building_id]
                owner_state_id = str(owner_building.get('state'))
                if owner_state_id in states:
                    owner_state = states[owner_state_id]
                    owner_country = owner_state.get('country')
        
        # Track foreign ownership
        if owner_country and target_country and owner_country != target_country:
            levels_owned_abroad[owner_country] += levels
            levels_foreign_owned_within[target_country] += levels
    
    return levels_owned_abroad, levels_foreign_owned_within, countries, human_countries

def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Super simple foreign ownership report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted save JSON file')
    parser.add_argument('--humans', action='store_true', help='Only show human-controlled countries')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Find the save file
    if args.save_file:
        save_path = args.save_file
    else:
        # Find the latest save file
        import glob
        saves = glob.glob('extracted-saves/*_extracted.json')
        if not saves:
            print("Error: No extracted save files found")
            sys.exit(1)
        save_path = max(saves, key=os.path.getmtime)
    
    if not os.path.exists(save_path):
        print(f"Error: Save file not found: {save_path}")
        sys.exit(1)
    
    print(f"Loading save data from {save_path}...")
    save_data = load_save_data(save_path)
    
    print("Analyzing foreign building ownership...")
    levels_owned_abroad, levels_foreign_owned_within, countries, human_countries = analyze_simple_foreign_ownership(save_data)
    
    # Prepare output
    output_lines = []
    
    output_lines.append("=" * 50)
    output_lines.append("BUILDING LEVELS OWNED ABROAD")
    output_lines.append("=" * 50)
    
    # Sort by levels owned abroad
    owned_abroad_data = []
    for country_id, levels in levels_owned_abroad.items():
        country_tag = get_country_tag(countries, country_id)
        if args.humans and human_countries and country_tag not in human_countries:
            continue
        owned_abroad_data.append((country_tag, levels))
    
    owned_abroad_data.sort(key=lambda x: -x[1])
    
    for country_tag, levels in owned_abroad_data:
        output_lines.append(f"{country_tag}: {levels} building levels abroad")
    
    output_lines.append("")
    output_lines.append("=" * 50)
    output_lines.append("BUILDING LEVELS OWNED BY FOREIGNERS")
    output_lines.append("=" * 50)
    
    # Sort by foreign ownership within
    foreign_owned_data = []
    for country_id, levels in levels_foreign_owned_within.items():
        country_tag = get_country_tag(countries, country_id)
        if args.humans and human_countries and country_tag not in human_countries:
            continue
        if levels > 0:  # Only show countries with foreign ownership
            foreign_owned_data.append((country_tag, levels))
    
    foreign_owned_data.sort(key=lambda x: -x[1])
    
    for country_tag, levels in foreign_owned_data:
        output_lines.append(f"{country_tag}: {levels} building levels foreign-owned")
    
    # Output to file or console
    output_text = '\n'.join(output_lines)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
        print(f"Report saved to: {args.output}")
    else:
        print(output_text)

if __name__ == '__main__':
    main()