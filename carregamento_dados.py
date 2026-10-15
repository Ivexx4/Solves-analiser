"""Load Cubolandia Timer singles and Ao5 exports into the dashboard schema."""

import json
import re
from io import BytesIO, IOBase
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
SINGLES_FILE = PROJECT_DIR / "data_Cubo3x3x3Normal.json"
AVERAGES_FILE = PROJECT_DIR / "data_Cubo3x3x3NormalAVG.json"
TIME_PATTERN = re.compile(r"\(?(?:DNF|\d+(?::\d+)?\.\d+\+?)\)?")
TIME_LINE_PATTERN = re.compile(r"^\(?\s*(?:DNF|\d+(?::\d+)?\.\d+\+?)\s*\)?$")
AO5_SINGLE_PATTERN = re.compile(r"\([1-5]\)$")


def parse_time(value: str) -> float:
    """Convert a Cubolandia time such as ``1:12.34`` or ``34.56`` to seconds."""
    if ":" in value:
        minutes, seconds = value.split(":", maxsplit=1)
        return int(minutes) * 60 + float(seconds)
    return float(value)


def _read_json(source: str | Path | BinaryIO):
    if isinstance(source, (str, Path)):
        with Path(source).open("r", encoding="utf-8") as export_file:
            return json.load(export_file)
    elif isinstance(source, IOBase) or (
        hasattr(source, "read") and hasattr(source, "seek")
    ):
        source.seek(0)
        return json.load(source)
    else:
        raise TypeError("A origem deve ser um caminho ou um ficheiro JSON aberto.")


def _read_bytes(source: str | Path | BinaryIO) -> bytes:
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    if isinstance(source, IOBase) or (
        hasattr(source, "read") and hasattr(source, "seek")
    ):
        source.seek(0)
        content = source.read()
        if isinstance(content, str):
            return content.encode("utf-8")
        return content
    raise TypeError("A origem deve ser um caminho ou um ficheiro aberto.")


def _read_export(source: str | Path | BinaryIO) -> list[dict]:
    data = _read_json(source)
    if not isinstance(data, list):
        raise ValueError("O ficheiro de exportação deve conter uma lista JSON.")
    return data


def detect_export_format(source: str | Path | BinaryIO) -> str:
    """Identify a supported timer export from its content."""
    content = _read_bytes(source)
    text = content.decode("utf-8-sig")
    first_character = text.lstrip()[:1]
    if first_character not in ("{", "["):
        try:
            columns = pd.read_csv(BytesIO(content), sep=None, engine="python", nrows=0).columns
        except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
            raise ValueError("O ficheiro não é um CSV válido.") from error
        normalized_columns = {str(column).strip().casefold() for column in columns}
        if {"time", "scramble", "date"}.issubset(normalized_columns):
            return "cstimer_csv"
        raise ValueError("Formato CSV não reconhecido como exportação CS Timer.")

    data = json.loads(text)
    if isinstance(data, dict):
        if any(
            re.fullmatch(r"session\d+", key)
            and isinstance(solves, list)
            for key, solves in data.items()
        ):
            return "cstimer"
        raise ValueError("Objeto JSON não reconhecido como exportação do CS Timer.")

    if not isinstance(data, list) or not data:
        raise ValueError("A exportação JSON deve conter registos numa lista.")
    if not all(
        isinstance(record, dict)
        and {"i", "n", "s", "t", "c"}.issubset(record)
        for record in data
    ):
        raise ValueError("Formato JSON não reconhecido como exportação Cubolandia ou CS Timer.")

    average_records = [
        record for record in data
        if isinstance(record.get("c"), str) and record["c"].strip()
    ]
    if not average_records:
        return "singles"
    if all(len(TIME_PATTERN.findall(record["c"])) == 5 for record in average_records):
        return "averages"
    if all(record["c"].strip().startswith("Avg:") for record in average_records):
        return "singles"
    raise ValueError(
        "O ficheiro tem estrutura Cubolandia, mas não foi possível confirmar "
        "se contém singles ou averages."
    )


def load_cstimer_csv(source: str | Path | BinaryIO) -> pd.DataFrame:
    """Load CS Timer CSV exports with time, scramble, and date columns."""
    content = _read_bytes(source)
    try:
        data = pd.read_csv(BytesIO(content), sep=None, engine="python")
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
        raise ValueError("Não foi possível ler o CSV do CS Timer.") from error

    column_lookup = {
        str(column).strip().casefold(): column
        for column in data.columns
    }
    required_columns = {"time", "scramble", "date"}
    if not required_columns.issubset(column_lookup):
        raise ValueError(
            "O CSV do CS Timer deve conter as colunas Time, Scramble e Date."
        )

    solves = []
    for row_number, row in data.iterrows():
        raw_time = str(row[column_lookup["time"]]).strip()
        if not raw_time or raw_time.casefold() in {"nan", "none"}:
            raise ValueError(f"Tempo em falta na linha {row_number + 2} do CSV.")
        if raw_time.upper().startswith("DNF"):
            time, penalty = np.inf, 2
        else:
            penalty = int(raw_time.endswith("+"))
            normalized_time = raw_time[:-1].strip() if penalty else raw_time
            try:
                time = parse_time(normalized_time)
            except ValueError as error:
                raise ValueError(
                    f"Tempo inválido na linha {row_number + 2} do CSV: {raw_time}"
                ) from error

        raw_date = row[column_lookup["date"]]
        date = pd.to_datetime(raw_date, errors="coerce")
        if pd.isna(date):
            raise ValueError(
                f"Data inválida na linha {row_number + 2} do CSV: {raw_date}"
            )

        raw_scramble = row[column_lookup["scramble"]]
        scramble = "" if pd.isna(raw_scramble) else str(raw_scramble)
        solves.append({
            "date": date,
            "time": time,
            "penalty": penalty,
            "scramble": scramble,
        })

    if not solves:
        raise ValueError("O CSV do CS Timer não contém solves.")
    return pd.DataFrame(solves, columns=["date", "time", "penalty", "scramble"])


def load_singles(path: str | Path | BinaryIO = SINGLES_FILE) -> pd.DataFrame:
    """Load individual solves, excluding component solves already supplied by Ao5."""
    singles = []
    for solve in _read_export(path):
        timestamp = str(solve["i"])
        if AO5_SINGLE_PATTERN.search(timestamp):
            continue

        time = float(solve["n"])
        penalty = int(solve["t"])
        if time == -1 or penalty == 2:
            time = np.inf
            penalty = 2

        singles.append({
            "date": timestamp,
            "time": time,
            "penalty": penalty,
            "scramble": solve.get("s", ""),
        })
    return pd.DataFrame(singles, columns=["date", "time", "penalty", "scramble"])


def load_averages(path: str | Path | BinaryIO = AVERAGES_FILE) -> pd.DataFrame:
    """Expand each Cubolandia Ao5 export into its five underlying solves."""
    solves = []
    for average in _read_export(path):
        tokens = TIME_PATTERN.findall(average["c"])
        lines = [line.strip() for line in average.get("s", "").splitlines()]
        scrambles = []
        for index, line in enumerate(lines):
            if not TIME_LINE_PATTERN.fullmatch(line):
                continue
            scramble = next(
                (following for following in lines[index + 1:] if following),
                "",
            )
            scrambles.append(scramble)

        for index, token in enumerate(tokens):
            raw = token.strip("()")
            if raw == "DNF":
                time, penalty = np.inf, 2
            else:
                penalty = int(raw.endswith("+"))
                time = parse_time(raw[:-1] if penalty else raw)

            solves.append({
                "date": average["i"],
                "time": time,
                "penalty": penalty,
                "scramble": scrambles[index] if index < len(scrambles) else "",
            })
    return pd.DataFrame(solves, columns=["date", "time", "penalty", "scramble"])


def load_cstimer(source: str | Path | BinaryIO) -> pd.DataFrame:
    """Load solves from a CS Timer JSON export, commonly saved with a .txt suffix."""
    if isinstance(source, (str, Path)):
        with Path(source).open("r", encoding="utf-8") as export_file:
            data = json.load(export_file)
    elif isinstance(source, IOBase) or (
        hasattr(source, "read") and hasattr(source, "seek")
    ):
        source.seek(0)
        data = json.load(source)
    else:
        raise TypeError("A origem deve ser um caminho ou um ficheiro CS Timer aberto.")

    if not isinstance(data, dict):
        raise ValueError("A exportação CS Timer deve conter um objeto JSON.")

    solves = []
    session_pattern = re.compile(r"session\d+")
    for session_name, session_solves in data.items():
        if not session_pattern.fullmatch(session_name):
            continue
        if not isinstance(session_solves, list):
            raise ValueError(f"A sessão {session_name} não contém uma lista de solves.")

        for solve in session_solves:
            if not isinstance(solve, list) or len(solve) < 4:
                raise ValueError(f"Formato de solve inválido na sessão {session_name}.")
            result = solve[0]
            if not isinstance(result, list) or len(result) < 2:
                raise ValueError(f"Tempo/penalização inválidos na sessão {session_name}.")

            raw_penalty = int(result[0])
            raw_time = float(result[1])
            timestamp = float(solve[3])

            if raw_penalty == -1 or raw_time < 0:
                time, penalty = np.inf, 2
            else:
                time = (raw_time + (2000 if raw_penalty == 2000 else 0)) / 1000
                penalty = 1 if raw_penalty == 2000 else 0

            # CS Timer records Unix timestamps in seconds; keep the same naive datetime schema.
            date = pd.to_datetime(timestamp, unit="s")
            solves.append({
                "date": date,
                "time": time,
                "penalty": penalty,
                "scramble": solve[1] if isinstance(solve[1], str) else "",
            })

    if not solves:
        raise ValueError("A exportação CS Timer não contém solves em sessões.")
    return pd.DataFrame(solves, columns=["date", "time", "penalty", "scramble"])

def combine_solves(*dfs: pd.DataFrame) -> pd.DataFrame:
    """Combine any number of solve DataFrames and normalize them for the dashboard."""

    combined = pd.concat(dfs, ignore_index=True)
    if "scramble" not in combined.columns:
        combined["scramble"] = ""
    combined["scramble"] = (
        combined["scramble"]
        .fillna("")
        .astype(str)
        .str.split()
        .str.join(" ")
    )

    combined["date"] = pd.to_datetime(combined["date"])
    combined["time"] = pd.to_numeric(combined["time"], errors="raise")
    combined["penalty"] = pd.to_numeric(combined["penalty"], errors="raise").astype(int)

    dnf_mask = combined["time"].eq(-1) | combined["penalty"].eq(2)
    combined.loc[dnf_mask, "time"] = np.inf
    combined.loc[dnf_mask, "penalty"] = 2

    return (
        combined.sort_values("date", kind="stable")
        .reset_index(drop=True)
    )


def deduplicate_solves(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove matching solve imports without collapsing rows lacking scramble data."""
    normalized = combine_solves(df)
    has_scramble = normalized["scramble"].ne("")
    with_scramble = normalized.loc[has_scramble].copy()
    with_scramble["_dedup_time"] = with_scramble["time"].round(2)
    with_scramble = with_scramble.drop_duplicates(
        subset=["scramble", "_dedup_time", "penalty"],
        keep="first",
    ).drop(columns="_dedup_time")
    without_scramble = normalized.loc[~has_scramble]
    deduplicated = (
        pd.concat([with_scramble, without_scramble], ignore_index=True)
        .sort_values("date", kind="stable")
        .reset_index(drop=True)
    )
    return deduplicated, len(normalized) - len(deduplicated)


def load_data(
    singles_path: str | Path | BinaryIO = SINGLES_FILE,
    averages_path: str | Path | BinaryIO = AVERAGES_FILE,
) -> pd.DataFrame:
    """Load and combine the two Cubolandia Timer exports."""
    singles = load_singles(singles_path)
    average_solves = load_averages(averages_path)
    return combine_solves(singles, average_solves)


if __name__ == "__main__":
    singles = load_singles()
    average_solves = load_averages()
    cstimer=load_cstimer(PROJECT_DIR / "cstimer_export.txt")
    combined = combine_solves(singles, average_solves ,cstimer)
    combined.to_csv(PROJECT_DIR / "combined_solves.csv", index=False)

    print(f"Singles carregados: {len(singles)}")
    print(f"Solves extraídas dos averages: {len(average_solves)}")
    print(f"Solves carregados do CS Timer: {len(cstimer)}")
    print(f"Total exportado: {len(combined)}")
