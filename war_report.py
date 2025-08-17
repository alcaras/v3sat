#!/usr/bin/env python3
"""
Victoria 3 War Report Tool

Analyzes ongoing wars from Victoria 3 save files, showing:
- Active wars and their participants
- War support levels for each side
- War exhaustion metrics
- Geographic distribution of conflicts
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
    
    # Try to find country in the countries data
    countries = data.get('countries', {})
    for country_id, country_data in countries.items():
        if country_data.get('definition', {}).get('country', '') == tag:
            # Try to get a proper name if available
            return tag
    
    return tag


def analyze_wars(data):
    """Analyze ongoing wars in the save file."""
    wars = data.get('war_manager', {}).get('database', {})
    countries = data.get('countries', {})
    game_date = data.get('meta_data', {}).get('game_date', 'Unknown')
    
    print(f"\n{'='*60}")
    print(f"Victoria 3 War Report - {game_date}")
    print(f"{'='*60}\n")
    
    if not wars:
        print("No wars data found in save file.")
        return
    
    # Separate ongoing and completed wars
    ongoing_wars = []
    completed_wars = []
    
    for war_id, war_data in wars.items():
        if isinstance(war_data, dict):
            # Check if war is ongoing (has war_support data)
            if 'war_support' in war_data or 'attacker' in war_data:
                ongoing_wars.append((war_id, war_data))
            else:
                completed_wars.append((war_id, war_data))
    
    # Report ongoing wars
    if ongoing_wars:
        print(f"ONGOING WARS: {len(ongoing_wars)}")
        print(f"{'-'*60}\n")
        
        for war_id, war_data in sorted(ongoing_wars, key=lambda x: x[0]):
            print(f"War #{war_id}")
            print("="*40)
            
            # Get participants
            attacker = war_data.get('attacker', {})
            defender = war_data.get('defender', {})
            
            if attacker:
                attacker_tag = attacker.get('country', 'Unknown')
                attacker_name = get_country_name(data, attacker_tag)
                attacker_support = war_data.get('war_support', {}).get('attacker', 0)
                print(f"Attacker: {attacker_name} ({attacker_tag})")
                print(f"  War Support: {attacker_support:.1f}%")
                
                # List attacker allies
                attacker_participants = attacker.get('participants', [])
                if attacker_participants:
                    print(f"  Allies: {', '.join([get_country_name(data, p.get('country', '')) for p in attacker_participants])}")
            
            if defender:
                defender_tag = defender.get('country', 'Unknown')
                defender_name = get_country_name(data, defender_tag)
                defender_support = war_data.get('war_support', {}).get('defender', 0)
                print(f"Defender: {defender_name} ({defender_tag})")
                print(f"  War Support: {defender_support:.1f}%")
                
                # List defender allies
                defender_participants = defender.get('participants', [])
                if defender_participants:
                    print(f"  Allies: {', '.join([get_country_name(data, p.get('country', '')) for p in defender_participants])}")
            
            # War goals if available
            war_goals = war_data.get('war_goals', [])
            if war_goals:
                print(f"War Goals: {len(war_goals)}")
            
            # War exhaustion if available
            war_exhaustion = war_data.get('war_exhaustion', {})
            if war_exhaustion:
                att_exhaustion = war_exhaustion.get('attacker', 0)
                def_exhaustion = war_exhaustion.get('defender', 0)
                print(f"War Exhaustion:")
                print(f"  Attacker: {att_exhaustion:.1f}%")
                print(f"  Defender: {def_exhaustion:.1f}%")
            
            print()
    else:
        print("No ongoing wars found.\n")
    
    # Summary statistics
    print(f"\n{'='*60}")
    print("WAR STATISTICS SUMMARY")
    print(f"{'='*60}")
    print(f"Total Wars Recorded: {len(wars)}")
    print(f"Ongoing Wars: {len(ongoing_wars)}")
    print(f"Completed Wars: {len(completed_wars)}")
    
    # Analyze war participation by country
    war_participation = {}
    for war_id, war_data in wars.items():
        if isinstance(war_data, dict):
            attacker = war_data.get('attacker', {})
            defender = war_data.get('defender', {})
            
            # Count main participants  
            if attacker:
                att_country = attacker.get('country', '')
                if att_country:
                    war_participation[att_country] = war_participation.get(att_country, 0) + 1
                    
                # Count allies
                for participant in attacker.get('participants', []):
                    if isinstance(participant, dict):
                        p_country = participant.get('country', '')
                        if p_country:
                            war_participation[p_country] = war_participation.get(p_country, 0) + 1
            
            if defender:
                def_country = defender.get('country', '')
                if def_country:
                    war_participation[def_country] = war_participation.get(def_country, 0) + 1
                    
                # Count allies
                for participant in defender.get('participants', []):
                    if isinstance(participant, dict):
                        p_country = participant.get('country', '')
                        if p_country:
                            war_participation[p_country] = war_participation.get(p_country, 0) + 1
    
    if war_participation:
        print(f"\nMost Belligerent Nations (by war participation):")
        sorted_participants = sorted(war_participation.items(), key=lambda x: x[1], reverse=True)[:10]
        for country, count in sorted_participants:
            country_name = get_country_name(data, country)
            print(f"  {country_name:20} {count:3} wars")


def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 war report')
    parser.add_argument('savefile', nargs='?', help='Path to extracted save file JSON')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    
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
                analyze_wars(data)
            sys.stdout = original_stdout
            print(f"War report saved to: {args.output}")
        else:
            analyze_wars(data)
            
    except Exception as e:
        print(f"Error analyzing save file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()