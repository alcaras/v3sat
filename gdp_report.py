#!/usr/bin/env python3
"""
Victoria 3 GDP Report Generator
Generates GDP reports from extracted save files
"""

import json
import csv
import sys
from pathlib import Path
import argparse
from datetime import datetime

def load_humans_list(humans_file="humans.txt"):
    """Load list of human-controlled countries from file"""
    humans = []
    try:
        with open(humans_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    humans.append(line)
    except FileNotFoundError:
        print(f"Warning: {humans_file} not found. Will report on all countries.")
    return humans

def get_country_name(country_data, tag):
    """Try to get a readable country name, fallback to tag"""
    # Try to get the definition name if available
    if 'definition' in country_data:
        return country_data.get('definition', tag)
    return tag

def extract_gdp_data(json_file, humans_list=None):
    """Extract GDP data from Victoria 3 save JSON"""
    
    print(f"Loading save file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get the game date
    game_date = data.get('date', 'Unknown')
    
    # Get country data
    countries_data = {}
    if 'country_manager' in data and 'database' in data['country_manager']:
        all_countries = data['country_manager']['database']
        
        for country_id, country_info in all_countries.items():
            # Skip non-dict entries (references)
            if not isinstance(country_info, dict):
                continue
                
            # Get the country tag from definition field
            tag = country_info.get('definition', country_id)
            
            # Skip if not in humans list (if list provided)
            if humans_list and tag not in humans_list:
                continue
            
            # Extract GDP value (it's a time series, get the latest)
            gdp_data = country_info.get('gdp', 0)
            if isinstance(gdp_data, dict):
                if 'channels' in gdp_data:
                    # Get the latest value from the time series
                    channel_0 = gdp_data.get('channels', {}).get('0', {})
                    values = channel_0.get('values', [])
                    gdp = values[-1] if values else 0
                else:
                    # Country exists but has no GDP history (likely just formed)
                    gdp = 0
            else:
                gdp = gdp_data if isinstance(gdp_data, (int, float)) else 0
            
            # Try to get additional info (also time series)
            prestige_data = country_info.get('prestige', 0)
            if isinstance(prestige_data, dict) and 'channels' in prestige_data:
                channel_0 = prestige_data.get('channels', {}).get('0', {})
                values = channel_0.get('values', [])
                prestige = values[-1] if values else 0
            else:
                prestige = prestige_data if isinstance(prestige_data, (int, float)) else 0
                
            literacy_data = country_info.get('literacy', 0)
            if isinstance(literacy_data, dict) and 'channels' in literacy_data:
                channel_0 = literacy_data.get('channels', {}).get('0', {})
                values = channel_0.get('values', [])
                literacy = values[-1] if values else 0
            else:
                literacy = literacy_data if isinstance(literacy_data, (int, float)) else 0
            
            # Skip population for now (complex to calculate)
            
            countries_data[tag] = {
                'tag': tag,
                'name': get_country_name(country_info, tag),
                'gdp': gdp,
                'prestige': prestige,
                'literacy': literacy
            }
    
    return {
        'date': game_date,
        'countries': countries_data
    }

def write_csv_report(gdp_data, output_file):
    """Write GDP data to CSV file"""
    
    countries = gdp_data['countries']
    if not countries:
        print("No country data found!")
        return
    
    # Sort countries by GDP (descending)
    sorted_countries = sorted(countries.values(), key=lambda x: x['gdp'], reverse=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['rank', 'tag', 'name', 'gdp', 'prestige', 'literacy']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write metadata row
        writer.writerow({
            'rank': f"# Date: {gdp_data['date']}",
            'tag': '',
            'name': '',
            'gdp': '',
            'prestige': '',
            'literacy': ''
        })
        
        # Write country data
        for rank, country in enumerate(sorted_countries, 1):
            writer.writerow({
                'rank': rank,
                'tag': country['tag'],
                'name': country['name'],
                'gdp': f"{country['gdp']:.2f}",
                'prestige': f"{country['prestige']:.2f}",
                'literacy': f"{country['literacy']:.2f}"
            })
    
    print(f"Report written to: {output_file}")
    print(f"Total countries: {len(sorted_countries)}")
    
    # Print top 5 summary
    print("\nTop 5 Countries by GDP:")
    for i, country in enumerate(sorted_countries[:5], 1):
        print(f"  {i}. {country['tag']} ({country['name']}): {country['gdp']:,.2f}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate GDP reports from Victoria 3 save files"
    )
    parser.add_argument(
        "save_json",
        nargs='?',
        help="Path to extracted JSON save file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output CSV file path (default: reports/gdp_report_<date>.csv)"
    )
    parser.add_argument(
        "--humans",
        default="humans.txt",
        help="Path to humans.txt file (default: humans.txt)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Report on all countries, not just humans"
    )
    
    args = parser.parse_args()
    
    # Default to latest extracted save if not specified
    if not args.save_json:
        extracted_dir = Path("extracted-saves")
        json_files = list(extracted_dir.glob("*.json"))
        if not json_files:
            print("No extracted JSON files found in extracted-saves/")
            sys.exit(1)
        args.save_json = str(max(json_files, key=lambda x: x.stat().st_mtime))
        print(f"Using latest save: {args.save_json}")
    
    # Load humans list unless --all specified
    humans_list = None
    if not args.all:
        humans_list = load_humans_list(args.humans)
        if humans_list:
            print(f"Tracking countries: {', '.join(humans_list)}")
    
    # Extract GDP data
    gdp_data = extract_gdp_data(args.save_json, humans_list)
    
    # Determine output file
    if not args.output:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = str(reports_dir / f"gdp_report_{timestamp}.csv")
    
    # Write report
    write_csv_report(gdp_data, args.output)

if __name__ == "__main__":
    main()