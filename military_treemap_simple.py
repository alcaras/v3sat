#!/usr/bin/env venv/bin/python
"""
Victoria 3 Military Power Treemap Generator using squarify (like goods treemaps)

Creates simple, flat treemaps for military power visualization.
"""

import json
import argparse
import os
from pathlib import Path
import matplotlib.pyplot as plt
import squarify
from collections import defaultdict

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

# Unit stats (offense + defense average)
UNIT_AVG_STATS = {
    # Army units
    'combat_unit_type_irregular_infantry': ('army', 10),
    'combat_unit_type_line_infantry': ('army', 22.5),
    'combat_unit_type_skirmish_infantry': ('army', 30),
    'combat_unit_type_trench_infantry': ('army', 35),
    'combat_unit_type_squad_infantry': ('army', 45),
    'combat_unit_type_mechanized_infantry': ('army', 55),
    'combat_unit_type_cannon_artillery': ('army', 20),
    'combat_unit_type_mobile_artillery': ('army', 22.5),
    'combat_unit_type_shrapnel_artillery': ('army', 35),
    'combat_unit_type_siege_artillery': ('army', 42.5),
    'combat_unit_type_heavy_tank': ('army', 52.5),
    'combat_unit_type_hussars': ('army', 12.5),
    'combat_unit_type_dragoons': ('army', 22.5),
    'combat_unit_type_cuirassiers': ('army', 22.5),
    'combat_unit_type_lancers': ('army', 25),
    'combat_unit_type_light_tanks': ('army', 45),
    # Navy units
    'combat_unit_type_frigate': ('navy', 12.5),
    'combat_unit_type_monitor': ('navy', 25),
    'combat_unit_type_destroyer': ('navy', 35),
    'combat_unit_type_torpedo_boat': ('navy', 35),
    'combat_unit_type_scout_cruiser': ('navy', 50),
    'combat_unit_type_man_o_war': ('navy', 25),
    'combat_unit_type_ironclad': ('navy', 50),
    'combat_unit_type_dreadnought': ('navy', 80),
    'combat_unit_type_battleship': ('navy', 100),
    'combat_unit_type_submarine': ('navy', 40),
    'combat_unit_type_carrier': ('navy', 90),
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

def calculate_military_scores(save_data):
    """Calculate military scores from save data."""
    countries = save_data.get('country_manager', {}).get('database', {})
    formations_db = save_data.get('military_formation_manager', {}).get('database', {})
    units_db = save_data.get('new_combat_unit_manager', {}).get('database', {})
    
    military_scores = {}
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        army_score = 0
        navy_score = 0
        
        # Find all formations for this country
        for fid, formation in formations_db.items():
            if isinstance(formation, dict) and formation.get('country') == int(country_id):
                # Count units in this formation
                unit_counts = defaultdict(int)
                
                for uid, unit in units_db.items():
                    if isinstance(unit, dict) and unit.get('formation') == int(fid):
                        unit_type = unit.get('type')
                        if unit_type and unit_type in UNIT_AVG_STATS:
                            unit_counts[unit_type] += 1
                
                # Calculate score for this formation
                for unit_type, count in unit_counts.items():
                    branch, avg_stat = UNIT_AVG_STATS[unit_type]
                    if branch == 'army':
                        army_score += count * avg_stat
                    else:
                        navy_score += count * avg_stat
        
        if army_score > 0 or navy_score > 0:
            military_scores[int(country_id)] = {
                'army': army_score,
                'navy': navy_score,
                'total': army_score + navy_score
            }
    
    return military_scores

def get_subject_relationships(save_data):
    """Extract subject relationships from pacts."""
    pacts = save_data.get('pacts', {}).get('database', {})
    direct_subjects = {}
    
    subject_types = ['dominion', 'puppet', 'protectorate', 'colony', 'personal_union', 'chartered_company']
    
    for pact_id, pact in pacts.items():
        if not isinstance(pact, dict):
            continue
        
        action = pact.get('action', '')
        if action not in subject_types:
            continue
        
        targets = pact.get('targets', {})
        first_country = targets.get('first')
        second_country = targets.get('second')
        
        if first_country and second_country:
            overlord = int(first_country)
            subject = int(second_country)
            
            if overlord not in direct_subjects:
                direct_subjects[overlord] = []
            direct_subjects[overlord].append(subject)
    
    return direct_subjects

def create_military_treemap(save_data, metric='total', min_score=1000, output_file=None):
    """Create a flat treemap for military power using squarify (like goods treemaps)."""
    countries = save_data.get('country_manager', {}).get('database', {})
    
    # Load human-controlled countries
    human_countries = set(load_humans_list())
    
    # Get military scores
    military_scores = calculate_military_scores(save_data)
    
    # Get subject relationships
    subject_relationships = get_subject_relationships(save_data)
    
    # Collect all countries with their scores
    all_countries = []
    
    for country_id, scores in military_scores.items():
        country_tag = get_country_tag(countries, country_id)
        country_score = scores.get(metric, 0)
        is_human = country_tag in human_countries
        
        if country_score > 0:
            all_countries.append((country_tag, country_score, is_human, country_id))
    
    # Sort by score
    all_countries.sort(key=lambda x: x[1], reverse=True)
    
    # Prepare data for treemap (similar to goods treemap logic)
    labels = []
    sizes = []
    colors = []
    
    # Dynamic threshold like goods treemap
    total_military = sum(x[1] for x in all_countries)
    base_min_value = min_score
    threshold = max(base_min_value, total_military * 0.02)  # 2% threshold
    max_countries_to_show = 15  # Maximum individual countries to show
    
    countries_shown = 0
    other_score = 0
    other_count = 0
    
    for country_tag, country_score, is_human, country_id in all_countries:
        # Show country if it's above threshold AND we haven't hit the limit
        if country_score >= threshold and countries_shown < max_countries_to_show:
            if country_score >= 1000:
                label = f"{country_tag}\n{country_score/1000:.1f}K"
            else:
                label = f"{country_tag}\n{country_score:.0f}"
            
            labels.append(label)
            sizes.append(country_score)
            
            # Determine if this is a subject and get color
            is_subject = False
            overlord_color = None
            for overlord_id, subjects in subject_relationships.items():
                if country_id in subjects:
                    is_subject = True
                    overlord_tag = get_country_tag(countries, overlord_id)
                    if overlord_tag in human_countries:
                        overlord_color = COUNTRY_COLORS.get(overlord_tag)
                    break
            
            # Color logic (same as goods treemap)
            if is_subject and overlord_color:
                # Fade the overlord's color for subjects
                r = int(overlord_color[1:3], 16)
                g = int(overlord_color[3:5], 16)
                b = int(overlord_color[5:7], 16)
                r = int(r * 0.6 + 128 * 0.4)
                g = int(g * 0.6 + 128 * 0.4)
                b = int(b * 0.6 + 128 * 0.4)
                color = f'#{r:02x}{g:02x}{b:02x}'
            elif is_human:
                color = COUNTRY_COLORS.get(country_tag, '#808080')
            else:
                color = '#707070' if country_score > threshold * 2 else '#606060'
            
            colors.append(color)
            countries_shown += 1
        else:
            # Add to "Other" category
            other_score += country_score
            other_count += 1
    
    # Add "Other" category if there are countries not shown
    if other_count > 0 and other_score > 10:
        if other_score >= 1000:
            label = f"Other ({other_count})\n{other_score/1000:.1f}K"
        else:
            label = f"Other ({other_count})\n{other_score:.0f}"
        labels.append(label)
        sizes.append(other_score)
        colors.append('#404040')
    
    # Create the treemap
    fig, ax = plt.subplots(figsize=(16, 10))
    
    if sizes:  # Only plot if there's data
        # Create treemap with larger font for readability
        squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.85,
                      text_kwargs={'fontsize': 12, 'weight': 'bold', 'color': 'white'},
                      ax=ax, pad=True, bar_kwargs={'linewidth': 1.5, 'edgecolor': 'white'})
    
    # Add title
    metric_title = {
        'army': 'Victoria 3 Army Power by Country',
        'navy': 'Victoria 3 Navy Power by Country', 
        'total': 'Victoria 3 Military Power by Country'
    }[metric]
    
    ax.set_title(metric_title, fontsize=18, fontweight='bold', pad=20)
    ax.axis('off')
    
    # Save outputs
    if output_file:
        # Save as PNG
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"Saved treemap to {output_file}")
        
        # Also save HTML version with same base name
        html_file = output_file.replace('.png', '.html')
        # For HTML, we'd need to convert to plotly, but for now just save the matplotlib version
        plt.savefig(html_file.replace('.html', '_matplotlib.png'), dpi=150, bbox_inches='tight', facecolor='white')
    else:
        plt.show()
    
    plt.close()
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 military power treemaps')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-m', '--metric', choices=['army', 'navy', 'total'], default='total',
                       help='Military metric to visualize (default: total)')
    parser.add_argument('-o', '--output', help='Output file path (.png)')
    parser.add_argument('--min-score', type=float, default=1000,
                       help='Minimum score to display individually (default: 1000)')
    
    args = parser.parse_args()
    
    # Find save file if not specified
    if not args.save_file:
        extracted_dir = Path("extracted-saves")
        json_files = list(extracted_dir.glob("*_extracted.json"))
        if not json_files:
            print("No extracted save files found")
            return
        args.save_file = str(max(json_files, key=lambda x: x.stat().st_mtime))
        print(f"Using latest save: {args.save_file}")
    
    # Load save data
    print(f"Loading save data from {args.save_file}...")
    save_data = load_save_data(args.save_file)
    
    # Get game date
    game_date = save_data.get('meta_data', {}).get('game_date', 'Unknown')
    print(f"Game date: {game_date}")
    
    # Create treemap
    print(f"Creating {args.metric} power treemap...")
    create_military_treemap(save_data, metric=args.metric, 
                           min_score=args.min_score, output_file=args.output)
    
    print("Done!")

if __name__ == '__main__':
    main()