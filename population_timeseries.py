#!/usr/bin/env python3
"""
Victoria 3 Population Time Series Extractor
Extracts full population time series data from save files
"""

import json
import csv
import sys
from pathlib import Path
import argparse
from datetime import datetime, timedelta

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

def parse_game_date(date_str):
    """Parse Victoria 3 date format (YYYY.M.D or YYYY.M.D.H)"""
    parts = date_str.split('.')
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    # Approximate date object (Victoria 3 uses its own calendar)
    return datetime(year, month, day)

def extract_population_timeseries(json_file, humans_list=None, italy_session3_file=None):
    """Extract full population time series from Victoria 3 save"""
    
    print(f"Loading save file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Load Session 3 data for Italy if provided
    session3_data = None
    if italy_session3_file and Path(italy_session3_file).exists():
        print(f"Loading Session 3 for Italy data: {italy_session3_file}")
        with open(italy_session3_file, 'r', encoding='utf-8') as f:
            session3_data = json.load(f)
    
    # Get the game dates
    current_date = data.get('date', 'Unknown')
    game_start = parse_game_date('1836.1.1')
    
    # Collect time series data
    timeseries_data = {}
    
    if 'country_manager' in data and 'database' in data['country_manager']:
        all_countries = data['country_manager']['database']
        
        for country_id, country_info in all_countries.items():
            # Skip non-dict entries
            if not isinstance(country_info, dict):
                continue
                
            tag = country_info.get('definition', country_id)
            
            # Skip if not in humans list (if provided)
            if humans_list and tag not in humans_list:
                continue
            
            # Extract population time series from pop_statistics
            pop_stats = country_info.get('pop_statistics', {})
            pop_data = pop_stats.get('trend_population', {})
            if isinstance(pop_data, dict) and 'channels' in pop_data:
                channel = pop_data['channels'].get('0', {})
                values = channel.get('values', [])
                
                if values:
                    # Victoria 3 actually samples DAILY (every game day)
                    sample_rate = 1
                    
                    # The values array covers the entire game from 1836.1.1 to current date
                    # Victoria 3 starts on 1836.1.1, so we calculate from there
                    game_start = parse_game_date('1836.1.1')
                    current_parts = current_date.split('.')[0:3]  # Year, month, day only
                    current = parse_game_date('.'.join(current_parts))
                    
                    # The series should start from 1836.1.1
                    series_start = game_start
                    
                    # Generate dates for each sample (daily from 1836.1.1)
                    dates = []
                    for i in range(len(values)):
                        sample_date = series_start + timedelta(days=i)
                        dates.append(sample_date)
                    
                    timeseries_data[tag] = {
                        'tag': tag,
                        'values': values,
                        'dates': dates,
                        'sample_rate': sample_rate,
                        'samples': len(values),
                        'start_date': series_start,
                        'end_date': current
                    }
    
    # Handle Italy data from Session 3 if needed
    if session3_data and 'ITA' in (humans_list or []):
        if 'ITA' not in timeseries_data:  # Only if Italy missing from main data
            print("Adding Italy data from Session 3...")
            cm_s3 = session3_data.get('country_manager', {})
            db_s3 = cm_s3.get('database', {})
            
            for country_id, country_info in db_s3.items():
                if isinstance(country_info, dict) and country_info.get('definition') == 'ITA':
                    pop_stats = country_info.get('pop_statistics', {})
                    pop_data = pop_stats.get('trend_population', {})
                    if isinstance(pop_data, dict) and 'channels' in pop_data:
                        channel = pop_data['channels'].get('0', {})
                        values = channel.get('values', [])
                        
                        if values:
                            sample_rate = 1  # Daily sampling
                            # Italy data starts from 1836.1.1 like all countries
                            game_start = parse_game_date('1836.1.1')
                            series_start = game_start
                            
                            dates = []
                            for i in range(len(values)):
                                sample_date = series_start + timedelta(days=i)
                                dates.append(sample_date)
                            
                            timeseries_data['ITA'] = {
                                'tag': 'ITA',
                                'values': values,
                                'dates': dates,
                                'sample_rate': sample_rate,
                                'samples': len(values),
                                'start_date': series_start,
                                'end_date': s3_current,
                                'source': 'Session 3'
                            }
                    break
    
    return {
        'current_date': current_date,
        'countries': timeseries_data
    }

def write_timeseries_csv(timeseries_data, output_file):
    """Write population time series to CSV"""
    
    countries = timeseries_data['countries']
    if not countries:
        print("No time series data found!")
        return
    
    # Find the maximum number of samples
    max_samples = max(c['samples'] for c in countries.values())
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        # Build header
        fieldnames = ['date_index', 'year']
        for tag in sorted(countries.keys()):
            fieldnames.append(f'{tag}_population')
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write data rows
        # Find earliest start date among all countries
        earliest_start = min(c['start_date'] for c in countries.values())
        latest_end = max(c['end_date'] for c in countries.values())
        sample_rate = 1  # Victoria 3 samples daily
        
        # Generate common timeline
        current_date = earliest_start
        date_index = 0
        
        while current_date <= latest_end:
            row = {}
            row['date_index'] = date_index
            row['year'] = current_date.year + (current_date.timetuple().tm_yday - 1) / 365.25
            
            # Add population values for each country at this date
            for tag, country_data in countries.items():
                # Find if this country has data for this date
                if current_date >= country_data['start_date'] and current_date <= country_data['end_date']:
                    # Calculate which sample this date corresponds to
                    days_from_start = (current_date - country_data['start_date']).days
                    sample_idx = days_from_start  # Daily sampling
                    if sample_idx < len(country_data['values']):
                        row[f'{tag}_population'] = str(int(country_data['values'][sample_idx]))
                    else:
                        row[f'{tag}_population'] = ''
                else:
                    row[f'{tag}_population'] = ''
            
            writer.writerow(row)
            current_date += timedelta(days=sample_rate)  # Daily increment
            date_index += 1
    
    print(f"Population time series written to: {output_file}")
    print(f"Countries included: {', '.join(sorted(countries.keys()))}")
    print(f"Maximum samples: {max_samples}")
    
    # Print summary
    print("\nPopulation Growth Summary:")
    for tag in sorted(countries.keys()):
        country = countries[tag]
        initial_pop = int(country['values'][0])
        final_pop = int(country['values'][-1])
        growth_pct = (final_pop/initial_pop - 1)*100
        print(f"  {tag}: {initial_pop:,} -> {final_pop:,} people "
              f"({growth_pct:+.1f}% growth)")

def main():
    parser = argparse.ArgumentParser(
        description="Extract population time series from Victoria 3 saves"
    )
    parser.add_argument(
        "save_json",
        nargs='?',
        help="Path to extracted JSON save file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output CSV file path (default: reports/population_timeseries_<date>.csv)"
    )
    parser.add_argument(
        "--humans",
        default="humans.txt",
        help="Path to humans.txt file (default: humans.txt)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Extract all countries, not just humans"
    )
    parser.add_argument(
        "--session3",
        help="Path to Session 3 JSON file (for Italy data)"
    )
    
    args = parser.parse_args()
    
    # Default to latest extracted save
    if not args.save_json:
        extracted_dir = Path("extracted-saves")
        json_files = list(extracted_dir.glob("*.json"))
        if not json_files:
            print("No extracted JSON files found")
            sys.exit(1)
        args.save_json = str(max(json_files, key=lambda x: x.stat().st_mtime))
        print(f"Using latest save: {args.save_json}")
    
    # Load humans list unless --all specified
    humans_list = None
    if not args.all:
        humans_list = load_humans_list(args.humans)
        if humans_list:
            print(f"Tracking countries: {', '.join(humans_list)}")
    
    # Extract time series
    timeseries_data = extract_population_timeseries(args.save_json, humans_list, args.session3)
    
    # Determine output file
    if not args.output:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = str(reports_dir / f"population_timeseries_{timestamp}.csv")
    
    # Write report
    write_timeseries_csv(timeseries_data, args.output)

if __name__ == "__main__":
    main()