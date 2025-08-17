#!/usr/bin/env python3
"""
Victoria 3 Ruler Comparison Tool
Compares rulers between two sessions to show changes in leadership
"""

import json
import argparse
from pathlib import Path
from ruler_report import load_save_file, calculate_age, get_culture_name, get_interest_group_name, get_ruler_title, format_traits, load_humans

def get_ruler_info(data, country_id, country_info, current_date):
    """Extract ruler information for a country"""
    ruler_id = country_info.get('ruler')
    if not ruler_id or ruler_id == 4294967295:  # Invalid ruler ID
        return None
    
    # Get character database
    if 'character_manager' not in data or 'database' not in data['character_manager']:
        return None
    
    characters = data['character_manager']['database']
    ruler_char = characters.get(str(ruler_id))
    if not ruler_char:
        return None
    
    # Extract basic info
    first_name = ruler_char.get('first_name', 'Unknown')
    last_name = ruler_char.get('last_name', '')
    full_name = f"{first_name} {last_name}".strip()
    
    # Get age
    birth_date = ruler_char.get('birth_date', '')
    age = calculate_age(birth_date, current_date) if birth_date else 'Unknown'
    
    # Get government type for title
    government_type = country_info.get('government', 'unknown')
    ruler_gender = 'female' if 'Isabel' in first_name or 'Victoria' in first_name else 'male'
    title = get_ruler_title(government_type, ruler_gender)
    
    # Get interest group
    ig_name = None
    if 'interest_groups' in data and 'database' in data['interest_groups']:
        ig_db = data['interest_groups']['database']
        
        # First, check if ruler leads an IG
        for ig_id, ig in ig_db.items():
            if isinstance(ig, dict) and ig.get('country') == int(country_id):
                if ig.get('leader') == ruler_id:
                    ig_name = get_interest_group_name(ig_id, data)
                    break
        
        # If ruler doesn't lead an IG, find the most powerful IG in government
        if not ig_name:
            max_clout = 0
            for ig_id, ig in ig_db.items():
                if isinstance(ig, dict) and ig.get('country') == int(country_id):
                    if ig.get('in_government', False):
                        clout = ig.get('clout', 0)
                        if clout > max_clout:
                            max_clout = clout
                            ig_name = get_interest_group_name(ig_id, data)
    
    if not ig_name:
        ig_name = 'None'
    
    # Get traits
    traits = ruler_char.get('traits', [])
    traits_str = format_traits(traits)
    
    # Get culture
    culture_id = ruler_char.get('culture')
    culture_name = get_culture_name(culture_id, data) if culture_id else 'Unknown'
    
    return {
        'title': title,
        'name': full_name,
        'age': age,
        'interest_group': ig_name,
        'traits': traits_str,
        'culture': culture_name
    }

def compare_rulers(session1_file, session2_file, humans_only=True):
    """Compare rulers between two sessions"""
    print(f"Loading first session: {session1_file}")
    data1 = load_save_file(session1_file)
    date1 = data1.get('date', 'Unknown')
    
    print(f"Loading second session: {session2_file}")
    data2 = load_save_file(session2_file)
    date2 = data2.get('date', 'Unknown')
    
    # Load human countries if filtering
    human_tags = load_humans() if humans_only else []
    
    # Get country managers
    country_db1 = data1.get('country_manager', {}).get('database', {})
    country_db2 = data2.get('country_manager', {}).get('database', {})
    
    # Collect ruler data
    rulers1 = {}
    rulers2 = {}
    
    # Process first session
    for country_id, country_info in country_db1.items():
        if country_id == '16777216':  # Skip 'none' country
            continue
        if not isinstance(country_info, dict):
            continue
        
        tag = country_info.get('definition')
        if not tag:
            continue
        
        if humans_only and human_tags and tag not in human_tags:
            continue
        
        ruler_info = get_ruler_info(data1, country_id, country_info, date1)
        if ruler_info:
            rulers1[tag] = ruler_info
    
    # Process second session
    for country_id, country_info in country_db2.items():
        if country_id == '16777216':  # Skip 'none' country
            continue
        if not isinstance(country_info, dict):
            continue
        
        tag = country_info.get('definition')
        if not tag:
            continue
        
        if humans_only and human_tags and tag not in human_tags:
            continue
        
        ruler_info = get_ruler_info(data2, country_id, country_info, date2)
        if ruler_info:
            rulers2[tag] = ruler_info
    
    # Print comparison report
    print("\n" + "="*100)
    print("Victoria 3 Ruler Comparison Report")
    print(f"Session 1: {date1} | Session 2: {date2}")
    print("="*100)
    
    # Get all country tags
    all_tags = sorted(set(rulers1.keys()) | set(rulers2.keys()))
    
    # Track changes
    changes = []
    no_changes = []
    
    for tag in all_tags:
        ruler1 = rulers1.get(tag)
        ruler2 = rulers2.get(tag)
        
        if ruler1 and ruler2:
            # Compare rulers
            if ruler1['name'] != ruler2['name']:
                # New ruler
                changes.append({
                    'tag': tag,
                    'type': 'NEW_RULER',
                    'old': ruler1,
                    'new': ruler2
                })
            elif ruler1['interest_group'] != ruler2['interest_group']:
                # Same ruler, different IG
                changes.append({
                    'tag': tag,
                    'type': 'IG_CHANGE',
                    'old': ruler1,
                    'new': ruler2
                })
            elif ruler1['title'] != ruler2['title']:
                # Same ruler, different title (government change)
                changes.append({
                    'tag': tag,
                    'type': 'TITLE_CHANGE',
                    'old': ruler1,
                    'new': ruler2
                })
            else:
                # No significant change (just aged)
                no_changes.append({
                    'tag': tag,
                    'ruler': ruler2
                })
        elif ruler1 and not ruler2:
            # Country lost ruler or disappeared
            changes.append({
                'tag': tag,
                'type': 'LOST_RULER',
                'old': ruler1,
                'new': None
            })
        elif not ruler1 and ruler2:
            # Country gained ruler
            changes.append({
                'tag': tag,
                'type': 'NEW_COUNTRY',
                'old': None,
                'new': ruler2
            })
    
    # Print changes
    if changes:
        print("\n" + "="*100)
        print("RULER CHANGES")
        print("="*100)
        
        for change in changes:
            tag = change['tag']
            change_type = change['type']
            old = change['old']
            new = change['new']
            
            print(f"\n{tag}:")
            
            if change_type == 'NEW_RULER':
                print(f"  ✦ NEW RULER")
                print(f"    Old: {old['title']} {old['name']} (Age {old['age']}, {old['interest_group']})")
                print(f"    New: {new['title']} {new['name']} (Age {new['age']}, {new['interest_group']})")
                print(f"    New Ruler Traits: {new['traits']}")
                
            elif change_type == 'IG_CHANGE':
                print(f"  ⚡ INTEREST GROUP CHANGE")
                print(f"    Ruler: {new['title']} {new['name']}")
                print(f"    Old IG: {old['interest_group']}")
                print(f"    New IG: {new['interest_group']}")
                
            elif change_type == 'TITLE_CHANGE':
                print(f"  👑 TITLE/GOVERNMENT CHANGE")
                print(f"    Ruler: {new['name']}")
                print(f"    Old Title: {old['title']}")
                print(f"    New Title: {new['title']}")
                
            elif change_type == 'LOST_RULER':
                print(f"  ✗ RULER LOST")
                print(f"    Was: {old['title']} {old['name']} (Age {old['age']}, {old['interest_group']})")
                
            elif change_type == 'NEW_COUNTRY':
                print(f"  ✓ NEW COUNTRY/RULER")
                print(f"    Now: {new['title']} {new['name']} (Age {new['age']}, {new['interest_group']})")
    
    # Print unchanged
    if no_changes:
        print("\n" + "="*100)
        print("UNCHANGED RULERS")
        print("="*100)
        
        print("\n" + "-"*100)
        print(f"{'Country':<8} {'Title':<12} {'Ruler Name':<25} {'Age S1':<7} {'Age S2':<7} {'Interest Group':<20}")
        print("-"*100)
        
        for item in no_changes:
            tag = item['tag']
            ruler = item['ruler']
            old_ruler = rulers1[tag]
            
            print(f"{tag:<8} {ruler['title']:<12} {ruler['name']:<25} {old_ruler['age']:<7} {ruler['age']:<7} {ruler['interest_group']:<20}")
    
    # Summary
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Total countries tracked: {len(all_tags)}")
    print(f"Ruler changes: {len([c for c in changes if c['type'] == 'NEW_RULER'])}")
    print(f"IG changes: {len([c for c in changes if c['type'] == 'IG_CHANGE'])}")
    print(f"Title/Gov changes: {len([c for c in changes if c['type'] == 'TITLE_CHANGE'])}")
    print(f"Unchanged rulers: {len(no_changes)}")

def main():
    parser = argparse.ArgumentParser(description='Compare rulers between two Victoria 3 sessions')
    parser.add_argument('session1', help='Path to first extracted save file (JSON)')
    parser.add_argument('session2', help='Path to second extracted save file (JSON)')
    parser.add_argument('--all', action='store_true', help='Include all countries (not just humans)')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Check if files exist
    if not Path(args.session1).exists():
        print(f"Error: First session file not found: {args.session1}")
        return
    
    if not Path(args.session2).exists():
        print(f"Error: Second session file not found: {args.session2}")
        return
    
    humans_only = not args.all
    
    if args.output:
        # Redirect output to file
        import sys
        original_stdout = sys.stdout
        with open(args.output, 'w') as f:
            sys.stdout = f
            compare_rulers(args.session1, args.session2, humans_only)
        sys.stdout = original_stdout
        print(f"Comparison saved to: {args.output}")
    else:
        compare_rulers(args.session1, args.session2, humans_only)

if __name__ == '__main__':
    main()