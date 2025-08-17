#!/usr/bin/env python3
"""
Victoria 3 Power Projection Report

Calculates military power projection for countries based on their formations and units.
Power Projection = (Average Offense + Defense) * (Total Manpower / 1000)
"""

import json
import os
import sys
import argparse
from pathlib import Path

# Unit type offense and defense values from game files
UNIT_STATS = {
    # Infantry
    'combat_unit_type_irregular_infantry': {'offense': 10, 'defense': 10},
    'combat_unit_type_line_infantry': {'offense': 20, 'defense': 25},
    'combat_unit_type_skirmish_infantry': {'offense': 25, 'defense': 35},
    'combat_unit_type_trench_infantry': {'offense': 30, 'defense': 40},
    'combat_unit_type_squad_infantry': {'offense': 40, 'defense': 50},
    'combat_unit_type_mechanized_infantry': {'offense': 50, 'defense': 60},
    
    # Artillery
    'combat_unit_type_cannon_artillery': {'offense': 25, 'defense': 15},
    'combat_unit_type_mobile_artillery': {'offense': 30, 'defense': 15},
    'combat_unit_type_shrapnel_artillery': {'offense': 45, 'defense': 25},
    'combat_unit_type_siege_artillery': {'offense': 55, 'defense': 30},
    'combat_unit_type_heavy_tank': {'offense': 70, 'defense': 35},
    
    # Cavalry
    'combat_unit_type_hussars': {'offense': 15, 'defense': 10},
    'combat_unit_type_dragoons': {'offense': 20, 'defense': 25},
    'combat_unit_type_cuirassiers': {'offense': 25, 'defense': 20},
    'combat_unit_type_lancers': {'offense': 30, 'defense': 20},
    'combat_unit_type_light_tanks': {'offense': 45, 'defense': 45},
    
    # Navy
    'combat_unit_type_frigate': {'offense': 10, 'defense': 15},
    'combat_unit_type_monitor': {'offense': 20, 'defense': 30},
    'combat_unit_type_destroyer': {'offense': 30, 'defense': 40},
    'combat_unit_type_torpedo_boat': {'offense': 40, 'defense': 30},
    'combat_unit_type_scout_cruiser': {'offense': 50, 'defense': 50},
    'combat_unit_type_man_o_war': {'offense': 25, 'defense': 25},
    'combat_unit_type_ironclad': {'offense': 50, 'defense': 50},
    'combat_unit_type_dreadnought': {'offense': 80, 'defense': 80},
    'combat_unit_type_battleship': {'offense': 100, 'defense': 100},
    'combat_unit_type_submarine': {'offense': 60, 'defense': 20},
    'combat_unit_type_carrier': {'offense': 120, 'defense': 60},
}

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

def calculate_formation_power(units_db, formation_id):
    """Calculate power projection for a single formation."""
    total_manpower = 0
    total_offense = 0
    total_defense = 0
    unit_count = 0
    
    for uid, unit in units_db.items():
        if isinstance(unit, dict) and unit.get('formation') == int(formation_id):
            unit_type = unit.get('type')
            manpower = unit.get('current_manpower', 0)
            
            if unit_type and unit_type in UNIT_STATS:
                stats = UNIT_STATS[unit_type]
                unit_count += 1
                total_manpower += manpower
                
                # Weight offense/defense by manpower
                if manpower > 0:
                    total_offense += stats['offense'] * manpower
                    total_defense += stats['defense'] * manpower
    
    if total_manpower > 0:
        avg_offense = total_offense / total_manpower
        avg_defense = total_defense / total_manpower
        avg_combined = avg_offense + avg_defense
        power_projection = avg_combined * (total_manpower / 1000)
        
        return {
            'manpower': total_manpower,
            'units': unit_count,
            'avg_offense': avg_offense,
            'avg_defense': avg_defense,
            'avg_combined': avg_combined,
            'power_projection': power_projection
        }
    
    return {
        'manpower': 0,
        'units': 0,
        'avg_offense': 0,
        'avg_defense': 0,
        'avg_combined': 0,
        'power_projection': 0
    }

def analyze_power_projection(save_data, filter_humans=False):
    """Analyze military power projection for countries."""
    countries = save_data.get('country_manager', {}).get('database', {})
    formations_db = save_data.get('military_formation_manager', {}).get('database', {})
    units_db = save_data.get('new_combat_unit_manager', {}).get('database', {})
    
    # Load human countries if filtering
    human_countries = set()
    if filter_humans and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Analyze each country
    country_power = []
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        tag = get_country_tag(countries, country_id)
        
        # Filter by human countries if requested
        if filter_humans and human_countries and tag not in human_countries:
            continue
        
        # Find all formations for this country
        army_formations = []
        navy_formations = []
        
        for fid, formation in formations_db.items():
            if isinstance(formation, dict) and formation.get('country') == int(country_id):
                formation_name = formation.get('name', 'Unknown')
                formation_type = formation.get('type')
                
                if formation_type == 'army':
                    army_formations.append((fid, formation_name))
                elif formation_type == 'fleet':
                    navy_formations.append((fid, formation_name))
        
        # Calculate power for each army formation
        army_power_total = 0
        army_manpower_total = 0
        army_details = []
        
        for fid, name in army_formations:
            power_data = calculate_formation_power(units_db, fid)
            if power_data['manpower'] > 0:
                army_power_total += power_data['power_projection']
                army_manpower_total += power_data['manpower']
                army_details.append({
                    'name': name,
                    'manpower': power_data['manpower'],
                    'units': power_data['units'],
                    'avg_combined': power_data['avg_combined'],
                    'power': power_data['power_projection']
                })
        
        # Calculate power for each navy formation
        navy_power_total = 0
        navy_manpower_total = 0
        navy_details = []
        
        for fid, name in navy_formations:
            power_data = calculate_formation_power(units_db, fid)
            if power_data['manpower'] > 0:
                navy_power_total += power_data['power_projection']
                navy_manpower_total += power_data['manpower']
                navy_details.append({
                    'name': name,
                    'manpower': power_data['manpower'],
                    'units': power_data['units'],
                    'avg_combined': power_data['avg_combined'],
                    'power': power_data['power_projection']
                })
        
        # Only include countries with military forces
        if army_power_total > 0 or navy_power_total > 0:
            country_power.append({
                'tag': tag,
                'army_power': army_power_total,
                'army_manpower': army_manpower_total,
                'army_formations': len(army_formations),
                'army_details': army_details,
                'navy_power': navy_power_total,
                'navy_manpower': navy_manpower_total,
                'navy_formations': len(navy_formations),
                'navy_details': navy_details,
                'total_power': army_power_total + navy_power_total
            })
    
    # Sort by total power projection
    country_power.sort(key=lambda x: x['total_power'], reverse=True)
    
    return country_power

def print_power_report(power_data, save_data, detailed=False):
    """Print the power projection report."""
    # Get current date
    meta_data = save_data.get('meta_data', {})
    game_date = meta_data.get('game_date', 'Unknown')
    
    print("=" * 80)
    print("VICTORIA 3 MILITARY POWER PROJECTION REPORT")
    print("=" * 80)
    print(f"Date: {game_date}")
    print(f"Countries with military: {len(power_data)}")
    print()
    
    # Summary table
    print("POWER PROJECTION RANKINGS")
    print("-" * 80)
    print(f"{'Rank':<6} {'Country':<8} {'Total Power':>12} {'Army Power':>12} {'Navy Power':>12}")
    print("-" * 80)
    
    for i, country in enumerate(power_data[:20], 1):  # Top 20
        print(f"{i:<6} {country['tag']:<8} {country['total_power']:>12.0f} "
              f"{country['army_power']:>12.0f} {country['navy_power']:>12.0f}")
    
    if detailed:
        # Detailed breakdown for top countries
        print()
        print("=" * 80)
        print("DETAILED FORMATION BREAKDOWN (Top 10)")
        print("=" * 80)
        
        for country in power_data[:10]:
            print()
            print(f"{country['tag']}")
            print("-" * 40)
            print(f"Total Power Projection: {country['total_power']:.0f}")
            
            if country['army_details']:
                print(f"\nArmy Formations ({country['army_formations']} total):")
                for formation in country['army_details']:
                    manpower_k = formation['manpower'] / 1000
                    print(f"  • {formation['name']:<20} "
                          f"Power: {formation['power']:>8.0f} | "
                          f"Manpower: {manpower_k:>6.1f}k | "
                          f"Avg Off+Def: {formation['avg_combined']:>5.1f}")
            
            if country['navy_details']:
                print(f"\nNavy Formations ({country['navy_formations']} fleets):")
                for formation in country['navy_details']:
                    manpower_k = formation['manpower'] / 1000
                    print(f"  • {formation['name']:<20} "
                          f"Power: {formation['power']:>8.0f} | "
                          f"Manpower: {manpower_k:>6.1f}k | "
                          f"Avg Off+Def: {formation['avg_combined']:>5.1f}")
    
    # Statistics
    print()
    print("-" * 80)
    print("STATISTICS")
    print("-" * 80)
    
    if power_data:
        total_power = sum(c['total_power'] for c in power_data)
        total_army = sum(c['army_power'] for c in power_data)
        total_navy = sum(c['navy_power'] for c in power_data)
        
        print(f"Global military power: {total_power:,.0f}")
        print(f"  Army power: {total_army:,.0f} ({total_army/total_power*100:.1f}%)")
        print(f"  Navy power: {total_navy:,.0f} ({total_navy/total_power*100:.1f}%)")
        
        # Top country dominance
        if len(power_data) > 0:
            top_country = power_data[0]
            print(f"\nDominant military: {top_country['tag']} with {top_country['total_power']:.0f} power")
            print(f"  ({top_country['total_power']/total_power*100:.1f}% of global power)")

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 military power projection report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('--humans', action='store_true', help='Only analyze human-controlled countries')
    parser.add_argument('--detailed', action='store_true', help='Show detailed formation breakdown')
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
    
    # Analyze power projection
    power_data = analyze_power_projection(save_data, filter_humans=args.humans)
    
    # Output report
    if args.output:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_power_report(power_data, save_data, detailed=args.detailed)
        
        with open(args.output, 'w') as f:
            f.write(output.getvalue())
        print(f"Report saved to: {args.output}")
    else:
        print_power_report(power_data, save_data, detailed=args.detailed)

if __name__ == '__main__':
    main()