#!/usr/bin/env python3
"""
Session Comparison Report for Victoria 3

Compares GDP and other metrics between two sessions, showing growth and changes.
"""

import json
import os
import argparse

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
    
    # Victoria 3's economic defines
    min_credit_base = 100000.0
    credit_scale_factor = 0.5
    
    # Calculate building cash reserves for each country
    from collections import defaultdict
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
        calculated_gdp = (credit - min_credit_base - building_reserves) / credit_scale_factor
        
        if calculated_gdp > 0:
            country_gdps[int(country_id)] = calculated_gdp
    
    return country_gdps, countries

def calculate_effective_gdp(save_data):
    """Calculate effective GDP (total economic control) for each country."""
    from collections import defaultdict
    
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    ownership_data = save_data.get('building_ownership_manager', {}).get('database', {})
    
    # First calculate base GDP
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
    
    # Calculate base GDP for each country
    country_base_gdps = {}
    
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
            country_base_gdps[int(country_id)] = calculated_gdp
    
    # Calculate foreign ownership matrix
    ownership_matrix = defaultdict(lambda: defaultdict(float))
    
    for ownership_id, ownership in ownership_data.items():
        if not isinstance(ownership, dict):
            continue
        
        identity = ownership.get('identity', {})
        owned_building_id = str(ownership.get('building'))
        levels = ownership.get('levels', 0)
        
        if not (owned_building_id and levels > 0):
            continue
        
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
        
        # Determine owner country
        owner_country_id = None
        if 'country' in identity:
            owner_country_id = identity['country']
        elif 'building' in identity:
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
        
        cash_reserves = building.get('cash_reserves', 0)
        profit_after_reserves = building.get('profit_after_reserves', 0)
        
        if cash_reserves > 0:
            building_value = cash_reserves * ownership_ratio
        elif profit_after_reserves > 0:
            annual_profit = profit_after_reserves * 52 * ownership_ratio
            building_value = annual_profit * 10
        else:
            building_value = levels * 50000
        
        ownership_matrix[owner_country_id][host_country_id] += float(building_value)
    
    # Calculate effective GDP for each country
    country_effective_gdps = {}
    
    for country_id, base_gdp in country_base_gdps.items():
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
        
        # Effective GDP = domestic control + foreign investments
        domestic_control = base_gdp - foreign_owned_in_country
        total_effective = domestic_control + gdp_owned_abroad
        
        country_effective_gdps[int(country_id)] = total_effective
    
    return country_effective_gdps, countries

def calculate_construction_usage(save_data):
    """Calculate construction usage from save data."""
    countries = save_data.get('country_manager', {}).get('database', {})
    construction_usage = {}
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
            
        used_construction = 0
        
        # Check government construction queue
        if 'government_queue' in country:
            gov_queue = country['government_queue'].get('construction_elements', [])
            if isinstance(gov_queue, list):
                for element in gov_queue:
                    if isinstance(element, dict):
                        base_speed = element.get('base_construction_speed', 0)
                        if isinstance(base_speed, (str, int, float)):
                            used_construction += float(base_speed)
        
        # Check private construction queue  
        if 'private_queue' in country:
            priv_queue = country['private_queue'].get('construction_elements', [])
            if isinstance(priv_queue, list):
                for element in priv_queue:
                    if isinstance(element, dict):
                        base_speed = element.get('base_construction_speed', 0)
                        if isinstance(base_speed, (str, int, float)):
                            used_construction += float(base_speed)
        
        if used_construction > 0:
            construction_usage[int(country_id)] = used_construction
    
    return construction_usage, countries

def calculate_military_scores(save_data):
    """Calculate military scores from save data."""
    from collections import defaultdict
    
    countries = save_data.get('country_manager', {}).get('database', {})
    formations_db = save_data.get('military_formation_manager', {}).get('database', {})
    units_db = save_data.get('new_combat_unit_manager', {}).get('database', {})
    
    # Unit stats (offense + defense average)
    unit_avg_stats = {
        'combat_unit_type_irregular_infantry': 10,  # (10+10)/2
        'combat_unit_type_line_infantry': 22.5,      # (20+25)/2
        'combat_unit_type_skirmish_infantry': 30,    # (25+35)/2
        'combat_unit_type_trench_infantry': 35,      # (30+40)/2
        'combat_unit_type_squad_infantry': 45,       # (40+50)/2
        'combat_unit_type_mechanized_infantry': 55,  # (50+60)/2
        'combat_unit_type_cannon_artillery': 20,     # (25+15)/2
        'combat_unit_type_mobile_artillery': 22.5,   # (30+15)/2
        'combat_unit_type_shrapnel_artillery': 35,   # (45+25)/2
        'combat_unit_type_siege_artillery': 42.5,    # (55+30)/2
        'combat_unit_type_heavy_tank': 52.5,         # (70+35)/2
        'combat_unit_type_hussars': 12.5,            # (15+10)/2
        'combat_unit_type_dragoons': 22.5,           # (20+25)/2
        'combat_unit_type_cuirassiers': 22.5,        # (25+20)/2
        'combat_unit_type_lancers': 25,              # (30+20)/2
        'combat_unit_type_light_tanks': 45,          # (45+45)/2
        'combat_unit_type_frigate': 12.5,            # (10+15)/2
        'combat_unit_type_monitor': 25,              # (20+30)/2
        'combat_unit_type_destroyer': 35,            # (30+40)/2
        'combat_unit_type_torpedo_boat': 35,         # (40+30)/2
        'combat_unit_type_scout_cruiser': 50,        # (50+50)/2
        'combat_unit_type_man_o_war': 25,            # (25+25)/2
        'combat_unit_type_ironclad': 50,             # (50+50)/2
        'combat_unit_type_dreadnought': 80,          # (80+80)/2
        'combat_unit_type_battleship': 100,          # (100+100)/2
        'combat_unit_type_submarine': 40,            # (60+20)/2
        'combat_unit_type_carrier': 90,              # (120+60)/2
    }
    
    military_scores = {}
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        total_score = 0
        
        # Find all formations for this country
        for fid, formation in formations_db.items():
            if isinstance(formation, dict) and formation.get('country') == int(country_id):
                # Count units in this formation
                unit_counts = defaultdict(int)
                
                for uid, unit in units_db.items():
                    if isinstance(unit, dict) and unit.get('formation') == int(fid):
                        unit_type = unit.get('type')
                        if unit_type and unit_type in unit_avg_stats:
                            unit_counts[unit_type] += 1
                
                # Calculate score for this formation
                for unit_type, count in unit_counts.items():
                    total_score += count * unit_avg_stats[unit_type]
        
        if total_score > 0:
            military_scores[int(country_id)] = total_score
    
    return military_scores, countries

def compare_sessions(session1_path, session2_path, metric='gdp'):
    """Compare two sessions and generate comparison data."""
    print(f"Loading {session1_path}...")
    session1_data = load_save_data(session1_path)
    
    print(f"Loading {session2_path}...")
    session2_data = load_save_data(session2_path)
    
    if metric == 'gdp':
        session1_metrics, countries1 = calculate_true_gdp(session1_data)
        session2_metrics, countries2 = calculate_true_gdp(session2_data)
    elif metric == 'effective_gdp':
        session1_metrics, countries1 = calculate_effective_gdp(session1_data)
        session2_metrics, countries2 = calculate_effective_gdp(session2_data)
    elif metric == 'construction':
        session1_metrics, countries1 = calculate_construction_usage(session1_data)
        session2_metrics, countries2 = calculate_construction_usage(session2_data)
    elif metric == 'military':
        session1_metrics, countries1 = calculate_military_scores(session1_data)
        session2_metrics, countries2 = calculate_military_scores(session2_data)
    else:
        raise ValueError(f"Metric {metric} not supported yet")
    
    # Load human countries
    human_countries = set()
    if os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Create comparison data
    comparison_data = []
    
    # Get all countries that exist in both sessions
    all_countries = set()
    for country_id in session1_metrics:
        tag = get_country_tag(countries1, country_id)
        if tag in human_countries:
            all_countries.add((country_id, tag))
    
    for country_id in session2_metrics:
        tag = get_country_tag(countries2, country_id)
        if tag in human_countries:
            all_countries.add((country_id, tag))
    
    for country_id, tag in all_countries:
        session1_value = session1_metrics.get(country_id, 0)
        session2_value = session2_metrics.get(country_id, 0)
        
        if session1_value > 0 or session2_value > 0:
            net_change = session2_value - session1_value
            pct_change = (net_change / session1_value * 100) if session1_value > 0 else 0
            
            comparison_data.append({
                'tag': tag,
                'session1': session1_value,
                'session2': session2_value,
                'net_change': net_change,
                'pct_change': pct_change
            })
    
    # Sort by percentage change (highest first)
    comparison_data.sort(key=lambda x: -x['pct_change'])
    
    return comparison_data

def print_comparison(comparison_data, session1_name, session2_name, metric='gdp'):
    """Print comparison in the requested format."""
    if metric == 'gdp':
        print("GDP COMPARISON BETWEEN SESSIONS")
        divisor = 1e6
        unit = ''
    elif metric == 'effective_gdp':
        print("EFFECTIVE GDP COMPARISON BETWEEN SESSIONS")
        print("(Total economic control including foreign investments)")
        divisor = 1e6
        unit = ''
    elif metric == 'construction':
        print("CONSTRUCTION COMPARISON BETWEEN SESSIONS")
        divisor = 1
        unit = ''
    elif metric == 'military':
        print("MILITARY SCORE COMPARISON BETWEEN SESSIONS")
        print("(Score = Units × Average(Offense + Defense))")
        divisor = 1
        unit = ''
    else:
        print(f"{metric.upper()} COMPARISON BETWEEN SESSIONS")
        divisor = 1
        unit = ''
    
    print("=" * 50)
    print()
    
    # Create column headers with session names
    # Extract just the session number (e.g., "Session 4" -> "Sess4")
    s1_num = ''.join(filter(str.isdigit, session1_name))
    s2_num = ''.join(filter(str.isdigit, session2_name))
    s1_header = f"Sess{s1_num}" if s1_num else session1_name[:6]
    s2_header = f"Sess{s2_num}" if s2_num else session2_name[:6]
    
    print(f"| Rank | Flag | {s1_header:^9} | {s2_header:^9} | {'Net':^9} | {'% Chg':^8} |")
    print("|------|------|-----------|-----------|-----------|----------|")
    
    for i, data in enumerate(comparison_data, 1):
        tag = data['tag']
        s1_val = data['session1'] / divisor
        s2_val = data['session2'] / divisor
        net_val = data['net_change'] / divisor
        pct_chg = data['pct_change']
        
        if metric in ['gdp', 'effective_gdp']:
            print(f"| {i:4} | {tag:4} | {s1_val:9.1f} | {s2_val:9.1f} | {net_val:+9.1f} | {pct_chg:7.1f}% |")
        elif metric == 'military':
            # Military scores can be large, need more space
            print(f"| {i:4} | {tag:4} | {s1_val:9.0f} | {s2_val:9.0f} | {net_val:+9.0f} | {pct_chg:7.1f}% |")
        else:
            print(f"| {i:4} | {tag:4} | {s1_val:9.0f} | {s2_val:9.0f} | {net_val:+9.0f} | {pct_chg:7.1f}% |")

def main():
    parser = argparse.ArgumentParser(description='Compare Victoria 3 sessions')
    parser.add_argument('session1', help='Path to first session JSON file')
    parser.add_argument('session2', help='Path to second session JSON file') 
    parser.add_argument('-m', '--metric', default='gdp', choices=['gdp', 'construction', 'effective_gdp', 'military'], help='Metric to compare')
    parser.add_argument('-o', '--output', help='Output file for the report')
    
    args = parser.parse_args()
    
    # Extract session names from filenames
    session1_name = os.path.basename(args.session1).replace('_extracted.json', '').replace('extracted-saves/', '')
    session2_name = os.path.basename(args.session2).replace('_extracted.json', '').replace('extracted-saves/', '')
    
    print("Victoria 3 Session Comparison")
    print("=" * 40)
    print(f"Comparing: {session1_name} vs {session2_name}")
    print()
    
    # Generate comparison
    comparison_data = compare_sessions(args.session1, args.session2, args.metric)
    
    # Generate output
    if args.output:
        with open(args.output, 'w') as f:
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            print_comparison(comparison_data, session1_name, session2_name, args.metric)
            sys.stdout = old_stdout
        print(f"Comparison report saved to: {args.output}")
    else:
        print_comparison(comparison_data, session1_name, session2_name, args.metric)

if __name__ == '__main__':
    main()