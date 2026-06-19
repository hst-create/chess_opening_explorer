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

The command downloads recent games if `--pgn` is not supplied, parses them with `python-chess`, aggregates positions where you made a move in the first 10-12 moves, skips the first three half-moves by default, queries the Lichess Opening Explorer once per unique filtered position, and writes a report.

To reuse games you already downloaded instead of fetching again, pass the saved PGN with `--pgn` and omit `--max-games` unless you are downloading a new file:

```bash
lichess-opening-analyzer \
  --username your_lichess_name \
  --pgn data/games.pgn \
  --color both \
  --ratings 1800 2000 2200 \
  --speeds rapid classical \
  --sort impact \
  --output reports/opening_leaks.md
```

## Authenticated Lichess access

Public game exports usually do not require authentication, but the Lichess Opening Explorer requires authentication. If Lichess returns `401 Unauthorized` or `403 Forbidden` while downloading games or querying Explorer, create a Lichess personal access token and either pass it directly or expose it as an environment variable:

```bash
export LICHESS_TOKEN=lip_your_token_here
lichess-opening-analyzer --username your_lichess_name --max-games 1000 --color both
```

Or pass the token for one command. The same `--lichess-token` value is used for both game downloads and Opening Explorer lookups:

```bash
lichess-opening-analyzer --username your_lichess_name --lichess-token lip_your_token_here --max-games 1000 --color both
```

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
- `--min-ply`: default `4`, so the first three half-moves are ignored before querying Explorer. Use `--min-ply 1` to include every move.
- `--include-line`: only report SAN lines containing the given text. Repeat it to whitelist multiple repertoire branches.
- `--exclude-line`: hide SAN lines containing the given text. Repeat it to blacklist stale repertoire branches such as an opening you no longer play.
- `--min-explorer-games`: default `1000`, minimum Explorer database games for the position.
- `--min-move-games`: default `100`, minimum Explorer games for each move being compared.
- `--ratings`: Lichess Explorer rating buckets, such as `1800 2000 2200`.
- `--speeds`: Lichess speed filters, such as `rapid classical`.
- `--cache`: SQLite cache path for Explorer API responses.
- `--sort delta|impact`: sort by largest score deficit or by frequency × deficit.

Line filters match text in the report's SAN `Line` value, case-insensitively. For example, to hide Open Sicilian structures while keeping other `1. e4` openings:

```bash
lichess-opening-analyzer \
  --username your_lichess_name \
  --pgn data/games.pgn \
  --include-line "1. e4" \
  --exclude-line "c5 2. Nf3 d6 3. d4" \
  --output reports/e4_without_open_sicilian.md
```


## Progress and runtime estimates

By default, the analyzer now writes progress updates to stderr while it works. It announces the download and PGN parsing phases, reports how many unique opening move candidates were found, and then prints Lichess Explorer query progress with elapsed time and an estimated time remaining. Use `--quiet` if you only want the final summary.

Runtime depends mostly on the number of repeated unique positions that pass `--min-own-occurrences`, because each one may need a Lichess Opening Explorer lookup. Cached positions are much faster on repeated runs. As a rough planning guide on a normal home connection:

| Download / analyzed games | Typical repeated Explorer candidates | First uncached run | Cached rerun |
|---:|---:|---:|---:|
| 100 games | 10-50 | under 1 minute | a few seconds |
| 1,000 games | 100-500 | 2-10 minutes | under 1 minute |
| 5,000 games | 500-2,000 | 10-40 minutes | 1-5 minutes |
| 10,000+ games | 1,000-4,000+ | 20-90+ minutes | a few minutes |

These are estimates, not guarantees: Lichess API latency, network speed, cache warmth, `--max-fullmove`, `--color`, and `--min-own-occurrences` can change the totals substantially. If a run appears slow, check the `Explorer queries: current/total` line to see whether it is still advancing.

## Output

Markdown reports contain columns like:

| Line | Move Played | Times | Explorer Score | Best Alternative | Best Score | Delta | Impact | Explorer Games | Analysis |
|---|---|---:|---:|---|---:|---:|---:|---:|---|
| 1. e4 e5 2. Nf3 Nf6 3. d4 exd4 4. Nxd4 Be7 | Be7 | 24 | 46.0% | c5 | 55.0% | -9.0% | 2.16 | 123456 | Lichess |

The `Line` column shows the SAN move sequence through the repeated move, and `Analysis` links to a Lichess analysis board for the position before that move. Score is computed from the perspective of the side you played: wins plus half draws divided by total games.

## Notes

- The tool intentionally limits analysis to early moves because deeper Explorer results increasingly reflect middlegame skill rather than opening move quality.
- API responses are cached locally in SQLite so repeated runs avoid unnecessary Lichess Opening Explorer requests. Opening Explorer requests use `--lichess-token` or `LICHESS_TOKEN` when provided.
- Future versions could add Stockfish evaluation, repertoire branch grouping, and visual summaries.
