# Lichess Opening Analyzer

Find opening moves you repeatedly play that score worse than common alternatives in the Lichess Opening Explorer for players around your rating and preferred time controls.

The first version focuses on one question:

> Which opening moves do I repeatedly play that score noticeably worse than the strongest common alternatives for players around my rating and preferred time controls?

## Install

```bash
python -m pip install -e .
```


## Step-by-step setup

These commands assume you have Git and Python 3.10+ installed. Replace `YOUR_GITHUB_NAME` and `YOUR_LICHESS_USERNAME` with your actual account names.

1. Clone the repository from GitHub:

   ```bash
   git clone https://github.com/YOUR_GITHUB_NAME/lichess-opening-analyzer.git
   cd lichess-opening-analyzer
   ```

2. Create and activate a virtual environment:

   macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Windows PowerShell:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the tool into that environment:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -e .
   ```

4. Run the analyzer. For example, to analyze your last 1,000 rapid/classical games as both colors around the 1800-2200 rating range:

   ```bash
   lichess-opening-analyzer \
     --username YOUR_LICHESS_USERNAME \
     --max-games 1000 \
     --color both \
     --max-fullmove 12 \
     --ratings 1800 2000 2200 \
     --speeds rapid classical \
     --min-own-occurrences 3 \
     --min-explorer-games 1000 \
     --min-move-games 100 \
     --sort impact \
     --output reports/opening_leaks.md
   ```

5. Open the generated report:

   ```bash
   open reports/opening_leaks.md
   ```

   On Windows, use:

   ```powershell
   start reports/opening_leaks.md
   ```

### Sample commands

If your Lichess username is `myLichessName`, run:

```bash
lichess-opening-analyzer --username myLichessName --max-games 1000 --color both --ratings 1800 2000 2200 --speeds rapid classical --sort impact --output reports/opening_leaks.md
```

Analyze only games where you had the black pieces:

```bash
lichess-opening-analyzer --username myLichessName --max-games 1000 --color black --ratings 1800 2000 2200 --speeds rapid classical --output reports/black_opening_leaks.md
```

Analyze games played since January 1, 2025:

```bash
lichess-opening-analyzer --username myLichessName --since 2025-01-01 --color both --ratings 1800 2000 2200 --speeds rapid classical --output reports/recent_opening_leaks.md
```

## Quick start from a Lichess download

```bash
lichess-opening-analyzer \
  --username your_lichess_name \
  --max-games 1000 \
  --color both \
  --max-fullmove 12 \
  --ratings 1800 2000 2200 \
  --speeds rapid classical \
  --output reports/opening_leaks.md
```

The command downloads recent games if `--pgn` is not supplied, parses them with `python-chess`, aggregates positions where you made a move in the first 10-12 moves, queries the Lichess Opening Explorer once per unique position, and writes a report.

## Analyze an existing PGN export

```bash
lichess-opening-analyzer \
  --username your_lichess_name \
  --pgn ~/Downloads/lichess_games.pgn \
  --color black \
  --since 2025-01-01 \
  --ratings 1800 2000 2200 \
  --speeds rapid classical \
  --sort impact \
  --format csv \
  --output reports/black_opening_leaks.csv
```

`--since` and `--until` only apply when the tool downloads games. Use Lichess export filters if you provide your own PGN.

## Important options

- `--color white|black|both`: restrict the analysis to games where you played one side.
- `--max-games`: limit downloaded game history.
- `--since` / `--until`: limit downloaded games by ISO date.
- `--max-fullmove`: default `12`, keeping the analysis in the opening phase.
- `--min-own-occurrences`: default `3`, so one-off moves are ignored.
- `--min-explorer-games`: default `1000`, minimum Explorer database games for the position.
- `--min-move-games`: default `100`, minimum Explorer games for each move being compared.
- `--ratings`: Lichess Explorer rating buckets, such as `1800 2000 2200`.
- `--speeds`: Lichess speed filters, such as `rapid classical`.
- `--cache`: SQLite cache path for Explorer API responses.
- `--sort delta|impact`: sort by largest score deficit or by frequency × deficit.

## Output

Markdown reports contain columns like:

| Move Played | Times | Explorer Score | Best Alternative | Best Score | Delta | Impact | Explorer Games |
|---|---:|---:|---|---:|---:|---:|---:|
| ...Be7 | 24 | 46.0% | ...c5 | 55.0% | -9.0% | 2.16 | 123456 |

Score is computed from the perspective of the side you played: wins plus half draws divided by total games.

## Notes

- The tool intentionally limits analysis to early moves because deeper Explorer results increasingly reflect middlegame skill rather than opening move quality.
- API responses are cached locally in SQLite so repeated runs avoid unnecessary Lichess Opening Explorer requests.
- Future versions could add Stockfish evaluation, repertoire branch grouping, and visual summaries.
