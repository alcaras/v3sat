#!/usr/bin/env python3
"""
True GDP-Based Foreign Ownership Analysis

Uses Victoria 3's actual GDP calculation formula discovered in Garibaldi:
GDP = (Credit Limit - Min Credit Base - Building Cash Reserves) / Credit Scale Factor

This should give us the most accurate foreign ownership percentages.
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

def calculate_true_gdp(save_data):
    """Calculate GDP using Victoria 3's actual formula from Garibaldi."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    
    # Victoria 3's economic defines (from Garibaldi/defines)
    min_credit_base = 100000.0  # COUNTRY_MIN_CREDIT_BASE = £100K
    credit_scale_factor = 0.5   # COUNTRY_MIN_CREDIT_SCALED = 0.5 (50% of GDP)
    
    # First, calculate building cash reserves for each country
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
    
    # Calculate GDP for each country
    country_gdps = {}
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
            
        budget = country.get('budget', {})
        credit = float(budget.get('credit', 0))
        
        if credit <= 0:
            continue
            
        building_reserves = country_building_reserves.get(int(country_id), 0)
        
        # Victoria 3's GDP formula: GDP = (Credit - Base - Reserves) / Scale
        calculated_gdp = (credit - min_credit_base - building_reserves) / credit_scale_factor
        
        if calculated_gdp > 0:
            country_gdps[int(country_id)] = calculated_gdp
    
    return country_gdps

def analyze_foreign_ownership_true_gdp(save_data):
    """Analyze foreign ownership using true GDP calculations."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    ownership_data = save_data.get('building_ownership_manager', {}).get('database', {})
    
    # Get true GDP values
    print("Calculating true GDP values using Victoria 3's formula...")
    country_gdps = calculate_true_gdp(save_data)
    
    # Load human countries
    human_countries = set()
    if os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Track foreign investments: investor_country -> {target_country -> building_value}
    foreign_investments = defaultdict(lambda: defaultdict(float))
    
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
        
        # Get building location
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
        
        # Calculate building value using cash reserves and profitability
        building_levels = building.get('levels', 1)
        ownership_ratio = levels / building_levels if building_levels > 0 else 0
        
        # Use cash reserves as a proxy for building value
        cash_reserves = building.get('cash_reserves', 0)
        profit_after_reserves = building.get('profit_after_reserves', 0)
        
        # Estimate annual building value
        if cash_reserves > 0:
            # Cash reserves represent stored economic value
            building_value = cash_reserves * ownership_ratio
        elif profit_after_reserves > 0:
            # Use annual profit as value proxy
            annual_profit = profit_after_reserves * 52 * ownership_ratio
            building_value = annual_profit * 10  # 10x profit multiplier
        else:
            # Basic construction value estimate
            building_value = levels * 50000  # £50K per level
        
        # Track foreign ownership
        if owner_country and target_country and owner_country != target_country:
            foreign_investments[owner_country][target_country] += building_value
    
    return foreign_investments, country_gdps, countries, human_countries

def print_true_gdp_analysis(foreign_investments, country_gdps, countries, human_countries, filter_humans=False):
    """Print foreign ownership analysis using true GDP values."""
    print("=" * 80)
    print("TRUE GDP-BASED FOREIGN OWNERSHIP ANALYSIS")
    print("=" * 80)
    print()
    print("Using Victoria 3's actual GDP formula:")
    print("GDP = (Credit Limit - £100K Base - Building Cash Reserves) / 0.5")
    print()
    
    # Compare with stored GDP values first
    print("GDP COMPARISON (True Formula vs Game Storage)")
    print("-" * 50)
    for country_id, true_gdp in sorted(country_gdps.items(), key=lambda x: -x[1])[:12]:
        country_tag = get_country_tag(countries, country_id)
        if filter_humans and human_countries and country_tag not in human_countries:
            continue
            
        # Get stored GDP
        country = countries.get(str(country_id), {})
        stored_gdp = 0
        gdp_data = country.get('gdp', {})
        if gdp_data:
            channels = gdp_data.get('channels', {})
            if channels:
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
                        stored_gdp = float(values[-1])
        
        accuracy = (min(true_gdp, stored_gdp) / max(true_gdp, stored_gdp) * 100) if stored_gdp > 0 else 0
        print(f"{country_tag}: True=${true_gdp/1e6:.1f}M vs Stored=${stored_gdp/1e6:.1f}M ({accuracy:.1f}% match)")
    
    print()
    print("FOREIGN OWNERSHIP ANALYSIS")
    print("-" * 50)
    
    # Analyze each country's foreign investments and ownership
    for country_id in sorted(country_gdps.keys(), key=lambda x: country_gdps[x], reverse=True):
        country_tag = get_country_tag(countries, country_id)
        if filter_humans and human_countries and country_tag not in human_countries:
            continue
            
        country_gdp = country_gdps[country_id]
        
        # Calculate investments abroad
        investments_abroad = foreign_investments.get(country_id, {})
        total_invested_abroad = sum(investments_abroad.values())
        
        # Calculate foreign ownership within this country
        foreign_owned_within = 0
        for investor_id, targets in foreign_investments.items():
            if country_id in targets:
                foreign_owned_within += targets[country_id]
        
        print(f"\n{country_tag}:")
        print(f"  GDP: ${country_gdp/1e6:.1f}M")
        
        if total_invested_abroad > 0:
            abroad_pct = (total_invested_abroad / country_gdp) * 100
            print(f"  Investments abroad: ${total_invested_abroad/1e6:.1f}M ({abroad_pct:.1f}% of GDP)")
            
            # Show all human country targets first, then top 3 non-human
            human_targets = []
            other_targets = []
            
            for target_id, value in investments_abroad.items():
                target_tag = get_country_tag(countries, target_id)
                if target_tag in human_countries:
                    human_targets.append((target_id, value, target_tag))
                else:
                    other_targets.append((target_id, value, target_tag))
            
            # Sort both lists by value
            human_targets.sort(key=lambda x: -x[1])
            other_targets.sort(key=lambda x: -x[1])
            
            # Print all human targets
            if human_targets:
                print("    Human countries:")
                for target_id, value, target_tag in human_targets:
                    target_gdp = country_gdps.get(target_id, 0)
                    if target_gdp > 0:
                        target_pct = (value / target_gdp) * 100
                        print(f"      • {target_tag}: ${value/1e6:.1f}M ({target_pct:.1f}% of {target_tag}'s GDP)")
            
            # Print top 3 non-human targets if any
            if other_targets:
                print("    Other major targets (top 3):")
                for target_id, value, target_tag in other_targets[:3]:
                    target_gdp = country_gdps.get(target_id, 0)
                    if target_gdp > 0:
                        target_pct = (value / target_gdp) * 100
                        print(f"      • {target_tag}: ${value/1e6:.1f}M ({target_pct:.1f}% of {target_tag}'s GDP)")
        
        if foreign_owned_within > 0:
            within_pct = (foreign_owned_within / country_gdp) * 100
            print(f"  Foreign-owned: ${foreign_owned_within/1e6:.1f}M ({within_pct:.1f}% of GDP)")

def main():
    import sys
    import argparse
    import glob
    
    parser = argparse.ArgumentParser(description='True GDP-based foreign ownership analysis')
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
    
    print("Analyzing foreign ownership using true GDP calculation...")
    foreign_investments, country_gdps, countries, human_countries = analyze_foreign_ownership_true_gdp(save_data)
    
    # Capture output for file writing if needed
    if args.output:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_true_gdp_analysis(foreign_investments, country_gdps, countries, human_countries, filter_humans=args.humans)
        
        with open(args.output, 'w') as f:
            f.write(output.getvalue())
        print(f"Report saved to: {args.output}")
    else:
        print_true_gdp_analysis(foreign_investments, country_gdps, countries, human_countries, filter_humans=args.humans)

if __name__ == '__main__':
    main()