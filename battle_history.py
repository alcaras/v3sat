#!/usr/bin/env python3
"""
Victoria 3 Battle History Tool

Extracts and analyzes historical battle data from Victoria 3 save files, showing:
- All battles fought throughout the campaign
- Battle outcomes and casualties
- Timeline of major conflicts
- Geographic distribution of battles
"""

import json
import argparse
import os
from pathlib import Path
from datetime import datetime


def load_save_file(filepath):
    """Load and parse Victoria 3 save file."""
    print(f"Loading save file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def get_latest_save():
    """Find the most recent extracted save file."""
    extracted_dir = Path("extracted-saves")
    if not extracted_dir.exists():
        raise FileNotFoundError("extracted-saves directory not found")
    
    save_files = list(extracted_dir.glob("*_extracted.json"))
    if not save_files:
        raise FileNotFoundError("No extracted save files found")
    
    return str(max(save_files, key=os.path.getmtime))


def get_country_name(data, tag):
    """Get country name from tag."""
    if not tag:
        return "Unknown"
    return tag


def parse_date(date_str):
    """Parse Victoria 3 date format (YYYY.M.D.H)."""
    if not date_str:
        return None
    try:
        parts = date_str.split('.')
        if len(parts) >= 3:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            return f"{year}-{month:02d}-{day:02d}"
    except:
        pass
    return date_str


def analyze_battles(data):
    """Analyze battle history in the save file."""
    wars = data.get('war_manager', {}).get('database', {})
    battles = data.get('battle_manager', {}).get('database', {})
    game_date = data.get('meta_data', {}).get('game_date', 'Unknown')
    
    print(f"\n{'='*70}")
    print(f"Victoria 3 Battle History Report - {game_date}")
    print(f"{'='*70}\n")
    
    if not battles:
        print("No battle data found in save file.")
        return
    
    # Collect all battles
    all_battles = []
    battle_count = len(battles)
    
    for battle_id, battle_data in battles.items():
        if isinstance(battle_data, dict):
            battle_info = {
                'battle_id': battle_id,
                'war_id': battle_data.get('war', ''),
                'date': battle_data.get('date', ''),
                'type': battle_data.get('type', ''),
                'status': battle_data.get('status', ''),
                'province': battle_data.get('province', ''),
                'attacker_province': battle_data.get('attacker_province', ''),
                'front': battle_data.get('front', ''),
                'name': battle_data.get('name', {}),
                'casualties': battle_data.get('casualties', {}),
                'victory': battle_data.get('victory', {}),
                'occupation': battle_data.get('occupation', {})
            }
            all_battles.append(battle_info)
    
    print(f"BATTLE SUMMARY")
    print(f"{'-'*70}")
    print(f"Total Wars: {len(wars)}")
    print(f"Total Battles: {battle_count}")
    
    if not all_battles:
        print("No battle data found.")
        return
    
    # Sort battles by date
    all_battles.sort(key=lambda x: x['date'])
    
    print(f"\nCHRONOLOGICAL BATTLE LIST")
    print(f"{'-'*70}")
    print(f"{'Date':<12} {'War':<6} {'Type':<8} {'Province':<10} {'Status':<20}")
    print(f"{'-'*70}")
    
    for battle in all_battles:
        date = parse_date(battle['date']) or 'Unknown'
        war_id = battle['war_id'] or 'N/A'
        battle_type = battle['type'] or 'Unknown'
        province = str(battle['province']) if battle['province'] else 'Unknown'
        status = battle['status'] or 'Unknown'
        
        print(f"{date:<12} #{war_id:<5} {battle_type:<8} {province:<10} {status:<20}")
    
    # Analyze by year
    print(f"\n\nBATTLES BY YEAR")
    print(f"{'-'*30}")
    
    battles_by_year = {}
    for battle in all_battles:
        date = battle['date']
        if date:
            try:
                year = date.split('.')[0]
                battles_by_year[year] = battles_by_year.get(year, 0) + 1
            except:
                pass
    
    for year in sorted(battles_by_year.keys()):
        count = battles_by_year[year]
        print(f"{year}: {count} battles")
    
    # Battle types
    print(f"\n\nBATTLE TYPES")
    print(f"{'-'*30}")
    
    battle_types = {}
    for battle in all_battles:
        battle_type = battle['type']
        if battle_type:
            battle_types[battle_type] = battle_types.get(battle_type, 0) + 1
    
    for battle_type, count in sorted(battle_types.items(), key=lambda x: x[1], reverse=True):
        print(f"{battle_type:<20} {count:3} battles")
    
    # Geographic distribution by province
    print(f"\n\nBATTLE LOCATIONS (by Province)")
    print(f"{'-'*40}")
    
    provinces = {}
    for battle in all_battles:
        province = battle['province']
        if province:
            provinces[province] = provinces.get(province, 0) + 1
    
    sorted_provinces = sorted(provinces.items(), key=lambda x: x[1], reverse=True)[:15]
    for province, count in sorted_provinces:
        print(f"Province {province:<15} {count:3} battles")
    
    # Battle results analysis
    print(f"\n\nBATTLE OUTCOMES")
    print(f"{'-'*30}")
    
    results = {}
    for battle in all_battles:
        result = battle['status']
        if result:
            results[result] = results.get(result, 0) + 1
    
    for result, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"{result:<25} {count:3} battles")
    
    # Recent battle activity
    print(f"\n\nRECENT BATTLES (Last 10)")
    print(f"{'-'*60}")
    
    recent_battles = all_battles[-10:] if len(all_battles) >= 10 else all_battles
    for battle in recent_battles:
        date = parse_date(battle['date']) or 'Unknown'
        war_id = battle['war_id'] or 'N/A'
        battle_type = battle['type'] or 'Unknown'
        province = str(battle['province']) if battle['province'] else 'Unknown'
        status = battle['status'] or 'Unknown'
        
        print(f"{date}: War #{war_id} - {battle_type} at Province {province} - {status}")


def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 battle history report')
    parser.add_argument('savefile', nargs='?', help='Path to extracted save file JSON')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--csv', action='store_true', help='Output CSV format')
    
    args = parser.parse_args()
    
    # Determine save file to use
    if args.savefile:
        savefile = args.savefile
    else:
        try:
            savefile = get_latest_save()
            print(f"Using latest save file: {savefile}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return
    
    # Load and analyze
    try:
        data = load_save_file(savefile)
        
        # Redirect output if specified
        if args.output:
            import sys
            original_stdout = sys.stdout
            with open(args.output, 'w') as f:
                sys.stdout = f
                if args.csv:
                    generate_csv_output(data)
                else:
                    analyze_battles(data)
            sys.stdout = original_stdout
            print(f"Battle history report saved to: {args.output}")
        else:
            if args.csv:
                generate_csv_output(data)
            else:
                analyze_battles(data)
            
    except Exception as e:
        print(f"Error analyzing save file: {e}")
        import traceback
        traceback.print_exc()


def generate_csv_output(data):
    """Generate CSV format output for battles."""
    battles = data.get('battle_manager', {}).get('database', {})
    
    print("Date,War,Type,Province,Status")
    
    for battle_id, battle_data in battles.items():
        if isinstance(battle_data, dict):
            date = parse_date(battle_data.get('date', ''))
            war_id = battle_data.get('war', '')
            battle_type = battle_data.get('type', '')
            province = battle_data.get('province', '')
            status = battle_data.get('status', '')
            
            print(f"{date},{war_id},{battle_type},{province},{status}")


if __name__ == "__main__":
    main()