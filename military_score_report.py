#!/usr/bin/env python3
"""
Victoria 3 Military Score Report

Calculates military scores based on:
Score = Number of Units × Average(Offense + Defense)
"""

import json
import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict

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

def calculate_formation_score(units_db, formation_id, formation_name):
    """Calculate score for a single formation."""
    unit_counts = defaultdict(int)
    
    # Count units by type
    for uid, unit in units_db.items():
        if isinstance(unit, dict) and unit.get('formation') == int(formation_id):
            unit_type = unit.get('type')
            if unit_type:
                unit_counts[unit_type] += 1
    
    # Calculate score
    total_score = 0
    details = []
    
    for unit_type, count in sorted(unit_counts.items()):
        if unit_type in UNIT_STATS:
            stats = UNIT_STATS[unit_type]
            avg_stat = (stats['offense'] + stats['defense']) / 2
            score = count * avg_stat
            total_score += score
            
            details.append({
                'type': unit_type.replace('combat_unit_type_', ''),
                'count': count,
                'offense': stats['offense'],
                'defense': stats['defense'],
                'avg': avg_stat,
                'score': score
            })
    
    return {
        'name': formation_name,
        'total_score': total_score,
        'unit_count': sum(unit_counts.values()),
        'details': details
    }

def analyze_military_scores(save_data, filter_humans=False):
    """Analyze military scores for countries."""
    countries = save_data.get('country_manager', {}).get('database', {})
    formations_db = save_data.get('military_formation_manager', {}).get('database', {})
    units_db = save_data.get('new_combat_unit_manager', {}).get('database', {})
    
    # Load human countries if filtering
    human_countries = set()
    if filter_humans and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Analyze each country
    country_scores = []
    
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
                    score_data = calculate_formation_score(units_db, fid, formation_name)
                    if score_data['total_score'] > 0:
                        army_formations.append(score_data)
                elif formation_type == 'fleet':
                    score_data = calculate_formation_score(units_db, fid, formation_name)
                    if score_data['total_score'] > 0:
                        navy_formations.append(score_data)
        
        # Calculate totals
        army_score = sum(f['total_score'] for f in army_formations)
        navy_score = sum(f['total_score'] for f in navy_formations)
        
        # Only include countries with military forces
        if army_score > 0 or navy_score > 0:
            country_scores.append({
                'tag': tag,
                'army_score': army_score,
                'army_formations': army_formations,
                'navy_score': navy_score,
                'navy_formations': navy_formations,
                'total_score': army_score + navy_score
            })
    
    # Sort by total score
    country_scores.sort(key=lambda x: x['total_score'], reverse=True)
    
    return country_scores

def print_military_scores(scores_data, save_data, detailed=False):
    """Print the military scores report."""
    # Get current date
    meta_data = save_data.get('meta_data', {})
    game_date = meta_data.get('game_date', 'Unknown')
    
    print("=" * 80)
    print("VICTORIA 3 MILITARY SCORES REPORT")
    print("=" * 80)
    print(f"Date: {game_date}")
    print(f"Countries with military: {len(scores_data)}")
    print()
    print("Formula: Score = Units × Average(Offense + Defense)")
    print()
    
    # Summary table
    print("MILITARY SCORE RANKINGS (TOTAL)")
    print("-" * 80)
    print(f"{'Rank':<6} {'Country':<8} {'Total Score':>12} {'Army Score':>12} {'Navy Score':>12}")
    print("-" * 80)
    
    for i, country in enumerate(scores_data[:20], 1):  # Top 20
        print(f"{i:<6} {country['tag']:<8} {country['total_score']:>12.0f} "
              f"{country['army_score']:>12.0f} {country['navy_score']:>12.0f}")
    
    # Army Power Rankings (sorted by army score)
    print()
    print("=" * 80)
    print("ARMY POWER RANKINGS")
    print("-" * 80)
    print(f"{'Rank':<6} {'Country':<8} {'Army Score':>12} {'Army Units':>12}")
    print("-" * 80)
    
    army_sorted = sorted([c for c in scores_data if c['army_score'] > 0], 
                        key=lambda x: x['army_score'], reverse=True)
    
    for i, country in enumerate(army_sorted[:15], 1):  # Top 15
        army_units = sum(f['unit_count'] for f in country['army_formations'])
        print(f"{i:<6} {country['tag']:<8} {country['army_score']:>12.0f} {army_units:>12}")
    
    # Navy Power Rankings (sorted by navy score)
    print()
    print("=" * 80)
    print("NAVY POWER RANKINGS")
    print("-" * 80)
    print(f"{'Rank':<6} {'Country':<8} {'Navy Score':>12} {'Navy Units':>12}")
    print("-" * 80)
    
    navy_sorted = sorted([c for c in scores_data if c['navy_score'] > 0],
                        key=lambda x: x['navy_score'], reverse=True)
    
    for i, country in enumerate(navy_sorted[:15], 1):  # Top 15
        navy_units = sum(f['unit_count'] for f in country['navy_formations'])
        print(f"{i:<6} {country['tag']:<8} {country['navy_score']:>12.0f} {navy_units:>12}")
    
    if detailed:
        # Detailed breakdown for top countries
        print()
        print("=" * 80)
        print("DETAILED FORMATION BREAKDOWN")
        print("=" * 80)
        
        for country in scores_data[:10]:
            print()
            print(f"{country['tag']}")
            print("-" * 60)
            print(f"Total Score: {country['total_score']:.0f}")
            print(f"Army Score: {country['army_score']:.0f}")
            print(f"Navy Score: {country['navy_score']:.0f}")
            
            if country['army_formations']:
                print(f"\nArmy Formations:")
                for formation in country['army_formations']:
                    print(f"  {formation['name']}: {formation['total_score']:.0f} score")
                    for unit in formation['details']:
                        print(f"    • {unit['count']:3d} × {unit['type']:<20} "
                              f"({unit['offense']}/{unit['defense']}) = "
                              f"{unit['count']} × {unit['avg']:.1f} = {unit['score']:.0f}")
            
            if country['navy_formations']:
                print(f"\nNavy Formations:")
                for formation in country['navy_formations']:
                    print(f"  {formation['name']}: {formation['total_score']:.0f} score")
                    for unit in formation['details']:
                        print(f"    • {unit['count']:3d} × {unit['type']:<20} "
                              f"({unit['offense']}/{unit['defense']}) = "
                              f"{unit['count']} × {unit['avg']:.1f} = {unit['score']:.0f}")

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 military scores report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('--humans', action='store_true', help='Only analyze human-controlled countries')
    parser.add_argument('--detailed', action='store_true', help='Show detailed unit breakdown')
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
    
    # Analyze military scores
    scores_data = analyze_military_scores(save_data, filter_humans=args.humans)
    
    # Output report
    if args.output:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_military_scores(scores_data, save_data, detailed=args.detailed)
        
        with open(args.output, 'w') as f:
            f.write(output.getvalue())
        print(f"Report saved to: {args.output}")
    else:
        print_military_scores(scores_data, save_data, detailed=args.detailed)

if __name__ == '__main__':
    main()