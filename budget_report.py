#!/usr/bin/env python3
"""
Budget Report for Victoria 3

Shows GDP, money, and debt percentage by country in the format:
Country |      GDP |    Money | Debt %
--------|----------|----------|-------
BIC     |   395.6M |  -161.0M |  42.6%
USA     |   375.3M |   -29.9M |   8.3%
etc.
"""

import json
import os

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

def calculate_true_gdp(save_data):
    """Calculate GDP using Victoria 3's actual formula from Garibaldi."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    
    # Victoria 3's economic defines (from Garibaldi/defines)
    min_credit_base = 100000.0  # COUNTRY_MIN_CREDIT_BASE = £100K
    credit_scale_factor = 0.5   # COUNTRY_MIN_CREDIT_SCALED = 0.5 (50% of GDP)
    
    # First, calculate building cash reserves for each country
    from collections import defaultdict
    country_building_reserves = defaultdict(float)
    
    for building_id, building in buildings.items():
        if not isinstance(building, dict):
            continue
        
        cash_reserves = building.get('cash_reserves', 0)
        if cash_reserves <= 0:
            continue
            
        state_id = str(building.get('state'))
        if not state_id or state_id not in states:
            continue
            
        state = states[state_id]
        country_id = state.get('country')
        if not country_id:
            continue
            
        country_building_reserves[country_id] += float(cash_reserves)
    
    # Calculate GDP for each country
    country_gdps = {}
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
            
        budget = country.get('budget', {})
        credit = float(budget.get('credit', 0))
        
        if credit <= 0:
            continue
            
        building_reserves = country_building_reserves.get(int(country_id), 0)
        
        # Victoria 3's GDP formula: GDP = (Credit - Base - Reserves) / Scale
        calculated_gdp = (credit - min_credit_base - building_reserves) / credit_scale_factor
        
        if calculated_gdp > 0:
            country_gdps[int(country_id)] = calculated_gdp
    
    return country_gdps

def get_country_finances(countries, country_id):
    """Get financial data for a country."""
    country = countries.get(str(country_id), {})
    if not isinstance(country, dict):
        return 0.0, 0.0, 0.0
        
    budget = country.get('budget', {})
    
    # Money (positive) or debt (negative)
    money = float(budget.get('money', 0))
    principal = float(budget.get('principal', 0))  # Debt principal
    credit = float(budget.get('credit', 0))  # Credit limit
    
    # If there's debt, show as negative money
    if principal > 0:
        money = -principal
        
    # Calculate debt percentage (principal / credit)
    debt_percentage = (principal / credit * 100) if credit > 0 else 0.0
    
    return money, debt_percentage

def generate_budget_report(save_data, humans_only=True):
    """Generate budget report."""
    countries = save_data.get('country_manager', {}).get('database', {})
    
    # Load human countries if filtering
    human_countries = set()
    if humans_only and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Get GDP data using Victoria 3's actual formula
    country_gdps = calculate_true_gdp(save_data)
    
    # Prepare report data
    report_data = []
    
    for country_id, gdp in country_gdps.items():
        tag = get_country_tag(countries, country_id)
        
        # Filter by human countries if requested
        if humans_only and human_countries and tag not in human_countries:
            continue
            
        money, debt_pct = get_country_finances(countries, country_id)
        
        if gdp > 0:
            report_data.append((tag, gdp, money, debt_pct))
    
    # Sort by GDP (highest first)
    report_data.sort(key=lambda x: -x[1])
    
    return report_data

def print_budget_report(report_data):
    """Print budget report in the requested format."""
    print("GDP, MONEY, AND DEBT BY COUNTRY")
    print("=" * 40)
    print()
    print("Country |      GDP |    Money | Debt %")
    print("--------|----------|----------|-------")
    
    for tag, gdp, money, debt_pct in report_data:
        gdp_m = gdp / 1e6
        money_m = money / 1e6
        print(f"{tag:7} | {gdp_m:7.1f}M | {money_m:7.1f}M | {debt_pct:5.1f}%")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Victoria 3 budget reports')
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
    report_data = generate_budget_report(save_data, humans_only)
    
    # Generate output
    if args.output:
        with open(args.output, 'w') as f:
            # Redirect print to file
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            print_budget_report(report_data)
            sys.stdout = old_stdout
        print(f"Budget report saved to: {args.output}")
    else:
        print_budget_report(report_data)

if __name__ == '__main__':
    main()