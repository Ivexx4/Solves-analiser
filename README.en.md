# Speedcubing Analysis Dashboard

An interactive Streamlit dashboard for exploring solve times, penalties,
consistency, training sessions, and long-term performance. Charts are built
with Plotly and support hover details, zooming, and interactive legends.

Portuguese documentation: [README.md](README.md).

## Requirements

- Python 3.10 or newer
- Streamlit
- pandas
- NumPy
- Plotly
- statsmodels (used for the trend line in “Speed vs Consistency”)

Install the dependencies with:

```powershell
python -m pip install -r requirements.txt
```

## Run locally

Start the app from the project directory:

```powershell
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Import data

The dashboard starts empty and provides an import screen. Use the **Language /
Idioma** selector to switch between Portuguese and English. Upload one or more
of these Cubolandia Timer or CS Timer exports, then click **Import solves**:

- Cubolandia Timer singles JSON.
- Cubolandia Timer averages JSON. The five component solves are extracted from
  each Ao5 record.
- CS Timer `.txt` or `.json` export.

Each import appends solves to the current Streamlit session. Duplicate detection compares scramble, time rounded to hundredths, and penalty
rather than date/time, which can be shared by different solves. Solves without
a scramble are kept because they cannot be reliably identified as duplicates.
If data was already loaded before this change, clear it and re-import the files
to include scrambles. The import summary reports new solves and removed
duplicates. Use **Clear imported data** to start a new history.

Imported data is kept in the current Streamlit session; it is not persisted
after the session or server ends. Parsed upload data is cached by file content
in the running process (up to 10 distinct file combinations). No local exports
are loaded automatically.

## Supported export formats

- Cubolandia Timer singles JSON: a list of records with `i` (date/time), `n`
  (time in seconds; `-1` means DNF), `s` (scramble), and `t` (penalty: `0`
  clean, `1` +2, `2` DNF).
- Cubolandia Timer averages JSON: a list of records with `i` (date/time) and
  `s` (the five component scrambles) and `c` (text containing the five Ao5
  component solves, including cut times, +2s, and DNFs).
- CS Timer export: JSON object containing `sessionN` arrays. Each solve uses
  the format `[[penalty, time_ms], scramble, comment, timestamp]`. Times are
  converted from milliseconds to seconds; +2 penalties and DNFs are supported.

The optional `carregamento_dados.py` module exposes `load_singles()`,
`load_averages()`, `load_cstimer()`, and `combine_solves()` for independent
loading and processing. To create a consolidated CSV for external analysis:

```powershell
.\.venv\Scripts\python.exe carregamento_dados.py
```

## Filters and calculations

The date filter applies to charts and analyses. Most dashboard metrics use
solves inside the selected range. The “Best Ao5” and “Best Ao12” headline
metrics are exceptions and are calculated across the complete imported history.

Time-based analyses use only finite solve times. DNF records can still count
toward total solves, penalties, sessions, and daily solve counts, as described
by each analysis.

- Ao5 and Ao12 use the WCA trim: remove the best and worst time from each
  window, then average the remaining times.
- Ao100 and Ao1000 are simple rolling arithmetic means.
- Moving averages normally appear only after a complete window is available.
- Consistency uses the coefficient of variation (standard deviation divided by
  mean, multiplied by 100) to compare relative variability across different
  average speeds. A lower CV indicates better relative consistency.
- PB analyses detect records within the selected date range. The first valid
  time is the baseline, not a new PB, so changing the start date may change PB
  counts.
- “PB probability” is an observed historical frequency, not a forecast for the
  next solve.
- Session duration is the interval between the first and last solve in a
  session; the break before the next session is excluded. A new session begins
  after more than 30 minutes without a solve.

## Analysis navigation

Choose a category tab, then select a chart from its **Chart** dropdown:

### Performance and Records

- **Time Evolution** — individual solves by penalty with Ao5/Ao12 moving averages.
- **Distribution** — histogram and box plot of valid solve times.
- **PB Progression** — cumulative personal best.
- **Overall Average** — cumulative mean and cumulative PB.
- **PB Frequency** — new PBs per month, latest PB, and average days between PBs.
- **PB Probability** — PB frequency over the latest 100, 500, and 1000 solves,
  plus a 100-solve rolling frequency.
- **Ao100 / Ao1000** — simple rolling averages compared with Ao5 and Ao12.

### Consistency

- **Monthly Consistency** — monthly box plots.
- **Consistency** — rolling coefficient of variation over 50 solves.
- **Percentiles** — rolling 10th, 50th, and 90th percentiles over 100 solves.
- **Speed vs Consistency** — rolling mean and relative variability over 50
  solves, with chronological color and path.
- **Warm-up** — compares the first and last 10 solves in sessions with at least
  20 valid solve times.
- **Fatigue** — average time by session progress block.
- **Control Chart** — solve times, 100-solve rolling mean, and rolling ±1/±2
  standard-deviation limits.

### Practice and Sessions

- **Sub-X Rate** — rolling share of solve times at or below the selected target.
- **Solves per Day** — daily solve counts and a seven-day moving average.
- **Sessions** — session summary table, best and longest session, average session
  size, and a size/performance/duration scatter plot. DNFs count toward session
  size but are excluded from time statistics.

### Penalties and Timing

- **Penalties** — counts of clean, +2, and DNF solves.
- **Time of Day** — solve-time distributions by hour.
- **Hour × Day** — heatmaps of average solve time and solve count by hour and
  weekday.
