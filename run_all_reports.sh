#!/bin/bash
# Victoria 3 Master Report Generator
# Runs all available analysis reports for a given extracted save file
#
# Usage: ./run_all_reports.sh [save_file] [comparison_save_file]
# Example: ./run_all_reports.sh "extracted-saves/Session 5_extracted.json" "extracted-saves/Session 4_extracted.json"

set -e  # Exit on any error

# Default to latest save if no argument provided
if [ $# -eq 0 ]; then
    echo "Looking for latest extracted save file..."
    SAVE_FILE=$(find extracted-saves -name "*_extracted.json" -type f -exec stat -f "%m %N" {} \; | sort -n -r | head -1 | cut -d' ' -f2-)
    if [ -z "$SAVE_FILE" ]; then
        echo "Error: No extracted save files found in extracted-saves/"
        echo "Please run extract_save.py first or specify a save file"
        exit 1
    fi
    echo "Using latest save: $SAVE_FILE"
else
    SAVE_FILE="$1"
fi

# Optional second parameter for comparison
COMPARISON_FILE=""
if [ $# -ge 2 ]; then
    COMPARISON_FILE="$2"
    echo "Will compare to: $COMPARISON_FILE"
fi

# Check if save file exists
if [ ! -f "$SAVE_FILE" ]; then
    echo "Error: Save file '$SAVE_FILE' not found"
    exit 1
fi

# Create reports directory if it doesn't exist
mkdir -p reports

# Get base filename for output files
BASE_NAME=$(basename "$SAVE_FILE" _extracted.json)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_DIR="reports/${BASE_NAME}_${TIMESTAMP}"
mkdir -p "$REPORT_DIR"

echo "Generating all reports for: $SAVE_FILE"
echo "Output directory: $REPORT_DIR"
echo "============================================"
echo ""

# 1. GDP Report
echo "📊 Generating GDP report..."
python3 gdp_report.py "$SAVE_FILE" -o "$REPORT_DIR/gdp_report.csv"

# 2. GDP Time Series
echo "📈 Generating GDP time series..."
python3 gdp_timeseries.py "$SAVE_FILE" -o "$REPORT_DIR/gdp_timeseries.csv"

# 3. GDP Chart
echo "📊 Creating GDP visualization..."
python3 create_gdp_chart.py "$REPORT_DIR/gdp_timeseries.csv" -o "$REPORT_DIR/gdp_chart.png"
python3 create_gdp_chart.py "$REPORT_DIR/gdp_timeseries.csv" --log -o "$REPORT_DIR/gdp_chart_log.png"

# 3b. GDP Treemap
echo "🗺️  Creating GDP treemap visualization..."
source venv/bin/activate && python gdp_treemap_plotly.py "$SAVE_FILE" -o "$REPORT_DIR/gdp_treemap.png"

# 3c. Population Treemap
echo "🗺️  Creating population treemap visualization..."
source venv/bin/activate && python population_treemap_plotly.py "$SAVE_FILE" -o "$REPORT_DIR/population_treemap.png"

# 3d. Military Treemaps
echo "⚔️  Creating military power treemap visualizations..."
source venv/bin/activate && python military_treemap_simple.py "$SAVE_FILE" -m total -o "$REPORT_DIR/military_treemap.png"
source venv/bin/activate && python military_treemap_simple.py "$SAVE_FILE" -m army -o "$REPORT_DIR/army_treemap.png"
source venv/bin/activate && python military_treemap_simple.py "$SAVE_FILE" -m navy -o "$REPORT_DIR/navy_treemap.png"

# 4. Population Reports
echo "👥 Generating population analysis..."
python3 population_report.py "$SAVE_FILE" -o "$REPORT_DIR/population_report.txt"
python3 population_timeseries.py "$SAVE_FILE" -o "$REPORT_DIR/population_timeseries.csv"
python3 create_population_chart.py "$REPORT_DIR/population_timeseries.csv" -o "$REPORT_DIR/population_chart.png"
python3 create_population_chart.py "$REPORT_DIR/population_timeseries.csv" --log -o "$REPORT_DIR/population_chart_log.png"

# 5. Standard of Living Reports  
echo "📊 Generating standard of living analysis..."
python3 standard_of_living_report.py "$SAVE_FILE" -o "$REPORT_DIR/sol_report.txt"

# 5b. Literacy Report
echo "📚 Generating literacy report..."
python3 literacy_report.py "$SAVE_FILE" --humans -o "$REPORT_DIR/literacy_report.txt"

# 5c. Prestige Report
echo "🏆 Generating prestige report..."
python3 prestige_report.py "$SAVE_FILE" --humans -o "$REPORT_DIR/prestige_report.txt"

# 5d. Military Score Report
echo "⚔️  Generating military score report..."
python3 military_score_report.py "$SAVE_FILE" --humans --detailed -o "$REPORT_DIR/military_score_report.txt"

# 5e. Power Projection Report (manpower-based)
echo "💪 Generating power projection report..."
python3 power_projection_report.py "$SAVE_FILE" --humans --detailed -o "$REPORT_DIR/power_projection_report.txt"

# 6. Additional Analysis Reports
echo "📊 Generating additional analysis reports..."
python3 construction_report.py "$SAVE_FILE" -o "$REPORT_DIR/construction_report.txt"
python3 infamy_report.py "$SAVE_FILE" -o "$REPORT_DIR/infamy_report.txt"
python3 budget_report.py "$SAVE_FILE" -o "$REPORT_DIR/budget_report.txt" 
python3 companies_report.py "$SAVE_FILE" -o "$REPORT_DIR/companies_report.txt"

# 6b. Company Profit Report
echo "💰 Generating company profit report..."
python3 company_profit_report.py "$SAVE_FILE" > "$REPORT_DIR/company_profit_report.txt"
python3 company_profit_report.py "$SAVE_FILE" --humans > "$REPORT_DIR/company_profit_humans.txt"

# 6c. Interest Groups Report
echo "🏛️  Generating interest groups report..."
python3 nations_ig.py "$SAVE_FILE" -o "$REPORT_DIR/interest_groups.txt"

# 6d. Ruler Report
echo "👑 Generating ruler report..."
python3 ruler_report.py "$SAVE_FILE" -o "$REPORT_DIR/ruler_report.txt"

# 7. Law Reports
echo "⚖️  Generating comprehensive law report..."
python3 law_report_comprehensive.py "$SAVE_FILE" --humans -o "$REPORT_DIR/laws_comprehensive.txt"

# 8. Power Bloc Report
echo "🤝 Generating power bloc report..."
python3 power_bloc_report.py "$SAVE_FILE" -o "$REPORT_DIR/power_blocs.txt"

# 9. Migration Report
echo "🌍 Generating migration attraction report..."
python3 migration_report.py "$SAVE_FILE" --humans -o "$REPORT_DIR/migration_report.txt"

# 10. Goods Production Report
echo "🏭 Generating goods production report..."
python3 nation_goods_production.py "$SAVE_FILE" -o "$REPORT_DIR/goods_production.txt"

# 10a. Goods Production Treemaps (Human Countries)
echo "📊 Generating goods production treemaps (human countries)..."
python3 goods_treemap_combined.py "$SAVE_FILE" -o "$REPORT_DIR/goods_treemap_humans"

# 10b. Goods Production Treemaps (Global)
echo "🌍 Generating goods production treemaps (global)..."
source venv/bin/activate && python goods_treemap_powerbloc.py "$SAVE_FILE" -o "$REPORT_DIR/goods_treemap_global"

# 11. War Analysis Reports
echo "⚔️  Generating war and battle analysis reports..."
python3 war_report.py "$SAVE_FILE" -o "$REPORT_DIR/war_report.txt"
python3 battle_history.py "$SAVE_FILE" -o "$REPORT_DIR/battle_history.txt"
python3 war_stats.py "$SAVE_FILE" -o "$REPORT_DIR/war_statistics.txt"
python3 diplomatic_plays.py "$SAVE_FILE" -o "$REPORT_DIR/diplomatic_tensions.txt"

# 12. Foreign Ownership Reports
echo "🌍 Generating foreign ownership reports..."

# Super simple version
echo "  • Simple building ownership totals..."
python3 super_simple_foreign_report.py "$SAVE_FILE" --humans -o "$REPORT_DIR/foreign_ownership_simple.txt"

# Detailed building types
echo "  • Detailed building ownership..."
python3 detailed_foreign_buildings.py "$SAVE_FILE" --humans -o "$REPORT_DIR/foreign_ownership_detailed.txt"

# By entity type
echo "  • Ownership by entity type..."
python3 ownership_by_entity.py "$SAVE_FILE" --humans -o "$REPORT_DIR/foreign_ownership_by_entity.txt"

# Full GDP-based analysis
echo "  • Full GDP-based foreign ownership..."
python3 foreign_ownership_report.py "$SAVE_FILE" --humans -o "$REPORT_DIR/foreign_ownership_full.txt"

# True GDP analysis (most accurate)
echo "  • True GDP-based analysis (most accurate)..."
python3 true_gdp_ownership.py "$SAVE_FILE" --humans -o "$REPORT_DIR/foreign_ownership_true_gdp.txt"

# Effective GDP analysis
echo "  • Effective GDP analysis (total economic control)..."
python3 effective_gdp_report.py "$SAVE_FILE" --humans -o "$REPORT_DIR/effective_gdp.txt"

# 12. Session Comparison Reports (if comparison file provided or previous session exists)
echo ""
echo "📊 Generating session comparison reports..."

# Create comparison subdirectory
COMPARISON_DIR="$REPORT_DIR/comparison"
mkdir -p "$COMPARISON_DIR"

# Use provided comparison file or find previous session
if [ -n "$COMPARISON_FILE" ]; then
    # Use the explicitly provided comparison file
    PREV_SESSION="$COMPARISON_FILE"
else
    # Find previous session by date
    PREV_SESSION=$(find extracted-saves -name "*_extracted.json" -type f ! -path "$SAVE_FILE" -exec stat -f "%m %N" {} \; | sort -n -r | head -1 | cut -d' ' -f2-)
fi

if [ -n "$PREV_SESSION" ] && [ "$PREV_SESSION" != "$SAVE_FILE" ]; then
    echo "  Comparing with: $(basename "$PREV_SESSION")"
    
    # Check if comparison file exists
    if [ ! -f "$PREV_SESSION" ]; then
        echo "  ⚠️  Warning: Comparison file not found: $PREV_SESSION"
    else
        # New comprehensive comparison with all metrics
        echo "  • Generating comprehensive comparison (all metrics)..."
        python3 session_comparison_comprehensive.py "$PREV_SESSION" "$SAVE_FILE" -o "$COMPARISON_DIR/full_comparison.txt"
        
        # Legacy comparisons for backward compatibility
        echo "  • Generating GDP comparison..."
        python3 session_comparison.py "$PREV_SESSION" "$SAVE_FILE" -o "$COMPARISON_DIR/gdp_comparison.txt"
        
        # Construction comparison
        echo "  • Generating construction comparison..."
        python3 session_comparison.py "$PREV_SESSION" "$SAVE_FILE" -m construction -o "$COMPARISON_DIR/construction_comparison.txt"
        
        # Effective GDP comparison
        echo "  • Generating effective GDP comparison..."
        python3 session_comparison.py "$PREV_SESSION" "$SAVE_FILE" -m effective_gdp -o "$COMPARISON_DIR/effective_gdp_comparison.txt"
        
        # Military score comparison
        echo "  • Generating military score comparison..."
        python3 session_comparison.py "$PREV_SESSION" "$SAVE_FILE" -m military -o "$COMPARISON_DIR/military_comparison.txt"
        
        # Company profit comparison
        echo "  • Generating company profit comparison..."
        python3 company_comparison.py "$PREV_SESSION" "$SAVE_FILE" -o "$COMPARISON_DIR/company_comparison.txt"
        
        # Ruler comparison
        echo "  • Generating ruler comparison..."
        python3 ruler_comparison.py "$PREV_SESSION" "$SAVE_FILE" -o "$COMPARISON_DIR/ruler_comparison.txt"
        
        echo "  ✅ Session comparisons complete!"
    fi
else
    echo "  ⚠️  No comparison session available"
fi

# 13. Generate HTML Report Viewer
echo ""
echo "🌐 Generating HTML report viewer..."
python3 html_report_generator.py "$REPORT_DIR"

echo ""
echo "✅ All reports generated successfully!"
echo "📁 Reports saved to: $REPORT_DIR"
echo ""
echo "Generated files:"
ls -la "$REPORT_DIR" | grep -v "^total" | awk '{print "  " $9 " (" $5 " bytes)"}'
echo ""
echo "🔍 Quick summary:"
echo "  • GDP data: gdp_report.csv, gdp_timeseries.csv"
echo "  • GDP visualizations: gdp_chart.png, gdp_chart_log.png, gdp_treemap.png/.html"
echo "  • Population data: population_report.txt, population_timeseries.csv"
echo "  • Population visualizations: population_chart.png, population_chart_log.png, population_treemap.png/.html"
echo "  • Military visualizations: military_treemap.png, army_treemap.png, navy_treemap.png"
echo "  • Standard of living: sol_report.txt"
echo "  • Literacy: literacy_report.txt"
echo "  • Prestige: prestige_report.txt"
echo "  • Military: military_score_report.txt (unit-based), power_projection_report.txt (manpower-based)"
echo "  • Analysis: construction_report.txt, infamy_report.txt, budget_report.txt, companies_report.txt, company_profit_report.txt"  
echo "  • Interest Groups: interest_groups.txt (political composition and clout)"
echo "  • Rulers: ruler_report.txt (ruler names, ages, interest groups, and traits)"
echo "  • Laws: laws_comprehensive.txt (all 23 law categories)"
echo "  • Diplomacy: power_blocs.txt"
echo "  • Migration: migration_report.txt"
echo "  • Goods Production: goods_production.txt (production rankings by good type)"
echo "  • Goods Treemaps: goods_treemap_humans_*.png (human countries) and goods_treemap_global_*.png (all major producers)"
echo "  • War Analysis: war_report.txt, battle_history.txt, war_statistics.txt, diplomatic_tensions.txt"
echo "  • Foreign ownership: foreign_ownership_*.txt (5 different analyses)"
echo "  • Effective GDP: effective_gdp.txt (total economic control per country)"
echo "  • Session comparisons: comparison/ subdirectory (if previous session exists)"
echo "  • HTML Report: web/index.html (open in browser for interactive viewing)"
echo ""
echo "💡 Tip: Use 'open $REPORT_DIR' to view all files in Finder (macOS)"
echo "💡 Tip: Use 'open $REPORT_DIR/web/index.html' to view the HTML report in your browser"