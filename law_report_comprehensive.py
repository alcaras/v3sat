#!/usr/bin/env python3
"""
Comprehensive Victoria 3 Law Report

Analyzes all law categories and shows which countries have adopted which laws.
Covers all 23 law groups in Victoria 3.
"""

import json
import os
import sys
import argparse
from collections import defaultdict
import glob

# Define all law groups and their laws - organized per Victoria 3 wiki
LAW_GROUPS = {
    # POWER STRUCTURE LAWS
    'governance_principles': {
        'name': 'Governance Principles',
        'laws': ['law_chiefdom', 'law_monarchy', 'law_presidential_republic', 'law_parliamentary_republic', 
                 'law_theocracy', 'law_council_republic', 'law_corporate_state']
    },
    'distribution_of_power': {
        'name': 'Distribution of Power',
        'laws': ['law_autocracy', 'law_technocracy', 'law_oligarchy', 'law_elder_council', 'law_landed_voting',
                 'law_wealth_voting', 'law_census_voting', 'law_universal_suffrage', 'law_anarchy', 'law_single_party_state']
    },
    'citizenship': {
        'name': 'Citizenship',
        'laws': ['law_ethnostate', 'law_national_supremacy', 'law_racial_segregation', 'law_cultural_exclusion', 'law_multicultural']
    },
    'church_and_state': {
        'name': 'Church and State',
        'laws': ['law_state_religion', 'law_freedom_of_conscience', 'law_total_separation', 'law_state_atheism']
    },
    'bureaucracy': {
        'name': 'Bureaucracy',
        'laws': ['law_hereditary_bureaucrats', 'law_appointed_bureaucrats', 'law_elected_bureaucrats']
    },
    'army_model': {
        'name': 'Army Model',
        'laws': ['law_peasant_levies', 'law_national_militia', 'law_professional_army', 'law_mass_conscription']
    },
    'internal_security': {
        'name': 'Internal Security',
        'laws': ['law_no_home_affairs', 'law_national_guard', 'law_secret_police', 'law_guaranteed_liberties']
    },
    # ECONOMY LAWS
    'economic_system': {
        'name': 'Economic System',
        'laws': ['law_traditionalism', 'law_interventionism', 'law_agrarianism', 'law_industry_banned', 
                 'law_extraction_economy', 'law_laissez_faire', 'law_command_economy', 'law_cooperative_ownership']
    },
    'trade_policy': {
        'name': 'Trade Policy',
        'laws': ['law_mercantilism', 'law_protectionism', 'law_free_trade', 'law_isolationism', 'law_canton_system']
    },
    'taxation': {
        'name': 'Taxation',
        'laws': ['law_consumption_based_taxation', 'law_land_based_taxation', 'law_per_capita_based_taxation', 
                 'law_proportional_taxation', 'law_graduated_taxation']
    },
    'land_reform': {
        'name': 'Land Reform',
        'laws': ['law_serfdom', 'law_tenant_farmers', 'law_commercialized_agriculture', 'law_homesteading', 
                 'law_collectivized_agriculture']
    },
    'colonization': {
        'name': 'Colonization',
        'laws': ['law_no_colonial_affairs', 'law_colonial_resettlement', 'law_frontier_colonization', 
                 'law_colonial_exploitation']
    },
    'policing': {
        'name': 'Policing',
        'laws': ['law_no_police', 'law_local_police', 'law_dedicated_police', 'law_militarized_police']
    },
    'education_system': {
        'name': 'Education System',
        'laws': ['law_no_schools', 'law_religious_schools', 'law_private_schools', 'law_public_schools']
    },
    'health_system': {
        'name': 'Health System',
        'laws': ['law_no_health_system', 'law_charity_hospitals', 'law_private_health_insurance', 
                 'law_public_health_insurance']
    },
    # HUMAN RIGHTS LAWS
    'free_speech': {
        'name': 'Free Speech',
        'laws': ['law_outlawed_dissent', 'law_censorship', 'law_right_of_assembly', 'law_protected_speech']
    },
    'labor_rights': {
        'name': 'Labor Rights',
        'laws': ['law_no_workers_rights', 'law_regulatory_bodies', 'law_worker_protections', 'law_union_representation']
    },
    'childrens_rights': {
        'name': 'Children\'s Rights',
        'laws': ['law_child_labor_allowed', 'law_restricted_child_labor', 'law_compulsory_primary_school']
    },
    'rights_of_women': {
        'name': 'Rights of Women',
        'laws': ['law_legal_guardianship', 'law_women_own_property', 'law_women_in_the_workplace', 'law_womens_suffrage']
    },
    'welfare': {
        'name': 'Welfare',
        'laws': ['law_no_social_security', 'law_poor_laws', 'law_wage_subsidies', 'law_old_age_pension']
    },
    'migration': {
        'name': 'Migration',
        'laws': ['law_no_migration_controls', 'law_migration_controls', 'law_closed_borders']
    },
    'slavery': {
        'name': 'Slavery',
        'laws': ['law_slavery_banned', 'law_debt_slavery', 'law_slave_trade', 'law_legacy_slavery']
    }
}

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

def analyze_laws(save_data, human_countries=None):
    """Analyze all laws for all countries."""
    countries = save_data.get('country_manager', {}).get('database', {})
    laws_db = save_data.get('laws', {}).get('database', {})
    
    # Track laws by country tag
    country_laws = {}
    
    # First, create a mapping of country IDs to tags
    country_id_to_tag = {}
    for country_id, country in countries.items():
        if isinstance(country, dict):
            tag = get_country_tag(countries, country_id)
            country_id_to_tag[int(country_id)] = tag
            # Initialize country laws list
            if not human_countries or tag in human_countries:
                country_laws[tag] = []
    
    # Process laws database to find active laws
    for law_id, law_data in laws_db.items():
        if not isinstance(law_data, dict):
            continue
        
        law_type = law_data.get('law')
        country_id = law_data.get('country')
        is_active = law_data.get('active', False)
        
        if law_type and country_id is not None and is_active:
            country_id = int(country_id)
            if country_id in country_id_to_tag:
                tag = country_id_to_tag[country_id]
                if tag in country_laws:  # Only add if we're tracking this country
                    country_laws[tag].append(law_type)
    
    return country_laws

def print_comprehensive_law_report(country_laws, human_countries=None):
    """Print a comprehensive report of all laws."""
    print("=" * 80)
    print("VICTORIA 3 COMPREHENSIVE LAW REPORT")
    print("=" * 80)
    
    if human_countries:
        print(f"\nAnalyzing {len(country_laws)} human-controlled countries")
    else:
        print(f"\nAnalyzing {len(country_laws)} countries")
    
    # Group categories
    power_structure_groups = ['governance_principles', 'distribution_of_power', 'citizenship', 
                             'church_and_state', 'bureaucracy', 'army_model', 'internal_security']
    economy_groups = ['economic_system', 'trade_policy', 'taxation', 'land_reform', 
                     'colonization', 'policing', 'education_system', 'health_system']
    human_rights_groups = ['free_speech', 'labor_rights', 'childrens_rights', 'rights_of_women',
                          'welfare', 'migration', 'slavery']
    
    # Print Power Structure Laws
    print("\n" + "=" * 80)
    print("POWER STRUCTURE LAWS")
    print("=" * 80)
    for law_group_key in power_structure_groups:
        if law_group_key in LAW_GROUPS:
            process_law_group(law_group_key, LAW_GROUPS[law_group_key], country_laws)
    
    # Print Economy Laws
    print("\n" + "=" * 80)
    print("ECONOMY LAWS")
    print("=" * 80)
    for law_group_key in economy_groups:
        if law_group_key in LAW_GROUPS:
            process_law_group(law_group_key, LAW_GROUPS[law_group_key], country_laws)
    
    # Print Human Rights Laws
    print("\n" + "=" * 80)
    print("HUMAN RIGHTS LAWS")
    print("=" * 80)
    for law_group_key in human_rights_groups:
        if law_group_key in LAW_GROUPS:
            process_law_group(law_group_key, LAW_GROUPS[law_group_key], country_laws)
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("-" * 80)
    
    # Count unique law combinations
    law_combinations = set()
    for tag, laws in country_laws.items():
        # Create a sorted tuple of laws for comparison
        law_tuple = tuple(sorted(laws))
        law_combinations.add(law_tuple)
    
    print(f"Total countries analyzed: {len(country_laws)}")
    print(f"Unique law combinations: {len(law_combinations)}")
    
    # Find countries with identical law sets (if human countries only)
    if human_countries and len(country_laws) > 1:
        print("\nCountries with identical law sets:")
        
        # Group countries by their law combinations
        law_groups = defaultdict(list)
        for tag, laws in country_laws.items():
            law_tuple = tuple(sorted(laws))
            law_groups[law_tuple].append(tag)
        
        # Find groups with more than one country
        identical_groups = [countries for countries in law_groups.values() if len(countries) > 1]
        
        if identical_groups:
            for group in identical_groups:
                print(f"  • {', '.join(sorted(group))}")
        else:
            print("  • None - all countries have unique law combinations")

def process_law_group(law_group_key, law_group_info, country_laws):
    """Process and print a single law group."""
    group_name = law_group_info['name']
    possible_laws = law_group_info['laws']
    
    print("\n" + "-" * 60)
    print(f"{group_name.upper()}")
    print("-" * 60)
    
    # Default laws for each category (first in list is usually the default)
    default_laws = {
        'rights_of_women': 'law_legal_guardianship',  # Most countries start with this
        'childrens_rights': 'law_child_labor_allowed',
        'welfare': 'law_no_social_security',
        'labor_rights': 'law_no_workers_rights',
        'free_speech': 'law_censorship',
        'migration': 'law_no_migration_controls',
        'slavery': 'law_slavery_banned',
        'health_system': 'law_no_health_system',
        'education_system': 'law_no_schools',
        'policing': 'law_no_police',
        'colonization': 'law_no_colonial_affairs',
    }
    
    # Count countries by law
    law_counts = defaultdict(list)
    
    for tag, laws in country_laws.items():
        # Find which law from this group the country has
        found_law = False
        for law in laws:
            if law in possible_laws:
                law_counts[law].append(tag)
                found_law = True
                break  # Each country can only have one law per group
        
        # If no law found in this category and we have a default, assign the default
        if not found_law and law_group_key in default_laws:
            default = default_laws[law_group_key]
            if default in possible_laws:
                law_counts[default].append(tag)
    
    # Sort by number of countries (most common first)
    sorted_laws = sorted(law_counts.items(), key=lambda x: (-len(x[1]), x[0]))
    
    if sorted_laws:
        for law, countries in sorted_laws:
            # Format law name nicely (remove 'law_' prefix for display)
            law_display = law[4:] if law.startswith('law_') else law
            law_display = law_display.replace('_', ' ').title()
            print(f"\n{law_display} ({len(countries)} countries):")
            
            # Sort countries alphabetically and display in columns
            sorted_countries = sorted(countries)
            
            # Display in columns of 8 for better readability
            for i in range(0, len(sorted_countries), 8):
                batch = sorted_countries[i:i+8]
                print("  " + ", ".join(batch))
    else:
        print("  No data available for this law category")

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive Victoria 3 law report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('--humans', action='store_true', help='Only analyze human-controlled countries')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Find the save file
    if args.save_file:
        save_path = args.save_file
    else:
        # Find the latest save file
        saves = glob.glob('extracted-saves/*_extracted.json')
        if not saves:
            print("Error: No extracted save files found")
            sys.exit(1)
        save_path = max(saves, key=os.path.getmtime)
    
    if not os.path.exists(save_path):
        print(f"Error: Save file not found: {save_path}")
        sys.exit(1)
    
    # Load human countries if requested
    human_countries = None
    if args.humans:
        human_countries = set()
        if os.path.exists('humans.txt'):
            with open('humans.txt', 'r') as f:
                human_countries = {line.strip() for line in f if line.strip()}
    
    print(f"Loading save data from {save_path}...")
    save_data = load_save_data(save_path)
    
    print("Analyzing laws...")
    country_laws = analyze_laws(save_data, human_countries)
    
    # Generate report
    if args.output:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_comprehensive_law_report(country_laws, human_countries)
        
        with open(args.output, 'w') as f:
            f.write(output.getvalue())
        print(f"Report saved to: {args.output}")
    else:
        print_comprehensive_law_report(country_laws, human_countries)

if __name__ == '__main__':
    main()