#!/usr/bin/env python3
"""
Victoria 3 Migration Attraction Report

Analyzes migration patterns to identify which countries are attracting or losing population.
Shows net migration flows and top migration destinations.
"""

import json
import os
import sys
import argparse
from collections import defaultdict
import glob

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

def analyze_migration(save_data):
    """Analyze migration patterns in the save data."""
    countries = save_data.get('country_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    
    # Load human countries
    human_countries = set()
    if os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Track migration by country
    country_emigration = defaultdict(float)  # People leaving
    country_immigration = defaultdict(float)  # People arriving
    migration_flows = defaultdict(lambda: defaultdict(float))  # From -> To -> Amount
    
    # First pass: collect all emigration data by state
    state_emigration = {}  # state_id -> (country_id, weekly_emigration, destinations)
    
    for state_id, state in states.items():
        if not isinstance(state, dict):
            continue
        
        country_id = state.get('country')
        if not country_id:
            continue
        
        migration_stats = state.get('last_week_pop_migration_statistics', {})
        weekly_emigration = migration_stats.get('weekly_emigration', 0)
        emigration_states = migration_stats.get('emigration_states', [])
        
        if weekly_emigration > 0:
            state_emigration[int(state_id)] = (country_id, weekly_emigration, emigration_states)
            country_emigration[country_id] += weekly_emigration
    
    # Second pass: track immigration by looking at who receives emigrants
    for source_state_id, (source_country, emigration_amount, dest_state_ids) in state_emigration.items():
        if dest_state_ids:
            # The emigration amount is split among destination states
            # The actual split might be weighted, but we'll assume equal for now
            amount_per_destination = emigration_amount / len(dest_state_ids)
            
            for dest_state_id in dest_state_ids:
                dest_state = states.get(str(dest_state_id))
                if dest_state and isinstance(dest_state, dict):
                    dest_country = dest_state.get('country')
                    if dest_country:
                        country_immigration[dest_country] += amount_per_destination
                        
                        # Track flows between countries
                        if dest_country != source_country:
                            migration_flows[source_country][dest_country] += amount_per_destination
    
    # Calculate net migration for each country
    net_migration = {}
    for country_id in set(list(country_emigration.keys()) + list(country_immigration.keys())):
        immigration = country_immigration.get(country_id, 0)
        emigration = country_emigration.get(country_id, 0)
        net = immigration - emigration
        net_migration[country_id] = {
            'immigration': immigration,
            'emigration': emigration,
            'net': net
        }
    
    return net_migration, migration_flows, countries, human_countries

def print_migration_report(net_migration, migration_flows, countries, human_countries, filter_humans=False):
    """Print the migration analysis report."""
    print("=" * 80)
    print("VICTORIA 3 MIGRATION ATTRACTION REPORT")
    print("=" * 80)
    print("\nNote: Migration values are weekly rates (people per week)")
    print("Positive net migration = Country is attracting immigrants")
    print("Negative net migration = Country is losing population to emigration\n")
    
    # Filter and sort countries by net migration
    migration_list = []
    for country_id, stats in net_migration.items():
        country_tag = get_country_tag(countries, country_id)
        
        # Apply human filter if requested
        if filter_humans and human_countries and country_tag not in human_countries:
            continue
        
        # Only include countries with significant migration
        if abs(stats['net']) > 0.001:  # Threshold for significance
            migration_list.append((country_tag, country_id, stats))
    
    # Sort by net migration (most attractive first)
    migration_list.sort(key=lambda x: x[2]['net'], reverse=True)
    
    # Print top immigration magnets
    print("TOP IMMIGRATION DESTINATIONS (Net Migration > 0)")
    print("-" * 50)
    
    immigration_count = 0
    for country_tag, country_id, stats in migration_list:
        if stats['net'] > 0:
            immigration_count += 1
            if immigration_count <= 15:  # Top 15
                print(f"{immigration_count:2}. {country_tag:3}: +{stats['net']*1000:.1f}/week")
                print(f"    Immigration: {stats['immigration']*1000:.1f}, Emigration: {stats['emigration']*1000:.1f}")
                
                # Show top sources of immigrants
                sources = []
                for source_id, destinations in migration_flows.items():
                    if country_id in destinations:
                        source_tag = get_country_tag(countries, source_id)
                        amount = destinations[country_id]
                        if amount > 0.001:
                            sources.append((source_tag, amount))
                
                if sources:
                    sources.sort(key=lambda x: -x[1])
                    top_sources = sources[:3]
                    source_str = ", ".join([f"{tag} ({amt*1000:.1f})" for tag, amt in top_sources])
                    print(f"    Main sources: {source_str}")
    
    if immigration_count > 15:
        print(f"\n... and {immigration_count - 15} more countries attracting immigrants")
    
    # Print top emigration sources
    print("\n" + "=" * 50)
    print("TOP EMIGRATION SOURCES (Net Migration < 0)")
    print("-" * 50)
    
    emigration_count = 0
    for country_tag, country_id, stats in reversed(migration_list):
        if stats['net'] < 0:
            emigration_count += 1
            if emigration_count <= 15:  # Top 15
                print(f"{emigration_count:2}. {country_tag:3}: {stats['net']*1000:.1f}/week")
                print(f"    Immigration: {stats['immigration']*1000:.1f}, Emigration: {stats['emigration']*1000:.1f}")
                
                # Show top destinations
                if country_id in migration_flows:
                    destinations = []
                    for dest_id, amount in migration_flows[country_id].items():
                        if amount > 0.001:
                            dest_tag = get_country_tag(countries, dest_id)
                            destinations.append((dest_tag, amount))
                    
                    if destinations:
                        destinations.sort(key=lambda x: -x[1])
                        top_dests = destinations[:3]
                        dest_str = ", ".join([f"{tag} ({amt*1000:.1f})" for tag, amt in top_dests])
                        print(f"    Main destinations: {dest_str}")
    
    if emigration_count > 15:
        print(f"\n... and {emigration_count - 15} more countries losing population")
    
    # Summary statistics
    print("\n" + "=" * 50)
    print("SUMMARY STATISTICS")
    print("-" * 50)
    
    total_immigration = sum(s['immigration'] for s in net_migration.values())
    total_emigration = sum(s['emigration'] for s in net_migration.values())
    
    print(f"Total global emigration: {total_emigration*1000:.1f} people/week")
    print(f"Total global immigration: {total_immigration*1000:.1f} people/week")
    print(f"Countries attracting immigrants: {immigration_count}")
    print(f"Countries losing population: {emigration_count}")
    
    # Human countries migration summary if filtered
    if filter_humans and human_countries:
        print("\n" + "=" * 50)
        print("HUMAN COUNTRIES MIGRATION SUMMARY")
        print("-" * 50)
        
        # Get migration data for ALL human countries, not just those in migration_list
        human_migration = []
        for country_tag in human_countries:
            # Find the country_id for this tag
            country_id = None
            for cid, country in countries.items():
                if isinstance(country, dict) and country.get('definition') == country_tag:
                    country_id = int(cid)  # Convert to int for matching
                    break
            
            if country_id and country_id in net_migration:
                stats = net_migration[country_id]
                human_migration.append((country_tag, stats))
            else:
                # Country not found or has no migration data - show as 0
                human_migration.append((country_tag, {
                    'immigration': 0,
                    'emigration': 0,
                    'net': 0
                }))
        
        human_migration.sort(key=lambda x: x[1]['net'], reverse=True)
        
        for country_tag, stats in human_migration:
            net = stats['net']
            # Scale: values are in thousands, so multiply by 1000 for actual people
            if net > 0.001:  # More than 1 person/week
                print(f"{country_tag:3}: ATTRACTING +{net*1000:.1f} people/week")
            elif net < -0.001:  # Less than -1 person/week
                print(f"{country_tag:3}: LOSING     {net*1000:.1f} people/week")
            else:
                print(f"{country_tag:3}: BALANCED   {net*1000:.1f} people/week")

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 migration attraction report')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output', help='Output file for the report')
    parser.add_argument('--humans', action='store_true', help='Focus on human-controlled countries')
    
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
    
    print(f"Loading save data: {save_path}")
    save_data = load_save_data(save_path)
    
    print("Analyzing migration patterns...")
    net_migration, migration_flows, countries, human_countries = analyze_migration(save_data)
    
    # Generate report
    if args.output:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            print_migration_report(net_migration, migration_flows, countries, human_countries, 
                                 filter_humans=args.humans)
        
        with open(args.output, 'w') as f:
            f.write(output.getvalue())
        print(f"Migration report saved to: {args.output}")
    else:
        print_migration_report(net_migration, migration_flows, countries, human_countries, 
                             filter_humans=args.humans)

if __name__ == '__main__':
    main()