#!/usr/bin/env python3
"""
Victoria 3 Interest Groups Report
Shows interest group composition, clout, and political status for human nations
"""

import json
import sys
import os
from pathlib import Path
import argparse

# IG Type display names (more readable than ig_armed_forces etc)
IG_DISPLAY_NAMES = {
    'ig_armed_forces': 'Armed Forces',
    'ig_industrialists': 'Industrialists',
    'ig_intelligentsia': 'Intelligentsia',
    'ig_landowners': 'Landowners',
    'ig_petty_bourgeoisie': 'Petty Bourgeoisie',
    'ig_rural_folk': 'Rural Folk',
    'ig_trade_unions': 'Trade Unions',
    'ig_devout': 'Devout',
}

def load_humans_list():
    """Load list of human-controlled countries from humans.txt"""
    humans_file = Path(__file__).parent / 'humans.txt'
    if not humans_file.exists():
        print(f"Warning: {humans_file} not found. Using default list.")
        return ['GBR', 'USA', 'FRA', 'BIC', 'POR', 'CHI', 'ITA', 'SPA', 'TUR', 'RUS', 'JAP', 'YUG']
    
    humans = []
    with open(humans_file, 'r') as f:
        for line in f:
            tag = line.strip()
            if tag and not tag.startswith('#'):
                humans.append(tag)
    return humans

def get_latest_save():
    """Get the most recent extracted save file"""
    extracted_dir = Path(__file__).parent / 'extracted-saves'
    if not extracted_dir.exists():
        return None
    
    json_files = list(extracted_dir.glob('*_extracted.json'))
    if not json_files:
        return None
    
    # Return the most recently modified file
    return str(max(json_files, key=lambda f: f.stat().st_mtime))

def analyze_interest_groups(save_file, humans_only=True):
    """Analyze interest groups from save file"""
    
    # Load the save file
    print(f"Loading save file: {save_file}")
    with open(save_file, 'r') as f:
        data = json.load(f)
    
    # Get the game date
    game_date = data.get('date', 'Unknown')
    
    # Build country ID to tag mapping
    country_map = {}
    if 'country_manager' in data and 'database' in data['country_manager']:
        for country_id, country_data in data['country_manager']['database'].items():
            if 'definition' in country_data:
                country_map[int(country_id)] = country_data['definition']
    
    # Build reverse mapping (tag to ID)
    tag_to_id = {tag: cid for cid, tag in country_map.items()}
    
    # Get list of countries to analyze
    if humans_only:
        countries_to_analyze = load_humans_list()
    else:
        countries_to_analyze = list(country_map.values())
    
    # Collect interest groups data
    country_igs = {}
    
    if 'interest_groups' in data and 'database' in data['interest_groups']:
        for ig_id, ig_data in data['interest_groups']['database'].items():
            if 'country' not in ig_data:
                continue
            
            country_id = ig_data['country']
            if country_id not in country_map:
                continue
            
            country_tag = country_map[country_id]
            if country_tag not in countries_to_analyze:
                continue
            
            if country_tag not in country_igs:
                country_igs[country_tag] = []
            
            # Extract IG info
            ig_info = {
                'type': ig_data.get('definition', 'unknown'),
                'clout': ig_data.get('clout', 0),
                'in_government': ig_data.get('in_government', False),
                'political_strength': ig_data.get('political_strength', 0),
                'influence_type': ig_data.get('influence_type', 'normal'),
                'approval': ig_data.get('approval', 0),
                'approval_state': ig_data.get('approval_state', 'neutral'),
            }
            
            country_igs[country_tag].append(ig_info)
    
    # Sort IGs within each country by clout
    for country_tag in country_igs:
        country_igs[country_tag].sort(key=lambda x: x['clout'], reverse=True)
    
    return country_igs, game_date

def format_report(country_igs, game_date):
    """Format the interest groups report"""
    lines = []
    lines.append("=" * 80)
    lines.append("Victoria 3 Interest Groups Report")
    lines.append(f"Date: {game_date}")
    lines.append("=" * 80)
    lines.append("")
    
    # Sort countries alphabetically
    sorted_countries = sorted(country_igs.keys())
    
    for country_tag in sorted_countries:
        igs = country_igs[country_tag]
        
        lines.append(f"{country_tag}")
        lines.append("-" * 40)
        
        # Separate IGs by status
        in_government = []
        in_opposition = []
        marginalized = []
        
        for ig in igs:
            ig_name = IG_DISPLAY_NAMES.get(ig['type'], ig['type'])
            clout_pct = ig['clout'] * 100
            
            # Add [Powerful] label if clout > 20%
            power_label = " [Powerful]" if clout_pct > 20 else ""
            
            ig_str = f"  {ig_name:20} {clout_pct:5.1f}%{power_label}"
            
            # Determine status: IGs below 5% clout are marginalized unless in government
            if ig['in_government']:
                in_government.append(ig_str)
            elif clout_pct < 5.0 and not ig['in_government']:
                # Marginalized if below 5% and not in government
                # (Note: We can't check ruler support without more data)
                marginalized.append(ig_str)
            else:
                in_opposition.append(ig_str)
        
        # Display groups
        if in_government:
            lines.append("In Government:")
            for ig_str in in_government:
                lines.append(ig_str)
        
        if in_opposition:
            lines.append("In Opposition:")
            for ig_str in in_opposition:
                lines.append(ig_str)
        
        if marginalized:
            lines.append("Marginalized:")
            for ig_str in marginalized:
                lines.append(ig_str)
        
        # Calculate totals
        total_gov_clout = sum(ig['clout'] for ig in igs if ig['in_government']) * 100
        # Opposition: not in government and clout >= 5%
        total_opp_clout = sum(ig['clout'] for ig in igs if not ig['in_government'] and ig['clout'] >= 0.05) * 100
        # Marginalized: not in government and clout < 5%
        total_marg_clout = sum(ig['clout'] for ig in igs if not ig['in_government'] and ig['clout'] < 0.05) * 100
        
        lines.append("")
        lines.append(f"Summary: Gov {total_gov_clout:.1f}% | Opp {total_opp_clout:.1f}% | Marg {total_marg_clout:.1f}%")
        lines.append("")
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 interest groups report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted save JSON file')
    parser.add_argument('--all', action='store_true', help='Include all countries, not just humans')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Determine save file to use
    save_file = args.save_file
    if not save_file:
        save_file = get_latest_save()
        if not save_file:
            print("Error: No extracted save files found in extracted-saves/")
            print("Please run extract_save.py first to extract a save file.")
            sys.exit(1)
    
    if not os.path.exists(save_file):
        print(f"Error: Save file not found: {save_file}")
        sys.exit(1)
    
    # Analyze interest groups
    country_igs, game_date = analyze_interest_groups(save_file, humans_only=not args.all)
    
    # Format report
    report = format_report(country_igs, game_date)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)

if __name__ == '__main__':
    main()