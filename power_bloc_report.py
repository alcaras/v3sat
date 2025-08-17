#!/usr/bin/env python3
"""
Victoria 3 Power Bloc Report Generator

Analyzes power blocs in Victoria 3 save files, including:
- Power bloc names and leaders
- Member countries
- Principles enacted
- Total GDP of each bloc
- Mandate progress
"""

import json
import argparse
import os
from pathlib import Path
from datetime import datetime

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
            # Definition is usually just the tag directly (e.g., "USA", "GBR")
            return definition
    return f"ID_{country_id}"

def get_country_name(countries, country_id):
    """Get country name or tag from country ID."""
    country = countries.get(str(country_id), {})
    if isinstance(country, dict):
        # Try to get custom name first
        if 'name' in country:
            if isinstance(country['name'], dict) and 'custom' in country['name']:
                return country['name']['custom']
        # Fall back to tag
        return get_country_tag(countries, country_id)
    return f"Unknown_{country_id}"

def get_country_gdp(countries, country_id):
    """Get the latest GDP value for a country."""
    country = countries.get(str(country_id), {})
    if not isinstance(country, dict):
        return 0.0
    
    gdp_data = country.get('gdp', {})
    if not gdp_data:
        return 0.0
    
    # GDP data is stored in channels, get the most recent channel
    channels = gdp_data.get('channels', {})
    if channels:
        # Get the channel with the highest index (most recent)
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
                # The last value in the array is the most recent
                return float(values[-1])
    
    return 0.0

def format_principles(principles):
    """Format principle names to be more readable."""
    formatted = []
    for principle in principles:
        # Remove 'principle_' prefix and replace underscores
        clean = principle.replace('principle_', '').replace('_', ' ').title()
        # Handle numbered principles (e.g., "External Trade 3")
        parts = clean.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            clean = f"{parts[0]} (Tier {parts[1]})"
        formatted.append(clean)
    return formatted

def format_identity(identity):
    """Format power bloc identity/type to be more readable."""
    if not identity:
        return "Unknown Type"
    
    # Remove 'identity_' prefix and format
    clean = identity.replace('identity_', '').replace('_', ' ').title()
    
    # Map to cleaner names
    identity_map = {
        'Trade League': 'Trade League',
        'Sovereign Empire': 'Sovereign Empire',
        'Military Treaty': 'Military Treaty',
        'Ideological Union': 'Ideological Union',
        'Religious Bloc': 'Religious Bloc',
        'Power Bloc': 'Power Bloc'  # Generic fallback
    }
    
    return identity_map.get(clean, clean)

def get_subject_relationships(save_data):
    """Extract subject relationships from pacts."""
    pacts = save_data.get('pacts', {}).get('database', {})
    subjects = {}  # overlord_id -> list of subject_ids
    
    # Subject pact types in Victoria 3
    subject_types = ['dominion', 'puppet', 'protectorate', 'colony', 'personal_union', 'chartered_company']
    
    for pact_id, pact in pacts.items():
        if not isinstance(pact, dict):
            continue
        
        action = pact.get('action', '')
        if action in subject_types:
            targets = pact.get('targets', {})
            overlord = targets.get('first')
            subject = targets.get('second')
            
            if overlord and subject:
                if overlord not in subjects:
                    subjects[overlord] = []
                subjects[overlord].append(subject)
    
    return subjects

def analyze_power_blocs(save_data):
    """Analyze power blocs in the save data."""
    countries = save_data.get('country_manager', {}).get('database', {})
    power_blocs = save_data.get('power_bloc_manager', {}).get('database', {})
    
    # Get subject relationships
    subject_relationships = get_subject_relationships(save_data)
    
    results = []
    
    for bloc_id, bloc in power_blocs.items():
        if not isinstance(bloc, dict):
            continue
        
        if bloc.get('status') != 'active':
            continue
        
        # Get bloc name
        name_data = bloc.get('name', {})
        if isinstance(name_data, dict) and 'name' in name_data:
            name_data = name_data['name']
        
        if isinstance(name_data, dict) and 'custom' in name_data:
            bloc_name = name_data['custom']
        else:
            bloc_name = f"Power Bloc {bloc_id}"
        
        # Get leader
        leader_id = bloc.get('leader')
        leader_tag = get_country_tag(countries, leader_id)
        leader_name = get_country_name(countries, leader_id)
        
        # Get founding date
        founding_date = bloc.get('founding_date', 'Unknown')
        
        # Get identity/type
        identity = bloc.get('identity', '')
        
        # Get principles
        principles_data = bloc.get('principles', {})
        if isinstance(principles_data, dict) and 'value' in principles_data:
            principles = principles_data['value']
        elif isinstance(principles_data, list):
            principles = principles_data
        else:
            principles = []
        
        # Get mandate progress
        mandate_progress = bloc.get('mandate_progress', 0)
        
        # Find all member countries
        members = []
        total_gdp = 0.0
        direct_members = set()  # Track direct members to find their subjects
        
        # First pass: find direct members
        for country_id, country in countries.items():
            if not isinstance(country, dict):
                continue
            
            # Check if this country is in this power bloc
            if country.get('power_bloc_as_core') == int(bloc_id):
                direct_members.add(int(country_id))
                tag = get_country_tag(countries, country_id)
                name = get_country_name(countries, country_id)
                gdp = get_country_gdp(countries, country_id)
                join_date = country.get('power_bloc_join_date', 'Unknown')
                
                # Check if this is the leader
                is_leader = (int(country_id) == leader_id)
                
                members.append({
                    'tag': tag,
                    'name': name,
                    'gdp': gdp,
                    'join_date': join_date,
                    'is_leader': is_leader,
                    'is_subject': False
                })
                total_gdp += gdp
        
        # Second pass: add subjects of members
        for member_id in direct_members:
            if member_id in subject_relationships:
                for subject_id in subject_relationships[member_id]:
                    # Check if subject is already a direct member (shouldn't happen but be safe)
                    if subject_id in direct_members:
                        continue
                    
                    subject = countries.get(str(subject_id), {})
                    if isinstance(subject, dict):
                        tag = get_country_tag(countries, subject_id)
                        name = get_country_name(countries, subject_id)
                        gdp = get_country_gdp(countries, subject_id)
                        
                        # Get overlord tag for display
                        overlord_tag = get_country_tag(countries, member_id)
                        
                        members.append({
                            'tag': tag,
                            'name': name,
                            'gdp': gdp,
                            'join_date': f'Subject of {overlord_tag}',
                            'is_leader': False,
                            'is_subject': True
                        })
                        total_gdp += gdp
        
        # Sort members: leader first, then direct members by GDP, subjects grouped with overlords
        members.sort(key=lambda x: (not x['is_leader'], x['is_subject'], -x['gdp']))
        
        results.append({
            'id': bloc_id,
            'name': bloc_name,
            'identity': identity,
            'leader_tag': leader_tag,
            'leader_name': leader_name,
            'founding_date': founding_date,
            'principles': principles,
            'mandate_progress': mandate_progress,
            'members': members,
            'total_gdp': total_gdp,
            'member_count': len(members)
        })
    
    # Sort blocs by total GDP
    results.sort(key=lambda x: -x['total_gdp'])
    
    return results

def format_gdp(gdp):
    """Format GDP value for display."""
    if gdp >= 1e9:
        return f"${gdp/1e9:.2f}B"
    elif gdp >= 1e6:
        return f"${gdp/1e6:.1f}M"
    else:
        return f"${gdp/1e3:.0f}K"

def generate_report(power_blocs, output_file=None):
    """Generate the power bloc report."""
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append("VICTORIA 3 POWER BLOC REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Summary
    total_blocs = len(power_blocs)
    total_members = sum(bloc['member_count'] for bloc in power_blocs)
    total_global_gdp = sum(bloc['total_gdp'] for bloc in power_blocs)
    
    report_lines.append(f"Total Power Blocs: {total_blocs}")
    report_lines.append(f"Total Member Countries: {total_members}")
    report_lines.append(f"Combined GDP of All Blocs: {format_gdp(total_global_gdp)}")
    report_lines.append("")
    report_lines.append("-" * 80)
    
    # Detailed bloc information
    for i, bloc in enumerate(power_blocs, 1):
        report_lines.append("")
        report_lines.append(f"{i}. {bloc['name']} ({format_identity(bloc['identity'])})")
        report_lines.append("=" * len(f"{i}. {bloc['name']}"))
        report_lines.append("")
        report_lines.append(f"Type: {format_identity(bloc['identity'])}")
        report_lines.append(f"Leader: {bloc['leader_tag']} ({bloc['leader_name']})")
        report_lines.append(f"Founded: {bloc['founding_date']}")
        report_lines.append(f"Total GDP: {format_gdp(bloc['total_gdp'])}")
        report_lines.append(f"Member Count: {bloc['member_count']}")
        report_lines.append(f"Mandate Progress: {bloc['mandate_progress']}")
        report_lines.append("")
        
        # Principles
        if bloc['principles']:
            report_lines.append("Principles:")
            formatted_principles = format_principles(bloc['principles'])
            for principle in formatted_principles:
                report_lines.append(f"  • {principle}")
            report_lines.append("")
        
        # Members
        report_lines.append("Members:")
        for member in bloc['members']:
            role = " (LEADER)" if member['is_leader'] else ""
            gdp_str = format_gdp(member['gdp'])
            report_lines.append(f"  • {member['tag']:<4} - GDP: {gdp_str:<10} - Joined: {member['join_date']}{role}")
        
        report_lines.append("")
        report_lines.append("-" * 80)
    
    # Output
    report_text = '\n'.join(report_lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_text)
        print(f"Report saved to: {output_file}")
    
    print(report_text)
    
    return report_text

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 power bloc reports')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output', help='Output file for the report')
    parser.add_argument('--csv', action='store_true', help='Generate CSV output')
    
    args = parser.parse_args()
    
    # Determine save file to use
    if args.save_file:
        save_path = args.save_file
    else:
        # Use latest extracted save
        extracted_dir = Path('extracted-saves')
        if not extracted_dir.exists():
            print("Error: extracted-saves directory not found")
            return
        
        json_files = list(extracted_dir.glob('*_extracted.json'))
        if not json_files:
            print("Error: No extracted save files found")
            print("Please run extract_save.py first to extract a save file")
            return
        
        # Get the most recent file
        save_path = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"Using latest save: {save_path.name}")
    
    # Load and analyze
    print(f"Loading save data...")
    save_data = load_save_data(save_path)
    
    print("Analyzing power blocs...")
    power_blocs = analyze_power_blocs(save_data)
    
    if not power_blocs:
        print("No active power blocs found in the save file")
        return
    
    # Generate CSV if requested
    if args.csv:
        csv_file = args.output if args.output else 'reports/power_blocs.csv'
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
        
        with open(csv_file, 'w') as f:
            # Header
            f.write("bloc_name,leader_tag,founding_date,total_gdp,member_count,mandate_progress,principles,members\n")
            
            # Data rows
            for bloc in power_blocs:
                principles_str = '; '.join(format_principles(bloc['principles']))
                members_str = '; '.join([f"{m['tag']}({format_gdp(m['gdp'])})" for m in bloc['members']])
                
                f.write(f'"{bloc["name"]}",{bloc["leader_tag"]},{bloc["founding_date"]},')
                f.write(f'{bloc["total_gdp"]},{bloc["member_count"]},{bloc["mandate_progress"]},')
                f.write(f'"{principles_str}","{members_str}"\n')
        
        print(f"CSV report saved to: {csv_file}")
    else:
        # Generate text report
        generate_report(power_blocs, args.output)

if __name__ == '__main__':
    main()