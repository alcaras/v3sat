#!/usr/bin/env python3
"""
HTML Report Generator for Victoria 3 Analysis

Creates a comprehensive HTML report viewer with all analysis results
in a subdued, clean design suitable for GitHub Pages deployment.
"""

import os
import json
import glob
import shutil
from pathlib import Path
from datetime import datetime

def create_html_template():
    """Create the main HTML template with subdued dark theme."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Victoria 3 Session Analysis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            background-color: #1a1a1a;
            color: #d0d0d0;
            line-height: 1.6;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: #e0e0e0;
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 300;
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            color: #888;
            font-size: 1.1rem;
            margin-bottom: 30px;
        }
        
        .nav-tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 30px;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }
        
        .nav-tab {
            padding: 8px 16px;
            background-color: #252525;
            border: 1px solid #333;
            border-radius: 4px;
            color: #aaa;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.95rem;
        }
        
        .nav-tab:hover {
            background-color: #2a2a2a;
            color: #ddd;
        }
        
        .nav-tab.active {
            background-color: #2d4a2b;
            color: #a4c09e;
            border-color: #3d5a3b;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .report-section {
            background-color: #222;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .report-section h2 {
            color: #c0c0c0;
            font-size: 1.5rem;
            margin-bottom: 15px;
            font-weight: 400;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }
        
        .report-section h3 {
            color: #a0a0a0;
            font-size: 1.2rem;
            margin: 20px 0 10px;
            font-weight: 400;
        }
        
        pre {
            background-color: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            color: #b0b0b0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        th {
            background-color: #2a2a2a;
            color: #c0c0c0;
            padding: 10px;
            text-align: left;
            font-weight: 500;
            border-bottom: 2px solid #333;
        }
        
        td {
            padding: 8px 10px;
            border-bottom: 1px solid #2a2a2a;
            color: #a0a0a0;
        }
        
        tr:hover {
            background-color: #252525;
        }
        
        .chart-container {
            background-color: #1a1a1a;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .metric-card {
            background-color: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 6px;
            padding: 15px;
        }
        
        .metric-label {
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        
        .metric-value {
            color: #d0d0d0;
            font-size: 1.8rem;
            font-weight: 300;
        }
        
        .metric-change {
            color: #7a7a7a;
            font-size: 0.9rem;
            margin-top: 5px;
        }
        
        .metric-change.positive {
            color: #5a8a5a;
        }
        
        .metric-change.negative {
            color: #8a5a5a;
        }
        
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #333;
            color: #666;
            text-align: center;
            font-size: 0.9rem;
        }
        
        a {
            color: #7a9a7a;
            text-decoration: none;
        }
        
        a:hover {
            color: #9aba9a;
            text-decoration: underline;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1a1a1a;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #444;
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Victoria 3 Session Analysis</h1>
        <div class="subtitle">{{SESSION_NAME}} - {{GAME_DATE}}</div>
        
        <div class="nav-tabs">
            <div class="nav-tab active" onclick="showTab('overview')">Overview</div>
            <div class="nav-tab" onclick="showTab('gdp')">GDP Analysis</div>
            <div class="nav-tab" onclick="showTab('population')">Population</div>
            <div class="nav-tab" onclick="showTab('sol')">Standard of Living</div>
            <div class="nav-tab" onclick="showTab('construction')">Construction</div>
            <div class="nav-tab" onclick="showTab('laws')">Laws</div>
            <div class="nav-tab" onclick="showTab('power-blocs')">Power Blocs</div>
            <div class="nav-tab" onclick="showTab('migration')">Migration</div>
            <div class="nav-tab" onclick="showTab('foreign')">Foreign Ownership</div>
            <div class="nav-tab" onclick="showTab('comparison')">Session Comparison</div>
        </div>
        
        {{CONTENT}}
        
        <div class="footer">
            Generated on {{GENERATED_DATE}} | 
            <a href="https://github.com/anthropics/victoria3-analysis">GitHub</a>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Remove active class from all nav tabs
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {
                selectedTab.classList.add('active');
            }
            
            // Add active class to clicked nav tab
            event.target.classList.add('active');
        }
    </script>
</body>
</html>"""

def read_report_file(filepath):
    """Read a report file and return its content."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Report not found: {filepath}"
    except Exception as e:
        return f"Error reading report: {str(e)}"

def format_text_report(content):
    """Format a text report for HTML display."""
    # Escape HTML characters
    content = content.replace('&', '&amp;')
    content = content.replace('<', '&lt;')
    content = content.replace('>', '&gt;')
    return f'<pre>{content}</pre>'

def format_csv_as_table(content):
    """Convert CSV content to HTML table."""
    lines = content.strip().split('\n')
    if not lines:
        return '<p>No data available</p>'
    
    html = '<table>'
    
    # Header
    headers = lines[0].split(',')
    html += '<thead><tr>'
    for header in headers:
        html += f'<th>{header.strip()}</th>'
    html += '</tr></thead>'
    
    # Body
    html += '<tbody>'
    for line in lines[1:]:
        if line.strip() and not line.startswith('#'):
            cells = line.split(',')
            html += '<tr>'
            for cell in cells:
                html += f'<td>{cell.strip()}</td>'
            html += '</tr>'
    html += '</tbody>'
    
    html += '</table>'
    return html

def create_overview_section(report_dir):
    """Create the overview section with key metrics."""
    html = '<div id="overview" class="tab-content active">'
    html += '<div class="report-section">'
    html += '<h2>Session Overview</h2>'
    
    # Try to extract key metrics from various reports
    html += '<div class="metric-grid">'
    
    # Read GDP report for top countries
    gdp_file = os.path.join(report_dir, 'gdp_report.csv')
    if os.path.exists(gdp_file):
        with open(gdp_file, 'r') as f:
            lines = f.readlines()
            if len(lines) > 2:
                # Extract top 3 countries
                for i in range(2, min(5, len(lines))):
                    parts = lines[i].strip().split(',')
                    if len(parts) >= 4:
                        rank = parts[0]
                        tag = parts[1]
                        gdp = parts[3]
                        html += f'''
                        <div class="metric-card">
                            <div class="metric-label">#{rank} GDP - {tag}</div>
                            <div class="metric-value">£{float(gdp)/1e6:.1f}M</div>
                        </div>'''
    
    html += '</div>'
    
    # Add charts if available
    for chart_type in ['gdp_chart.png', 'gdp_treemap.png', 'population_treemap.png']:
        chart_path = os.path.join(report_dir, chart_type)
        if os.path.exists(chart_path):
            chart_name = chart_type.replace('_', ' ').replace('.png', '').title()
            html += f'''
            <div class="chart-container">
                <h3>{chart_name}</h3>
                <img src="{chart_type}" alt="{chart_name}">
            </div>'''
    
    html += '</div></div>'
    return html

def create_report_section(title, tab_id, report_files, report_dir):
    """Create a report section for a specific category."""
    html = f'<div id="{tab_id}" class="tab-content">'
    html += f'<div class="report-section">'
    html += f'<h2>{title}</h2>'
    
    for report_file in report_files:
        filepath = os.path.join(report_dir, report_file)
        if os.path.exists(filepath):
            content = read_report_file(filepath)
            
            # Format based on file type
            if report_file.endswith('.csv'):
                html += f'<h3>{report_file}</h3>'
                html += format_csv_as_table(content)
            elif report_file.endswith('.png'):
                html += f'''
                <div class="chart-container">
                    <h3>{report_file.replace("_", " ").replace(".png", "").title()}</h3>
                    <img src="{report_file}" alt="{report_file}">
                </div>'''
            else:
                html += f'<h3>{report_file}</h3>'
                html += format_text_report(content)
    
    html += '</div></div>'
    return html

def generate_html_report(report_dir):
    """Generate the complete HTML report for a session."""
    # Get session info
    session_name = os.path.basename(report_dir)
    
    # Try to get game date from save data
    game_date = "Unknown Date"
    
    # Create HTML content
    template = create_html_template()
    
    # Build content sections
    content = ""
    
    # Overview
    content += create_overview_section(report_dir)
    
    # GDP Analysis
    content += create_report_section(
        "GDP Analysis",
        "gdp",
        ['gdp_report.csv', 'gdp_timeseries.csv', 'gdp_chart.png', 'gdp_chart_log.png', 'gdp_treemap.png'],
        report_dir
    )
    
    # Population
    content += create_report_section(
        "Population Analysis",
        "population",
        ['population_report.txt', 'population_timeseries.csv', 'population_chart.png', 'population_chart_log.png', 'population_treemap.png'],
        report_dir
    )
    
    # Standard of Living
    content += create_report_section(
        "Standard of Living & Literacy",
        "sol",
        ['sol_report.txt', 'literacy_report.txt'],
        report_dir
    )
    
    # Construction
    content += create_report_section(
        "Construction & Economy",
        "construction",
        ['construction_report.txt', 'infamy_report.txt', 'budget_report.txt', 'companies_report.txt'],
        report_dir
    )
    
    # Laws
    content += create_report_section(
        "Laws & Governance",
        "laws",
        ['laws_comprehensive.txt'],
        report_dir
    )
    
    # Power Blocs
    content += create_report_section(
        "Power Blocs",
        "power-blocs",
        ['power_blocs.txt'],
        report_dir
    )
    
    # Migration
    content += create_report_section(
        "Migration Patterns",
        "migration",
        ['migration_report.txt'],
        report_dir
    )
    
    # Foreign Ownership
    content += create_report_section(
        "Foreign Ownership",
        "foreign",
        ['foreign_ownership_simple.txt', 'foreign_ownership_detailed.txt', 'foreign_ownership_by_entity.txt', 'foreign_ownership_full.txt', 'foreign_ownership_true_gdp.txt'],
        report_dir
    )
    
    # Session Comparison
    comparison_dir = os.path.join(report_dir, 'comparison')
    if os.path.exists(comparison_dir):
        comparison_files = [f for f in os.listdir(comparison_dir) if f.endswith('.txt')]
        content += create_report_section(
            "Session Comparison",
            "comparison",
            [os.path.join('comparison', f) for f in comparison_files],
            report_dir
        )
    else:
        content += '<div id="comparison" class="tab-content"><div class="report-section"><h2>Session Comparison</h2><p>No comparison data available</p></div></div>'
    
    # Replace placeholders
    html = template.replace('{{SESSION_NAME}}', session_name)
    html = html.replace('{{GAME_DATE}}', game_date)
    html = html.replace('{{CONTENT}}', content)
    html = html.replace('{{GENERATED_DATE}}', datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    return html

def create_html_reports(report_dir):
    """Create HTML reports in a web subfolder."""
    # Create web subfolder
    web_dir = os.path.join(report_dir, 'web')
    os.makedirs(web_dir, exist_ok=True)
    
    # Generate HTML
    html = generate_html_report(report_dir)
    
    # Write HTML file
    html_path = os.path.join(web_dir, 'index.html')
    with open(html_path, 'w') as f:
        f.write(html)
    
    # Copy image files to web directory
    for img_file in glob.glob(os.path.join(report_dir, '*.png')):
        shutil.copy(img_file, web_dir)
    
    # Copy HTML treemap files if they exist
    for html_file in glob.glob(os.path.join(report_dir, '*.html')):
        if 'index.html' not in html_file:
            shutil.copy(html_file, web_dir)
    
    print(f"HTML report generated: {html_path}")
    print(f"Open file://{os.path.abspath(html_path)} in your browser to view")
    
    return html_path

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate HTML report viewer for Victoria 3 analysis')
    parser.add_argument('report_dir', nargs='?', help='Path to report directory')
    
    args = parser.parse_args()
    
    if args.report_dir:
        report_dir = args.report_dir
    else:
        # Find the latest report directory
        report_dirs = glob.glob('reports/*_*')
        if not report_dirs:
            print("No report directories found")
            return
        report_dir = max(report_dirs, key=os.path.getmtime)
        print(f"Using latest report directory: {report_dir}")
    
    if not os.path.exists(report_dir):
        print(f"Report directory not found: {report_dir}")
        return
    
    create_html_reports(report_dir)

if __name__ == '__main__':
    main()