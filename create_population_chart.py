#!/usr/bin/env python3
"""
Create a beautiful population time series chart from Victoria 3 data
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import argparse
from pathlib import Path

def create_population_chart(csv_file, output_file=None, log_scale=False):
    """Create a pretty population chart from CSV data"""
    
    # Read the CSV data
    df = pd.read_csv(csv_file)
    
    # Convert date_index to actual dates (starting from 1836.1.1)
    # Victoria 3 uses daily sampling, so date_index corresponds to days since 1836.1.1
    game_start = datetime(1836, 1, 1)
    df['date'] = df['date_index'].apply(lambda x: game_start + timedelta(days=x))
    
    # Set up the plot style
    plt.style.use('default')
    
    # Define colors based on Victoria 3 country colors
    v3_colors = {
        'GBR': '#e6454e',      # Great Britain - default red
        'USA': '#425ec1',      # America - default blue (66 94 193 -> hex)
        'FRA': '#1432d2',      # France - default blue (20 50 210 -> hex)
        'BIC': '#bc713d',      # British India Company - default (188 113 61 -> hex)
        'POR': '#1c5294',      # Portugal - default blue (28 82 148 -> hex)
        'CHI': '#fcb93d',      # China - default yellow (252 185 61 -> hex)
        'ITA': '#7dab54',      # Italy - default green (125 171 84 -> hex)
        'SPA': '#d48806',      # Spain - default yellow/orange
        'TUR': '#aacea2',     # Turkey - default green (170 206 162 -> hex)
        'RUS': '#2f5b12',      # Russia - default green (47 91 18 -> hex)
        'JAP': '#c2353c',      # Japan - default red (194 53 60 -> hex)
        'YUG': '#db1f3e',      # Yugoslavia (using default red similar to other Slavic)
    }
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Get population columns
    population_columns = [col for col in df.columns if col.endswith('_population')]
    countries = [col.replace('_population', '') for col in population_columns]
    
    # Plot each country's population over time
    for col, country in zip(population_columns, countries):
        # Remove empty values and convert to numeric
        country_data = df[['date', col]].copy()
        country_data[col] = pd.to_numeric(country_data[col], errors='coerce')
        country_data = country_data.dropna()
        
        if len(country_data) > 0:
            # Convert population to millions for better readability
            country_data[col] = country_data[col] / 1_000_000
            
            # Get Victoria 3 color for this country, fallback to default if not found
            color = v3_colors.get(country, '#666666')
            ax.plot(country_data['date'], country_data[col], 
                   linewidth=2.5, label=country, alpha=0.8, color=color)
    
    # Customize the chart (no title)
    ax.set_xlabel('Year', fontsize=14, fontweight='bold')
    
    # Set x-axis limits based on actual data range
    ax.set_xlim(df['date'].min(), df['date'].max())
    
    # Set y-axis scale
    if log_scale:
        ax.set_yscale('log')
        ax.set_ylabel('Population (Millions, log scale)', fontsize=14, fontweight='bold')
        # For log scale, use simpler formatting
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:g}M'))
    else:
        ax.set_ylabel('Population (Millions)', fontsize=14, fontweight='bold')
        # Format y-axis with commas
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}M'))
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_minor_locator(mdates.YearLocator(1))
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Customize legend
    legend = ax.legend(loc='upper left', frameon=True, fancybox=True, 
                      shadow=True, ncol=2, fontsize=11)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_alpha(0.9)
    
    # Set background color
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#f8f9fa')
    
    # Rotate x-axis labels for better readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    # Add some styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)
    
    # Tight layout
    plt.tight_layout()
    
    # Save or show
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"Chart saved to: {output_file}")
    else:
        plt.show()
    
    # Print some stats
    print("\nPopulation Growth Summary:")
    print("-" * 50)
    for col, country in zip(population_columns, countries):
        country_data = df[col].dropna()
        if len(country_data) >= 2:
            start_pop = int(country_data.iloc[0])
            end_pop = int(country_data.iloc[-1])
            growth = (end_pop / start_pop - 1) * 100
            print(f"{country:3s}: {start_pop/1_000_000:6.1f}M → {end_pop/1_000_000:6.1f}M ({growth:+5.1f}%)")

def main():
    parser = argparse.ArgumentParser(description="Create population chart from Victoria 3 data")
    parser.add_argument("csv_file", nargs='?', help="Path to CSV file with time series data")
    parser.add_argument("--output", "-o", help="Output image file (PNG/PDF/SVG)")
    parser.add_argument("--log", action="store_true", help="Use logarithmic y-axis scale")
    
    args = parser.parse_args()
    
    # Find latest CSV if not specified
    if not args.csv_file:
        reports_dir = Path("reports")
        csv_files = list(reports_dir.glob("population_timeseries_*.csv"))
        if not csv_files:
            print("No CSV files found in reports/")
            return
        args.csv_file = str(max(csv_files, key=lambda x: x.stat().st_mtime))
        print(f"Using latest CSV: {args.csv_file}")
    
    # Generate output filename if not specified
    if not args.output:
        csv_path = Path(args.csv_file)
        scale_suffix = "_log" if args.log else ""
        args.output = str(csv_path.parent / f"population_timeseries_chart{scale_suffix}.png")
    
    # Create the chart
    create_population_chart(args.csv_file, args.output, args.log)

if __name__ == "__main__":
    main()