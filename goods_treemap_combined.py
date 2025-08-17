#!/usr/bin/env python3
"""
Victoria 3 Goods Production Combined Treemaps
Creates individual treemaps for each good and combines them into category images
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
        print(f"Warning: {humans_file} not found. Will report on all countries.")
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

def extract_goods_production(json_file):
    """Extract actual goods production data from Victoria 3 save using output_goods"""
    
    print(f"Loading save file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get the game date
    game_date = data.get('date', 'Unknown')
    
    # Get country tags for each numeric ID
    country_tags = {}
    if 'country_manager' in data and 'database' in data['country_manager']:
        for country_id, country_info in data['country_manager']['database'].items():
            if isinstance(country_info, dict) and 'definition' in country_info:
                country_tags[country_id] = country_info['definition']
    
    # Get states to map to countries
    state_to_country = {}
    if 'states' in data and 'database' in data['states']:
        for state_id, state_info in data['states']['database'].items():
            if isinstance(state_info, dict) and 'country' in state_info:
                state_to_country[state_id] = state_info['country']
                state_to_country[int(state_id)] = state_info['country']
    
    # Calculate goods production by country and good type using actual output_goods
    goods_production = defaultdict(lambda: defaultdict(float))
    
    if 'building_manager' in data and 'database' in data['building_manager']:
        buildings = data['building_manager']['database']
        
        for building_id, building_info in buildings.items():
            if not isinstance(building_info, dict):
                continue
            
            state_id = building_info.get('state')
            if state_id not in state_to_country:
                continue
            
            country_id = state_to_country[state_id]
            country_tag = country_tags.get(str(country_id), str(country_id))
            
            # Get actual production from output_goods
            output_goods = building_info.get('output_goods', {})
            if isinstance(output_goods, dict) and 'goods' in output_goods:
                goods = output_goods['goods']
                for good_id, good_data in goods.items():
                    if isinstance(good_data, dict) and 'value' in good_data:
                        good_name = GOODS_ID_TO_NAME.get(good_id, f'unknown_{good_id}')
                        production_value = good_data['value']
                        goods_production[good_name][country_tag] += production_value
    
    return {
        'date': game_date,
        'production': goods_production
    }

def load_icon(good_name):
    """Load icon for a good if it exists"""
    icon_path = Path(f"icons/40px-Goods_{good_name}.png")
    if icon_path.exists():
        return Image.open(icon_path)
    return None

def create_good_treemap(ax, good_name, country_production):
    """Create a treemap for a single good in the given axes"""
    
    # Sort countries by production
    sorted_countries = sorted(country_production.items(), key=lambda x: x[1], reverse=True)
    
    # Prepare data
    labels = []
    sizes = []
    colors = []
    
    for country, value in sorted_countries:
        # Skip very small values to avoid division by zero
        if value < 1:
            continue
        if value >= 1000:
            label = f"{country}\n{value/1000:.1f}K"
        else:
            label = f"{country}\n{value:.0f}"
        labels.append(label)
        sizes.append(value)
        colors.append(COUNTRY_COLORS.get(country, '#808080'))
    
    # Clear the axes
    ax.clear()
    
    if sizes:  # Only plot if there's data
        # Create treemap with better text visibility
        squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.85,
                      text_kwargs={'fontsize': 10, 'weight': 'bold', 'color': 'white'},
                      ax=ax, pad=True, bar_kwargs={'linewidth': 1.5, 'edgecolor': 'white'})
    
    # Add title with icon
    title = good_name.replace('_', ' ').title()
    
    # Try to load and add icon
    icon = load_icon(good_name)
    if icon:
        # Create a box for title with icon
        # Add icon to the left of the title text
        imagebox = OffsetImage(icon, zoom=0.35)
        ab = AnnotationBbox(imagebox, (0.15, 1.02), xycoords='axes fraction',
                          frameon=False, box_alignment=(0.5, 0.5))
        ax.add_artist(ab)
        # Adjust title position to make room for icon
        ax.set_title(title, fontsize=12, fontweight='bold', pad=8, loc='center')
    else:
        ax.set_title(title, fontsize=12, fontweight='bold', pad=8)
    
    ax.axis('off')

def create_category_combined_treemap(category_name, goods_list, production_data, humans_list):
    """Create a combined image with individual treemaps for each good in the category"""
    
    # Filter goods that have production
    goods_with_production = []
    for good in goods_list:
        if good in production_data:
            good_production = production_data[good]
            # Filter by humans
            filtered = {k: v for k, v in good_production.items() if k in humans_list}
            if filtered:
                goods_with_production.append((good, filtered))
    
    if not goods_with_production:
        return None
    
    # Calculate grid dimensions - more landscape friendly
    n_goods = len(goods_with_production)
    
    # Use more columns for landscape layout
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
    
    # Create figure with landscape proportions
    fig = plt.figure(figsize=(5 * n_cols, 4 * n_rows))
    fig.suptitle(f'{category_name} Production Treemaps', fontsize=18, fontweight='bold', y=1.02)
    
    # Create GridSpec with spacing
    gs = gridspec.GridSpec(n_rows, n_cols, figure=fig, 
                          hspace=0.3, wspace=0.2,
                          left=0.05, right=0.95, top=0.94, bottom=0.02)
    
    # Create individual treemap for each good
    for idx, (good_name, country_production) in enumerate(goods_with_production):
        row = idx // n_cols
        col = idx % n_cols
        ax = fig.add_subplot(gs[row, col])
        
        create_good_treemap(ax, good_name, country_production)
    
    # Hide any empty subplots
    for idx in range(n_goods, n_rows * n_cols):
        row = idx // n_cols
        col = idx % n_cols
        ax = fig.add_subplot(gs[row, col])
        ax.axis('off')
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Victoria 3 goods production combined treemap visualizations')
    parser.add_argument('save_file', nargs='?', help='Path to extracted JSON save file')
    parser.add_argument('-o', '--output-prefix', default='goods_treemap_combined', 
                       help='Output file prefix (default: goods_treemap_combined)')
    
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
    
    # Load humans list
    humans_list = load_humans_list()
    if not humans_list:
        print("Error: No human countries found in humans.txt")
        sys.exit(1)
    
    # Extract data
    goods_data = extract_goods_production(json_file)
    production = goods_data['production']
    
    print(f"\nGenerating combined treemaps for goods production (Date: {goods_data['date']})")
    print("=" * 60)
    
    # Generate combined treemap for each category
    for category_name, goods_list in GOODS_CATEGORIES.items():
        print(f"\nProcessing {category_name}...")
        
        fig = create_category_combined_treemap(category_name, goods_list, production, humans_list)
        
        if fig:
            # Save as PNG with higher resolution
            filename = f"{args.output_prefix}_{category_name.lower().replace(' ', '_')}.png"
            fig.savefig(filename, dpi=200, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            print(f"  Saved: {filename}")
        else:
            print(f"  No production data for {category_name}")
    
    print("\n✅ Combined treemap generation complete!")
    print("\nGenerated files:")
    print("  • goods_treemap_combined_staple_goods.png")
    print("  • goods_treemap_combined_luxury_goods.png")
    print("  • goods_treemap_combined_industrial_goods.png")
    print("  • goods_treemap_combined_military_goods.png")
    print("\nEach image contains individual treemaps for all goods in that category.")

if __name__ == "__main__":
    main()