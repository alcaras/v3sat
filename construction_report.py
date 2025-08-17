#!/usr/bin/env python3
"""
Construction Report for Victoria 3

Shows construction capacity usage by country in the format:
1. USA (America) - 3,006.9
2. GBR (Great Britain) - 2,765.7
etc.
"""

import json
import os
from collections import defaultdict

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

def get_country_name(countries, localization, country_id):
    """Get localized country name."""
    country = countries.get(str(country_id), {})
    if isinstance(country, dict):
        tag = country.get('definition', '').strip('"')
        if tag and tag in localization.get('nations', {}):
            return localization['nations'][tag]
        elif tag:
            # Fallback country names
            fallback_names = {
                'USA': 'America',
                'GBR': 'Great Britain', 
                'BIC': 'British India',
                'FRA': 'France',
                'CHI': 'China',
                'RUS': 'Russia',
                'ITA': 'Italy',
                'GER': 'Germany',
                'JAP': 'Japan',
                'TUR': 'Ottomans',
                'POR': 'Portugal',
                'SPA': 'Spain',
                'YUG': 'Yugoslavia'
            }
            return fallback_names.get(tag, tag)
    return f"Country_{country_id}"

def calculate_construction_usage(save_data):
    """Calculate construction usage from actual save data."""
    countries = save_data.get('country_manager', {}).get('database', {})
    
    # Track construction usage by country
    construction_usage = defaultdict(float)
    
    # Extract used construction from each country's construction queues
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
            elif isinstance(gov_queue, dict):
                for element_id, element in gov_queue.items():
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
            elif isinstance(priv_queue, dict):
                for element_id, element in priv_queue.items():
                    if isinstance(element, dict):
                        base_speed = element.get('base_construction_speed', 0)
                        if isinstance(base_speed, (str, int, float)):
                            used_construction += float(base_speed)
        
        # Store the used construction if > 0
        if used_construction > 0:
            construction_usage[int(country_id)] = used_construction
    
    return construction_usage, countries

def generate_construction_report(save_data, humans_only=True):
    """Generate construction report."""
    # Load human countries if filtering
    human_countries = set()
    if humans_only and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    construction_usage, countries = calculate_construction_usage(save_data)
    
    # Create localization dict (simplified)
    localization = {'nations': {}}
    
    # Prepare report data
    report_data = []
    
    for country_id, usage in construction_usage.items():
        tag = get_country_tag(countries, country_id)
        
        # Filter by human countries if requested
        if humans_only and human_countries and tag not in human_countries:
            continue
            
        name = get_country_name(countries, localization, country_id)
        
        if usage > 0:
            report_data.append((tag, name, usage))
    
    # Sort by construction usage (highest first)
    report_data.sort(key=lambda x: -x[2])
    
    return report_data

def print_construction_report(report_data):
    """Print construction report in the requested format."""
    print("CONSTRUCTION CAPACITY USAGE")
    print("=" * 40)
    print()
    
    if not report_data:
        print("No construction data found.")
        return
    
    print("| Rank | Country | Construction |")
    print("|------|---------|--------------|")
    
    for i, (tag, name, usage) in enumerate(report_data, 1):
        print(f"| {i:4d} | {tag:7s} | {usage:>12,.1f} |")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Victoria 3 construction reports')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output', help='Output file for the report')
    parser.add_argument('--humans', action='store_true', default=True, help='Only analyze human-controlled countries')
    parser.add_argument('--all', action='store_true', help='Analyze all countries')
    
    args = parser.parse_args()
    
    # Determine save file to use
    if args.save_file:
        save_path = args.save_file
    else:
        # Use latest extracted save
        from pathlib import Path
        extracted_dir = Path('extracted-saves')
        if not extracted_dir.exists():
            print("Error: extracted-saves directory not found")
            return
        
        json_files = list(extracted_dir.glob('*_extracted.json'))
        if not json_files:
            print("Error: No extracted save files found")
            return
        
        # Get the most recent file
        save_path = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"Using latest save: {save_path.name}")
    
    # Load and analyze
    print(f"Loading save data...")
    save_data = load_save_data(save_path)
    
    humans_only = not args.all
    report_data = generate_construction_report(save_data, humans_only)
    
    # Generate output
    if args.output:
        with open(args.output, 'w') as f:
            # Redirect print to file
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            print_construction_report(report_data)
            sys.stdout = old_stdout
        print(f"Construction report saved to: {args.output}")
    else:
        print_construction_report(report_data)

if __name__ == '__main__':
    main()