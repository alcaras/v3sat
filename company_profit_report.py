#!/usr/bin/env python3
"""
Extract company names and profitability from Victoria 3 save files.
Companies in V3 own multiple buildings - we need to sum their profits.
"""

import json
import sys
from pathlib import Path
from company_localization import get_company_display_name

def get_latest_save():
    """Get the most recent extracted save file."""
    extracted_dir = Path('extracted-saves')
    if not extracted_dir.exists():
        return None
    
    json_files = list(extracted_dir.glob('*.json'))
    if not json_files:
        return None
    
    # Get the most recent file
    latest = max(json_files, key=lambda f: f.stat().st_mtime)
    return latest

def extract_company_profits(save_file, humans_only=False):
    """Extract company names and calculate total profits from all their buildings."""
    
    print(f"Loading save file: {save_file}")
    with open(save_file, 'r') as f:
        data = json.load(f)
    
    companies = data.get('companies', {}).get('database', {})
    buildings = data.get('building_manager', {}).get('database', {})
    ownership = data.get('building_ownership_manager', {}).get('database', {})
    countries = data.get('country_manager', {}).get('database', {})
    
    print(f"Found {len(companies)} companies")
    
    # Build a map of building ownership
    company_buildings = {}  # company_id -> list of building_ids
    
    # Method 1: Check ownership database for company-owned buildings
    for owner_id, owner_data in ownership.items():
        if 'identity' in owner_data and 'building' in owner_data['identity']:
            # This is a company owning another building
            company_building_id = owner_data['identity']['building']
            owned_building_id = owner_data.get('building')
            
            # Find which company owns this building
            for cid, company in companies.items():
                if str(company.get('building')) == str(company_building_id):
                    if cid not in company_buildings:
                        company_buildings[cid] = []
                    company_buildings[cid].append(str(owned_building_id))
                    break
    
    # Method 2: Add the main building each company owns
    for cid, company in companies.items():
        if 'building' in company:
            if cid not in company_buildings:
                company_buildings[cid] = []
            company_buildings[cid].append(str(company['building']))
    
    # Calculate total profits for each company
    company_data = []
    
    for cid, company in companies.items():
        # Add ID to company data for display name function
        company['id'] = cid
        
        # Get company display name using localization
        name = get_company_display_name(company)
        
        # Get country tag from country_manager
        country_id = company.get('country', 0)
        country_tag = 'UNK'
        
        # Try to get tag from country_manager
        if str(country_id) in countries:
            country_data = countries[str(country_id)]
            if isinstance(country_data, dict) and 'definition' in country_data:
                country_tag = country_data['definition']
            elif isinstance(country_data, str):
                country_tag = country_data
        
        # Fallback for countries not in the manager
        if country_tag == 'UNK':
            country_tag = f'C{country_id}'
        
        # Calculate total profit from all buildings
        # Note: The game displays ownership_income in the company view, not profit_after_reserves
        total_profit = 0
        building_count = 0
        
        if cid in company_buildings:
            for bid in company_buildings[cid]:
                if bid in buildings:
                    building = buildings[bid]
                    # Use ownership_income as that's what the game displays
                    profit = building.get('ownership_income', 0)
                    total_profit += profit
                    building_count += 1
        
        # Also check regional_hqs for additional buildings
        regional_hqs = company.get('regional_hqs', [])
        for hq_id in regional_hqs:
            hq_bid = str(hq_id)
            if hq_bid in buildings and hq_bid not in company_buildings.get(cid, []):
                building = buildings[hq_bid]
                # Use ownership_income as that's what the game displays
                profit = building.get('ownership_income', 0)
                total_profit += profit
                building_count += 1
        
        # Get main building + regional HQs profit (what the game UI shows)
        # The game displays the sum of main building + regional HQs, not total ownership
        ui_display_profit = 0
        main_building_id = str(company.get('building', ''))
        if main_building_id in buildings:
            ui_display_profit += buildings[main_building_id].get('ownership_income', 0)
        
        # Add regional HQs income (these are shown in the game UI)
        for hq_id in company.get('regional_hqs', []):
            hq_bid = str(hq_id)
            if hq_bid in buildings:
                ui_display_profit += buildings[hq_bid].get('ownership_income', 0)
        
        company_data.append({
            'id': cid,
            'name': name,
            'country': country_tag,
            'building_count': building_count,
            'profit': total_profit,
            'ui_display_profit': ui_display_profit,
            'company_type': company.get('company_type', 'unknown')
        })
    
    # Sort by UI display profit (what the game shows)
    company_data.sort(key=lambda x: x['ui_display_profit'], reverse=True)
    
    # Add rank to each company
    for i, comp in enumerate(company_data, 1):
        comp['rank'] = i
    
    # Load human countries if filtering
    human_countries = set()
    if humans_only:
        humans_file = Path('humans.txt')
        if humans_file.exists():
            with open(humans_file, 'r') as f:
                human_countries = {line.strip() for line in f if line.strip() and not line.startswith('#')}
    
    # Filter to human countries if requested
    display_data = company_data
    if humans_only and human_countries:
        display_data = [c for c in company_data if c['country'] in human_countries]
    
    # Print report
    print("\n" + "=" * 80)
    if humans_only:
        print("VICTORIA 3 COMPANY PROFITABILITY REPORT - HUMAN PLAYERS ONLY")
    else:
        print("VICTORIA 3 COMPANY PROFITABILITY REPORT")
    print("=" * 80)
    
    if humans_only:
        print(f"\n{'Global':<6} {'Rank':<5} {'Company Name':<40} {'Country':<10} {'Buildings':<10} {'Profit':<15}")
        print("-" * 90)
        
        for i, comp in enumerate(display_data[:50], 1):  # Top 50 human companies
            name = comp['name'][:38]  # Truncate long names
            print(f"#{comp['rank']:<5} {i:<5} {name:<40} {comp['country']:<10} {comp['building_count']:<10} £{comp['ui_display_profit']:>13,.2f}")
    else:
        print(f"\n{'Rank':<5} {'Company Name':<45} {'Country':<10} {'Buildings':<10} {'Profit':<15}")
        print("-" * 85)
        
        for i, comp in enumerate(display_data[:50], 1):  # Top 50 companies
            name = comp['name'][:43]  # Truncate long names
            print(f"{i:<5} {name:<45} {comp['country']:<10} {comp['building_count']:<10} £{comp['ui_display_profit']:>13,.2f}")
    
    # Summary stats
    print("\n" + "-" * 85)
    total_ui_profit = sum(c['ui_display_profit'] for c in company_data)
    avg_profit = total_ui_profit / len(company_data) if company_data else 0
    profitable = sum(1 for c in company_data if c['ui_display_profit'] > 0)
    
    print(f"Total companies: {len(company_data)}")
    print(f"Profitable companies: {profitable}")
    print(f"Total profit: £{total_ui_profit:,.2f}")
    print(f"Average profit per company: £{avg_profit:,.2f}")
    
    # Find companies with player-assigned custom names
    print("\n" + "=" * 80)
    print("COMPANIES WITH PLAYER-ASSIGNED CUSTOM NAMES")
    print("=" * 80)
    
    # Only show companies that have actual custom_name field set
    custom_companies = []
    for cid, company in companies.items():
        if company.get('custom_name'):  # Only if custom_name field exists and is not empty
            for comp in company_data:
                if comp['id'] == cid:
                    custom_companies.append(comp)
                    break
    
    custom_companies.sort(key=lambda x: x['ui_display_profit'], reverse=True)
    
    for comp in custom_companies:
        print(f"\n{comp['name']}")
        print(f"  Type: {comp['company_type']}")
        print(f"  Buildings: {comp['building_count']}")
        print(f"  Profit: £{comp['ui_display_profit']:,.2f}")
    
    return company_data

def main():
    # Check for --humans flag
    humans_only = '--humans' in sys.argv
    if humans_only:
        sys.argv.remove('--humans')
    
    if len(sys.argv) > 1:
        save_file = Path(sys.argv[1])
    else:
        save_file = get_latest_save()
    
    if not save_file or not save_file.exists():
        print("Error: No save file found")
        print("Usage: python3 company_profit_report.py [save_file.json] [--humans]")
        sys.exit(1)
    
    extract_company_profits(save_file, humans_only=humans_only)

if __name__ == "__main__":
    main()