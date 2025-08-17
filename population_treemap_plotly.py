#!/usr/bin/env venv/bin/python
"""
Victoria 3 Population Tree Map Generator using Plotly

Creates a hierarchical treemap with power blocs as parent nodes
and countries as child nodes, sized by population.
"""

import json
import argparse
import os
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Victoria 3 authentic country colors
COUNTRY_COLORS = {
    'GBR': '#e6454e',    # British red
    'USA': '#425ec1',    # American blue  
    'FRA': '#1432d2',    # French blue
    'BIC': '#bc713d',    # Colonial brown
    'CHI': '#fcb93d',    # Imperial yellow
    'ITA': '#7dab54',    # Italian green
    'SPA': '#d48806',    # Spanish orange
    'POR': '#c4561e',    # Portuguese orange-red
    'TUR': '#a3542b',    # Ottoman brown
    'RUS': '#4a7c2a',    # Russian green
    'JAP': '#cc3333',    # Japanese red
    'YUG': '#8b4a8b',    # Yugoslav purple
}

def load_save_data(filepath):
    """Load JSON save data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)

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
        print(f"Warning: {humans_file} not found.")
    return humans

def get_country_tag(countries, country_id):
    """Get country tag from country ID."""
    country = countries.get(str(country_id), {})
    if isinstance(country, dict):
        definition = country.get('definition', '')
        if definition:
            return definition
    return f"ID_{country_id}"

def get_country_population(countries, country_id):
    """Get the total population for a country."""
    country = countries.get(str(country_id), {})
    if not isinstance(country, dict):
        return 0
    
    # Get population from country data
    population = country.get('population', 0)
    if population > 0:
        return population
    
    # If not directly available, try to calculate from pop_statistics
    pop_stats = country.get('pop_statistics', {})
    if pop_stats:
        # Sum all population strata
        total_pop = 0
        total_pop += pop_stats.get('population_lower_strata', 0)
        total_pop += pop_stats.get('population_middle_strata', 0)
        total_pop += pop_stats.get('population_upper_strata', 0)
        
        if total_pop > 0:
            return total_pop
        
        # Alternative: sum workforce types
        workforce_total = 0
        workforce_total += pop_stats.get('population_salaried_workforce', 0)
        workforce_total += pop_stats.get('population_subsisting_workforce', 0)
        workforce_total += pop_stats.get('population_unemployed_workforce', 0)
        workforce_total += pop_stats.get('population_government_workforce', 0)
        workforce_total += pop_stats.get('population_military_workforce', 0)
        
        # Workforce is typically about 40% of population, so estimate total
        if workforce_total > 0:
            return workforce_total * 2.5  # Rough estimate
    
    return 0

def get_subject_relationships(save_data):
    """Extract subject relationships from pacts, including transitive relationships."""
    pacts = save_data.get('pacts', {}).get('database', {})
    direct_subjects = {}  # Direct overlord -> [subjects] mapping
    all_subjects = {}  # Final overlord -> [all subjects including indirect]
    
    subject_types = ['dominion', 'puppet', 'protectorate', 'colony', 'personal_union', 'chartered_company']
    
    # First pass: get direct relationships
    for pact_id, pact in pacts.items():
        if not isinstance(pact, dict):
            continue
        
        action = pact.get('action', '')
        if action in subject_types:
            targets = pact.get('targets', {})
            overlord = targets.get('first')
            subject = targets.get('second')
            
            if overlord and subject:
                if overlord not in direct_subjects:
                    direct_subjects[overlord] = []
                direct_subjects[overlord].append(subject)
    
    # Second pass: build transitive relationships
    def get_all_subjects(country_id, visited=None):
        """Recursively get all subjects of a country."""
        if visited is None:
            visited = set()
        
        if country_id in visited:
            return []  # Avoid cycles
        
        visited.add(country_id)
        result = []
        
        if country_id in direct_subjects:
            for subject in direct_subjects[country_id]:
                result.append(subject)
                # Recursively get subjects of subjects
                result.extend(get_all_subjects(subject, visited))
        
        return result
    
    # Build final mapping with all transitive relationships
    for overlord in direct_subjects:
        all_subjects[overlord] = get_all_subjects(overlord)
    
    return all_subjects

def analyze_power_blocs(save_data, humans_list, min_pop_threshold=1000000):
    """Analyze power blocs and return data for treemap."""
    countries = save_data.get('country_manager', {}).get('database', {})
    power_blocs = save_data.get('power_bloc_manager', {}).get('database', {})
    
    subject_relationships = get_subject_relationships(save_data)
    
    # Get ALL countries with their population first
    all_countries = {}  # All countries for power bloc analysis
    display_countries = {}  # Countries above threshold for display
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        tag = get_country_tag(countries, country_id)
        population = get_country_population(countries, country_id)
        
        if population > 0:  # Only include countries with some population
            country_data = {
                'tag': tag,
                'population': population,
                'is_human': tag in humans_list,
                'power_bloc': None,
                'is_subject': False,
                'overlord': None
            }
            
            all_countries[int(country_id)] = country_data
            
            # Also add to display list if above threshold
            if population > min_pop_threshold:
                display_countries[int(country_id)] = country_data
    
    countries_in_blocs = set()
    power_bloc_data = {}
    bloc_totals = {}  # Track total population and count for each bloc
    
    # Analyze power blocs using ALL countries for totals
    for bloc_id, bloc in power_blocs.items():
        if not isinstance(bloc, dict):
            continue
        
        # Get bloc name
        name_data = bloc.get('name', {})
        if isinstance(name_data, dict):
            if 'name' in name_data:
                name_data = name_data['name']
            if isinstance(name_data, dict) and 'custom' in name_data:
                name = name_data['custom']
            else:
                name = f'Bloc_{bloc_id}'
        else:
            name = f'Bloc_{bloc_id}'
        leader = bloc.get('leader')
        
        if not leader:
            continue
        
        # Get leader tag
        leader_tag = get_country_tag(countries, leader)
        
        # Find members by checking countries for power_bloc_as_core
        bloc_countries = []
        total_pop = 0
        total_countries = 0
        direct_members = set()
        
        # First pass: find direct members
        for country_id in all_countries:
            country_data = countries.get(str(country_id), {})
            if isinstance(country_data, dict):
                if country_data.get('power_bloc_as_core') == int(bloc_id):
                    all_countries[country_id]['power_bloc'] = name
                    bloc_countries.append(country_id)
                    countries_in_blocs.add(country_id)
                    direct_members.add(country_id)
                    total_pop += all_countries[country_id]['population']
                    total_countries += 1
        
        # Second pass: add subjects of members
        for member_id in direct_members:
            if member_id in subject_relationships:
                for subject_id in subject_relationships[member_id]:
                    if subject_id in all_countries and subject_id not in countries_in_blocs:
                        all_countries[subject_id]['power_bloc'] = name
                        all_countries[subject_id]['is_subject'] = True
                        all_countries[subject_id]['overlord'] = member_id
                        bloc_countries.append(subject_id)
                        countries_in_blocs.add(subject_id)
                        total_pop += all_countries[subject_id]['population']
                        total_countries += 1
        
        if bloc_countries:
            power_bloc_data[name] = {
                'countries': bloc_countries,
                'leader': leader,
                'leader_tag': leader_tag
            }
            bloc_totals[name] = {
                'total_pop': total_pop,
                'total_countries': total_countries
            }
    
    # Handle unaligned countries
    unaligned = []
    unaligned_pop = 0
    unaligned_count = 0
    
    for country_id, country in all_countries.items():
        if country_id not in countries_in_blocs:
            country['power_bloc'] = 'Independent Countries'
            unaligned.append(country_id)
            unaligned_pop += country['population']
            unaligned_count += 1
    
    if unaligned:
        power_bloc_data['Independent Countries'] = {
            'countries': unaligned,
            'leader': None,
            'leader_tag': None
        }
        bloc_totals['Independent Countries'] = {
            'total_pop': unaligned_pop,
            'total_countries': unaligned_count
        }
    
    return power_bloc_data, all_countries, display_countries, bloc_totals

def create_treemap(power_bloc_data, all_countries, display_countries, bloc_totals, humans_list, save_data):
    """Create the treemap visualization."""
    
    # Get game date from save data
    game_date = save_data.get('meta_data', {}).get('game_date', 'Unknown')
    
    # Format date nicely
    date_parts = game_date.split('.')
    if len(date_parts) >= 3:
        year = date_parts[0]
        month = date_parts[1]
        day = date_parts[2]
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        try:
            month_name = months[int(month)]
            formatted_date = f"{month_name} {int(day)}, {year}"
        except:
            formatted_date = game_date
    else:
        formatted_date = game_date
    
    # Prepare data for treemap
    data = []
    
    # Sort power blocs by total population
    sorted_blocs = sorted(bloc_totals.items(), key=lambda x: x[1]['total_pop'], reverse=True)
    
    for bloc_name, totals in sorted_blocs:
        bloc_info = power_bloc_data[bloc_name]
        
        # Create aggregated "Other" entries for small countries
        bloc_display_countries = []
        other_countries = []
        other_pop = 0
        
        for country_id in bloc_info['countries']:
            if country_id in display_countries:
                bloc_display_countries.append(country_id)
            elif country_id in all_countries:
                other_countries.append(country_id)
                other_pop += all_countries[country_id]['population']
        
        # Add displayed countries
        for country_id in bloc_display_countries:
            country = all_countries[country_id]
            
            # Determine color
            if country['is_human']:
                if country['is_subject']:
                    # Player subject keeps player color
                    base_color = COUNTRY_COLORS.get(country['tag'], '#808080')
                else:
                    # Player country with full color
                    base_color = COUNTRY_COLORS.get(country['tag'], '#808080')
            else:
                if country['is_subject'] and country['overlord'] in all_countries:
                    overlord_tag = all_countries[country['overlord']]['tag']
                    if overlord_tag in COUNTRY_COLORS:
                        # AI subject gets faded overlord color
                        base_color = COUNTRY_COLORS.get(overlord_tag, '#808080')
                        # Lighten the color for AI subjects
                        base_color = f"{base_color}80"  # Add transparency
                    else:
                        base_color = '#606060'
                else:
                    # Non-subject AI country
                    base_color = '#606060'
            
            data.append({
                'country': f"{country['tag']}",
                'power_bloc': f"{bloc_name} ({totals['total_pop']/1e6:.1f}M) ({totals['total_countries']} countries)",
                'population': country['population'],
                'population_display': f"{country['population']/1e6:.1f}M",
                'color': base_color,
                'is_leader': country_id == bloc_info['leader']
            })
        
        # Add "Other" entry if there are small countries
        if other_countries:
            data.append({
                'country': f"Other ({len(other_countries)} countries)",
                'power_bloc': f"{bloc_name} ({totals['total_pop']/1e6:.1f}M) ({totals['total_countries']} countries)",
                'population': other_pop,
                'population_display': f"{other_pop/1e6:.1f}M",
                'color': '#404040',
                'is_leader': False
            })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create color map from data
    color_map = {row['color']: row['color'] for _, row in df.iterrows()}
    
    # Create treemap
    fig = px.treemap(
        df,
        path=['power_bloc', 'country'],
        values='population',
        color='color',
        color_discrete_map=color_map,
        hover_data={'population_display': True}
    )
    
    # Update layout
    fig.update_traces(
        texttemplate='<b>%{label}</b><br>%{customdata[0]}',
        textposition='middle center',
        hovertemplate='<b>%{label}</b><br>Population: %{customdata[0]}<extra></extra>'
    )
    
    # Style the power bloc parent nodes with bigger size and better title
    fig.update_layout(
        margin=dict(t=100, l=0, r=0, b=0),
        title={
            'text': f'Population by Power Bloc<br><sub>{formatted_date} • Player countries in color • Subjects faded • AI in gray</sub>',
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24)
        },
        font=dict(size=14),
        height=1200,
        width=2000
    )
    
    # Update power bloc parent colors to be dark
    fig.data[0].marker.colors = [
        '#202020' if '(' in label else color 
        for label, color in zip(fig.data[0].labels, fig.data[0].marker.colors)
    ]
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 population treemap by power blocs')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output', help='Output file for the chart (PNG or HTML)')
    parser.add_argument('--min-pop', type=float, default=1.0, 
                       help='Minimum population in millions to display individually (default: 1M)')
    
    args = parser.parse_args()
    
    # Find save file
    if args.save_file:
        save_path = args.save_file
    else:
        import glob
        saves = glob.glob('extracted-saves/*_extracted.json')
        if not saves:
            print("Error: No extracted save files found")
            return
        save_path = max(saves, key=os.path.getmtime)
    
    if not os.path.exists(save_path):
        print(f"Error: Save file not found: {save_path}")
        return
    
    print(f"Loaded {len(load_humans_list())} human-controlled countries")
    
    # Load and analyze data
    print("Loading save data...")
    save_data = load_save_data(save_path)
    humans_list = load_humans_list()
    
    print(f"Analyzing power blocs (population threshold: {args.min_pop:.1f}M)...")
    power_bloc_data, all_countries, display_countries, bloc_totals = analyze_power_blocs(
        save_data, humans_list, min_pop_threshold=args.min_pop * 1e6
    )
    
    # Create treemap
    fig = create_treemap(power_bloc_data, all_countries, display_countries, bloc_totals, humans_list, save_data)
    
    # Save output
    if args.output:
        output_path = Path(args.output)
        if output_path.suffix.lower() == '.png':
            fig.write_image(str(output_path), width=2000, height=1200)
            print(f"Static treemap saved to: {output_path}")
        else:
            # Save as HTML by default
            html_path = output_path.with_suffix('.html')
            fig.write_html(str(html_path))
            print(f"Interactive treemap saved to: {html_path}")
            
            # Also save as PNG if requested
            if output_path.suffix.lower() != '.html':
                png_path = output_path.with_suffix('.png')
                fig.write_image(str(png_path), width=2000, height=1200)
                print(f"Static treemap saved to: {png_path}")
    else:
        # Show in browser
        fig.show()
    
    # Print summary
    print("\nPower Bloc Summary (by total population):")
    sorted_blocs = sorted(bloc_totals.items(), key=lambda x: x[1]['total_pop'], reverse=True)
    for bloc_name, totals in sorted_blocs:
        bloc_info = power_bloc_data[bloc_name]
        
        # Count player countries
        player_count = sum(1 for c_id in bloc_info['countries'] 
                          if c_id in all_countries and all_countries[c_id]['is_human'])
        
        # Count subjects
        subject_count = sum(1 for c_id in bloc_info['countries'] 
                           if c_id in all_countries and all_countries[c_id]['is_subject'])
        
        print(f"• {bloc_name}: {totals['total_pop']/1e6:.1f}M people ({totals['total_countries']} countries)")
        
        if player_count > 0:
            print(f"  - {player_count} player countries")
        if subject_count > 0:
            print(f"  - {subject_count} subjects")

if __name__ == '__main__':
    main()