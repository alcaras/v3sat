#!/usr/bin/env python3
"""
Foreign Building Ownership by Entity Type

Shows foreign ownership broken down by:
- Direct country ownership
- Company ownership (e.g., US Steel, Lee Wilson)
- Regional company HQ ownership  
- Financial district ownership
- Manor house ownership
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

def classify_owner_entity(building_type):
    """Classify the type of owning entity."""
    if not building_type:
        return "Unknown"
    
    building_type = building_type.lower()
    
    if 'financial_district' in building_type:
        return "Financial District"
    elif 'manor_house' in building_type:
        return "Manor House"
    elif 'regional_company' in building_type:
        return "Regional Company HQ"
    elif 'company' in building_type:
        return "Company"
    else:
        return "Other Building"

def analyze_ownership_by_entity(save_data):
    """Analyze foreign building ownership by entity type."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    ownership_data = save_data.get('building_ownership_manager', {}).get('database', {})
    
    # Load human countries
    human_countries = set()
    if os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Track: investor_country -> {target_country -> {entity_type -> {building_type -> levels}}}
    investments_by_entity = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    
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
        
        owned_building_type = format_building_type(building.get('building', 'unknown'))
        state_id = str(building.get('state'))
        if not state_id:
            continue
        
        state = states.get(state_id)
        if not state:
            continue
        
        target_country = state.get('country')
        if not target_country:
            continue
        
        # Determine the owner's country and entity type
        owner_country = None
        entity_type = "Unknown"
        entity_name = "Unknown"
        
        if 'country' in identity:
            # Direct country ownership
            owner_country = identity['country']
            entity_type = "Direct Government"
            entity_name = "Government"
        elif 'building' in identity:
            # Building-based ownership (company, financial district, etc.)
            owner_building_id = str(identity['building'])
            if owner_building_id in buildings:
                owner_building = buildings[owner_building_id]
                owner_building_type = owner_building.get('building', 'unknown')
                entity_type = classify_owner_entity(owner_building_type)
                entity_name = format_building_type(owner_building_type)
                
                owner_state_id = str(owner_building.get('state'))
                if owner_state_id in states:
                    owner_state = states[owner_state_id]
                    owner_country = owner_state.get('country')
        
        # Track foreign ownership
        if owner_country and target_country and owner_country != target_country:
            # Create entity key that includes both type and specific name
            entity_key = f"{entity_type} ({entity_name})" if entity_name != entity_type else entity_type
            
            investments_by_entity[owner_country][target_country][entity_key][owned_building_type] += levels
    
    return investments_by_entity, countries, human_countries

def print_ownership_by_entity(investments_by_entity, countries, human_countries, target_country=None):
    """Print foreign ownership broken down by entity type."""
    
    if target_country:
        # Focus on one country
        country_id = None
        for cid, country in countries.items():
            if isinstance(country, dict) and country.get('definition') == target_country:
                country_id = int(cid)
                break
        
        if not country_id:
            print(f"Country {target_country} not found!")
            return
        
        print("=" * 80)
        print(f"FOREIGN OWNERSHIP BREAKDOWN IN {target_country}")
        print("=" * 80)
        print()
        
        total_foreign_levels = 0
        investors_data = []
        
        for investor_id, targets in investments_by_entity.items():
            if country_id in targets:
                investor_tag = get_country_tag(countries, investor_id)
                entity_data = targets[country_id]
                investor_total = sum(sum(sum(bt.values()) for bt in ed.values()) for ed in entity_data.values())
                total_foreign_levels += investor_total
                investors_data.append((investor_tag, entity_data, investor_total))
        
        # Sort by total investment
        investors_data.sort(key=lambda x: -x[2])
        
        print(f"Total foreign-owned building levels in {target_country}: {total_foreign_levels}")
        print()
        
        for investor_tag, entity_data, investor_total in investors_data:
            print(f"{investor_tag}: {investor_total} levels")
            
            # Sort entities by total levels
            entity_totals = []
            for entity_key, building_types in entity_data.items():
                entity_total = sum(sum(bt.values()) for bt in building_types.values())
                entity_totals.append((entity_key, building_types, entity_total))
            
            entity_totals.sort(key=lambda x: -x[2])
            
            for entity_key, building_types, entity_total in entity_totals:
                print(f"  • {entity_key}: {entity_total} levels")
                
                # Show top building types for this entity
                all_buildings = defaultdict(int)
                for bt_dict in building_types.values():
                    for bt, levels in bt_dict.items():
                        all_buildings[bt] += levels
                
                sorted_buildings = sorted(all_buildings.items(), key=lambda x: -x[1])
                for building_type, levels in sorted_buildings[:3]:  # Top 3 building types
                    print(f"    - {building_type}: {levels}")
            print()
        
    else:
        # Show all countries
        print("=" * 80)
        print("FOREIGN INVESTMENTS BY ENTITY TYPE (HUMAN COUNTRIES)")
        print("=" * 80)
        print()
        
        # Sort countries by total foreign investment
        country_totals = []
        for investor_id, targets in investments_by_entity.items():
            investor_tag = get_country_tag(countries, investor_id)
            if human_countries and investor_tag not in human_countries:
                continue
            
            # Calculate total levels more carefully
            total_levels = 0
            for entity_data in targets.values():  # For each target country
                for entity_dict in entity_data.values():  # For each entity type
                    for building_dict in entity_dict.values():  # For each building type
                        if isinstance(building_dict, int):
                            total_levels += building_dict
                        elif isinstance(building_dict, dict):
                            total_levels += sum(building_dict.values())
            country_totals.append((investor_tag, investor_id, total_levels))
        
        country_totals.sort(key=lambda x: -x[2])
        
        for investor_tag, investor_id, total_levels in country_totals:
            print(f"{investor_tag}: {total_levels} building levels abroad")
            
            targets = investments_by_entity[investor_id]
            
            # Sort targets by total levels
            target_totals = []
            for target_id, entity_data in targets.items():
                target_tag = get_country_tag(countries, target_id)
                # Calculate target total more carefully
                target_total = 0
                for entity_dict in entity_data.values():  # For each entity type
                    for building_dict in entity_dict.values():  # For each building type
                        if isinstance(building_dict, int):
                            target_total += building_dict
                        elif isinstance(building_dict, dict):
                            target_total += sum(building_dict.values())
                target_totals.append((target_tag, entity_data, target_total))
            
            target_totals.sort(key=lambda x: -x[2])
            
            # Show top 5 targets
            for target_tag, entity_data, target_total in target_totals[:5]:
                print(f"  • {target_tag}: {target_total} levels")
                
                # Show breakdown by entity type
                entity_totals = []
                for entity_key, building_types in entity_data.items():
                    # Calculate entity total more carefully
                    entity_total = 0
                    for building_dict in building_types.values():
                        if isinstance(building_dict, int):
                            entity_total += building_dict
                        elif isinstance(building_dict, dict):
                            entity_total += sum(building_dict.values())
                    entity_totals.append((entity_key, entity_total))
                
                entity_totals.sort(key=lambda x: -x[1])
                
                for entity_key, entity_total in entity_totals:
                    print(f"    - {entity_key}: {entity_total}")
            
            if len(targets) > 5:
                remaining = len(targets) - 5
                print(f"    ... and {remaining} more countries")
            print()

def main():
    import sys
    import argparse
    import glob
    
    parser = argparse.ArgumentParser(description='Foreign ownership by entity type report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted save JSON file')
    parser.add_argument('--humans', action='store_true', help='Only show human-controlled countries')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--country', help='Focus on a specific country')
    
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
    
    print("Analyzing ownership by entity type...")
    investments_by_entity, countries, human_countries = analyze_ownership_by_entity(save_data)
    
    # Output handling
    if args.output:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            if args.country:
                print_ownership_by_entity(investments_by_entity, countries, human_countries, args.country)
            else:
                # Filter by humans if requested
                filtered_countries = human_countries if args.humans else set()
                print_ownership_by_entity(investments_by_entity, countries, filtered_countries, None)
        
        with open(args.output, 'w') as f:
            f.write(output.getvalue())
        print(f"Report saved to: {args.output}")
    else:
        if args.country:
            print_ownership_by_entity(investments_by_entity, countries, human_countries, args.country)
        else:
            # Filter by humans if requested
            filtered_countries = human_countries if args.humans else set()
            print_ownership_by_entity(investments_by_entity, countries, filtered_countries, None)

if __name__ == '__main__':
    main()