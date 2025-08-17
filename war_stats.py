#!/usr/bin/env python3
"""
Victoria 3 War Statistics Tool

Calculates comprehensive war statistics and patterns from Victoria 3 save files:
- War frequency and duration analysis
- Geographic hotspots and patterns
- Belligerent nations ranking
- War timeline and trends
- Casualty and participation statistics
"""

import json
import argparse
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict


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
    
    # Try to find the country in country_manager
    country_manager = data.get('country_manager', {}).get('database', {})
    country_data = country_manager.get(str(tag), {})
    
    if isinstance(country_data, dict):
        country_tag = country_data.get('definition', '')
        if country_tag:
            return country_tag
    
    return str(tag)


def get_province_info(data, province_id):
    """Get province information including state and region."""
    if not province_id:
        return "Unknown", "Unknown"
    
    # Look up province in the provinces data
    provinces = data.get('provinces', {})
    province_data = provinces.get(str(province_id), {})
    
    if province_data:
        state_id = province_data.get('state', '')
        if state_id:
            # Try to get state region information
            states = data.get('state_manager', {}).get('database', {})
            state_data = states.get(str(state_id), {})
            if state_data:
                region = state_data.get('region', '')
                return f"State {state_id}", region
    
    return f"Province {province_id}", "Unknown Region"


def parse_date(date_str):
    """Parse Victoria 3 date format (YYYY.M.D.H) to year."""
    if not date_str:
        return None
    try:
        parts = date_str.split('.')
        if len(parts) >= 1:
            return int(parts[0])
    except:
        pass
    return None


def calculate_war_stats(data):
    """Calculate comprehensive war statistics."""
    wars = data.get('war_manager', {}).get('database', {})
    battles = data.get('battle_manager', {}).get('database', {})
    game_date = data.get('meta_data', {}).get('game_date', 'Unknown')
    current_year = parse_date(game_date) or 1883
    
    print(f"\n{'='*80}")
    print(f"Victoria 3 War Statistics Analysis - {game_date}")
    print(f"{'='*80}\n")
    
    if not wars:
        print("No wars data found in save file.")
        return
    
    # Initialize statistics
    total_wars = len(wars)
    ongoing_wars = 0
    completed_wars = 0
    total_battles = len(battles)
    wars_by_year = defaultdict(int)
    battles_by_year = defaultdict(int)
    war_participation = defaultdict(int)
    battle_participation = defaultdict(int)
    geographic_distribution = defaultdict(int)
    war_durations = []
    battle_results = defaultdict(int)
    
    # Analyze each war
    for war_id, war_data in wars.items():
        if isinstance(war_data, dict):
            # Check if ongoing
            if 'war_support' in war_data or 'attacker' in war_data:
                ongoing_wars += 1
            else:
                completed_wars += 1
            
            # Get war start date
            start_date = war_data.get('start_date', '')
            start_year = parse_date(start_date)
            if start_year:
                wars_by_year[start_year] += 1
            
            # Calculate war duration for completed wars
            end_date = war_data.get('end_date', '')
            if start_date and end_date:
                start_year = parse_date(start_date)
                end_year = parse_date(end_date)
                if start_year and end_year:
                    duration = end_year - start_year
                    war_durations.append(max(1, duration))  # Minimum 1 year
            
            # Count participants from war goals (more accurate)
            attacker_goals = war_data.get('attacker_peace_deal', {}).get('pressed_attacker_war_goals', [])
            defender_goals = war_data.get('defender_peace_deal', {}).get('pressed_defender_war_goals', [])
            
            # Count unique participants from attacker side
            attacker_participants = set()
            for goal in attacker_goals:
                if isinstance(goal, dict):
                    holder = goal.get('holder', '')
                    creator = goal.get('creator', '')
                    if holder:
                        attacker_participants.add(get_country_name(data, holder))
                    if creator and creator != holder:
                        attacker_participants.add(get_country_name(data, creator))
            
            # Count unique participants from defender side  
            defender_participants = set()
            for goal in defender_goals:
                if isinstance(goal, dict):
                    holder = goal.get('holder', '')
                    creator = goal.get('creator', '')
                    if holder:
                        defender_participants.add(get_country_name(data, holder))
                    if creator and creator != holder:
                        defender_participants.add(get_country_name(data, creator))
            
            # Add to war participation counts
            for participant in attacker_participants:
                war_participation[participant] += 1
            for participant in defender_participants:
                war_participation[participant] += 1
            
    # Analyze battles separately from battle_manager
    for battle_id, battle_data in battles.items():
        if isinstance(battle_data, dict):
            # Battle date
            battle_date = battle_data.get('date', '')
            battle_year = parse_date(battle_date)
            if battle_year:
                battles_by_year[battle_year] += 1
            
            # Get war info to determine participants
            battle_war = battle_data.get('war', '')
            if battle_war and str(battle_war) in wars:
                war_info = wars[str(battle_war)]
                
                # Try to get participants from war goals
                attacker_goals = war_info.get('attacker_peace_deal', {}).get('pressed_attacker_war_goals', [])
                defender_goals = war_info.get('defender_peace_deal', {}).get('pressed_defender_war_goals', [])
                
                # Count attacker participation
                for goal in attacker_goals:
                    if isinstance(goal, dict):
                        holder = goal.get('holder', '')
                        if holder:
                            country_tag = get_country_name(data, holder)
                            battle_participation[country_tag] += 1
                
                # Count defender participation
                for goal in defender_goals:
                    if isinstance(goal, dict):
                        holder = goal.get('holder', '')
                        if holder:
                            country_tag = get_country_name(data, holder)
                            battle_participation[country_tag] += 1
            
            # Geographic location with province info
            province = battle_data.get('province', '')
            if province:
                state_name, region = get_province_info(data, province)
                geographic_distribution[f"{state_name} ({region})"] += 1
            
            # Battle result
            result = battle_data.get('status', '')
            if result:
                battle_results[result] += 1
    
    # Display basic statistics
    print(f"BASIC WAR STATISTICS")
    print(f"{'-'*50}")
    print(f"Total Wars: {total_wars}")
    print(f"Ongoing Wars: {ongoing_wars}")
    print(f"Completed Wars: {completed_wars}")
    print(f"Total Battles: {total_battles}")
    print(f"Average Battles per War: {total_battles/total_wars:.1f}" if total_wars > 0 else "N/A")
    
    # War duration analysis
    if war_durations:
        avg_duration = sum(war_durations) / len(war_durations)
        max_duration = max(war_durations)
        min_duration = min(war_durations)
        print(f"\nWAR DURATION ANALYSIS")
        print(f"{'-'*50}")
        print(f"Average War Duration: {avg_duration:.1f} years")
        print(f"Longest War: {max_duration} years")
        print(f"Shortest War: {min_duration} years")
    
    # Wars by year
    if wars_by_year:
        print(f"\nWARS STARTED BY YEAR")
        print(f"{'-'*30}")
        for year in sorted(wars_by_year.keys()):
            count = wars_by_year[year]
            print(f"{year}: {count} wars")
        
        # Calculate war frequency trends
        recent_years = [y for y in wars_by_year.keys() if y >= current_year - 10]
        if len(recent_years) >= 3:
            recent_wars = sum(wars_by_year[y] for y in recent_years)
            avg_recent = recent_wars / len(recent_years)
            print(f"\nRecent War Activity (last 10 years): {avg_recent:.1f} wars per year")
    
    # Battles by year
    if battles_by_year:
        print(f"\nBATTLES BY YEAR")
        print(f"{'-'*30}")
        for year in sorted(battles_by_year.keys()):
            count = battles_by_year[year]
            print(f"{year}: {count} battles")
    
    # Most belligerent nations
    if war_participation:
        print(f"\nMOST BELLIGERENT NATIONS (War Participation)")
        print(f"{'-'*60}")
        sorted_participants = sorted(war_participation.items(), key=lambda x: x[1], reverse=True)[:15]
        
        print(f"{'Country':<20} {'Wars':<6} {'% of Total'}")
        print(f"{'-'*35}")
        for country, count in sorted_participants:
            country_name = get_country_name(data, country)
            percentage = (count / total_wars) * 100 if total_wars > 0 else 0
            print(f"{country_name:<20} {count:<6} {percentage:6.1f}%")
    
    # Most active battle participants
    if battle_participation:
        print(f"\nMOST ACTIVE BATTLE PARTICIPANTS")
        print(f"{'-'*50}")
        sorted_battle_participants = sorted(battle_participation.items(), key=lambda x: x[1], reverse=True)[:15]
        
        print(f"{'Country':<20} {'Battles':<8} {'% of Total'}")
        print(f"{'-'*38}")
        for country, count in sorted_battle_participants:
            country_name = get_country_name(data, country)
            percentage = (count / total_battles) * 100 if total_battles > 0 else 0
            print(f"{country_name:<20} {count:<8} {percentage:6.1f}%")
    
    # Geographic hotspots
    if geographic_distribution:
        print(f"\nGEOGRAPHIC BATTLE HOTSPOTS")
        print(f"{'-'*60}")
        sorted_locations = sorted(geographic_distribution.items(), key=lambda x: x[1], reverse=True)[:15]
        
        print(f"{'Location':<40} {'Battles':<8} {'% of Total'}")
        print(f"{'-'*58}")
        for location, count in sorted_locations:
            percentage = (count / total_battles) * 100 if total_battles > 0 else 0
            print(f"{location:<40} {count:<8} {percentage:6.1f}%")
            
        # Regional analysis
        print(f"\nBATTLES BY STRATEGIC REGION")
        print(f"{'-'*40}")
        regional_battles = defaultdict(int)
        for location, count in geographic_distribution.items():
            if "(" in location and ")" in location:
                region = location.split("(")[1].split(")")[0]
                regional_battles[region] += count
        
        sorted_regions = sorted(regional_battles.items(), key=lambda x: x[1], reverse=True)[:10]
        for region, count in sorted_regions:
            percentage = (count / total_battles) * 100 if total_battles > 0 else 0
            print(f"{region:<25} {count:<8} {percentage:6.1f}%")
    
    # Battle outcomes
    if battle_results:
        print(f"\nBATTLE OUTCOME DISTRIBUTION")
        print(f"{'-'*40}")
        
        print(f"{'Result':<20} {'Count':<8} {'% of Total'}")
        print(f"{'-'*38}")
        for result, count in sorted(battle_results.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_battles) * 100 if total_battles > 0 else 0
            print(f"{result:<20} {count:<8} {percentage:6.1f}%")
    
    # War intensity analysis
    print(f"\nWAR INTENSITY ANALYSIS")
    print(f"{'-'*40}")
    
    # Calculate intensity metrics
    total_war_years = sum(wars_by_year.values())
    total_battle_years = len([y for y in battles_by_year.keys() if battles_by_year[y] > 0])
    
    if wars_by_year:
        peak_war_year = max(wars_by_year.items(), key=lambda x: x[1])
        print(f"Peak War Year: {peak_war_year[0]} ({peak_war_year[1]} wars)")
    
    if battles_by_year:
        peak_battle_year = max(battles_by_year.items(), key=lambda x: x[1])
        print(f"Peak Battle Year: {peak_battle_year[0]} ({peak_battle_year[1]} battles)")
        
        bloodiest_period = []
        for year in sorted(battles_by_year.keys())[-5:]:  # Last 5 years of data
            if battles_by_year[year] > 0:
                bloodiest_period.append((year, battles_by_year[year]))
        
        if bloodiest_period:
            print(f"Recent Battle Activity:")
            for year, count in bloodiest_period:
                print(f"  {year}: {count} battles")
    
    # Peace vs war periods analysis
    campaign_start = 1836
    campaign_years = current_year - campaign_start + 1
    war_years = len([y for y in wars_by_year.keys() if wars_by_year[y] > 0])
    peace_years = campaign_years - war_years
    
    print(f"\nPEACE VS WAR ANALYSIS")
    print(f"{'-'*30}")
    print(f"Campaign Duration: {campaign_years} years")
    print(f"Years with Wars: {war_years}")
    print(f"Peaceful Years: {peace_years}")
    print(f"Peace Percentage: {(peace_years/campaign_years)*100:.1f}%" if campaign_years > 0 else "N/A")
    
    # War escalation trends
    if len(wars_by_year) >= 3:
        recent_years = sorted(wars_by_year.keys())[-5:]  # Last 5 years
        early_years = sorted(wars_by_year.keys())[:5]   # First 5 years
        
        recent_avg = sum(wars_by_year[y] for y in recent_years) / len(recent_years)
        early_avg = sum(wars_by_year[y] for y in early_years) / len(early_years)
        
        print(f"\nWAR TREND ANALYSIS")
        print(f"{'-'*25}")
        print(f"Early Period Average: {early_avg:.1f} wars/year")
        print(f"Recent Period Average: {recent_avg:.1f} wars/year")
        
        if recent_avg > early_avg * 1.5:
            print("📈 War activity is ESCALATING significantly")
        elif recent_avg > early_avg * 1.1:
            print("📈 War activity is increasing")
        elif recent_avg < early_avg * 0.5:
            print("📉 War activity is declining significantly")
        elif recent_avg < early_avg * 0.9:
            print("📉 War activity is decreasing")
        else:
            print("📊 War activity is relatively stable")


def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 war statistics')
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
                calculate_war_stats(data)
            sys.stdout = original_stdout
            print(f"War statistics saved to: {args.output}")
        else:
            calculate_war_stats(data)
            
    except Exception as e:
        print(f"Error analyzing save file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()