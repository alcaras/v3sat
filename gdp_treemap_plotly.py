#!/usr/bin/env venv/bin/python
"""
Victoria 3 GDP Tree Map Generator using Plotly

Creates a proper hierarchical treemap with power blocs as parent nodes
and countries as child nodes, sized by GDP.
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

def get_country_gdp(countries, country_id):
    """Get the latest GDP value for a country."""
    country = countries.get(str(country_id), {})
    if not isinstance(country, dict):
        return 0.0
    
    gdp_data = country.get('gdp', {})
    if not gdp_data:
        return 0.0
    
    channels = gdp_data.get('channels', {})
    if channels:
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
                return float(values[-1])
    
    return 0.0

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

def analyze_power_blocs(save_data, humans_list, min_gdp_threshold=10000000):
    """Analyze power blocs and return data for treemap."""
    countries = save_data.get('country_manager', {}).get('database', {})
    power_blocs = save_data.get('power_bloc_manager', {}).get('database', {})
    
    subject_relationships = get_subject_relationships(save_data)
    
    # Get ALL countries with their GDP first
    all_countries = {}  # All countries for power bloc analysis
    display_countries = {}  # Countries above threshold for display
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        tag = get_country_tag(countries, country_id)
        gdp = get_country_gdp(countries, country_id)
        
        if gdp > 0:  # Only include countries with some GDP
            country_data = {
                'tag': tag,
                'gdp': gdp,
                'is_human': tag in humans_list,
                'power_bloc': None,
                'is_subject': False,
                'overlord': None
            }
            
            all_countries[int(country_id)] = country_data
            
            # Also add to display list if above threshold
            if gdp > min_gdp_threshold:
                display_countries[int(country_id)] = country_data
    
    countries_in_blocs = set()
    power_bloc_data = {}
    bloc_totals = {}  # Track total GDP and count for each bloc
    
    # Analyze power blocs using ALL countries for totals
    for bloc_id, bloc in power_blocs.items():
        if not isinstance(bloc, dict) or bloc.get('status') != 'active':
            continue
        
        # Get bloc name
        name_data = bloc.get('name', {})
        if isinstance(name_data, dict) and 'name' in name_data:
            name_data = name_data['name']
        
        if isinstance(name_data, dict) and 'custom' in name_data:
            bloc_name = name_data['custom']
        else:
            bloc_name = f"Power Bloc {bloc_id}"
        
        # Shorten long names
        if len(bloc_name) > 30:
            bloc_name = bloc_name[:27] + "..."
        
        # Find ALL members (for totals) and display members (for treemap)
        all_bloc_members = []  # All members for total calculation
        display_bloc_members = []  # Members above threshold for display
        small_bloc_members = []  # Members below threshold
        direct_members = set()
        
        for country_id, country in countries.items():
            if not isinstance(country, dict):
                continue
            
            if country.get('power_bloc_as_core') == int(bloc_id):
                country_id_int = int(country_id)
                if country_id_int in all_countries:
                    direct_members.add(country_id_int)
                    all_countries[country_id_int]['power_bloc'] = bloc_name
                    countries_in_blocs.add(country_id_int)
                    all_bloc_members.append(all_countries[country_id_int])
                    
                    # Add to display list if above threshold or human-controlled
                    if country_id_int in display_countries or all_countries[country_id_int]['is_human']:
                        display_bloc_members.append(all_countries[country_id_int])
                    else:
                        small_bloc_members.append(all_countries[country_id_int])
        
        # Add subjects of bloc members (including transitive subjects)
        for member_id in direct_members:
            if member_id in subject_relationships:
                for subject_id in subject_relationships[member_id]:
                    if subject_id in all_countries and subject_id not in countries_in_blocs:
                        # Find the immediate overlord for color determination
                        immediate_overlord = member_id
                        for potential_overlord, subjects in subject_relationships.items():
                            if subject_id in subjects and potential_overlord in all_countries:
                                immediate_overlord = potential_overlord
                                break
                        
                        all_countries[subject_id]['power_bloc'] = bloc_name
                        all_countries[subject_id]['is_subject'] = True
                        all_countries[subject_id]['overlord'] = all_countries[immediate_overlord]['tag']
                        countries_in_blocs.add(subject_id)
                        all_bloc_members.append(all_countries[subject_id])
                        
                        # Add to display list if above threshold or if human-controlled
                        if subject_id in display_countries or all_countries[subject_id]['is_human']:
                            display_bloc_members.append(all_countries[subject_id])
                        else:
                            small_bloc_members.append(all_countries[subject_id])
        
        if all_bloc_members:
            # Store totals for bloc titles
            bloc_totals[bloc_name] = {
                'total_gdp': sum(c['gdp'] for c in all_bloc_members),
                'total_count': len(all_bloc_members)
            }
            
            # Create display list with "Other" entry if needed
            if small_bloc_members:
                small_gdp = sum(c['gdp'] for c in small_bloc_members)
                small_tags = [c['tag'] for c in small_bloc_members]
                small_tags_str = ', '.join(small_tags[:8])  # Show first 8
                if len(small_tags) > 8:
                    small_tags_str += f" ... (+{len(small_tags)-8} more)"
                
                other_entry = {
                    'tag': f"Other ({len(small_bloc_members)} countries)",
                    'gdp': small_gdp,
                    'is_human': False,
                    'power_bloc': bloc_name,
                    'is_subject': False,
                    'overlord': None,
                    'small_countries_list': small_tags_str
                }
                display_bloc_members.append(other_entry)
            
            power_bloc_data[bloc_name] = display_bloc_members
    
    # Add independent countries (above threshold or human-controlled)
    independent_display = []
    independent_small = []
    
    for country_id, country_data in all_countries.items():
        if country_id not in countries_in_blocs:
            # Always show human countries, regardless of GDP threshold
            if country_id in display_countries or country_data['is_human']:
                independent_display.append(country_data)
            else:
                independent_small.append(country_data)
    
    if independent_display or independent_small:
        # Calculate totals for independent countries
        all_independent = independent_display + independent_small
        total_independent_gdp = sum(c['gdp'] for c in all_independent)
        total_independent_count = len(all_independent)
        
        bloc_totals["Independent Countries"] = {
            'total_gdp': total_independent_gdp,
            'total_count': total_independent_count
        }
        
        # Add "Other" entry for small independent countries if needed
        if independent_small:
            small_gdp = sum(c['gdp'] for c in independent_small)
            small_tags = [c['tag'] for c in independent_small]
            small_tags_str = ', '.join(small_tags[:10])  # Show first 10
            if len(small_tags) > 10:
                small_tags_str += f" ... (+{len(small_tags)-10} more)"
            
            other_entry = {
                'tag': f"Other ({len(independent_small)} countries)",
                'gdp': small_gdp,
                'is_human': False,
                'power_bloc': None,
                'is_subject': False,
                'overlord': None,
                'small_countries_list': small_tags_str
            }
            independent_display.append(other_entry)
        
        power_bloc_data["Independent Countries"] = independent_display
    
    return power_bloc_data, bloc_totals

def format_gdp(gdp):
    """Format GDP for display."""
    if gdp >= 1e9:
        return f"£{gdp/1e9:.1f}B"
    elif gdp >= 1e6:
        return f"£{gdp/1e6:.0f}M"
    else:
        return f"£{gdp/1e3:.0f}K"

def fade_color(hex_color, opacity=0.4):
    """Convert a hex color to a faded version by mixing with white."""
    # Remove the # if present
    hex_color = hex_color.lstrip('#')
    
    # Parse RGB values
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16) 
    b = int(hex_color[4:6], 16)
    
    # Mix with white to create faded effect
    r_faded = int(r * opacity + 255 * (1 - opacity))
    g_faded = int(g * opacity + 255 * (1 - opacity))
    b_faded = int(b * opacity + 255 * (1 - opacity))
    
    return f"#{r_faded:02x}{g_faded:02x}{b_faded:02x}"

def create_plotly_treemap(power_bloc_data, humans_list, bloc_totals, save_data, output_file='gdp_treemap_plotly.html'):
    """Create a proper hierarchical treemap using Plotly."""
    
    # Get game date and session name from save data
    game_date = save_data.get('meta_data', {}).get('game_date', 'Unknown')
    # Extract session name from output file path if available
    import os
    session_name = 'Victoria 3'
    if 'Session' in output_file:
        parts = os.path.basename(output_file).split('_')
        for part in parts:
            if 'Session' in part:
                session_name = part
                break
    
    # Prepare data for Plotly treemap
    data_rows = []
    
    for bloc_name, countries in power_bloc_data.items():
        # Sort countries by GDP within each bloc
        sorted_countries = sorted(countries, key=lambda x: x['gdp'], reverse=True)
        
        for country in sorted_countries:
            # Determine country type and color
            if country['is_human']:
                country_type = "Player"
                color = COUNTRY_COLORS.get(country['tag'], '#8B0000')
            elif country['is_subject']:
                if country['is_human']:  # Player-controlled subject (like BIC)
                    country_type = "Player Subject"
                    color = COUNTRY_COLORS.get(country['tag'], '#8B0000')
                else:
                    # Non-player subject - use faded color of overlord
                    country_type = "AI Subject"
                    overlord_color = COUNTRY_COLORS.get(country['overlord'], '#666666')
                    color = fade_color(overlord_color, 0.4)
            else:
                country_type = "AI"
                color = '#666666'
            
            # Create label - no need for subject text since color shows it
            gdp_formatted = format_gdp(country['gdp'])
            if 'small_countries_list' in country:
                # Special handling for "Other Countries" entry
                label = f"{country['tag']}<br>{gdp_formatted}<br>{country['small_countries_list']}"
            else:
                label = f"{country['tag']}<br>{gdp_formatted}"
            
            data_rows.append({
                'ids': f"{bloc_name}/{country['tag']}",
                'labels': label,
                'parents': bloc_name,
                'values': country['gdp'],
                'country_tag': country['tag'],
                'bloc': bloc_name,
                'country_type': country_type,
                'color': color,
                'text_color': 'white',  # White text for countries
                'gdp_formatted': gdp_formatted
            })
    
    # Add parent nodes (power blocs) using correct totals
    for bloc_name in power_bloc_data.keys():
        if bloc_name in bloc_totals:
            total_gdp = bloc_totals[bloc_name]['total_gdp']
            total_count = bloc_totals[bloc_name]['total_count']
        else:
            # Fallback for independent/other countries
            countries = power_bloc_data[bloc_name]
            total_gdp = sum(c['gdp'] for c in countries)
            total_count = len(countries)
        
        data_rows.append({
            'ids': bloc_name,
            'labels': f"{bloc_name} (£{total_gdp/1e6:.0f}M) ({total_count} countries)",
            'parents': "",
            'values': total_gdp,
            'country_tag': "",
            'bloc': bloc_name,
            'country_type': "Power Bloc",
            'color': '#333333',  # Dark gray/black for blocs
            'text_color': 'black',  # Black text for power blocs
            'gdp_formatted': format_gdp(total_gdp)
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(data_rows)
    
    # Create the treemap
    fig = go.Figure(go.Treemap(
        ids=df['ids'],
        labels=df['labels'],
        parents=df['parents'],
        values=df['values'],
        branchvalues="total",
        # Use custom colors
        marker=dict(
            colors=df['color'],
            line=dict(width=2, color='white')
        ),
        # Hover information
        hovertemplate='<b>%{label}</b><br>GDP: %{customdata}<extra></extra>',
        customdata=df['gdp_formatted'],
        # Text styling
        textfont=dict(size=12, color='white'),
        pathbar=dict(visible=True, thickness=20),
        maxdepth=3,
        tiling=dict(
            squarifyratio=1,
            flip='x'
        )
    ))
    
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
    
    # Update layout with bigger size and better title
    fig.update_layout(
        title=dict(
            text=f"{session_name} - GDP by Power Bloc<br><sub>{formatted_date} • Player countries in color • Subjects in gray • AI in dark gray</sub>",
            x=0.5,
            font=dict(size=24)
        ),
        width=2000,
        height=1200,
        margin=dict(t=100, l=20, r=20, b=20),
        font=dict(family="Arial", size=12),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    # Save as HTML
    html_file = output_file.replace('.png', '.html')
    fig.write_html(html_file)
    print(f"Interactive treemap saved to: {html_file}")
    
    # Also save as static PNG if requested
    if output_file.endswith('.png'):
        try:
            fig.write_image(output_file, width=2000, height=1200)
            print(f"Static treemap saved to: {output_file}")
        except Exception as e:
            print(f"Note: Could not save PNG ({e}), but HTML version is available")
    
    # Print summary
    print(f"\nPower Bloc Summary (by total GDP):")
    sorted_blocs = sorted(bloc_totals.items(), key=lambda x: x[1]['total_gdp'] if isinstance(x[1], dict) else x[1], reverse=True)
    
    for bloc_name, bloc_info in sorted_blocs:
        if isinstance(bloc_info, dict):
            total_gdp = bloc_info['total_gdp']
            total_count = bloc_info['total_count']
        else:
            total_gdp = bloc_info
            total_count = len(power_bloc_data.get(bloc_name, []))
        
        countries = power_bloc_data.get(bloc_name, [])
        player_count = sum(1 for c in countries if c.get('is_human', False))
        subject_count = sum(1 for c in countries if c.get('is_subject', False))
        
        print(f"• {bloc_name}: {format_gdp(total_gdp)} ({total_count} countries)")
        if player_count > 0:
            print(f"  - {player_count} player countries")
        if subject_count > 0:
            print(f"  - {subject_count} subjects")
    
    return html_file

def main():
    parser = argparse.ArgumentParser(description='Generate Plotly treemap for Victoria 3 GDP data')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output', default='reports/gdp_treemap_plotly.html',
                       help='Output file for the treemap (HTML or PNG)')
    parser.add_argument('--humans', default='humans.txt',
                       help='File containing list of human-controlled countries')
    parser.add_argument('--min-gdp', type=float, default=1.0,
                       help='Minimum GDP in millions to include (default: 1M)')
    
    args = parser.parse_args()
    
    # Determine save file
    if args.save_file:
        save_path = args.save_file
    else:
        # Find latest extracted save file
        extracted_dir = Path('extracted-saves')
        if not extracted_dir.exists():
            print("Error: extracted-saves directory not found")
            return
        
        json_files = list(extracted_dir.glob('*_extracted.json'))
        if not json_files:
            print("Error: No extracted save files found")
            return
        
        save_path = max(json_files, key=lambda p: p.stat().st_mtime)
        
        print(f"Using save file: {save_path}")
    
    # Load data
    humans_list = load_humans_list(args.humans)
    print(f"Loaded {len(humans_list)} human-controlled countries")
    
    print(f"Loading save data...")
    save_data = load_save_data(save_path)
    
    print(f"Analyzing power blocs (GDP threshold: £{args.min_gdp}M)...")
    power_bloc_data, bloc_totals = analyze_power_blocs(save_data, humans_list,
                                                      min_gdp_threshold=args.min_gdp * 1e6)
    
    if not power_bloc_data:
        print("No GDP data found above threshold")
        return
    
    # Create output directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Generate treemap
    create_plotly_treemap(power_bloc_data, humans_list, bloc_totals, save_data, args.output)

if __name__ == '__main__':
    main()