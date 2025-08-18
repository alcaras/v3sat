# Victoria 3 Save Analysis Tools (V3SAT)

A collection of tools for analyzing Victoria 3 save files. These scripts help convert save files from compressed binary format to JSON and generate various reports and visualizations.

**Note:** This is a community project and many scripts are still work-in-progress. Results should be considered estimates and may not perfectly match in-game values.

## Quick Start

1. **Download Rakaly**: Download the Rakaly CLI binary for your platform from [https://github.com/rakaly/cli/releases](https://github.com/rakaly/cli/releases)
   - Create a `rakaly/` directory in this folder
   - Download the appropriate file for your platform:
     - **Windows**: `rakaly-x86_64-pc-windows-msvc.zip` (extract `rakaly.exe`)
     - **macOS**: `rakaly-x86_64-apple-darwin.tar.gz` (extract `rakaly`)
     - **Linux**: `rakaly-x86_64-unknown-linux-musl.tar.gz` (extract `rakaly`)
   - Place the binary in the `rakaly/` directory
   - On macOS/Linux, make it executable: `chmod +x rakaly/rakaly`

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
- **GDP Reports**: Current rankings and historical time series
- **GDP Visualizations**: Charts using Victoria 3 country colors
- **GDP Treemaps**: Visualization by power blocs with colonial relationships

### 👥 Population & Social Analysis
- **Population Reports**: Demographics and growth trends
- **Standard of Living**: Attempts to extract quality of life metrics (may not match in-game values)
- **Literacy Analysis**: Education levels and development
- **Migration**: Population movement and attraction patterns

### ⚔️ Military Analysis
- **Military Power**: Unit-based scoring for army and navy strength
- **Power Projection**: Approximation of military capacity (does not match in-game power projection exactly)
- **Military Treemaps**: Visual comparison of total, army, and navy power
- **War Reports**: Battle tracking (still in development)
- **Diplomatic Plays**: Analysis of diplomatic tensions (work in progress)

### 🏛️ Political & Diplomatic Analysis
- **Interest Groups**: Political composition and clout distribution
- **Rulers**: Leader information, ages, traits, and succession tracking
- **Laws**: Comprehensive analysis of all 23 law categories
- **Power Blocs**: Alliance membership, principles, and economic power

### 🏭 Economic Deep Dive
- **Foreign Ownership**: Estimated cross-border investments (calculated approximations, hard to verify against game)
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
├── icons/              # Victoria 3 goods and market icons (optional, for enhanced visualizations)
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
- **Rakaly CLI binary**: Download from [https://github.com/rakaly/cli/releases](https://github.com/rakaly/cli/releases)
- **Victoria 3 game data**: Copy from your Victoria 3 installation (see setup above)
- **Python packages**: 
  - matplotlib, pandas (for basic charts)
  - plotly, kaleido (for interactive treemaps - run `pip install plotly kaleido`)
  - squarify (for simple treemaps - run `pip install squarify`)

## Known Limitations

- **Battle History & Diplomatic Plays**: Still under development
- **Power Projection**: Our approximation doesn't match the in-game calculation exactly
- **Standard of Living**: Extracted values may differ from what's shown in-game
- **Foreign Ownership**: All foreign GDP ownership numbers are estimates/calculations. While they seem directionally correct, they're difficult to verify against the game since there's no easy way to see these stats in Victoria 3
- **GDP Sampling**: Victoria 3 samples GDP data every 7 days (not 28 as the data structure suggests)
- **Multiplayer Saves**: GDP history may be lost when players leave/rejoin in multiplayer games

## Contributing

This toolset analyzes Victoria 3's save file format using [Rakaly CLI](https://github.com/rakaly/cli) for binary-to-JSON conversion. Game data definitions must be copied from your Victoria 3 installation.

For questions or improvements, ensure you have the required game data directories from your Victoria 3 installation.