#!/usr/bin/env venv/bin/python
"""
Victoria 3 Goods Production Power Bloc Treemaps

Creates hierarchical treemaps for goods production organized by power blocs.
Shows all nations (not just humans) with proper subject coloring.
"""

import json
import sys
from pathlib import Path
import argparse
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
import matplotlib.gridspec as gridspec
import squarify
import numpy as np
from PIL import Image

# Goods categories
GOODS_CATEGORIES = {
    'Staple Goods': [
        'clothes', 'fabric', 'fish', 'furniture', 'grain', 
        'groceries', 'merchant_marine', 'paper', 'wood'
    ],
    'Luxury Goods': [
        'automobiles', 'coffee', 'fine_art', 'fruit', 'gold',
        'liquor', 'luxury_clothes', 'luxury_furniture', 'meat',
        'opium', 'porcelain', 'radios', 'sugar', 'tea',
        'telephones', 'tobacco', 'wine'
    ],
    'Industrial Goods': [
        'clippers', 'coal', 'dye', 'engines', 'explosives',
        'fertilizer', 'glass', 'hardwood', 'iron', 'lead',
        'oil', 'rubber', 'silk', 'steamers', 'steel',
        'sulfur', 'tools'
    ],
    'Military Goods': [
        'aeroplanes', 'ammunition', 'artillery', 'ironclads',
        'man_o_wars', 'small_arms', 'tanks'
    ]
}

# Map goods IDs to names
GOODS_ID_TO_NAME = {
    '0': 'ammunition',
    '1': 'small_arms', 
    '2': 'artillery',
    '3': 'tanks',
    '4': 'aeroplanes',
    '5': 'man_o_wars',
    '6': 'ironclads',
    '7': 'grain',
    '8': 'fish',
    '9': 'fabric',
    '10': 'wood',
    '11': 'groceries',
    '12': 'clothes',
    '13': 'furniture',
    '14': 'paper',
    '15': 'services',
    '16': 'transportation',
    '17': 'electricity',
    '18': 'merchant_marine',
    '19': 'clippers',
    '20': 'steamers',
    '21': 'silk',
    '22': 'dye',
    '23': 'sulfur',
    '24': 'coal',
    '25': 'iron',
    '26': 'lead',
    '27': 'hardwood',
    '28': 'rubber',
    '29': 'oil',
    '30': 'engines',
    '31': 'steel',
    '32': 'glass',
    '33': 'fertilizer',
    '34': 'tools',
    '35': 'explosives',
    '36': 'porcelain',
    '37': 'meat',
    '38': 'fruit',
    '39': 'liquor',
    '40': 'wine',
    '41': 'coffee',
    '42': 'tea',
    '43': 'sugar',
    '44': 'tobacco',
    '45': 'opium',
    '46': 'automobiles',
    '47': 'telephones',
    '48': 'radios',
    '49': 'gold',
    '50': 'fine_art',
    '51': 'luxury_clothes',
    '52': 'luxury_furniture',
}

# Victoria 3 country colors - consistent with other treemaps
COUNTRY_COLORS = {
    'GBR': '#e6454e',  # British red
    'USA': '#425ec1',  # American blue  
    'FRA': '#1432d2',  # French blue
    'BIC': '#bc713d',  # Colonial brown
    'CHI': '#fcb93d',  # Imperial yellow
    'ITA': '#7dab54',  # Italian green
    'SPA': '#d48806',  # Spanish orange
    'POR': '#c4561e',  # Portuguese orange-red
    'TUR': '#a3542b',  # Ottoman brown
    'RUS': '#4a7c2a',  # Russian green
    'JAP': '#cc3333',  # Japanese red
    'YUG': '#8b4a8b',  # Yugoslav purple
}

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

def get_latest_save():
    """Get the latest extracted save file"""
    extracted_dir = Path("extracted-saves")
    if not extracted_dir.exists():
        return None
    
    json_files = list(extracted_dir.glob("*_extracted.json"))
    if not json_files:
        return None
    
    latest = max(json_files, key=lambda f: f.stat().st_mtime)
    return str(latest)

def get_subject_relationships(save_data):
    """Extract subject relationships from pacts."""
    pacts = save_data.get('pacts', {}).get('database', {})
    direct_subjects = {}
    all_subjects = {}
    
    subject_types = ['dominion', 'puppet', 'protectorate', 'colony', 'personal_union', 'chartered_company']
    
    # First pass: get direct relationships
    for pact_id, pact in pacts.items():
        if not isinstance(pact, dict):
            continue
        
        action = pact.get('action', '')
        if action not in subject_types:
            continue
        
        # Correct field structure - targets contains first and second directly
        targets = pact.get('targets', {})
        first_country = targets.get('first')
        second_country = targets.get('second')
        
        if first_country and second_country:
            overlord = int(first_country)
            subject = int(second_country)
            
            if overlord not in direct_subjects:
                direct_subjects[overlord] = []
            direct_subjects[overlord].append(subject)
    
    # Second pass: build transitive relationships
    def get_all_subjects(overlord, visited=None):
        if visited is None:
            visited = set()
        
        if overlord in visited:
            return []
        
        visited.add(overlord)
        subjects = []
        
        if overlord in direct_subjects:
            for subject in direct_subjects[overlord]:
                subjects.append(subject)
                subjects.extend(get_all_subjects(subject, visited))
        
        return subjects
    
    for overlord in direct_subjects:
        all_subjects[overlord] = get_all_subjects(overlord)
    
    return all_subjects

def get_power_bloc_data(save_data):
    """Extract power bloc membership and names."""
    power_blocs = save_data.get('power_bloc_manager', {}).get('database', {})
    countries = save_data.get('country_manager', {}).get('database', {})
    
    bloc_data = {}
    country_to_bloc = {}
    
    # Get active power blocs
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
        
        # Get leader
        leader = bloc.get('leader')
        
        bloc_data[int(bloc_id)] = {
            'name': bloc_name,
            'leader': leader,
            'members': []
        }
    
    # Map countries to blocs
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        bloc_id = country.get('power_bloc_as_core')
        if bloc_id and int(bloc_id) in bloc_data:
            bloc_data[int(bloc_id)]['members'].append(int(country_id))
            country_to_bloc[int(country_id)] = int(bloc_id)
    
    return bloc_data, country_to_bloc

def extract_goods_production_by_country(save_data):
    """Extract actual goods production data from Victoria 3 save using output_goods"""
    
    # Get country tags for each numeric ID
    country_tags = {}
    if 'country_manager' in save_data and 'database' in save_data['country_manager']:
        for country_id, country_info in save_data['country_manager']['database'].items():
            if isinstance(country_info, dict) and 'definition' in country_info:
                country_tags[int(country_id)] = country_info['definition']
    
    # Get states to map to countries
    state_to_country = {}
    if 'states' in save_data and 'database' in save_data['states']:
        for state_id, state_info in save_data['states']['database'].items():
            if isinstance(state_info, dict) and 'country' in state_info:
                state_to_country[state_id] = state_info['country']
                state_to_country[int(state_id)] = state_info['country']
    
    # Calculate goods production by country ID and good type using actual output_goods
    goods_production = defaultdict(lambda: defaultdict(float))
    
    if 'building_manager' in save_data and 'database' in save_data['building_manager']:
        buildings = save_data['building_manager']['database']
        
        for building_id, building_info in buildings.items():
            if not isinstance(building_info, dict):
                continue
            
            state_id = building_info.get('state')
            if state_id not in state_to_country:
                continue
            
            country_id = state_to_country[state_id]
            
            # Get actual production from output_goods
            output_goods = building_info.get('output_goods', {})
            if isinstance(output_goods, dict) and 'goods' in output_goods:
                goods = output_goods['goods']
                for good_id, good_data in goods.items():
                    if isinstance(good_data, dict) and 'value' in good_data:
                        good_name = GOODS_ID_TO_NAME.get(good_id, f'unknown_{good_id}')
                        production_value = good_data['value']
                        goods_production[good_name][int(country_id)] += production_value
    
    return goods_production, country_tags

def load_icon(good_name):
    """Load icon for a good if it exists"""
    icon_path = Path(f"icons/40px-Goods_{good_name}.png")
    if icon_path.exists():
        return Image.open(icon_path)
    return None

def create_good_powerbloc_treemap(ax, good_name, country_production, bloc_data, country_to_bloc, 
                                  subject_relationships, country_tags, human_countries):
    """Create a power bloc treemap for a single good in the given axes"""
    
    # Calculate total production and determine dynamic threshold
    total_production = sum(country_production.values())
    
    # More aggressive threshold: 4% of total production or 200, whichever is larger
    # Also set a maximum number of countries to display
    base_min_value = 200
    threshold = max(base_min_value, total_production * 0.04)
    max_countries_to_show = 10  # Maximum individual countries to show
    
    # Collect all countries with their production
    all_countries = []
    
    for country_id, production in country_production.items():
        if production > 0:
            country_tag = country_tags.get(country_id, f'ID_{country_id}')
            is_human = country_tag in human_countries
            all_countries.append((country_tag, production, is_human, country_id))
    
    # Sort by production
    all_countries.sort(key=lambda x: x[1], reverse=True)
    
    # Prepare data for treemap
    labels = []
    sizes = []
    colors = []
    
    # Take top countries up to max limit
    countries_shown = 0
    other_production = 0
    other_count = 0
    
    for country_tag, production, is_human, country_id in all_countries:
        # Show country if it's above threshold AND we haven't hit the limit
        # Don't force show human countries if they're too small - they'll go in "Other"
        if production >= threshold and countries_shown < max_countries_to_show:
            if production >= 1000:
                label = f"{country_tag}\n{production/1000:.1f}K"
            else:
                label = f"{country_tag}\n{production:.0f}"
            
            labels.append(label)
            sizes.append(production)
            
            # Determine if this is a subject
            is_subject = False
            overlord_color = None
            for overlord_id, subjects in subject_relationships.items():
                if country_id in subjects:
                    is_subject = True
                    overlord_tag = country_tags.get(overlord_id)
                    if overlord_tag in human_countries:
                        overlord_color = COUNTRY_COLORS.get(overlord_tag)
                    break
            
            # Color logic
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
                color = '#707070' if production > threshold * 2 else '#606060'
            
            colors.append(color)
            countries_shown += 1
        else:
            # Add to "Other" category
            other_production += production
            other_count += 1
    
    # Add "Other" category if there are countries not shown
    if other_count > 0 and other_production > 10:
        if other_production >= 1000:
            label = f"Other ({other_count})\n{other_production/1000:.1f}K"
        else:
            label = f"Other ({other_count})\n{other_production:.0f}"
        labels.append(label)
        sizes.append(other_production)
        colors.append('#404040')
    
    # Clear the axes
    ax.clear()
    
    if sizes:  # Only plot if there's data
        # Create treemap with larger font for readability
        squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.85,
                      text_kwargs={'fontsize': 10, 'weight': 'bold', 'color': 'white'},
                      ax=ax, pad=True, bar_kwargs={'linewidth': 1.5, 'edgecolor': 'white'})
    
    # Add title with icon
    title = good_name.replace('_', ' ').title()
    
    # Try to load and add icon
    icon = load_icon(good_name)
    if icon:
        imagebox = OffsetImage(icon, zoom=0.3)
        ab = AnnotationBbox(imagebox, (0.12, 1.02), xycoords='axes fraction',
                          frameon=False, box_alignment=(0.5, 0.5))
        ax.add_artist(ab)
        ax.set_title(title, fontsize=11, fontweight='bold', pad=6, loc='center')
    else:
        ax.set_title(title, fontsize=11, fontweight='bold', pad=6)
    
    ax.axis('off')

def create_category_powerbloc_treemap(category_name, goods_list, goods_production, 
                                      bloc_data, country_to_bloc, subject_relationships,
                                      country_tags, human_countries):
    """Create a combined image with power bloc treemaps for each good in the category"""
    
    # Filter goods that have production
    goods_with_production = []
    for good in goods_list:
        if good in goods_production:
            good_production = goods_production[good]
            # Check if there's any significant production
            total_production = sum(good_production.values())
            if total_production > 0:
                goods_with_production.append((good, good_production))
    
    if not goods_with_production:
        return None
    
    # Calculate grid dimensions - landscape friendly
    n_goods = len(goods_with_production)
    
    if n_goods <= 4:
        n_cols = n_goods
        n_rows = 1
    elif n_goods <= 8:
        n_cols = 4
        n_rows = 2
    elif n_goods <= 12:
        n_cols = 4
        n_rows = 3
    elif n_goods <= 20:
        n_cols = 5
        n_rows = 4
    else:
        n_cols = 6
        n_rows = (n_goods + n_cols - 1) // n_cols
    
    # Create figure
    fig = plt.figure(figsize=(4.5 * n_cols, 4 * n_rows))
    fig.suptitle(f'{category_name} Production Treemaps', fontsize=16, fontweight='bold', y=1.01)
    
    # Create GridSpec
    gs = gridspec.GridSpec(n_rows, n_cols, figure=fig, 
                          hspace=0.25, wspace=0.15,
                          left=0.04, right=0.96, top=0.94, bottom=0.02)
    
    # Create individual treemap for each good
    for idx, (good_name, country_production) in enumerate(goods_with_production):
        row = idx // n_cols
        col = idx % n_cols
        ax = fig.add_subplot(gs[row, col])
        
        create_good_powerbloc_treemap(ax, good_name, country_production, 
                                     bloc_data, country_to_bloc, subject_relationships,
                                     country_tags, human_countries)
    
    # Hide any empty subplots
    for idx in range(n_goods, n_rows * n_cols):
        row = idx // n_cols
        col = idx % n_cols
        ax = fig.add_subplot(gs[row, col])
        ax.axis('off')
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 goods production power bloc treemap visualizations')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output-prefix', default='goods_treemap_powerbloc', 
                       help='Output file prefix (default: goods_treemap_powerbloc)')
    
    args = parser.parse_args()
    
    # Determine which save file to use
    if args.save_file:
        json_file = args.save_file
    else:
        json_file = get_latest_save()
        if not json_file:
            print("Error: No extracted save files found in extracted-saves/")
            print("Please run extract_save.py first to extract a save file.")
            sys.exit(1)
    
    # Check if file exists
    if not Path(json_file).exists():
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    # Load save data
    print(f"Loading save file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        save_data = json.load(f)
    
    # Get game date
    game_date = save_data.get('date', 'Unknown')
    
    # Load humans list
    human_countries = set(load_humans_list())
    
    # Extract all necessary data
    print("Extracting goods production data...")
    goods_production, country_tags = extract_goods_production_by_country(save_data)
    
    print("Extracting power bloc data...")
    bloc_data, country_to_bloc = get_power_bloc_data(save_data)
    
    print("Extracting subject relationships...")
    subject_relationships = get_subject_relationships(save_data)
    
    print(f"\nGenerating global production treemaps (Date: {game_date})")
    print("=" * 60)
    
    # Generate combined treemap for each category
    for category_name, goods_list in GOODS_CATEGORIES.items():
        print(f"\nProcessing {category_name}...")
        
        fig = create_category_powerbloc_treemap(
            category_name, goods_list, goods_production,
            bloc_data, country_to_bloc, subject_relationships,
            country_tags, human_countries
        )
        
        if fig:
            # Save as PNG
            filename = f"{args.output_prefix}_{category_name.lower().replace(' ', '_')}.png"
            fig.savefig(filename, dpi=200, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            print(f"  Saved: {filename}")
        else:
            print(f"  No production data for {category_name}")
    
    print("\n✅ Global production treemap generation complete!")
    print("\nGenerated files:")
    print("  • goods_treemap_powerbloc_staple_goods.png")
    print("  • goods_treemap_powerbloc_luxury_goods.png")
    print("  • goods_treemap_powerbloc_industrial_goods.png")
    print("  • goods_treemap_powerbloc_military_goods.png")
    print("\nEach image shows global production with all major producers.")

if __name__ == "__main__":
    main()