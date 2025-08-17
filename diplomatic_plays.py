#!/usr/bin/env python3
"""
Victoria 3 Diplomatic Plays Tool

Tracks ongoing diplomatic plays and tensions from Victoria 3 save files:
- Active diplomatic plays that could escalate to war
- Diplomatic action types and participants
- Escalation timelines and war risk assessment
- International incident tracking
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
        return "Unknown"
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


def analyze_diplomatic_plays(data):
    """Analyze ongoing diplomatic plays."""
    diplomatic_plays = data.get('diplomatic_plays', {}).get('database', {})
    game_date = data.get('meta_data', {}).get('game_date', 'Unknown')
    
    print(f"\n{'='*70}")
    print(f"Victoria 3 Diplomatic Plays Report - {game_date}")
    print(f"{'='*70}\n")
    
    if not diplomatic_plays:
        print("No diplomatic plays data found in save file.")
        return
    
    active_plays = 0
    escalation_risk = []
    
    print(f"ACTIVE DIPLOMATIC PLAYS")
    print(f"{'-'*70}\n")
    
    for play_id, play_data in diplomatic_plays.items():
        if isinstance(play_data, dict):
            active_plays += 1
            
            print(f"Diplomatic Play #{play_id}")
            print("="*50)
            
            # Get basic info
            play_type = play_data.get('type', 'Unknown')
            target_country = play_data.get('target', '')
            initiator_country = play_data.get('initiator', '')
            
            target_name = get_country_name(data, str(target_country))
            initiator_name = get_country_name(data, str(initiator_country))
            
            print(f"Type: {play_type}")
            print(f"Initiator: {initiator_name} ({initiator_country})")
            print(f"Target: {target_name} ({target_country})")
            
            # Timeline info
            start_date = play_data.get('start_date', '')
            if start_date:
                formatted_date = parse_date(start_date)
                print(f"Started: {formatted_date}")
            
            # Escalation potential
            escalation_level = play_data.get('escalation', 0)
            if escalation_level > 0:
                print(f"Escalation Level: {escalation_level}")
                escalation_risk.append((play_id, escalation_level, initiator_name, target_name))
            
            # War goal if available
            war_goal = play_data.get('war_goal', '')
            if war_goal:
                print(f"War Goal: {war_goal}")
            
            # Participants/supporters
            supporters = play_data.get('supporters', [])
            if supporters:
                supporter_names = [get_country_name(data, s.get('country', '')) for s in supporters]
                print(f"Supporters: {', '.join(supporter_names)}")
            
            opponents = play_data.get('opponents', [])
            if opponents:
                opponent_names = [get_country_name(data, o.get('country', '')) for o in opponents]
                print(f"Opponents: {', '.join(opponent_names)}")
            
            # Maneuvers or actions
            maneuvers = play_data.get('maneuvers', [])
            if maneuvers:
                print(f"Active Maneuvers: {len(maneuvers)}")
                for maneuver in maneuvers[:3]:  # Show first 3
                    if isinstance(maneuver, dict):
                        maneuver_type = maneuver.get('type', 'Unknown')
                        maneuver_country = maneuver.get('country', '')
                        maneuver_name = get_country_name(data, maneuver_country)
                        print(f"  - {maneuver_type} by {maneuver_name}")
            
            # Progress or status
            progress = play_data.get('progress', 0)
            if progress > 0:
                print(f"Progress: {progress}%")
            
            print()
    
    # Summary statistics
    print(f"{'='*70}")
    print(f"DIPLOMATIC TENSION SUMMARY")
    print(f"{'='*70}")
    print(f"Total Active Diplomatic Plays: {active_plays}")
    
    if escalation_risk:
        print(f"\nHIGH ESCALATION RISK SITUATIONS:")
        print(f"{'-'*50}")
        escalation_risk.sort(key=lambda x: x[1], reverse=True)
        for play_id, level, initiator, target in escalation_risk:
            print(f"Play #{play_id}: {initiator} vs {target} (Escalation: {level})")
    
    # Analyze by type
    play_types = {}
    countries_involved = set()
    
    for play_id, play_data in diplomatic_plays.items():
        if isinstance(play_data, dict):
            play_type = play_data.get('type', 'Unknown')
            play_types[play_type] = play_types.get(play_type, 0) + 1
            
            # Count countries involved
            initiator = play_data.get('initiator', '')
            target = play_data.get('target', '')
            if initiator:
                countries_involved.add(str(initiator))
            if target:
                countries_involved.add(str(target))
            
            # Add supporters and opponents
            for supporter in play_data.get('supporters', []):
                country = supporter.get('country', '')
                if country:
                    countries_involved.add(country)
            
            for opponent in play_data.get('opponents', []):
                country = opponent.get('country', '')
                if country:
                    countries_involved.add(country)
    
    if play_types:
        print(f"\nDIPLOMATIC PLAY TYPES:")
        print(f"{'-'*30}")
        for play_type, count in sorted(play_types.items(), key=lambda x: x[1], reverse=True):
            print(f"{play_type:<25} {count}")
    
    print(f"\nCOUNTRIES INVOLVED IN DIPLOMACY: {len(countries_involved)}")
    
    if len(countries_involved) > 0:
        print(f"\nMost Diplomatically Active Countries:")
        print(f"{'-'*40}")
        
        # Count involvement per country
        country_involvement = {}
        for play_id, play_data in diplomatic_plays.items():
            if isinstance(play_data, dict):
                initiator = play_data.get('initiator', '')
                target = play_data.get('target', '')
                
                if initiator:
                    country_involvement[initiator] = country_involvement.get(initiator, 0) + 1
                if target:
                    country_involvement[target] = country_involvement.get(target, 0) + 1
                
                for supporter in play_data.get('supporters', []):
                    country = supporter.get('country', '')
                    if country:
                        country_involvement[country] = country_involvement.get(country, 0) + 1
                
                for opponent in play_data.get('opponents', []):
                    country = opponent.get('country', '')
                    if country:
                        country_involvement[country] = country_involvement.get(country, 0) + 1
        
        sorted_involvement = sorted(country_involvement.items(), key=lambda x: x[1], reverse=True)[:10]
        for country, count in sorted_involvement:
            country_name = get_country_name(data, country)
            print(f"{country_name:<20} {count} plays")
    
    # War risk assessment
    high_risk_count = len([x for x in escalation_risk if x[1] >= 75])
    medium_risk_count = len([x for x in escalation_risk if 25 <= x[1] < 75])
    low_risk_count = len([x for x in escalation_risk if x[1] < 25])
    
    print(f"\nWAR RISK ASSESSMENT:")
    print(f"{'-'*25}")
    print(f"High Risk (75%+): {high_risk_count} plays")
    print(f"Medium Risk (25-74%): {medium_risk_count} plays")
    print(f"Low Risk (<25%): {low_risk_count} plays")
    
    if active_plays > 0:
        risk_percentage = (high_risk_count / active_plays) * 100
        print(f"Overall War Risk: {risk_percentage:.1f}% of plays at high escalation")


def main():
    parser = argparse.ArgumentParser(description='Analyze Victoria 3 diplomatic plays')
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
                analyze_diplomatic_plays(data)
            sys.stdout = original_stdout
            print(f"Diplomatic plays report saved to: {args.output}")
        else:
            analyze_diplomatic_plays(data)
            
    except Exception as e:
        print(f"Error analyzing save file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()