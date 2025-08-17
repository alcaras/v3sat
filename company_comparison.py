#!/usr/bin/env python3
"""
Compare company profitability between two Victoria 3 sessions.
Shows growth in profit and changes in company rankings.
"""

import json
import sys
from pathlib import Path
from company_localization import get_company_display_name

def load_companies(save_file):
    """Load and process company data from a save file."""
    with open(save_file, 'r') as f:
        data = json.load(f)
    
    companies = data.get('companies', {}).get('database', {})
    buildings = data.get('building_manager', {}).get('database', {})
    ownership = data.get('building_ownership_manager', {}).get('database', {})
    
    # Country ID to tag mapping
    country_map = {
        1: 'GBR', 3: 'RUS', 4: 'FRA', 5: 'PRS', 8: 'ITA', 9: 'USA',
        17: 'JAP', 23: 'TUR', 30: 'AUS', 36: 'SPA', 63: 'POR', 
        92: 'CHI', 94: 'YUG', 121: 'ETH', 155: 'SIA', 193: 'KOR',
        199: 'PER', 216: 'BIC', 40: 'BEL', 53: 'SER', 55: 'GRE'
    }
    
    company_data = {}
    
    for cid, company in companies.items():
        # Skip non-dict entries
        if not isinstance(company, dict):
            continue
            
        # Add ID for display name function
        company['id'] = cid
        
        # Get display name
        name = get_company_display_name(company)
        
        # Get country tag
        country_id = company.get('country', 0)
        country_tag = country_map.get(country_id, f'C{country_id}')
        
        # Calculate UI display profit (main building + regional HQs)
        ui_profit = 0
        main_building_id = str(company.get('building', ''))
        if main_building_id in buildings:
            ui_profit += buildings[main_building_id].get('ownership_income', 0)
        
        # Add regional HQs income
        for hq_id in company.get('regional_hqs', []):
            hq_bid = str(hq_id)
            if hq_bid in buildings:
                ui_profit += buildings[hq_bid].get('ownership_income', 0)
        
        # Create unique key for comparison (company type + country)
        # This helps match companies across sessions even if IDs change
        company_key = f"{company.get('company_type', 'unknown')}_{country_id}"
        
        # For custom-named companies, use the name as key
        if company.get('custom_name'):
            company_key = f"custom_{company['custom_name']}"
        
        company_data[company_key] = {
            'name': name,
            'country': country_tag,
            'profit': ui_profit,
            'buildings': len(company.get('regional_hqs', [])) + 1,
            'type': company.get('company_type', 'unknown')
        }
    
    return company_data

def compare_sessions(session1_file, session2_file, output_file=None):
    """Compare company data between two sessions."""
    
    print(f"Loading Session 1: {session1_file}")
    session1 = load_companies(session1_file)
    
    print(f"Loading Session 2: {session2_file}")
    session2 = load_companies(session2_file)
    
    # Find matching companies and calculate changes
    comparisons = []
    
    for key, s2_data in session2.items():
        s1_data = session1.get(key)
        
        if s1_data:
            # Company exists in both sessions
            profit_change = s2_data['profit'] - s1_data['profit']
            pct_change = (profit_change / s1_data['profit'] * 100) if s1_data['profit'] > 0 else 0
            
            comparisons.append({
                'name': s2_data['name'],
                'country': s2_data['country'],
                's1_profit': s1_data['profit'],
                's2_profit': s2_data['profit'],
                'change': profit_change,
                'pct_change': pct_change,
                's1_buildings': s1_data['buildings'],
                's2_buildings': s2_data['buildings'],
                'status': 'existing'
            })
        else:
            # New company in session 2
            comparisons.append({
                'name': s2_data['name'],
                'country': s2_data['country'],
                's1_profit': 0,
                's2_profit': s2_data['profit'],
                'change': s2_data['profit'],
                'pct_change': 100,
                's1_buildings': 0,
                's2_buildings': s2_data['buildings'],
                'status': 'new'
            })
    
    # Find companies that disappeared
    for key, s1_data in session1.items():
        if key not in session2:
            comparisons.append({
                'name': s1_data['name'],
                'country': s1_data['country'],
                's1_profit': s1_data['profit'],
                's2_profit': 0,
                'change': -s1_data['profit'],
                'pct_change': -100,
                's1_buildings': s1_data['buildings'],
                's2_buildings': 0,
                'status': 'removed'
            })
    
    # Sort by absolute profit change
    comparisons.sort(key=lambda x: abs(x['change']), reverse=True)
    
    # Generate report
    output = []
    output.append("=" * 100)
    output.append("VICTORIA 3 COMPANY PROFIT COMPARISON")
    output.append("=" * 100)
    output.append("")
    
    # Extract session names from filenames
    s1_name = Path(session1_file).stem.replace('_extracted', '')
    s2_name = Path(session2_file).stem.replace('_extracted', '')
    
    output.append(f"Comparing: {s1_name} → {s2_name}")
    output.append("")
    
    # Top gainers
    output.append("TOP PROFIT GAINERS")
    output.append("-" * 100)
    output.append(f"{'Rank':<5} {'Company':<40} {'Country':<8} {s1_name[:10]:<12} {s2_name[:10]:<12} {'Change':<15} {'%':<8}")
    output.append("-" * 100)
    
    gainers = [c for c in comparisons if c['change'] > 0][:20]
    for i, comp in enumerate(gainers, 1):
        name = comp['name'][:38]
        output.append(f"{i:<5} {name:<40} {comp['country']:<8} £{comp['s1_profit']/1000000:>10.2f}M £{comp['s2_profit']/1000000:>10.2f}M £{comp['change']/1000000:>+13.2f}M {comp['pct_change']:>+7.1f}%")
    
    # Top losers
    output.append("")
    output.append("TOP PROFIT LOSERS")
    output.append("-" * 100)
    output.append(f"{'Rank':<5} {'Company':<40} {'Country':<8} {s1_name[:10]:<12} {s2_name[:10]:<12} {'Change':<15} {'%':<8}")
    output.append("-" * 100)
    
    losers = [c for c in comparisons if c['change'] < 0][:20]
    for i, comp in enumerate(losers, 1):
        name = comp['name'][:38]
        output.append(f"{i:<5} {name:<40} {comp['country']:<8} £{comp['s1_profit']/1000000:>10.2f}M £{comp['s2_profit']/1000000:>10.2f}M £{comp['change']/1000000:>+13.2f}M {comp['pct_change']:>+7.1f}%")
    
    # Summary statistics
    output.append("")
    output.append("SUMMARY STATISTICS")
    output.append("-" * 100)
    
    total_s1 = sum(c['s1_profit'] for c in comparisons if c['status'] != 'new')
    total_s2 = sum(c['s2_profit'] for c in comparisons if c['status'] != 'removed')
    total_change = total_s2 - total_s1
    
    new_companies = len([c for c in comparisons if c['status'] == 'new'])
    removed_companies = len([c for c in comparisons if c['status'] == 'removed'])
    existing_companies = len([c for c in comparisons if c['status'] == 'existing'])
    
    output.append(f"Total profit {s1_name}: £{total_s1/1000000:,.2f}M")
    output.append(f"Total profit {s2_name}: £{total_s2/1000000:,.2f}M")
    output.append(f"Total change: £{total_change/1000000:+,.2f}M ({(total_change/total_s1*100) if total_s1 > 0 else 0:+.1f}%)")
    output.append("")
    output.append(f"Companies in both sessions: {existing_companies}")
    output.append(f"New companies: {new_companies}")
    output.append(f"Removed companies: {removed_companies}")
    
    # Output results
    report_text = '\n'.join(output)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_text)
        print(f"Report saved to: {output_file}")
    else:
        print(report_text)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 company_comparison.py <session1.json> <session2.json> [-o output.txt]")
        sys.exit(1)
    
    session1_file = Path(sys.argv[1])
    session2_file = Path(sys.argv[2])
    
    output_file = None
    if len(sys.argv) > 3 and sys.argv[3] == '-o' and len(sys.argv) > 4:
        output_file = Path(sys.argv[4])
    
    if not session1_file.exists():
        print(f"Error: Session 1 file not found: {session1_file}")
        sys.exit(1)
    
    if not session2_file.exists():
        print(f"Error: Session 2 file not found: {session2_file}")
        sys.exit(1)
    
    compare_sessions(session1_file, session2_file, output_file)

if __name__ == "__main__":
    main()