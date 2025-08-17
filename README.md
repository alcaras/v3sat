# Victoria 3 Save Analysis Tools (V3SAT)

A comprehensive suite of tools for analyzing Victoria 3 save files, converting them from compressed binary format to JSON for easier analysis and generating detailed reports and visualizations.

## Quick Start

1. **Download Rakaly**: Download the Rakaly binary for your platform from [https://github.com/rakaly/librakaly](https://github.com/rakaly/librakaly)
   - Create a `rakaly/` directory in this folder
   - Place the `rakaly` binary inside (make sure it's executable: `chmod +x rakaly/rakaly`)

2. **Copy Victoria 3 game data**: Copy these directories from your Victoria 3 installation to this folder:
   - `common/` (from `Victoria 3/game/common/`)
   - `events/` (from `Victoria 3/game/events/`)  
   - `localization/` (from `Victoria 3/game/localization/`)
   
   **Where to find your Victoria 3 installation:**
   - **Steam (Windows)**: `C:\Program Files (x86)\Steam\steamapps\common\Victoria 3\game\`
   - **Steam (macOS)**: `~/Library/Application Support/Steam/steamapps/common/Victoria 3/game/`
   - **Steam (Linux)**: `~/.steam/steam/steamapps/common/Victoria 3/game/`
   - **Game Pass**: `C:\XboxGames\Victoria 3\Content\game\`

3. **Place your save files**: Copy your Victoria 3 save files (`.v3` files) into the `save-files/` directory

4. **Extract a save file**:
   ```bash
   python3 extract_save.py "YourSaveFile.v3"
   ```

5. **Generate all reports**:
   ```bash
   ./run_all_reports.sh
   ```

That's it! All reports will be generated in a timestamped directory under `reports/`.

## Features

### 🏆 Core Economic Analysis
- **GDP Reports**: Current rankings and full historical time series
- **GDP Visualizations**: Beautiful charts with authentic Victoria 3 colors
- **GDP Treemaps**: Hierarchical visualization by power blocs with colonial relationships
- **Effective GDP**: Total economic control including foreign ownership

### 👥 Population & Social Analysis
- **Population Reports**: Demographics and growth trends
- **Standard of Living**: Quality of life metrics across nations
- **Literacy Analysis**: Education levels and development
- **Migration**: Population movement and attraction patterns

### ⚔️ Military Analysis
- **Military Power**: Unit-based scoring for army and navy strength
- **Power Projection**: Manpower-based military capacity
- **Military Treemaps**: Visual comparison of total, army, and navy power
- **War Reports**: Battle history, statistics, and diplomatic tensions

### 🏛️ Political & Diplomatic Analysis
- **Interest Groups**: Political composition and clout distribution
- **Rulers**: Leader information, ages, traits, and succession tracking
- **Laws**: Comprehensive analysis of all 23 law categories
- **Power Blocs**: Alliance membership, principles, and economic power

### 🏭 Economic Deep Dive
- **Foreign Ownership**: Cross-border investment analysis (5 different methodologies)
- **Company Analysis**: Profitability and ownership patterns
- **Goods Production**: Production rankings and treemap visualizations
- **Construction**: Infrastructure development tracking

### 📊 Session Comparison
- **Growth Analysis**: Compare metrics between different saves
- **Ruler Changes**: Track succession and political shifts
- **Economic Development**: Analyze growth patterns over time

## Directory Structure

```
v3sat/
├── save-files/          # Place your .v3 save files here
├── extracted-saves/     # JSON files created by extraction
├── reports/            # Generated analysis reports
├── rakaly/             # Rakaly binary (download separately)
├── common/             # Victoria 3 game data files (copy from game)
├── events/             # Victoria 3 event definitions (copy from game)
├── localization/       # Game localization files (copy from game)
├── humans.txt          # List of human-controlled countries
└── *.py                # Analysis scripts
```

## Configuration

### Human Countries Tracking
Edit `humans.txt` to specify which countries are human-controlled. This filters many reports to focus on player nations:

```
GBR
USA
FRA
ITA
# Add your player countries here
```

## Requirements

- **Python 3.x**
- **Rakaly binary**: Download from [https://github.com/rakaly/librakaly](https://github.com/rakaly/librakaly)
- **Victoria 3 game data**: Copy from your Victoria 3 installation (see setup above)
- **Python packages**: 
  - matplotlib, pandas (for basic charts)
  - plotly, kaleido (for interactive treemaps - run `pip install plotly kaleido`)
  - squarify (for simple treemaps - run `pip install squarify`)

## Understanding the Data

### GDP Sampling
Victoria 3 samples GDP data **every 7 days**, not the 28 days shown in the data structure. Our tools use the correct 7-day sampling for accurate historical reconstruction.

### Multiplayer Bug Handling
Victoria 3 has a bug where GDP history is lost when players leave/rejoin. Use the `--session3` parameter in gdp_timeseries.py to merge data from previous saves when needed.

### Foreign Ownership
We provide 5 different foreign ownership analysis methods:
- **Simple**: Basic building counts
- **Detailed**: By building types
- **By Entity**: Companies vs other ownership types
- **Full GDP**: GDP-weighted analysis
- **True GDP**: Most accurate using Victoria 3's actual formula

## Data Accuracy

Our tools have been validated against Victoria 3's internal calculations:
- ✅ GDP calculations match the game's formula exactly
- ✅ Military scoring uses actual unit statistics
- ✅ Time series data validated across multiple save files
- ✅ Foreign ownership percentages confirmed accurate

## Troubleshooting

**"rakaly not found"**: Download Rakaly binary and place in `rakaly/rakaly`
**"No save files found"**: Place `.v3` files in `save-files/` directory
**"Permission denied"**: Make sure rakaly binary is executable (`chmod +x rakaly/rakaly`)
**"Module not found"**: Install required Python packages (`pip install plotly kaleido squarify`)
**"Game data not found"**: Copy `common/`, `events/`, and `localization/` directories from your Victoria 3 installation

## Contributing

This toolset analyzes Victoria 3's save file format using [Rakaly](https://github.com/rakaly/librakaly) for binary-to-JSON conversion. Game data definitions must be copied from your Victoria 3 installation.

For questions or improvements, ensure you have the required game data directories from your Victoria 3 installation.