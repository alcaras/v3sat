#!/usr/bin/env python3
"""
Comprehensive Session Comparison Tool for Victoria 3

Compares all major metrics between two sessions including:
- GDP, Population, Construction
- Standard of Living, Literacy, Prestige, Infamy
- Law changes
- Power bloc changes
- Territory changes
- Goods production (tools, steel, etc.)
"""

import json
import os
import sys
import argparse
from collections import defaultdict
from pathlib import Path

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

def calculate_true_gdp(save_data):
    """Calculate GDP using Victoria 3's actual formula."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    
    min_credit_base = 100000.0
    credit_scale_factor = 0.5
    
    country_building_reserves = defaultdict(float)
    
    for building_id, building in buildings.items():
        if not isinstance(building, dict):
            continue
        
        cash_reserves = building.get('cash_reserves', 0)
        if cash_reserves <= 0:
            continue
            
        state_id = str(building.get('state'))
        if not state_id or state_id not in states:
            continue
            
        state = states[state_id]
        country_id = state.get('country')
        if not country_id:
            continue
            
        country_building_reserves[country_id] += float(cash_reserves)
    
    country_gdps = {}
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
            
        budget = country.get('budget', {})
        credit = float(budget.get('credit', 0))
        
        if credit <= 0:
            continue
            
        building_reserves = country_building_reserves.get(int(country_id), 0)
        calculated_gdp = (credit - min_credit_base - building_reserves) / credit_scale_factor
        
        if calculated_gdp > 0:
            country_gdps[int(country_id)] = calculated_gdp
    
    return country_gdps

def get_sol_data(save_data):
    """Get average standard of living for each country from avgsoltrend."""
    countries = save_data.get('country_manager', {}).get('database', {})
    sol_data = {}
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        avgsoltrend = country.get('avgsoltrend', {})
        if isinstance(avgsoltrend, dict):
            channels = avgsoltrend.get('channels', {})
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
                        sol_data[int(country_id)] = float(values[-1])
    
    return sol_data

def get_literacy_data(save_data):
    """Get literacy rate for each country."""
    countries = save_data.get('country_manager', {}).get('database', {})
    literacy_data = {}
    
    for country_id, country in countries.items():
        if not isinstance(country, dict):
            continue
        
        literacy_raw = country.get('literacy', 0)
        # Handle literacy as time series dict or number
        if isinstance(literacy_raw, dict):
            # Check for time series structure
            if 'channels' in literacy_raw:
                channels = literacy_raw.get('channels', {})
                if channels:
                    # Get channel 0 which typically has the current value
                    channel_0 = channels.get('0', {})
                    values = channel_0.get('values', [])
                    literacy = float(values[-1]) if values else 0.0
                else:
                    literacy = 0.0
            elif 'value' in literacy_raw:
                literacy = float(literacy_raw['value'])
            else:
                literacy = 0.0
        elif isinstance(literacy_raw, (int, float)):
            literacy = float(literacy_raw)
        else:
            literacy = 0
        
        if literacy > 0:
            literacy_data[int(country_id)] = literacy
    
    return literacy_data

def get_country_laws(save_data):
    """Get laws for each country."""
    countries = save_data.get('country_manager', {}).get('database', {})
    laws_db = save_data.get('laws', {}).get('database', {})
    
    # Track laws by country ID
    laws_data = defaultdict(set)
    
    # Process laws database to find active laws
    for law_id, law_data in laws_db.items():
        if not isinstance(law_data, dict):
            continue
        
        law_type = law_data.get('law')
        country_id = law_data.get('country')
        is_active = law_data.get('active', False)
        
        if law_type and country_id is not None and is_active:
            country_id = int(country_id)
            laws_data[country_id].add(law_type)
    
    return dict(laws_data)

def get_state_counts(save_data):
    """Count states controlled by each country."""
    states = save_data.get('states', {}).get('database', {})
    state_counts = defaultdict(int)
    
    for state_id, state in states.items():
        if isinstance(state, dict):
            country_id = state.get('country')
            if country_id:
                state_counts[country_id] += 1
    
    return dict(state_counts)

def calculate_military_scores(save_data):
    """Calculate military scores from save data, separated by army and navy."""
    from collections import defaultdict
    
    countries = save_data.get('country_manager', {}).get('database', {})
    formations_db = save_data.get('military_formation_manager', {}).get('database', {})
    units_db = save_data.get('new_combat_unit_manager', {}).get('database', {})
    
    # Unit stats (offense + defense average)
    unit_avg_stats = {
        # Army units
        'combat_unit_type_irregular_infantry': ('army', 10),  # (10+10)/2
        'combat_unit_type_line_infantry': ('army', 22.5),      # (20+25)/2
        'combat_unit_type_skirmish_infantry': ('army', 30),    # (25+35)/2
        'combat_unit_type_trench_infantry': ('army', 35),      # (30+40)/2
        'combat_unit_type_squad_infantry': ('army', 45),       # (40+50)/2
        'combat_unit_type_mechanized_infantry': ('army', 55),  # (50+60)/2
        'combat_unit_type_cannon_artillery': ('army', 20),     # (25+15)/2
        'combat_unit_type_mobile_artillery': ('army', 22.5),   # (30+15)/2
        'combat_unit_type_shrapnel_artillery': ('army', 35),   # (45+25)/2
        'combat_unit_type_siege_artillery': ('army', 42.5),    # (55+30)/2
        'combat_unit_type_heavy_tank': ('army', 52.5),         # (70+35)/2
        'combat_unit_type_hussars': ('army', 12.5),            # (15+10)/2
        'combat_unit_type_dragoons': ('army', 22.5),           # (20+25)/2
        'combat_unit_type_cuirassiers': ('army', 22.5),        # (25+20)/2
        'combat_unit_type_lancers': ('army', 25),              # (30+20)/2
        'combat_unit_type_light_tanks': ('army', 45),          # (45+45)/2
        # Navy units
        'combat_unit_type_frigate': ('navy', 12.5),            # (10+15)/2
        'combat_unit_type_monitor': ('navy', 25),              # (20+30)/2
        'combat_unit_type_destroyer': ('navy', 35),            # (30+40)/2
        'combat_unit_type_torpedo_boat': ('navy', 35),         # (40+30)/2
        'combat_unit_type_scout_cruiser': ('navy', 50),        # (50+50)/2
        'combat_unit_type_man_o_war': ('navy', 25),            # (25+25)/2
        'combat_unit_type_ironclad': ('navy', 50),             # (50+50)/2
        'combat_unit_type_dreadnought': ('navy', 80),          # (80+80)/2
        'combat_unit_type_battleship': ('navy', 100),          # (100+100)/2
        'combat_unit_type_submarine': ('navy', 40),            # (60+20)/2
        'combat_unit_type_carrier': ('navy', 90),              # (120+60)/2
    }
    
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
                        if unit_type and unit_type in unit_avg_stats:
                            unit_counts[unit_type] += 1
                
                # Calculate score for this formation
                for unit_type, count in unit_counts.items():
                    branch, avg_stat = unit_avg_stats[unit_type]
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

def get_power_bloc_membership(save_data):
    """Get power bloc membership for countries."""
    countries = save_data.get('country_manager', {}).get('database', {})
    power_blocs = save_data.get('power_bloc_manager', {}).get('database', {})
    
    membership = {}
    bloc_names = {}
    
    # Get bloc names
    for bloc_id, bloc in power_blocs.items():
        if isinstance(bloc, dict) and bloc.get('status') == 'active':
            name_data = bloc.get('name', {})
            if isinstance(name_data, dict) and 'name' in name_data:
                name_data = name_data['name']
            
            if isinstance(name_data, dict) and 'custom' in name_data:
                bloc_names[int(bloc_id)] = name_data['custom']
            else:
                bloc_names[int(bloc_id)] = f"Power Bloc {bloc_id}"
    
    # Get membership
    for country_id, country in countries.items():
        if isinstance(country, dict):
            bloc_id = country.get('power_bloc_as_core')
            if bloc_id and bloc_id in bloc_names:
                membership[int(country_id)] = bloc_names[bloc_id]
    
    return membership

def get_goods_production(save_data):
    """Extract goods production using actual output_goods values."""
    countries = save_data.get('country_manager', {}).get('database', {})
    buildings = save_data.get('building_manager', {}).get('database', {})
    states = save_data.get('states', {}).get('database', {})
    
    # Map goods IDs to names for key goods we want to compare
    key_goods_ids = {
        '34': 'Tools',
        '31': 'Steel', 
        '24': 'Coal',
        '25': 'Iron',
        '1': 'Small Arms',
        '2': 'Artillery',
        '30': 'Engines',
        '18': 'Ships',  # merchant_marine
        '11': 'Groceries',
        '12': 'Clothes'
    }
    
    # Get country tags
    country_tags = {}
    for country_id, country_info in countries.items():
        if isinstance(country_info, dict) and 'definition' in country_info:
            country_tags[country_id] = country_info['definition']
    
    # Get state to country mapping
    state_to_country = {}
    for state_id, state_info in states.items():
        if isinstance(state_info, dict) and 'country' in state_info:
            state_to_country[state_id] = state_info['country']
            state_to_country[int(state_id)] = state_info['country']
    
    # Calculate production by country and good using output_goods
    production_by_country = defaultdict(lambda: defaultdict(float))
    
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
                if good_id in key_goods_ids and isinstance(good_data, dict) and 'value' in good_data:
                    good_name = key_goods_ids[good_id]
                    production_value = good_data['value']
                    production_by_country[country_tag][good_name] += production_value
    
    return dict(production_by_country)

def get_interest_groups_data(save_data):
    """Get interest group data for each country."""
    countries = save_data.get('country_manager', {}).get('database', {})
    interest_groups_db = save_data.get('interest_groups', {}).get('database', {})
    
    # Track IGs by country
    country_igs = defaultdict(list)
    
    # Process interest groups database
    for ig_id, ig_data in interest_groups_db.items():
        if not isinstance(ig_data, dict):
            continue
        
        country_id = ig_data.get('country')
        if not country_id:
            continue
        
        # Extract IG info
        ig_info = {
            'type': ig_data.get('definition', 'unknown'),
            'clout': ig_data.get('clout', 0),
            'in_government': ig_data.get('in_government', False),
            'influence_type': ig_data.get('influence_type', 'normal'),
        }
        
        country_igs[country_id].append(ig_info)
    
    # Sort IGs within each country by clout
    for country_id in country_igs:
        country_igs[country_id].sort(key=lambda x: x['clout'], reverse=True)
    
    return dict(country_igs)

def format_comparison_section(title, data, formatter=None):
    """Format a comparison section."""
    output = []
    output.append("=" * 60)
    output.append(title)
    
    if not data:
        output.append("No changes detected.")
        return "\n".join(output) + "\n"
    
    output.append("-" * 60)
    
    # Sort by absolute change or other criteria
    sorted_data = sorted(data, key=lambda x: abs(x[3]) if len(x) > 3 else 0, reverse=True)
    
    output.append(f"{'Country':<8} {'Session 4':<12} {'Session 5':<12} {'Change':<15}")
    output.append("-" * 60)
    
    for item in sorted_data[:20]:  # Top 20
        tag = item[0]
        val1 = item[1]
        val2 = item[2]
        
        if formatter:
            val1_str = formatter(val1) if val1 is not None else "N/A"
            val2_str = formatter(val2) if val2 is not None else "N/A"
        else:
            val1_str = str(val1) if val1 is not None else "N/A"
            val2_str = str(val2) if val2 is not None else "N/A"
        
        if len(item) > 3:
            change = item[3]
            if isinstance(change, (int, float)):
                if formatter and '%' in str(formatter(0)):
                    # For percentage values, show change as percentage points
                    change_str = f"{change:+.1f}pp"
                else:
                    change_str = f"{change:+.1f}"
            else:
                change_str = str(change)
        else:
            change_str = ""
        
        output.append(f"{tag:<8} {val1_str:<12} {val2_str:<12} {change_str:<15}")
    
    if len(sorted_data) > 20:
        output.append(f"... and {len(sorted_data) - 20} more countries")
    
    return "\n".join(output) + "\n"

def compare_sessions(session1_data, session2_data, countries1, countries2, human_countries):
    """Compare all metrics between two sessions."""
    output = []
    
    # Get dates
    date1 = session1_data.get('meta_data', {}).get('game_date', 'Unknown')
    date2 = session2_data.get('meta_data', {}).get('game_date', 'Unknown')
    
    output.append("VICTORIA 3 COMPREHENSIVE SESSION COMPARISON")
    output.append("=" * 60)
    output.append(f"Session 4: {date1}")
    output.append(f"Session 5: {date2}")
    output.append("")
    
    # GDP Comparison
    gdp1 = calculate_true_gdp(session1_data)
    gdp2 = calculate_true_gdp(session2_data)
    
    gdp_changes = []
    for country_id in set(list(gdp1.keys()) + list(gdp2.keys())):
        tag = get_country_tag(countries1 if country_id in gdp1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        val1 = gdp1.get(country_id)
        val2 = gdp2.get(country_id)
        
        if val1 and val2:
            gdp_changes.append((tag, val1/1e6, val2/1e6))
    
    # Sort by absolute change for display
    gdp_changes.sort(key=lambda x: abs(x[2] - x[1]), reverse=True)
    
    output.append("=" * 60)
    output.append("GDP COMPARISON (£ millions)")
    output.append("-" * 60)
    output.append(f"{'Country':<8} {'Session 4':<10} {'Session 5':<10} {'Change':<12} {'% Change':<10}")
    output.append("-" * 60)
    
    for tag, val1, val2 in gdp_changes[:20]:
        change = val2 - val1
        pct_change = ((val2 / val1) - 1) * 100 if val1 > 0 else 0
        sign = '+' if change >= 0 else ''
        pct_sign = '+' if pct_change >= 0 else ''
        output.append(f"{tag:<8} £{val1:>6.1f}M   £{val2:>6.1f}M   {sign}{change:>6.1f}M    {pct_sign}{pct_change:>5.1f}%")
    output.append("")
    
    # Population Comparison
    pop_changes = []
    for country_id, country in countries1.items():
        if isinstance(country, dict):
            tag = get_country_tag(countries1, country_id)
            if human_countries and tag not in human_countries:
                continue
            
            # Get population from pop_statistics
            pop_stats1 = country.get('pop_statistics', {})
            pop1 = 0
            for key in ['population_lower_strata', 'population_middle_strata', 'population_upper_strata']:
                pop1 += pop_stats1.get(key, 0)
            
            country2 = countries2.get(country_id, {})
            pop2 = 0
            if isinstance(country2, dict):
                pop_stats2 = country2.get('pop_statistics', {})
                for key in ['population_lower_strata', 'population_middle_strata', 'population_upper_strata']:
                    pop2 += pop_stats2.get(key, 0)
            
            if pop1 > 0 and pop2 > 0:
                pop_changes.append((tag, pop1/1e6, pop2/1e6))
    
    # Sort by absolute change for display
    pop_changes.sort(key=lambda x: abs(x[2] - x[1]), reverse=True)
    
    output.append("=" * 60)
    output.append("POPULATION COMPARISON (millions)")
    output.append("-" * 60)
    output.append(f"{'Country':<8} {'Session 4':<10} {'Session 5':<10} {'Change':<12} {'% Change':<10}")
    output.append("-" * 60)
    
    for tag, val1, val2 in pop_changes[:20]:
        change = val2 - val1
        pct_change = ((val2 / val1) - 1) * 100 if val1 > 0 else 0
        sign = '+' if change >= 0 else ''
        pct_sign = '+' if pct_change >= 0 else ''
        output.append(f"{tag:<8} {val1:>7.2f}M   {val2:>7.2f}M   {sign}{change:>6.1f}M     {pct_sign}{pct_change:>5.1f}%")
    output.append("")
    
    # Standard of Living Comparison
    sol1 = get_sol_data(session1_data)
    sol2 = get_sol_data(session2_data)
    
    sol_changes = []
    for country_id in set(list(sol1.keys()) + list(sol2.keys())):
        tag = get_country_tag(countries1 if country_id in sol1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        val1 = sol1.get(country_id)
        val2 = sol2.get(country_id)
        
        if val1 and val2:
            sol_changes.append((tag, val1, val2, val2 - val1))
    
    output.append(format_comparison_section("STANDARD OF LIVING COMPARISON",
                                           sol_changes,
                                           lambda x: f"{x:.1f}"))
    
    # Literacy Comparison
    lit1 = get_literacy_data(session1_data)
    lit2 = get_literacy_data(session2_data)
    
    lit_changes = []
    for country_id in set(list(lit1.keys()) + list(lit2.keys())):
        tag = get_country_tag(countries1 if country_id in lit1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        val1 = lit1.get(country_id)
        val2 = lit2.get(country_id)
        
        if val1 is not None and val2 is not None:
            # Convert to percentage for display
            pct1 = val1 * 100
            pct2 = val2 * 100
            lit_changes.append((tag, pct1, pct2))
    
    # Sort by absolute pp change for display
    lit_changes.sort(key=lambda x: abs(x[2] - x[1]), reverse=True)
    
    output.append("=" * 60)
    output.append("LITERACY COMPARISON")
    output.append("-" * 60)
    output.append(f"{'Country':<8} {'Session 4':<10} {'Session 5':<10} {'PP Change':<10} {'% Change':<10}")
    output.append("-" * 60)
    
    for tag, val1, val2 in lit_changes[:20]:
        pp_change = val2 - val1
        pct_change = ((val2 / val1) - 1) * 100 if val1 > 0 else 0
        pp_sign = '+' if pp_change >= 0 else ''
        pct_sign = '+' if pct_change >= 0 else ''
        output.append(f"{tag:<8} {val1:>5.1f}%     {val2:>5.1f}%     {pp_sign}{pp_change:>5.1f}pp    {pct_sign}{pct_change:>5.1f}%")
    output.append("")
    
    # Prestige Comparison
    prestige_changes = []
    for country_id, country in countries1.items():
        if isinstance(country, dict):
            tag = get_country_tag(countries1, country_id)
            if human_countries and tag not in human_countries:
                continue
            
            pres1_raw = country.get('prestige', 0)
            # Handle prestige as time series dict or number
            if isinstance(pres1_raw, dict):
                # Check for time series structure
                if 'channels' in pres1_raw:
                    channels = pres1_raw.get('channels', {})
                    if channels:
                        # Get channel 0 which typically has the current value
                        channel_0 = channels.get('0', {})
                        values = channel_0.get('values', [])
                        pres1 = float(values[-1]) if values else 0.0
                    else:
                        pres1 = 0.0
                elif 'value' in pres1_raw:
                    pres1 = float(pres1_raw['value'])
                else:
                    pres1 = 0.0
            else:
                pres1 = float(pres1_raw) if pres1_raw else 0
            
            country2 = countries2.get(country_id, {})
            if isinstance(country2, dict):
                pres2_raw = country2.get('prestige', 0)
                if isinstance(pres2_raw, dict):
                    # Check for time series structure
                    if 'channels' in pres2_raw:
                        channels = pres2_raw.get('channels', {})
                        if channels:
                            # Get channel 0 which typically has the current value
                            channel_0 = channels.get('0', {})
                            values = channel_0.get('values', [])
                            pres2 = float(values[-1]) if values else 0.0
                        else:
                            pres2 = 0.0
                    elif 'value' in pres2_raw:
                        pres2 = float(pres2_raw['value'])
                    else:
                        pres2 = 0.0
                else:
                    pres2 = float(pres2_raw) if pres2_raw else 0
            else:
                pres2 = 0
            
            if pres1 > 0 or pres2 > 0:
                prestige_changes.append((tag, pres1, pres2))
    
    # Sort by absolute change for display
    prestige_changes.sort(key=lambda x: abs(x[2] - x[1]), reverse=True)
    
    output.append("=" * 60)
    output.append("PRESTIGE COMPARISON")
    output.append("-" * 60)
    output.append(f"{'Country':<8} {'Session 4':<10} {'Session 5':<10} {'Change':<12} {'% Change':<10}")
    output.append("-" * 60)
    
    for tag, val1, val2 in prestige_changes[:20]:
        change = val2 - val1
        pct_change = ((val2 / val1) - 1) * 100 if val1 > 0 else float('inf') if val2 > 0 else 0
        sign = '+' if change >= 0 else ''
        pct_sign = '+' if pct_change >= 0 else ''
        # Handle infinite percentage for prestige from 0
        if pct_change == float('inf'):
            pct_str = "new"
        else:
            pct_str = f"{pct_sign}{pct_change:>5.1f}%"
        output.append(f"{tag:<8} {val1:>7.0f}    {val2:>7.0f}    {sign}{change:>7.0f}     {pct_str:>8}")
    output.append("")
    
    # Military Score Comparison - Army
    mil1 = calculate_military_scores(session1_data)
    mil2 = calculate_military_scores(session2_data)
    
    # Army Rankings (sorted by Session 5 army score)
    army_rankings = []
    for country_id in set(list(mil1.keys()) + list(mil2.keys())):
        tag = get_country_tag(countries1 if country_id in mil1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        val1 = mil1.get(country_id, {}).get('army', 0)
        val2 = mil2.get(country_id, {}).get('army', 0)
        
        if val1 > 0 or val2 > 0:
            change = val2 - val1
            pct_change = (change / val1 * 100) if val1 > 0 else 0
            army_rankings.append((tag, val1, val2, change, pct_change))
    
    # Sort by Session 5 value (descending)
    army_rankings.sort(key=lambda x: x[2], reverse=True)
    
    output.append("=" * 60)
    output.append("ARMY POWER RANKINGS (by Session 5)")
    output.append("-" * 60)
    output.append(f"{'Rank':<5} {'Country':<8} {'Session 4':<12} {'Session 5':<12} {'Change':<15}")
    output.append("-" * 60)
    
    for i, (tag, val1, val2, change, pct) in enumerate(army_rankings[:15], 1):
        change_str = f"{change:+.0f} ({pct:+.1f}%)" if val1 > 0 else f"{change:+.0f}"
        output.append(f"{i:<5} {tag:<8} {val1:<12.0f} {val2:<12.0f} {change_str:<15}")
    output.append("")
    
    # Navy Rankings (sorted by Session 5 navy score)
    navy_rankings = []
    for country_id in set(list(mil1.keys()) + list(mil2.keys())):
        tag = get_country_tag(countries1 if country_id in mil1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        val1 = mil1.get(country_id, {}).get('navy', 0)
        val2 = mil2.get(country_id, {}).get('navy', 0)
        
        if val1 > 0 or val2 > 0:
            change = val2 - val1
            pct_change = (change / val1 * 100) if val1 > 0 else 0
            navy_rankings.append((tag, val1, val2, change, pct_change))
    
    # Sort by Session 5 value (descending)
    navy_rankings.sort(key=lambda x: x[2], reverse=True)
    
    output.append("=" * 60)
    output.append("NAVY POWER RANKINGS (by Session 5)")
    output.append("-" * 60)
    output.append(f"{'Rank':<5} {'Country':<8} {'Session 4':<12} {'Session 5':<12} {'Change':<15}")
    output.append("-" * 60)
    
    for i, (tag, val1, val2, change, pct) in enumerate(navy_rankings[:15], 1):
        change_str = f"{change:+.0f} ({pct:+.1f}%)" if val1 > 0 else f"{change:+.0f}"
        output.append(f"{i:<5} {tag:<8} {val1:<12.0f} {val2:<12.0f} {change_str:<15}")
    output.append("")
    
    # Military Score Comparison - Total
    total_changes = []
    for country_id in set(list(mil1.keys()) + list(mil2.keys())):
        tag = get_country_tag(countries1 if country_id in mil1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        val1 = mil1.get(country_id, {}).get('total', 0)
        val2 = mil2.get(country_id, {}).get('total', 0)
        
        if val1 > 0 or val2 > 0:
            total_changes.append((tag, val1, val2, val2 - val1))
    
    output.append(format_comparison_section("TOTAL MILITARY SCORE COMPARISON",
                                           total_changes,
                                           lambda x: f"{x:.0f}"))
    output.append("(Score = Units × Average(Offense + Defense))\n")
    
    # Infamy Comparison
    infamy_changes = []
    for country_id, country in countries1.items():
        if isinstance(country, dict):
            tag = get_country_tag(countries1, country_id)
            if human_countries and tag not in human_countries:
                continue
            
            inf1_raw = country.get('infamy', 0)
            # Handle infamy as dict or number
            if isinstance(inf1_raw, dict):
                inf1 = inf1_raw.get('value', 0) if 'value' in inf1_raw else 0
            else:
                inf1 = float(inf1_raw) if inf1_raw else 0
            
            country2 = countries2.get(country_id, {})
            if isinstance(country2, dict):
                inf2_raw = country2.get('infamy', 0)
                if isinstance(inf2_raw, dict):
                    inf2 = inf2_raw.get('value', 0) if 'value' in inf2_raw else 0
                else:
                    inf2 = float(inf2_raw) if inf2_raw else 0
            else:
                inf2 = 0
            
            if inf1 > 0 or inf2 > 0:
                infamy_changes.append((tag, inf1, inf2, inf2 - inf1))
    
    output.append(format_comparison_section("INFAMY COMPARISON",
                                           infamy_changes,
                                           lambda x: f"{x:.1f}"))
    
    # Goods Production Comparison
    goods1 = get_goods_production(session1_data)
    goods2 = get_goods_production(session2_data)
    
    # Get list of all goods produced
    all_goods = set()
    for country_goods in list(goods1.values()) + list(goods2.values()):
        all_goods.update(country_goods.keys())
    
    output.append("=" * 80)
    output.append("GOODS PRODUCTION COMPARISON")
    output.append("-" * 80)
    
    for good_name in sorted(all_goods):
        good_changes = []
        
        # Collect production data for this good
        all_countries = set(list(goods1.keys()) + list(goods2.keys()))
        for country_tag in all_countries:
            if human_countries and country_tag not in human_countries:
                continue
            
            val1 = goods1.get(country_tag, {}).get(good_name, 0)
            val2 = goods2.get(country_tag, {}).get(good_name, 0)
            
            if val1 > 0 or val2 > 0:
                good_changes.append((country_tag, val1, val2, val2 - val1))
        
        if good_changes:
            # Sort by Session 5 production (descending)
            good_changes.sort(key=lambda x: x[2], reverse=True)
            
            output.append(f"\n{good_name} Production (£K/week):")
            output.append(f"{'Country':<8} {'Session 4':<12} {'Session 5':<12} {'Change':<15}")
            output.append("-" * 50)
            
            for tag, val1, val2, change in good_changes[:10]:  # Top 10 producers
                # Convert to K for display
                val1_k = val1 / 1000
                val2_k = val2 / 1000
                change_k = change / 1000
                pct_change = ((val2 / val1) - 1) * 100 if val1 > 0 else (100 if val2 > 0 else 0)
                sign = '+' if change >= 0 else ''
                pct_sign = '+' if pct_change >= 0 else ''
                output.append(f"{tag:<8} {val1_k:>8.1f}K    {val2_k:>8.1f}K    {sign}{change_k:>6.1f}K ({pct_sign}{pct_change:>5.1f}%)")
    
    output.append("")
    
    # Territory Changes (State Count)
    states1 = get_state_counts(session1_data)
    states2 = get_state_counts(session2_data)
    
    territory_changes = []
    for country_id in set(list(states1.keys()) + list(states2.keys())):
        tag = get_country_tag(countries1 if country_id in states1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        count1 = states1.get(country_id, 0)
        count2 = states2.get(country_id, 0)
        
        if count1 > 0 or count2 > 0:
            territory_changes.append((tag, count1, count2, count2 - count1))
    
    output.append(format_comparison_section("TERRITORY COMPARISON (State Count)",
                                           territory_changes,
                                           lambda x: f"{x} states"))
    
    # Law Changes
    laws1 = get_country_laws(session1_data)
    laws2 = get_country_laws(session2_data)
    
    output.append("=" * 80)
    output.append("LAW CHANGES")
    output.append("-" * 80)
    
    # Define law categories to match old and new laws
    law_categories = {
        # Power Structure
        'governance': ['law_chiefdom', 'law_monarchy', 'law_presidential_republic', 'law_parliamentary_republic', 
                       'law_theocracy', 'law_council_republic', 'law_corporate_state'],
        'power': ['law_autocracy', 'law_technocracy', 'law_oligarchy', 'law_elder_council', 'law_landed_voting',
                  'law_wealth_voting', 'law_census_voting', 'law_universal_suffrage', 'law_anarchy', 'law_single_party_state'],
        'citizenship': ['law_ethnostate', 'law_national_supremacy', 'law_racial_segregation', 'law_cultural_exclusion', 
                        'law_multicultural'],
        'church': ['law_state_religion', 'law_freedom_of_conscience', 'law_total_separation', 'law_state_atheism'],
        'bureaucracy': ['law_hereditary_bureaucrats', 'law_appointed_bureaucrats', 'law_elected_bureaucrats'],
        'army': ['law_peasant_levies', 'law_national_militia', 'law_professional_army', 'law_mass_conscription'],
        'security': ['law_no_home_affairs', 'law_national_guard', 'law_secret_police', 'law_guaranteed_liberties'],
        # Economy
        'economic': ['law_traditionalism', 'law_interventionism', 'law_agrarianism', 'law_industry_banned', 
                     'law_extraction_economy', 'law_laissez_faire', 'law_command_economy', 'law_cooperative_ownership'],
        'trade': ['law_mercantilism', 'law_protectionism', 'law_free_trade', 'law_isolationism', 'law_canton_system'],
        'tax': ['law_consumption_based_taxation', 'law_land_based_taxation', 'law_per_capita_based_taxation', 
                'law_proportional_taxation', 'law_graduated_taxation'],
        'land': ['law_serfdom', 'law_tenant_farmers', 'law_commercialized_agriculture', 'law_homesteading', 
                 'law_collectivized_agriculture'],
        'colonial': ['law_no_colonial_affairs', 'law_colonial_resettlement', 'law_frontier_colonization', 
                     'law_colonial_exploitation'],
        'police': ['law_no_police', 'law_local_police', 'law_dedicated_police', 'law_militarized_police'],
        'education': ['law_no_schools', 'law_religious_schools', 'law_private_schools', 'law_public_schools'],
        'health': ['law_no_health_system', 'law_charity_hospitals', 'law_private_health_insurance', 
                   'law_public_health_insurance'],
        # Human Rights
        'speech': ['law_outlawed_dissent', 'law_censorship', 'law_right_of_assembly', 'law_protected_speech'],
        'labor': ['law_no_workers_rights', 'law_regulatory_bodies', 'law_worker_protections', 'law_union_representation'],
        'children': ['law_child_labor_allowed', 'law_restricted_child_labor', 'law_compulsory_primary_school'],
        'women': ['law_legal_guardianship', 'law_women_own_property', 'law_women_in_the_workplace', 'law_womens_suffrage'],
        'welfare': ['law_no_social_security', 'law_poor_laws', 'law_wage_subsidies', 'law_old_age_pension'],
        'migration': ['law_no_migration_controls', 'law_migration_controls', 'law_closed_borders'],
        'slavery': ['law_slavery_banned', 'law_debt_slavery', 'law_slave_trade', 'law_legacy_slavery']
    }
    
    # Default laws for categories (first law is usually the default)
    default_laws = {
        'health': 'law_no_health_system',
        'education': 'law_no_schools',
        'police': 'law_no_police',
        'colonial': 'law_no_colonial_affairs',
        'welfare': 'law_no_social_security',
        'labor': 'law_no_workers_rights',
        'security': 'law_no_home_affairs',
        'migration': 'law_no_migration_controls',
        'children': 'law_child_labor_allowed',
        'women': 'law_legal_guardianship',
    }
    
    def find_law_in_category(law, laws_set, categories):
        """Find what law from the same category was replaced."""
        for category, category_laws in categories.items():
            if law in category_laws:
                # Find what other law from this category exists in the set
                for other_law in category_laws:
                    if other_law in laws_set and other_law != law:
                        return other_law
                # If no explicit law found and we have a default for this category, use it
                if category in default_laws and default_laws[category] not in laws_set:
                    return default_laws[category]
        return None
    
    law_changes_found = False
    countries_with_changes = []
    all_tracked_countries = []
    
    for country_id in set(list(laws1.keys()) + list(laws2.keys())):
        tag = get_country_tag(countries1 if country_id in laws1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        all_tracked_countries.append(tag)
        old_laws = laws1.get(country_id, set())
        new_laws = laws2.get(country_id, set())
        
        added_laws = new_laws - old_laws
        removed_laws = old_laws - new_laws
        
        if added_laws:
            law_changes_found = True
            countries_with_changes.append(tag)
            output.append(f"\n{tag}:")
            for law in sorted(added_laws):
                clean_law = law.replace('law_', '').replace('_', ' ').title()
                # Find what law it replaced
                old_law = find_law_in_category(law, old_laws, law_categories)
                if old_law:
                    clean_old = old_law.replace('law_', '').replace('_', ' ').title()
                    output.append(f"  {clean_law} (from {clean_old})")
                else:
                    output.append(f"  {clean_law} (new)")
    
    # List countries with no changes
    countries_no_changes = [c for c in all_tracked_countries if c not in countries_with_changes]
    if countries_no_changes:
        for country in sorted(countries_no_changes):
            output.append(f"\n{country}:")
            output.append(f"  No changes")
    
    if not law_changes_found:
        output.append("No law changes detected.")
    
    # Power Bloc Changes
    blocs1 = get_power_bloc_membership(session1_data)
    blocs2 = get_power_bloc_membership(session2_data)
    
    output.append("\n" + "=" * 80)
    output.append("POWER BLOC CHANGES")
    output.append("-" * 80)
    
    bloc_changes_found = False
    for country_id in set(list(blocs1.keys()) + list(blocs2.keys())):
        tag = get_country_tag(countries1 if country_id in blocs1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        old_bloc = blocs1.get(country_id, "None")
        new_bloc = blocs2.get(country_id, "None")
        
        if old_bloc != new_bloc:
            bloc_changes_found = True
            output.append(f"{tag}: {old_bloc} → {new_bloc}")
    
    if not bloc_changes_found:
        output.append("No power bloc membership changes detected.")
    
    # Interest Groups Comparison
    igs1 = get_interest_groups_data(session1_data)
    igs2 = get_interest_groups_data(session2_data)
    
    output.append("\n" + "=" * 80)
    output.append("INTEREST GROUPS CHANGES")
    output.append("-" * 80)
    
    ig_changes_found = False
    for country_id in set(list(igs1.keys()) + list(igs2.keys())):
        tag = get_country_tag(countries1 if country_id in igs1 else countries2, country_id)
        if human_countries and tag not in human_countries:
            continue
        
        old_igs = igs1.get(country_id, [])
        new_igs = igs2.get(country_id, [])
        
        # Compare government composition
        old_gov = [ig['type'] for ig in old_igs if ig.get('in_government', False)]
        new_gov = [ig['type'] for ig in new_igs if ig.get('in_government', False)]
        
        # Compare clout percentages for major changes
        old_clouts = {ig['type']: ig['clout'] for ig in old_igs}
        new_clouts = {ig['type']: ig['clout'] for ig in new_igs}
        
        gov_changed = set(old_gov) != set(new_gov)
        
        # Find biggest clout changes
        clout_changes = []
        for ig_type in set(list(old_clouts.keys()) + list(new_clouts.keys())):
            old_clout = old_clouts.get(ig_type, 0) * 100
            new_clout = new_clouts.get(ig_type, 0) * 100
            change = new_clout - old_clout
            if abs(change) > 5:  # Only show changes > 5%
                clout_changes.append((ig_type, old_clout, new_clout, change))
        
        if gov_changed or clout_changes:
            ig_changes_found = True
            output.append(f"\n{tag}:")
            
            if gov_changed:
                # Show government changes
                added_to_gov = set(new_gov) - set(old_gov)
                removed_from_gov = set(old_gov) - set(new_gov)
                
                if added_to_gov:
                    for ig in added_to_gov:
                        clean_ig = ig.replace('ig_', '').replace('_', ' ').title()
                        output.append(f"  + {clean_ig} joined government")
                
                if removed_from_gov:
                    for ig in removed_from_gov:
                        clean_ig = ig.replace('ig_', '').replace('_', ' ').title()
                        output.append(f"  - {clean_ig} left government")
            
            if clout_changes:
                # Sort by absolute change
                clout_changes.sort(key=lambda x: abs(x[3]), reverse=True)
                for ig_type, old_cl, new_cl, change in clout_changes[:3]:  # Show top 3 changes
                    clean_ig = ig_type.replace('ig_', '').replace('_', ' ').title()
                    sign = '+' if change >= 0 else ''
                    output.append(f"  {clean_ig}: {old_cl:.1f}% → {new_cl:.1f}% ({sign}{change:.1f}%)")
    
    if not ig_changes_found:
        output.append("No significant interest group changes detected.")
    
    # Summary
    output.append("\n" + "=" * 80)
    output.append("SUMMARY: BIGGEST CHANGES")
    output.append("-" * 80)
    
    if gdp_changes:
        top_gdp = max(gdp_changes, key=lambda x: abs(x[2]/1e6 - x[1]/1e6))
        pct_change = ((top_gdp[2] / top_gdp[1]) - 1) * 100 if top_gdp[1] > 0 else 0
        output.append(f"Biggest GDP change: {top_gdp[0]} ({pct_change:+.1f}%)")
    
    if sol_changes:
        top_sol = max(sol_changes, key=lambda x: abs(x[3]))
        output.append(f"Biggest SoL change: {top_sol[0]} ({top_sol[3]:+.1f})")
    
    if lit_changes:
        top_lit = max(lit_changes, key=lambda x: abs(x[2] - x[1]))
        pp_change = top_lit[2] - top_lit[1]
        output.append(f"Biggest literacy change: {top_lit[0]} ({pp_change:+.1f}pp)")
    
    if territory_changes:
        top_territory = max(territory_changes, key=lambda x: abs(x[3]))
        if top_territory[3] != 0:
            output.append(f"Biggest territory change: {top_territory[0]} ({top_territory[3]:+d} states)")
    
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Victoria 3 session comparison')
    parser.add_argument('session1', nargs='?', help='Path to session 1 JSON file')
    parser.add_argument('session2', nargs='?', help='Path to session 2 JSON file')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Find session files if not specified
    if not args.session1 or not args.session2:
        import glob
        saves = sorted(glob.glob('extracted-saves/*_extracted.json'), key=os.path.getmtime)
        
        if len(saves) < 2:
            print("Error: Need at least 2 extracted save files for comparison")
            sys.exit(1)
        
        # Use the two most recent saves
        args.session1 = saves[-2]  # Second most recent
        args.session2 = saves[-1]  # Most recent
        
        print(f"Comparing:")
        print(f"  Session 1: {os.path.basename(args.session1)}")
        print(f"  Session 2: {os.path.basename(args.session2)}")
    
    # Load save data
    print("Loading session data...")
    session1_data = load_save_data(args.session1)
    session2_data = load_save_data(args.session2)
    
    # Get countries databases
    countries1 = session1_data.get('country_manager', {}).get('database', {})
    countries2 = session2_data.get('country_manager', {}).get('database', {})
    
    # Load human countries list
    human_countries = set()
    if os.path.exists('humans.txt'):
        with open('humans.txt', 'r') as f:
            human_countries = {line.strip() for line in f if line.strip()}
    
    # Generate comparison
    print("Generating comprehensive comparison...")
    result = compare_sessions(session1_data, session2_data, countries1, countries2, human_countries)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        print(f"Comparison saved to: {args.output}")
    else:
        print(result)

if __name__ == '__main__':
    main()