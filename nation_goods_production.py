#!/usr/bin/env python3
"""
Victoria 3 Nation Goods Production Report V2
Shows actual production values for goods by human nations
Uses output_goods.value field for accurate production numbers
"""

import json
import sys
from pathlib import Path
import argparse
from collections import defaultdict

# Goods categories - these are for display organization only
GOODS_CATEGORIES = {
    'Staple Goods': [
        'clothes', 'fabric', 'fish', 'furniture', 'grain', 
        'groceries', 'merchant_marine', 'paper', 'wood'
    ],
    'Luxury Goods': [
        'automobiles', 'coffee', 'fine_art', 'fruit', 'gold',
        'liquor', 'luxury_clothes', 'luxury_furniture', 'meat',
        'opium', 'porcelain', 'radios', 'sugar', 'tea',
        'telephones', 'tobacco', 'wine'
    ],
    'Industrial Goods': [
        'clippers', 'coal', 'dye', 'engines', 'explosives',
        'fertilizer', 'glass', 'hardwood', 'iron', 'lead',
        'oil', 'rubber', 'silk', 'steamers', 'steel',
        'sulfur', 'tools'
    ],
    'Military Goods': [
        'aeroplanes', 'ammunition', 'artillery', 'ironclads',
        'manowars', 'small_arms', 'tanks'
    ]
}

# Map goods IDs to names (based on order in 00_goods.txt)
GOODS_ID_TO_NAME = {
    '0': 'ammunition',
    '1': 'small_arms', 
    '2': 'artillery',
    '3': 'tanks',
    '4': 'aeroplanes',
    '5': 'manowars',
    '6': 'ironclads',
    '7': 'grain',
    '8': 'fish',
    '9': 'fabric',
    '10': 'wood',
    '11': 'groceries',
    '12': 'clothes',
    '13': 'furniture',
    '14': 'paper',
    '15': 'services',
    '16': 'transportation',
    '17': 'electricity',
    '18': 'merchant_marine',
    '19': 'clippers',
    '20': 'steamers',
    '21': 'silk',
    '22': 'dye',
    '23': 'sulfur',
    '24': 'coal',
    '25': 'iron',
    '26': 'lead',
    '27': 'hardwood',
    '28': 'rubber',
    '29': 'oil',
    '30': 'engines',
    '31': 'steel',
    '32': 'glass',
    '33': 'fertilizer',
    '34': 'tools',
    '35': 'explosives',
    '36': 'porcelain',
    '37': 'meat',
    '38': 'fruit',
    '39': 'liquor',
    '40': 'wine',
    '41': 'coffee',
    '42': 'tea',
    '43': 'sugar',
    '44': 'tobacco',
    '45': 'opium',
    '46': 'automobiles',
    '47': 'telephones',
    '48': 'radios',
    '49': 'gold',
    '50': 'fine_art',
    '51': 'luxury_clothes',
    '52': 'luxury_furniture',
}

def load_humans_list(humans_file="humans.txt"):
    """Load list of human-controlled countries from file"""
    humans = []
    try:
        with open(humans_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    humans.append(line)
    except FileNotFoundError:
        print(f"Warning: {humans_file} not found. Will report on all countries.")
    return humans

def get_latest_save():
    """Get the latest extracted save file"""
    extracted_dir = Path("extracted-saves")
    if not extracted_dir.exists():
        return None
    
    json_files = list(extracted_dir.glob("*_extracted.json"))
    if not json_files:
        return None
    
    # Sort by modification time, get the most recent
    latest = max(json_files, key=lambda f: f.stat().st_mtime)
    return str(latest)

def extract_goods_production(json_file):
    """Extract actual goods production data from Victoria 3 save using output_goods"""
    
    print(f"Loading save file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get the game date
    game_date = data.get('date', 'Unknown')
    
    # Get country tags for each numeric ID
    country_tags = {}
    if 'country_manager' in data and 'database' in data['country_manager']:
        for country_id, country_info in data['country_manager']['database'].items():
            if isinstance(country_info, dict) and 'definition' in country_info:
                country_tags[country_id] = country_info['definition']
    
    # Get states to map to countries (converting state IDs to strings)
    state_to_country = {}
    if 'states' in data and 'database' in data['states']:
        for state_id, state_info in data['states']['database'].items():
            if isinstance(state_info, dict) and 'country' in state_info:
                # Store both string and numeric versions of state ID for lookup
                state_to_country[state_id] = state_info['country']
                state_to_country[int(state_id)] = state_info['country']
    
    # Calculate goods production by country and good type using actual output_goods
    goods_production = defaultdict(lambda: defaultdict(float))
    
    if 'building_manager' in data and 'database' in data['building_manager']:
        buildings = data['building_manager']['database']
        
        for building_id, building_info in buildings.items():
            if not isinstance(building_info, dict):
                continue
            
            # Get the building's state
            state_id = building_info.get('state')
            if state_id not in state_to_country:
                continue
            
            country_id = state_to_country[state_id]
            # Convert country_id to string for lookup in country_tags
            country_tag = country_tags.get(str(country_id), str(country_id))
            
            # Get actual production from output_goods
            output_goods = building_info.get('output_goods', {})
            if isinstance(output_goods, dict) and 'goods' in output_goods:
                goods = output_goods['goods']
                for good_id, good_data in goods.items():
                    if isinstance(good_data, dict) and 'value' in good_data:
                        # Map good ID to name
                        good_name = GOODS_ID_TO_NAME.get(good_id, f'unknown_{good_id}')
                        # Add production value (this is weekly production value in pounds)
                        production_value = good_data['value']
                        goods_production[good_name][country_tag] += production_value
    
    return {
        'date': game_date,
        'production': goods_production
    }

def print_report(goods_data, humans_list=None):
    """Print goods production report organized by category"""
    
    production = goods_data['production']
    
    print(f"\nVictoria 3 Nation Goods Production Report")
    print(f"Date: {goods_data['date']}")
    print(f"(Values shown are weekly production in £)")
    print("=" * 80)
    
    for category, goods_list in GOODS_CATEGORIES.items():
        print(f"\n{category}")
        print("-" * 60)
        
        category_has_production = False
        
        for good in goods_list:
            if good not in production:
                continue
            
            good_production = production[good]
            
            # Filter by humans if list provided
            if humans_list:
                filtered_production = {k: v for k, v in good_production.items() if k in humans_list}
            else:
                filtered_production = good_production
            
            if not filtered_production:
                continue
            
            category_has_production = True
            
            # Sort by production (descending)
            sorted_countries = sorted(filtered_production.items(), key=lambda x: x[1], reverse=True)
            
            # Format good name for display
            display_name = good.replace('_', ' ').title()
            print(f"\n  {display_name}:")
            
            for rank, (country, prod) in enumerate(sorted_countries, 1):
                # Format production value
                if prod >= 1000:
                    prod_str = f"{prod/1000:>8.1f}K"
                else:
                    prod_str = f"{prod:>8.1f} "
                print(f"    {rank:2}. {country:<6} {prod_str}")
        
        if not category_has_production:
            print("  (No production in this category)")

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 goods production report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('--all', action='store_true', help='Include all countries (not just humans)')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Determine which save file to use
    if args.save_file:
        json_file = args.save_file
    else:
        json_file = get_latest_save()
        if not json_file:
            print("Error: No extracted save files found in extracted-saves/")
            print("Please run extract_save.py first to extract a save file.")
            sys.exit(1)
    
    # Check if file exists
    if not Path(json_file).exists():
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    # Load humans list unless --all specified
    humans_list = None if args.all else load_humans_list()
    
    # Extract data
    goods_data = extract_goods_production(json_file)
    
    # Print or save report
    if args.output:
        # Redirect stdout to file
        import sys
        original_stdout = sys.stdout
        with open(args.output, 'w') as f:
            sys.stdout = f
            print_report(goods_data, humans_list)
        sys.stdout = original_stdout
        print(f"Report saved to: {args.output}")
    else:
        print_report(goods_data, humans_list)

if __name__ == "__main__":
    main()