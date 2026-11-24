"""Measure separate-chaining lookup costs and compare them with simple estimates."""

import csv
import math
from pathlib import Path
import random

from src.hash_table import HashTable


CAPACITY = 4093
RESULTS_CSV = Path(__file__).resolve().parent / "results.csv"
RESULTS_SVG = Path(__file__).resolve().parent / "results.svg"


def measure_load_factors(capacity: int = CAPACITY) -> list[tuple[float, int, float, float, float, float]]:
    rows = []
    random_source = random.Random(2026)
    sample_keys = [
        f"https://example.com/{random_source.getrandbits(64):016x}/{index}"
        for index in range(round(4 * capacity))
    ]
    for quarter in range(1, 17):
        load_factor = quarter / 4
        item_count = round(load_factor * capacity)
        table = HashTable(capacity=capacity)
        keys = sample_keys[:item_count]
        for key in keys:
            table.set(key, key)

        successful_probes = 0
        for key in keys:
            if table.get(key) != key:
                raise AssertionError(f"stored value mismatch for {key!r}")
            successful_probes += table.last_probes

        missing_keys: list[str | None] = [None] * capacity
        uncovered = capacity
        candidate = 0
        while uncovered and candidate < capacity * 20:
            key = (
                "https://missing.example/"
                f"{random_source.getrandbits(64):016x}/{candidate}"
            )
            bucket, _ = table.explain_hash(key)
            if missing_keys[bucket] is None:
                missing_keys[bucket] = key
                uncovered -= 1
            candidate += 1
        if uncovered:
            raise RuntimeError(f"could not sample every bucket ({uncovered} remain)")

        unsuccessful_probes = 0
        for key in missing_keys:
            if key is None:
                raise RuntimeError("missing-key sample was not fully populated")
            if table.contains(key):
                raise AssertionError("an absent key unexpectedly exists")
            unsuccessful_probes += table.last_probes

        successful_average = successful_probes / item_count
        unsuccessful_average = unsuccessful_probes / capacity
        rows.append(
            (
                load_factor,
                item_count,
                successful_average,
                1 + load_factor / 2,
                unsuccessful_average,
                load_factor,
            )
        )
    return rows


def write_csv(rows: list[tuple[float, int, float, float, float, float]], path: Path) -> None:
    headers = (
        "load_factor",
        "item_count",
        "successful_measured",
        "successful_theoretical",
        "unsuccessful_measured",
        "unsuccessful_theoretical",
    )
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(
                (f"{row[0]:.2f}", row[1], *(f"{value:.4f}" for value in row[2:]))
            )


def write_svg(rows: list[tuple[float, int, float, float, float, float]], path: Path) -> None:
    width, height = 800, 500
    left, right, top, bottom = 80, 30, 45, 70
    plot_width = width - left - right
    plot_height = height - top - bottom
    maximum = max(max(row[2], row[3], row[4], row[5]) for row in rows)
    y_max = max(5, math.ceil(maximum))

    def point(load_factor: float, probes: float) -> tuple[float, float]:
        x = left + load_factor / 4 * plot_width
        y = top + (y_max - probes) / y_max * plot_height
        return x, y

    series = (
        ("Successful measured", 2, "#1769aa", ""),
        ("Successful theory: 1 + alpha/2", 3, "#1769aa", "7 5"),
        ("Unsuccessful measured", 4, "#d1495b", ""),
        ("Unsuccessful theory: alpha", 5, "#d1495b", "7 5"),
    )
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<title>Separate chaining lookup cost by load factor</title>",
        '<rect width="100%" height="100%" fill="white"/>',
    ]

    for tick in range(y_max + 1):
        y = top + (y_max - tick) / y_max * plot_height
        elements.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" '
            'stroke="#dddddd"/>'
        )
        elements.append(
            f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" '
            f'font-family="sans-serif" font-size="12">{tick}</text>'
        )

    elements.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" '
            'stroke="#333"/>',
            f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" '
            f'y2="{height-bottom}" stroke="#333"/>',
            f'<text x="{left + plot_width/2:.1f}" y="{height-20}" text-anchor="middle" '
            'font-family="sans-serif" font-size="14">Load factor (alpha)</text>',
            f'<text x="20" y="{top + plot_height/2:.1f}" text-anchor="middle" '
            'font-family="sans-serif" font-size="14" '
            f'transform="rotate(-90 20 {top + plot_height/2:.1f})">Average nodes examined</text>',
        )
    )

    for load_factor in range(5):
        x = left + load_factor / 4 * plot_width
        elements.append(
            f'<text x="{x:.1f}" y="{height-bottom+22}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="12">{load_factor}</text>'
        )

    for label, column, color, dash in series:
        coordinates = [point(row[0], row[column]) for row in rows]
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in coordinates)
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        elements.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            f'stroke-width="2"{dash_attribute}/>'
        )
        if not dash:
            for x, y in coordinates:
                elements.append(
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>'
                )

    for index, (label, _, color, dash) in enumerate(series):
        y = 24 + index * 18
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        elements.append(
            f'<line x1="475" y1="{y}" x2="505" y2="{y}" stroke="{color}" '
            f'stroke-width="2"{dash_attribute}/>'
        )
        elements.append(
            f'<text x="512" y="{y+4}" font-family="sans-serif" font-size="12">'
            f"{label}</text>"
        )

    elements.append("</svg>")
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def main() -> None:
    rows = measure_load_factors()
    write_csv(rows, RESULTS_CSV)
    write_svg(rows, RESULTS_SVG)

    print("alpha  n     success measured/theory   unsuccessful measured/theory")
    for alpha, count, success, success_theory, miss, miss_theory in rows:
        print(
            f"{alpha:4.2f}  {count:4d}  {success:7.3f}/{success_theory:<7.3f}"
            f"           {miss:7.3f}/{miss_theory:<7.3f}"
        )
    print(f"\nWrote {RESULTS_CSV.relative_to(Path.cwd())}")
    print(f"Wrote {RESULTS_SVG.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
