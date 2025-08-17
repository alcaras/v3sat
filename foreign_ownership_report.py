#!/usr/bin/env python3
"""
Victoria 3 Foreign Ownership Report Generator

Analyzes foreign investment patterns, showing:
- Each country's GDP
- What percentage of other countries' GDP they own
- What percentage of their own GDP is foreign-owned
"""

import json
import argparse
import os
from pathlib import Path
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

def get_country_gdp(countries, country_id):
    """Get the latest GDP value for a country."""
    country = countries.get(str(country_id), {})
    if not isinstance(country, dict):
        return 0.0
    
    gdp_data = country.get('gdp', {})
    if not gdp_data:
        return 0.0
    
    # GDP data is stored in channels
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

def calculate_foreign_ownership(save_data):
    """Calculate foreign ownership percentages based on building ownership."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})  # States database
    ownership_data = save_data.get('building_ownership_manager', {}).get('database', {})
    
    # Track foreign investments: investor_country -> {target_country -> total_value}
    foreign_investments = defaultdict(lambda: defaultdict(float))
    
    # Track domestic ownership value for each country
    domestic_value = defaultdict(float)
    
    # Process all building ownership
    for ownership_id, ownership in ownership_data.items():
        if not isinstance(ownership, dict):
            continue
        
        building_id = ownership.get('building')
        owner_identity = ownership.get('identity', {})
        owner_country = owner_identity.get('country') if isinstance(owner_identity, dict) else None
        levels = ownership.get('levels', 0)
        
        if not (building_id and owner_country and levels > 0):
            continue
        
        # Get the building
        building = buildings.get(str(building_id))
        if not building:
            continue
        
        # Get the state where the building is located
        state_id = building.get('state')
        if not state_id:
            continue
        
        state = states.get(str(state_id))
        if not state:
            continue
        
        state_owner = state.get('country')  # States use 'country' not 'owner'
        if not state_owner:
            continue
        
        # Calculate building value based on Victoria 3's actual dividend system
        # According to Dev Diary #110: 25-50% of profit goes to cash reserves, rest as dividends
        building_levels = building.get('levels', 1)
        profit_after_reserves = building.get('profit_after_reserves', 0)
        cash_reserves = building.get('cash_reserves', 0)
        
        # Calculate ownership ratio
        ownership_ratio = levels / building_levels if building_levels > 0 else 0
        
        # Use Victoria 3's actual dividend calculation
        if profit_after_reserves > 0:
            # Building is profitable - calculate annual dividends
            weekly_dividends = profit_after_reserves * ownership_ratio
            annual_dividend_value = weekly_dividends * 52
            
            # Estimate building value using dividend yield approach (10-15% yield assumption)
            # This represents the capital value needed to generate these dividends
            estimated_building_value = annual_dividend_value / 0.12  # 12% yield assumption
        else:
            # For unprofitable buildings, use cash reserves and construction cost estimates
            # Cash reserves represent stored value from past profits
            cash_value = cash_reserves * ownership_ratio if cash_reserves > 0 else 0
            
            # Add estimated construction/infrastructure value
            # Based on building level and type - more sophisticated than flat rate
            construction_value = levels * 100000  # $100K per level base construction cost
            
            estimated_building_value = cash_value + construction_value
        
        # Use the estimated building value as the foreign investment value
        annual_value = estimated_building_value
        
        if owner_country == state_owner:
            # Domestic ownership
            domestic_value[state_owner] += annual_value
        else:
            # Foreign ownership
            foreign_investments[owner_country][state_owner] += annual_value
            domestic_value[state_owner] += annual_value  # Still counts toward total domestic economy
    
    return foreign_investments, domestic_value

def format_value(value):
    """Format monetary values for display."""
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.1f}M"
    elif value >= 1e3:
        return f"${value/1e3:.0f}K"
    else:
        return f"${value:.0f}"

def generate_report(save_data, output_file=None, humans_only=False):
    """Generate the foreign ownership report."""
    countries = save_data.get('country_manager', {}).get('database', {})
    
    # Load human countries if filtering
    human_countries = set()
    if humans_only and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Calculate foreign ownership
    print("Calculating foreign ownership patterns...")
    foreign_investments, domestic_value = calculate_foreign_ownership(save_data)
    
    # Build report data
    report_data = []
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        tag = get_country_tag(countries, country_id)
        
        # Filter by human countries if requested
        if humans_only and human_countries and tag not in human_countries:
            continue
        
        gdp = get_country_gdp(countries, country_id)
        if gdp <= 0:
            continue
        
        country_id_int = int(country_id)
        
        # Calculate total foreign investments by this country
        investments_by_country = foreign_investments.get(country_id_int, {})
        total_foreign_investment = sum(investments_by_country.values())
        
        # Calculate foreign ownership IN this country
        foreign_owned_in_country = 0
        foreign_owners = {}
        for investor_id, targets in foreign_investments.items():
            if country_id_int in targets:
                foreign_owned_in_country += targets[country_id_int]
                foreign_owners[investor_id] = targets[country_id_int]
        
        # Calculate percentages
        foreign_investment_pct = (total_foreign_investment / gdp * 100) if gdp > 0 else 0
        foreign_owned_pct = (foreign_owned_in_country / gdp * 100) if gdp > 0 else 0
        
        report_data.append({
            'tag': tag,
            'country_id': country_id_int,
            'gdp': gdp,
            'foreign_investment_value': total_foreign_investment,
            'foreign_investment_pct': foreign_investment_pct,
            'foreign_owned_value': foreign_owned_in_country,
            'foreign_owned_pct': foreign_owned_pct,
            'investments_by_country': investments_by_country,
            'foreign_owners': foreign_owners
        })
    
    # Sort by GDP
    report_data.sort(key=lambda x: -x['gdp'])
    
    # Generate report text
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("VICTORIA 3 FOREIGN OWNERSHIP REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("Note: Foreign ownership is calculated based on building ownership data.")
    report_lines.append("Percentages show foreign-owned building value as % of GDP.")
    report_lines.append("")
    report_lines.append("-" * 80)
    
    for country_data in report_data:
        tag = country_data['tag']
        gdp = country_data['gdp']
        
        report_lines.append("")
        report_lines.append(f"{tag}")
        report_lines.append("=" * len(tag))
        report_lines.append(f"GDP: {format_value(gdp)}")
        
        # Show foreign investments BY this country
        if country_data['foreign_investment_value'] > 0:
            report_lines.append(f"Foreign investments: {format_value(country_data['foreign_investment_value'])} ({country_data['foreign_investment_pct']:.1f}% of their GDP)")
            
            # List top investment targets
            if country_data['investments_by_country']:
                report_lines.append("  Invests in:")
                sorted_investments = sorted(
                    country_data['investments_by_country'].items(),
                    key=lambda x: -x[1]
                )
                for target_id, value in sorted_investments[:5]:
                    target_tag = get_country_tag(countries, target_id)
                    target_gdp = get_country_gdp(countries, target_id)
                    pct_of_target = (value / target_gdp * 100) if target_gdp > 0 else 0
                    report_lines.append(f"    • {target_tag}: {format_value(value)} ({pct_of_target:.1f}% of {target_tag}'s GDP)")
        
        # Show foreign ownership IN this country
        if country_data['foreign_owned_value'] > 0:
            report_lines.append(f"Foreign-owned: {format_value(country_data['foreign_owned_value'])} ({country_data['foreign_owned_pct']:.1f}% of their GDP)")
            
            # List top foreign owners
            if country_data['foreign_owners']:
                report_lines.append("  Owned by:")
                sorted_owners = sorted(
                    country_data['foreign_owners'].items(),
                    key=lambda x: -x[1]
                )
                for owner_id, value in sorted_owners[:5]:
                    owner_tag = get_country_tag(countries, owner_id)
                    pct_of_gdp = (value / gdp * 100) if gdp > 0 else 0
                    report_lines.append(f"    • {owner_tag}: {format_value(value)} ({pct_of_gdp:.1f}% of GDP)")
        
        if country_data['foreign_investment_value'] == 0 and country_data['foreign_owned_value'] == 0:
            report_lines.append("  No foreign investment activity")
        
        report_lines.append("")
        report_lines.append("-" * 80)
    
    # Summary statistics
    total_countries = len(report_data)
    countries_investing = sum(1 for c in report_data if c['foreign_investment_value'] > 0)
    countries_with_foreign = sum(1 for c in report_data if c['foreign_owned_value'] > 0)
    
    report_lines.append("")
    report_lines.append("SUMMARY")
    report_lines.append("=" * 7)
    report_lines.append(f"Total countries analyzed: {total_countries}")
    report_lines.append(f"Countries with foreign investments: {countries_investing}")
    report_lines.append(f"Countries with foreign ownership: {countries_with_foreign}")
    
    # Output
    report_text = '\n'.join(report_lines)
    
    if output_file:
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report_text)
        print(f"Report saved to: {output_file}")
    
    print(report_text)
    
    return report_text

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 foreign ownership reports')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output', help='Output file for the report')
    parser.add_argument('--humans', action='store_true', help='Only analyze human-controlled countries')
    
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
    
    # Generate report
    generate_report(save_data, args.output, args.humans)

if __name__ == '__main__':
    main()