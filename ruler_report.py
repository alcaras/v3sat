#!/usr/bin/env python3
"""
Victoria 3 Ruler Report Tool
Shows ruler information for each nation including name, interest group, traits, and age
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

def calculate_age(birth_date, current_date):
    """Calculate age from birth date and current date"""
    # Victoria 3 dates are in format YYYY.M.D
    birth_parts = birth_date.split('.')
    current_parts = current_date.split('.')
    
    birth_year = int(birth_parts[0])
    current_year = int(current_parts[0])
    
    # Simple year difference
    return current_year - birth_year

def load_save_file(filepath):
    """Load and parse Victoria 3 save file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_latest_save():
    """Get the most recent extracted save file"""
    extracted_dir = Path('extracted-saves')
    if not extracted_dir.exists():
        raise FileNotFoundError("No extracted-saves directory found")
    
    json_files = list(extracted_dir.glob('*_extracted.json'))
    if not json_files:
        raise FileNotFoundError("No extracted save files found")
    
    return str(max(json_files, key=lambda f: f.stat().st_mtime))

def load_humans():
    """Load list of human-controlled countries"""
    humans_file = Path('humans.txt')
    if not humans_file.exists():
        return []
    
    with open(humans_file, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_interest_group_name(ig_id, data):
    """Get interest group name from ID"""
    # Map of interest group definitions to names
    ig_names = {
        'ig_devout': 'Devout',
        'ig_landowners': 'Landowners',
        'ig_armed_forces': 'Armed Forces',
        'ig_petty_bourgeoisie': 'Petty Bourgeoisie',
        'ig_industrialists': 'Industrialists',
        'ig_intelligentsia': 'Intelligentsia',
        'ig_trade_unions': 'Trade Unions',
        'ig_rural_folk': 'Rural Folk'
    }
    
    # Try to find the interest group in the database
    if 'interest_groups' in data and 'database' in data['interest_groups']:
        ig_db = data['interest_groups']['database']
        ig_info = ig_db.get(str(ig_id))
        if ig_info and 'definition' in ig_info:
            definition = ig_info['definition']
            return ig_names.get(definition, definition.replace('ig_', '').replace('_', ' ').title())
    
    # Fallback to the ID itself
    return f"IG {ig_id}"

def get_culture_name(culture_id, data):
    """Get culture name from ID"""
    # Extended map of culture IDs to names (from Victoria 3 game data)
    culture_names = {
        # European
        1: 'British',
        2: 'Irish',
        3: 'Anglo Canadian',
        4: 'Scottish',
        5: 'Welsh',
        6: 'Yankee',
        7: 'Dixie',
        8: 'Texan',
        9: 'Afro American',
        10: 'Australian',
        11: 'Boer',
        12: 'Dutch',
        13: 'Flemish',
        14: 'Wallonian',
        31: 'North German',
        32: 'South German',
        33: 'Swiss',
        36: 'English',
        40: 'South Italian',  # Fixed from Afro-Antillean
        43: 'Spanish',
        45: 'Portuguese',
        46: 'French',
        47: 'Breton',
        48: 'Occitan',
        49: 'Corsican',
        50: 'Serbian',  # Fixed from Maltese
        56: 'North Italian',
        57: 'South Italian',
        58: 'Central Italian',
        60: 'Spanish',
        61: 'Russian',  # Fixed from Catalan
        62: 'Basque',
        63: 'Galician',
        64: 'Portuguese',
        65: 'Brazilian',
        66: 'Platinean',
        67: 'Greek',
        68: 'Turkish',
        69: 'Albanian',
        70: 'Bulgarian',
        71: 'Turkish',  # Fixed from Romanian
        72: 'Serbian',
        73: 'Croatian',
        74: 'Slovene',
        75: 'Bosniak',
        76: 'Polish',
        77: 'Czech',
        78: 'Slovak',
        79: 'Hungarian',
        80: 'Pashtun',
        81: 'Tajik',
        82: 'Kazakh',
        83: 'Uzbek',
        84: 'Turkmen',
        85: 'Kyrgyz',
        86: 'Russian',
        87: 'Ukrainian',
        88: 'Belarusian',
        89: 'Estonian',
        90: 'Latvian',
        91: 'Lithuanian',
        92: 'Finnish',
        93: 'Swedish',
        94: 'Norwegian',
        95: 'Danish',
        96: 'Icelandic',
        # Asian
        100: 'Han',
        101: 'Manchu',
        102: 'Mongol',
        103: 'Tibetan',
        104: 'Min',
        105: 'Hakka',
        106: 'Yue',
        107: 'Miao',
        108: 'Yi',
        109: 'Zhuang',
        110: 'Japanese',
        111: 'Korean',
        112: 'Vietnamese',
        113: 'Thai',
        114: 'Lao',
        115: 'Khmer',
        116: 'Malay',
        117: 'Javan',
        118: 'Filipino',
        119: 'Dayak',
        120: 'Moluccan',
        127: 'Japanese',  # Fixed from Manchu
        128: 'Manchu',
        # Indian
        130: 'Bengali',
        131: 'Bihari',
        132: 'Oriya',
        133: 'Assamese',
        134: 'Gujarati',
        135: 'Marathi',
        136: 'Punjabi',
        137: 'Kashmiri',
        138: 'Sindhi',
        139: 'Rajput',
        140: 'Hindi',
        141: 'Nepali',
        142: 'Sinhala',
        143: 'Tamil',
        144: 'Telugu',
        145: 'Kannada',
        146: 'Malayalam',
        # Middle Eastern
        150: 'Arab',
        151: 'Egyptian',
        152: 'Maghrebi',
        153: 'Berber',
        154: 'Bedouin',
        155: 'Persian',
        156: 'Kurdish',
        157: 'Armenian',
        158: 'Georgian',
        159: 'Azerbaijani',
        160: 'Baluchi',
        # African
        170: 'Amhara',
        171: 'Tigray',
        172: 'Oromo',
        173: 'Somali',
        174: 'Harari',
        175: 'Afar',
        176: 'Sidama',
        177: 'Swahili',
        178: 'Kikuyu',
        179: 'Luo',
        180: 'Maasai',
        181: 'Yankee',  # Fixed from Sukuma - USA culture
        182: 'Chagga',
        183: 'Nyamwezi',
        184: 'Hehe',
        185: 'Ganda',
        186: 'Rundi',
        187: 'Rwandan',
        188: 'Luba',
        189: 'Kongo',
        190: 'Ovimbundu',
        191: 'Umbundu',
        192: 'Bakongo',
        193: 'Yoruba',
        194: 'Igbo',
        195: 'Hausa',
        196: 'Fulani',
        197: 'Kanuri',
        198: 'Tuareg',
        199: 'Songhai',
        200: 'Bambara',
        201: 'Malinke',
        202: 'Soninke',
        203: 'Wolof',
        204: 'Serer',
        205: 'Fulbe',
        206: 'Mossi',
        207: 'Akan',
        208: 'Ewe',
        209: 'Fon',
        210: 'Edo',
        # Americas
        220: 'Mexican',
        221: 'Central American',
        222: 'Caribbean',
        223: 'North Andean',
        224: 'South Andean',
        225: 'Guarani',
        226: 'Amazonian',
        227: 'Patagonian',
        228: 'Arctic',
        229: 'Inuit',
        230: 'Native American',
        231: 'Cherokee',
        232: 'Iroquois',
        233: 'Sioux',
        234: 'Apache',
        235: 'Navajo',
        236: 'Pueblo',
        237: 'Cree',
        238: 'Maya',
        239: 'Nahua',
        240: 'Zapotec',
        241: 'Mixtec',
        242: 'Tarascan',
        243: 'Quechua',
        244: 'Aimara',
        245: 'Tupi',
        246: 'Mapuche'
    }
    
    return culture_names.get(culture_id, f'Culture {culture_id}')

def get_ruler_title(government_type, ruler_gender='male'):
    """Get ruler title based on government type"""
    title_map = {
        # Monarchies
        'gov_absolute_monarchy': 'King' if ruler_gender == 'male' else 'Queen',
        'gov_constitutional_monarchy': 'King' if ruler_gender == 'male' else 'Queen',
        'gov_parliamentary_monarchy': 'King' if ruler_gender == 'male' else 'Queen',
        'gov_hm_government': 'King' if ruler_gender == 'male' else 'Queen',
        'gov_theocratic_monarchy': 'King' if ruler_gender == 'male' else 'Queen',
        
        # Republics
        'gov_presidential_republic': 'President',
        'gov_presidential_democracy': 'President',
        'gov_parliamentary_republic': 'Prime Minister',
        'gov_parliamentary_democracy': 'Prime Minister',
        'gov_french_2nd_republic_presidential': 'President',
        
        # Dictatorships
        'gov_military_dictatorship': 'General',
        'gov_military_junta': 'General',
        'gov_fascist_state': 'Leader',
        'gov_corporate_state': 'Leader',
        
        # Socialist
        'gov_council_republic': 'Chairman',
        'gov_soviet_republic': 'Chairman',
        'gov_communist_state': 'Chairman',
        
        # Theocracies
        'gov_theocracy': 'Patriarch',
        'gov_papal_state': 'Pope',
        
        # Other
        'gov_oligarchy': 'President',
        'gov_technocracy': 'Director',
        'gov_landed_voting': 'President',
        'gov_wealth_voting': 'President',
        'gov_census_voting': 'President',
        'gov_universal_suffrage': 'President',
        'gov_anarchy': 'Speaker',
        'gov_single_party_state': 'Chairman',
        
        # Empires
        'gov_empire': 'Emperor' if ruler_gender == 'male' else 'Empress',
        'gov_celestial_empire': 'Emperor' if ruler_gender == 'male' else 'Empress',
        'gov_constitutional_empire': 'Emperor' if ruler_gender == 'male' else 'Empress',
        'gov_absolute_empire': 'Emperor' if ruler_gender == 'male' else 'Empress',
        
        # Specific monarchies
        'gov_constitutional_kingdom': 'King' if ruler_gender == 'male' else 'Queen',
        'gov_tsardom': 'Tsar' if ruler_gender == 'male' else 'Tsarina',
        'gov_sultanate': 'Sultan',
    }
    
    return title_map.get(government_type, 'Ruler')

def format_traits(traits):
    """Format traits list into a readable string"""
    if not traits:
        return "None"
    
    # Clean up trait names
    formatted = []
    for trait in traits:
        # Remove prefixes like 'basic_' and convert underscores to spaces
        clean_trait = trait.replace('basic_', '').replace('_', ' ').title()
        formatted.append(clean_trait)
    
    return ", ".join(formatted)

def generate_ruler_report(save_file, humans_only=True):
    """Generate ruler report from save file"""
    print(f"Loading save file: {save_file}")
    data = load_save_file(save_file)
    
    # Get current game date
    current_date = data.get('date', '1883.1.1')
    
    # Load human countries if filtering
    human_tags = load_humans() if humans_only else []
    
    # Get character database
    if 'character_manager' not in data or 'database' not in data['character_manager']:
        print("Error: No character database found in save file")
        return
    
    characters = data['character_manager']['database']
    
    # Get country manager
    if 'country_manager' not in data:
        print("Error: No country manager found in save file")
        return
    
    country_manager = data['country_manager']
    
    # Get country definitions and ruler mappings
    country_db = country_manager.get('database', {})
    country_rulers = country_manager.get('country_ruler', {})
    
    # Build report data
    report_data = []
    
    for country_id, country_info in country_db.items():
        if country_id == '16777216':  # Skip 'none' country
            continue
            
        # Check if it's a dictionary with country info
        if not isinstance(country_info, dict):
            continue
            
        # Get country tag
        tag = country_info.get('definition')
        if not tag:
            continue
            
        # Filter by human countries if requested
        if humans_only and human_tags and tag not in human_tags:
            continue
            
        # Get ruler ID
        ruler_id = country_info.get('ruler')
        if not ruler_id or ruler_id == 4294967295:  # Invalid ruler ID
            continue
            
        # Get ruler character
        ruler_char = characters.get(str(ruler_id))
        if not ruler_char:
            continue
            
        # Extract ruler information
        first_name = ruler_char.get('first_name', 'Unknown')
        last_name = ruler_char.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        
        # Get age
        birth_date = ruler_char.get('birth_date', '')
        age = calculate_age(birth_date, current_date) if birth_date else 'Unknown'
        
        # Get government type for title
        government_type = country_info.get('government', 'unknown')
        
        # Determine gender (simplified - could be enhanced with actual gender data)
        ruler_gender = 'female' if 'Isabel' in first_name or 'Victoria' in first_name else 'male'
        title = get_ruler_title(government_type, ruler_gender)
        
        # Get interest group by finding which IG the ruler leads
        ig_name = None
        if 'interest_groups' in data and 'database' in data['interest_groups']:
            ig_db = data['interest_groups']['database']
            
            # First, check if ruler leads an IG
            for ig_id, ig in ig_db.items():
                if isinstance(ig, dict) and ig.get('country') == int(country_id):
                    if ig.get('leader') == ruler_id:
                        ig_name = get_interest_group_name(ig_id, data)
                        break
            
            # If ruler doesn't lead an IG, find the most powerful IG in government
            if not ig_name:
                max_clout = 0
                for ig_id, ig in ig_db.items():
                    if isinstance(ig, dict) and ig.get('country') == int(country_id):
                        if ig.get('in_government', False):
                            clout = ig.get('clout', 0)
                            if clout > max_clout:
                                max_clout = clout
                                ig_name = get_interest_group_name(ig_id, data)
                
        if not ig_name:
            ig_name = 'None'
        
        # Get traits
        traits = ruler_char.get('traits', [])
        traits_str = format_traits(traits)
        
        # Get culture (optional, for context)
        culture_id = ruler_char.get('culture')
        culture_name = get_culture_name(culture_id, data) if culture_id else 'Unknown'
        
        report_data.append({
            'tag': tag,
            'title': title,
            'name': full_name,
            'age': age,
            'interest_group': ig_name,
            'traits': traits_str,
            'culture': culture_name
        })
    
    # Sort by country tag
    report_data.sort(key=lambda x: x['tag'])
    
    # Print report
    print("\n" + "="*80)
    print(f"Victoria 3 Ruler Report - {current_date}")
    print("="*80)
    
    if humans_only:
        print(f"Showing rulers for human-controlled nations only")
    else:
        print(f"Showing rulers for all nations")
    
    print("\n" + "-"*90)
    print(f"{'Country':<8} {'Title':<12} {'Ruler Name':<25} {'Age':<5} {'Interest Group':<15} {'Traits':<25}")
    print("-"*90)
    
    for ruler in report_data:
        # Truncate long fields for display
        title = ruler['title'][:11]
        name = ruler['name'][:24]
        ig = ruler['interest_group'][:14]
        traits = ruler['traits'][:24]
        
        print(f"{ruler['tag']:<8} {title:<12} {name:<25} {ruler['age']:<5} {ig:<15} {traits:<25}")
    
    print("-"*90)
    print(f"Total rulers shown: {len(report_data)}")
    
    # Create detailed report
    print("\n" + "="*80)
    print("Detailed Ruler Information")
    print("="*80)
    
    for ruler in report_data:
        print(f"\n{ruler['tag']} - {ruler['title']} {ruler['name']}")
        print(f"  Age: {ruler['age']}")
        print(f"  Interest Group: {ruler['interest_group']}")
        print(f"  Traits: {ruler['traits']}")
        print(f"  Culture: {ruler['culture']}")

def main():
    parser = argparse.ArgumentParser(description='Generate ruler report from Victoria 3 save files')
    parser.add_argument('save_file', nargs='?', help='Path to extracted save file (JSON)')
    parser.add_argument('--all', action='store_true', help='Show all countries (not just humans)')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Get save file
    if args.save_file:
        save_file = args.save_file
    else:
        try:
            save_file = get_latest_save()
            print(f"Using latest save file: {save_file}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return
    
    # Check if file exists
    if not Path(save_file).exists():
        print(f"Error: Save file not found: {save_file}")
        return
    
    # Generate report
    humans_only = not args.all
    
    if args.output:
        # Redirect output to file
        import sys
        original_stdout = sys.stdout
        with open(args.output, 'w') as f:
            sys.stdout = f
            generate_ruler_report(save_file, humans_only)
        sys.stdout = original_stdout
        print(f"Report saved to: {args.output}")
    else:
        generate_ruler_report(save_file, humans_only)

if __name__ == '__main__':
    main()