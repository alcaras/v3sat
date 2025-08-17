#!/usr/bin/env python3
"""
Companies Report for Victoria 3

Shows companies by country in the format:
  USA (5 Companies)

  - Carnegie Steel Company
  - Panama Canal Company
  - Lee Wilson & Company
  - Basic Metalworks Company
  - Basic Home Goods Company
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

def format_company_name(building_type, company_name=None):
    """Format company name for display."""
    # Company name mappings based on building types
    company_names = {
        'building_company_us_steel': 'Carnegie Steel Company',
        'building_company_panama_canal': 'Panama Canal Company', 
        'building_company_lee_wilson': 'Lee Wilson & Company',
        'building_company_suez_canal': 'Suez Canal Company',
        'building_company_armstrong_whitworth': 'Sir W.G. Armstrong Whitworth & Co',
        'building_company_anglo_persian_oil': 'Anglo-Persian Oil Company',
        'building_company_bolckow_vaughan': 'Bolckow, Vaughan & Co',
        'building_company_tata_group': 'Tata Group',
        'building_company_david_sassoon': 'David Sassoon & Co',
        'building_company_dollfus_mieg': 'Dollfus-Mieg et Compagnie',
        'building_company_generale_voitures': 'Compagnie Générale des Voitures',
        'building_company_schneider': 'Schneider et Cie',
        'building_company_altos_hornos': 'Altos Hornos de Vizcaya',
        'building_company_espana_industrial': 'España Industrial',
        'building_company_mitsui': 'Mitsui & Co',
        'building_company_zastava': 'Zastava',
        'building_company_ong_lung_sheng': 'Ong Lung Sheng Tea Company',
        'building_company_russian_american': 'Russian-American Company',
        'building_company_basic_metalworks': 'Basic Metalworks Company',
        'building_company_basic_steel': 'Basic Steel Company',
        'building_company_basic_paper': 'Basic Paper Manufacturing',
        'building_company_basic_home_goods': 'Basic Home Goods Company',
        'building_company_basic_colonial_plantations': 'Basic Colonial Plantations Company',
        'building_company_basic_food': 'Basic Food Company',
        'building_company_basic_gold_mining': 'Basic Gold Mining Company',
        'building_company_basic_wine_fruit': 'Basic Wine and Fruit Company',
        'building_company_basic_paper_company': 'Basic Paper Company',
        'building_company_basic_metal_mining': 'Basic Metal Mining Company',
    }
    
    # Try to get the proper name
    if building_type in company_names:
        return company_names[building_type]
    
    # Fallback: clean up the building type name
    if building_type.startswith('building_company_'):
        name = building_type.replace('building_company_', '')
        name = name.replace('_', ' ').title()
        return f"{name} Company"
    
    return building_type

def analyze_companies(save_data):
    """Analyze companies by country."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    
    # Track companies by country
    companies_by_country = defaultdict(list)
    
    # Find all company buildings
    for building_id, building in buildings.items():
        if not isinstance(building, dict):
            continue
            
        building_type = building.get('building', '')
        if not building_type or 'company' not in building_type:
            continue
        
        # Skip regional company buildings
        if 'regional' in building_type.lower():
            continue
            
        # Get building location
        state_id = str(building.get('state'))
        if not state_id or state_id not in states:
            continue
            
        state = states[state_id]
        country_id = state.get('country')
        if not country_id:
            continue
            
        # Format company name
        company_name = format_company_name(building_type)
        
        companies_by_country[country_id].append(company_name)
    
    # Sort companies within each country
    for country_id in companies_by_country:
        companies_by_country[country_id].sort()
    
    return companies_by_country, countries

def generate_companies_report(save_data, humans_only=True):
    """Generate companies report."""
    # Load human countries if filtering
    human_countries = set()
    if humans_only and os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    companies_by_country, countries = analyze_companies(save_data)
    
    # Prepare report data
    report_data = []
    
    for country_id, companies in companies_by_country.items():
        tag = get_country_tag(countries, country_id)
        
        # Filter by human countries if requested
        if humans_only and human_countries and tag not in human_countries:
            continue
            
        if companies:
            report_data.append((tag, companies))
    
    # Sort by number of companies (most first)
    report_data.sort(key=lambda x: -len(x[1]))
    
    return report_data

def print_companies_report(report_data):
    """Print companies report in the requested format."""
    print("COMPANIES BY COUNTRY")
    print("=" * 30)
    print()
    
    if not report_data:
        print("No companies found.")
        return
    
    for tag, companies in report_data:
        count = len(companies)
        print(f"  {tag} ({count} Compan{'y' if count == 1 else 'ies'})")
        print()
        
        for company in companies:
            print(f"  - {company}")
        
        print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Victoria 3 companies reports')
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
    report_data = generate_companies_report(save_data, humans_only)
    
    # Generate output
    if args.output:
        with open(args.output, 'w') as f:
            # Redirect print to file
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            print_companies_report(report_data)
            sys.stdout = old_stdout
        print(f"Companies report saved to: {args.output}")
    else:
        print_companies_report(report_data)

if __name__ == '__main__':
    main()