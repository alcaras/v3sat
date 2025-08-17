#!/usr/bin/env python3
"""
Detailed Foreign Building Ownership Report

Shows:
1. Building types owned abroad by each country
2. Foreign ownership within each country
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

def format_building_type(building_type):
    """Format building type for display."""
    if not building_type:
        return "Unknown"
    
    # Remove 'building_' prefix and format nicely
    clean = building_type.replace('building_', '').replace('_', ' ').title()
    
    # Handle specific cases
    replacements = {
        'Company Basic': 'Company -',
        'Company Us Steel': 'US Steel Company',
        'Company Lee Wilson': 'Lee Wilson Company',
        'Company Panama Company': 'Panama Company',
        'Company Suez Company': 'Suez Company',
        'Company Bolckow Vaughan': 'Bolckow Vaughan Company',
        'Regional Company': 'Regional Company -',
        'Gold Fields': 'Gold Mining',
        'Urban Center': 'Urban Center',
        'Trade Center': 'Trade Center',
        'Financial District': 'Financial District',
        'Manor House': 'Manor House'
    }
    
    for old, new in replacements.items():
        clean = clean.replace(old, new)
    
    return clean

def analyze_detailed_foreign_ownership(save_data):
    """Analyze detailed foreign building ownership."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    ownership_data = save_data.get('building_ownership_manager', {}).get('database', {})
    
    # Load human countries
    human_countries = set()
    if os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Track investments by type: investor_country -> {target_country -> {building_type -> levels}}
    investments_by_type = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    # Track foreign ownership within countries: target_country -> {investor_country -> {building_type -> levels}}
    foreign_owned_within = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for ownership_id, ownership in ownership_data.items():
        if not isinstance(ownership, dict):
            continue
        
        identity = ownership.get('identity', {})
        owned_building_id = str(ownership.get('building'))
        levels = ownership.get('levels', 0)
        
        if not (owned_building_id and levels > 0):
            continue
        
        # Get the owned building's details
        building = buildings.get(owned_building_id)
        if not building:
            continue
        
        building_type = building.get('building', 'unknown')
        state_id = str(building.get('state'))
        if not state_id:
            continue
        
        state = states.get(state_id)
        if not state:
            continue
        
        target_country = state.get('country')
        if not target_country:
            continue
        
        # Determine the owner's country and type
        owner_country = None
        ownership_method = "unknown"
        
        if 'country' in identity:
            # Direct country ownership
            owner_country = identity['country']
            ownership_method = "direct"
        elif 'building' in identity:
            # Building-based ownership (company, financial district, etc.)
            owner_building_id = str(identity['building'])
            if owner_building_id in buildings:
                owner_building = buildings[owner_building_id]
                ownership_method = format_building_type(owner_building.get('building', 'unknown'))
                owner_state_id = str(owner_building.get('state'))
                if owner_state_id in states:
                    owner_state = states[owner_state_id]
                    owner_country = owner_state.get('country')
        
        # Track foreign ownership
        if owner_country and target_country and owner_country != target_country:
            formatted_building_type = format_building_type(building_type)
            
            # Track investments by the owner
            investments_by_type[owner_country][target_country][formatted_building_type] += levels
            
            # Track foreign ownership within the target country
            foreign_owned_within[target_country][owner_country][formatted_building_type] += levels
    
    return investments_by_type, foreign_owned_within, countries, human_countries

def print_investments_abroad(investments_by_type, countries, human_countries):
    """Print foreign investments made by human countries."""
    print("=" * 80)
    print("FOREIGN INVESTMENTS BY HUMAN COUNTRIES")
    print("=" * 80)
    print()
    
    # Sort countries by total foreign investment
    country_totals = []
    for investor_id, targets in investments_by_type.items():
        investor_tag = get_country_tag(countries, investor_id)
        if human_countries and investor_tag not in human_countries:
            continue
        
        total_levels = sum(sum(building_types.values()) for building_types in targets.values())
        country_totals.append((investor_tag, investor_id, total_levels))
    
    country_totals.sort(key=lambda x: -x[2])
    
    for investor_tag, investor_id, total_levels in country_totals:
        print(f"{investor_tag}: {total_levels} building levels abroad")
        
        targets = investments_by_type[investor_id]
        
        # Sort targets by total levels
        sorted_targets = sorted(
            targets.items(), 
            key=lambda x: sum(x[1].values()), 
            reverse=True
        )
        
        for target_id, building_types in sorted_targets[:10]:  # Top 10 targets
            target_tag = get_country_tag(countries, target_id)
            target_total = sum(building_types.values())
            
            print(f"  • {target_tag}: {target_total} levels")
            
            # Show top building types
            sorted_types = sorted(building_types.items(), key=lambda x: -x[1])
            for building_type, levels in sorted_types[:5]:  # Top 5 building types
                print(f"    - {building_type}: {levels}")
        
        if len(targets) > 10:
            remaining = len(targets) - 10
            print(f"    ... and {remaining} more countries")
        print()

def print_foreign_ownership_within(foreign_owned_within, countries, human_countries):
    """Print foreign ownership within human countries."""
    print("=" * 80)
    print("FOREIGN OWNERSHIP WITHIN HUMAN COUNTRIES")
    print("=" * 80)
    print()
    
    # Sort countries by total foreign ownership within them
    country_totals = []
    for target_id, investors in foreign_owned_within.items():
        target_tag = get_country_tag(countries, target_id)
        if human_countries and target_tag not in human_countries:
            continue
        
        total_levels = sum(sum(building_types.values()) for building_types in investors.values())
        if total_levels > 0:
            country_totals.append((target_tag, target_id, total_levels))
    
    country_totals.sort(key=lambda x: -x[2])
    
    if not country_totals:
        print("No foreign ownership found within human countries.")
        return
    
    for target_tag, target_id, total_levels in country_totals:
        print(f"{target_tag}: {total_levels} building levels foreign-owned")
        
        investors = foreign_owned_within[target_id]
        
        # Sort investors by total levels
        sorted_investors = sorted(
            investors.items(), 
            key=lambda x: sum(x[1].values()), 
            reverse=True
        )
        
        for investor_id, building_types in sorted_investors:
            investor_tag = get_country_tag(countries, investor_id)
            investor_total = sum(building_types.values())
            
            print(f"  • {investor_tag}: {investor_total} levels")
            
            # Show top building types
            sorted_types = sorted(building_types.items(), key=lambda x: -x[1])
            for building_type, levels in sorted_types[:5]:  # Top 5 building types
                print(f"    - {building_type}: {levels}")
        print()

def main():
    import sys
    import argparse
    import glob
    
    parser = argparse.ArgumentParser(description='Detailed foreign building ownership report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted save JSON file')
    parser.add_argument('--humans', action='store_true', help='Only show human-controlled countries')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Find the save file
    if args.save_file:
        save_path = args.save_file
    else:
        # Find the latest save file
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
    
    print("Analyzing detailed foreign building ownership...")
    investments_by_type, foreign_owned_within, countries, human_countries = analyze_detailed_foreign_ownership(save_data)
    
    # Capture output if needed
    if args.output:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            if not args.humans or human_countries:
                print_investments_abroad(investments_by_type, countries, human_countries if args.humans else set())
                print_foreign_ownership_within(foreign_owned_within, countries, human_countries if args.humans else set())
        
        with open(args.output, 'w') as f:
            f.write(output.getvalue())
        print(f"Report saved to: {args.output}")
    else:
        # Print both reports
        if not args.humans or human_countries:
            print_investments_abroad(investments_by_type, countries, human_countries if args.humans else set())
            print_foreign_ownership_within(foreign_owned_within, countries, human_countries if args.humans else set())

if __name__ == '__main__':
    main()