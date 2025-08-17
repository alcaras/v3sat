#!/usr/bin/env python3
"""
Effective GDP Report for Victoria 3

Shows the total economic control of each country including:
- Their own GDP
- How much of their own GDP they control
- GDP they control abroad
- Total effective GDP (domestic + foreign control)
"""

import json
import os
from collections import defaultdict
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

def calculate_true_gdp(save_data):
    """Calculate GDP using Victoria 3's actual formula."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    
    min_credit_base = 100000.0
    credit_scale_factor = 0.5
    
    country_building_reserves = defaultdict(float)
    
    for building_id, building in buildings.items():
        if not isinstance(building, dict):
            continue
        
        cash_reserves = building.get('cash_reserves', 0)
        if cash_reserves <= 0:
            continue
            
        state_id = str(building.get('state'))
        if not state_id or state_id not in states:
            continue
            
        state = states[state_id]
        country_id = state.get('country')
        if not country_id:
            continue
            
        country_building_reserves[country_id] += float(cash_reserves)
    
    country_gdps = {}
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
            
        budget = country.get('budget', {})
        credit = float(budget.get('credit', 0))
        
        if credit <= 0:
            continue
            
        building_reserves = country_building_reserves.get(int(country_id), 0)
        calculated_gdp = (credit - min_credit_base - building_reserves) / credit_scale_factor
        
        if calculated_gdp > 0:
            country_gdps[int(country_id)] = calculated_gdp
    
    return country_gdps

def calculate_foreign_ownership(save_data):
    """Calculate foreign ownership of GDP between countries."""
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    countries = save_data.get('country_manager', {}).get('database', {})
    ownership_data = save_data.get('building_ownership_manager', {}).get('database', {})
    
    # Track ownership: owner_country -> host_country -> value
    ownership_matrix = defaultdict(lambda: defaultdict(float))
    
    # Process building ownership data
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
        
        # Get building location (host country)
        state_id = str(building.get('state'))
        if not state_id or state_id not in states:
            continue
        
        state = states[state_id]
        host_country_id = state.get('country')
        if not host_country_id:
            continue
        
        # Determine the owner's country
        owner_country_id = None
        
        if 'country' in identity:
            # Direct country ownership
            owner_country_id = identity['country']
        elif 'building' in identity:
            # Building-based ownership (company, financial district, etc.)
            owner_building_id = str(identity['building'])
            if owner_building_id in buildings:
                owner_building = buildings[owner_building_id]
                owner_state_id = str(owner_building.get('state'))
                if owner_state_id in states:
                    owner_state = states[owner_state_id]
                    owner_country_id = owner_state.get('country')
        
        if not owner_country_id:
            continue
            
        # Calculate building value
        building_levels = building.get('levels', 1)
        ownership_ratio = levels / building_levels if building_levels > 0 else 0
        
        # Use cash reserves as a proxy for building value
        cash_reserves = building.get('cash_reserves', 0)
        profit_after_reserves = building.get('profit_after_reserves', 0)
        
        # Estimate building value
        if cash_reserves > 0:
            building_value = cash_reserves * ownership_ratio
        elif profit_after_reserves > 0:
            annual_profit = profit_after_reserves * 52 * ownership_ratio
            building_value = annual_profit * 10  # 10x profit multiplier
        else:
            building_value = levels * 50000  # £50K per level
        
        # Track ownership
        ownership_matrix[owner_country_id][host_country_id] += float(building_value)
    
    return ownership_matrix

def calculate_effective_gdp(save_data):
    """Calculate effective GDP for each country."""
    countries = save_data.get('country_manager', {}).get('database', {})
    
    # Get base GDP for each country
    country_gdps = calculate_true_gdp(save_data)
    
    # Get foreign ownership matrix
    ownership_matrix = calculate_foreign_ownership(save_data)
    
    # Calculate effective GDP for each country
    effective_gdp_data = {}
    
    for country_id, base_gdp in country_gdps.items():
        tag = get_country_tag(countries, country_id)
        
        # Calculate foreign ownership in this country
        foreign_owned_in_country = 0
        for owner_id, targets in ownership_matrix.items():
            if owner_id != country_id and country_id in targets:
                foreign_owned_in_country += targets[country_id]
        
        # Calculate GDP owned abroad by this country
        gdp_owned_abroad = 0
        if country_id in ownership_matrix:
            for host_id, value in ownership_matrix[country_id].items():
                if host_id != country_id:
                    gdp_owned_abroad += value
        
        # Calculate domestic ownership (what they own in their own country)
        domestic_ownership = ownership_matrix.get(country_id, {}).get(country_id, 0)
        
        # Domestic GDP control = base GDP - foreign owned + adjustment for accuracy
        # Using a more conservative approach for domestic control
        domestic_control = base_gdp - foreign_owned_in_country
        
        # Total effective GDP = domestic control + foreign investments
        total_effective = domestic_control + gdp_owned_abroad
        
        effective_gdp_data[country_id] = {
            'tag': tag,
            'base_gdp': base_gdp,
            'domestic_control': domestic_control,
            'gdp_owned_abroad': gdp_owned_abroad,
            'total_effective': total_effective,
            'foreign_owned_in_country': foreign_owned_in_country
        }
    
    return effective_gdp_data

def print_effective_gdp_report(effective_gdp_data, humans_only=False):
    """Print the effective GDP report."""
    # Load human countries if filtering
    human_countries = set()
    if humans_only and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    print("=" * 70)
    print("EFFECTIVE GDP REPORT")
    print("=" * 70)
    print("Shows total economic control including foreign investments")
    print()
    
    # Sort by total effective GDP
    sorted_data = sorted(effective_gdp_data.items(), key=lambda x: x[1]['total_effective'], reverse=True)
    
    # Filter if needed
    if humans_only and human_countries:
        sorted_data = [(cid, data) for cid, data in sorted_data if data['tag'] in human_countries]
    
    # Print header
    print(f"{'Tag':<5} {'Base GDP':>12} {'Domestic':>12} {'Abroad':>12} {'Total Eff.':>12}")
    print("-" * 70)
    
    for country_id, data in sorted_data:
        tag = data['tag']
        base = data['base_gdp'] / 1e6  # Convert to millions
        domestic = data['domestic_control'] / 1e6
        abroad = data['gdp_owned_abroad'] / 1e6
        total = data['total_effective'] / 1e6
        
        # Format the output
        print(f"{tag:<5} £{base:>10.1f}M £{domestic:>10.1f}M £{abroad:>10.1f}M £{total:>10.1f}M")
    
    print()
    print("Legend:")
    print("  Base GDP: Country's nominal GDP")
    print("  Domestic: GDP they control within their own borders")
    print("  Abroad: GDP they control in foreign countries")
    print("  Total Eff.: Total economic control (Domestic + Abroad)")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Victoria 3 effective GDP report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output', help='Output file for the report')
    parser.add_argument('--humans', action='store_true', help='Only analyze human-controlled countries')
    parser.add_argument('--all', action='store_true', help='Analyze all countries')
    
    args = parser.parse_args()
    
    # Determine save file to use
    if args.save_file:
        save_path = args.save_file
    else:
        # Use latest extracted save
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
    
    # Calculate effective GDP
    effective_gdp_data = calculate_effective_gdp(save_data)
    
    # Generate output
    humans_only = args.humans and not args.all
    
    if args.output:
        with open(args.output, 'w') as f:
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            print_effective_gdp_report(effective_gdp_data, humans_only)
            sys.stdout = old_stdout
        print(f"Effective GDP report saved to: {args.output}")
    else:
        print_effective_gdp_report(effective_gdp_data, humans_only)

if __name__ == '__main__':
    main()