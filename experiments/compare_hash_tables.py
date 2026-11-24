"""Compare separate chaining and linear probing on identical key sets."""

import csv
from dataclasses import dataclass
import math
from pathlib import Path
import random

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


CAPACITY = 1000
QUERY_COUNT = 5000
RESULTS_DIR = Path(__file__).resolve().parent / "results"


@dataclass(frozen=True)
class ComparisonRow:
    load_factor: float
    item_count: int
    chaining_successful: float
    chaining_successful_theory: float
    chaining_unsuccessful: float
    chaining_unsuccessful_theory: float
    linear_successful: float
    linear_successful_theory: float
    linear_unsuccessful: float
    linear_unsuccessful_theory: float


def measure_comparison(
    capacity: int = CAPACITY, query_count: int = QUERY_COUNT
) -> list[ComparisonRow]:
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("capacity must be a positive integer")
    if isinstance(query_count, bool) or not isinstance(query_count, int) or query_count <= 0:
        raise ValueError("query_count must be a positive integer")

    key_source = random.Random(2026)
    sample_keys = [
        f"stored-{key_source.getrandbits(64):016x}"
        for _ in range(round(0.9 * capacity))
    ]
    query_source = random.Random(404)
    missing_keys = [
        f"absent-{query_source.getrandbits(64):016x}-{index}"
        for index in range(query_count)
    ]

    rows = []
    for step in range(1, 10):
        load_factor = step / 10
        item_count = round(load_factor * capacity)
        keys = sample_keys[:item_count]
        chaining = HashTable[str](capacity=capacity)
        linear = LinearProbingHashTable[str](capacity=capacity)

        for key in keys:
            chaining.set(key, key)
            linear.set(key, key)

        chaining_successful_probes = 0
        linear_successful_probes = 0
        for key in keys:
            if chaining.get(key) != key or linear.get(key) != key:
                raise AssertionError(f"stored value mismatch for {key!r}")
            chaining_successful_probes += chaining.last_probes
            linear_successful_probes += linear.last_probes

        chaining_unsuccessful_probes = 0
        linear_unsuccessful_probes = 0
        for key in missing_keys:
            if chaining.contains(key) or linear.contains(key):
                raise AssertionError(f"an absent key unexpectedly exists: {key!r}")
            chaining_unsuccessful_probes += chaining.last_probes
            linear_unsuccessful_probes += linear.last_probes

        rows.append(
            ComparisonRow(
                load_factor=load_factor,
                item_count=item_count,
                chaining_successful=chaining_successful_probes / item_count,
                chaining_successful_theory=1 + load_factor / 2,
                chaining_unsuccessful=chaining_unsuccessful_probes / query_count,
                chaining_unsuccessful_theory=load_factor,
                linear_successful=linear_successful_probes / item_count,
                linear_successful_theory=0.5
                * (1 + 1 / (1 - load_factor)),
                linear_unsuccessful=linear_unsuccessful_probes / query_count,
                linear_unsuccessful_theory=0.5
                * (1 + 1 / (1 - load_factor) ** 2),
            )
        )
    return rows


def write_csv(rows: list[ComparisonRow], path: Path) -> None:
    fields = tuple(ComparisonRow.__dataclass_fields__)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(fields)
        for row in rows:
            writer.writerow(
                f"{value:.4f}" if isinstance(value, float) else value
                for value in (getattr(row, field) for field in fields)
            )


def write_svg(rows: list[ComparisonRow], path: Path) -> None:
    width, height = 1000, 560
    panels = (
        (
            40,
            "Successful searches",
            ("chaining_successful", "chaining_successful_theory"),
            ("linear_successful", "linear_successful_theory"),
        ),
        (
            520,
            "Unsuccessful searches",
            ("chaining_unsuccessful", "chaining_unsuccessful_theory"),
            ("linear_unsuccessful", "linear_unsuccessful_theory"),
        ),
    )
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<title>Chaining and linear probing lookup costs</title>",
        '<rect width="100%" height="100%" fill="white"/>',
    ]

    for left, title, chain_columns, linear_columns in panels:
        plot_left, plot_top = left + 52, 125
        plot_width, plot_height = 390, 345
        plot_bottom = plot_top + plot_height
        maximum = max(
            max(getattr(row, column) for row in rows)
            for column in (*chain_columns, *linear_columns)
        )
        y_max = max(1, math.ceil(maximum * 1.08))

        elements.append(
            f'<text x="{left+245}" y="35" text-anchor="middle" '
            f'font-family="sans-serif" font-size="18">{title}</text>'
        )
        for tick in range(5):
            value = y_max * tick / 4
            y = plot_bottom - tick / 4 * plot_height
            elements.extend(
                (
                    f'<line x1="{plot_left}" y1="{y:.1f}" '
                    f'x2="{plot_left+plot_width}" y2="{y:.1f}" stroke="#dddddd"/>',
                    f'<text x="{plot_left-8}" y="{y+4:.1f}" text-anchor="end" '
                    f'font-family="sans-serif" font-size="11">{value:.1f}</text>',
                )
            )
        elements.extend(
            (
                f'<line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" '
                f'y2="{plot_bottom}" stroke="#333"/>',
                f'<line x1="{plot_left}" y1="{plot_bottom}" '
                f'x2="{plot_left+plot_width}" y2="{plot_bottom}" stroke="#333"/>',
                f'<text x="{plot_left+plot_width/2:.1f}" y="{plot_bottom+38}" '
                'text-anchor="middle" font-family="sans-serif" font-size="13">'
                'Load factor (alpha)</text>',
            )
        )
        for tick in range(6):
            alpha = tick / 5
            x = plot_left + alpha * plot_width
            elements.append(
                f'<text x="{x:.1f}" y="{plot_bottom+18}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="10">{alpha:.1f}</text>'
            )

        series = (
            ("Chaining measured", chain_columns[0], "#1769aa", ""),
            ("Chaining theory", chain_columns[1], "#1769aa", "6 4"),
            ("Linear measured", linear_columns[0], "#d1495b", ""),
            ("Linear theory", linear_columns[1], "#d1495b", "6 4"),
        )
        for label, field, color, dash in series:
            points = []
            for row in rows:
                x = plot_left + row.load_factor * plot_width
                y = plot_bottom - getattr(row, field) / y_max * plot_height
                points.append((x, y))
            coordinate_text = " ".join(
                f"{x:.1f},{y:.1f}" for x, y in points
            )
            dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
            elements.append(
                f'<polyline points="{coordinate_text}" fill="none" stroke="{color}" '
                f'stroke-width="2"{dash_attribute}/>'
            )
            if not dash:
                for x, y in points:
                    elements.append(
                        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{color}"/>'
                    )

        for index, (label, _, color, dash) in enumerate(series):
            legend_x = left + 45 + (index % 2) * 205
            legend_y = 70 + (index // 2) * 20
            dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
            elements.extend(
                (
                    f'<line x1="{legend_x}" y1="{legend_y}" '
                    f'x2="{legend_x+25}" y2="{legend_y}" stroke="{color}" '
                    f'stroke-width="2"{dash_attribute}/>',
                    f'<text x="{legend_x+31}" y="{legend_y+4}" '
                    f'font-family="sans-serif" font-size="11">{label}</text>',
                )
            )
    elements.append("</svg>")
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def write_markdown(rows: list[ComparisonRow], path: Path) -> None:
    largest_chain_difference = max(
        abs(row.chaining_successful - row.chaining_successful_theory)
        for row in rows
    )
    largest_linear_difference = max(
        abs(row.linear_unsuccessful - row.linear_unsuccessful_theory)
        for row in rows
    )
    lines = [
        "# Linear probing and chaining comparison",
        "",
        "Reproduce with `make experiment`. Both tables have capacity 1,000 and receive "
        "the same seeded 64-bit keys at each load factor. Successful searches visit "
        "every stored key once; unsuccessful searches use the same 5,000 seeded "
        "absent-key queries for both implementations. Linear-probing counts include "
        "the final empty cell examined on a miss.",
        "",
        "Theory: chaining successful `1 + alpha/2`, unsuccessful `alpha`; linear "
        "probing successful `0.5 * (1 + 1/(1-alpha))`, unsuccessful "
        "`0.5 * (1 + 1/(1-alpha)^2)`.",
        "",
        "| alpha | n | Chain success measured/theory | Chain miss measured/theory | "
        "Linear success measured/theory | Linear miss measured/theory |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.load_factor:.1f} | {row.item_count} "
            f"| {row.chaining_successful:.3f}/{row.chaining_successful_theory:.3f} "
            f"| {row.chaining_unsuccessful:.3f}/{row.chaining_unsuccessful_theory:.3f} "
            f"| {row.linear_successful:.3f}/{row.linear_successful_theory:.3f} "
            f"| {row.linear_unsuccessful:.3f}/{row.linear_unsuccessful_theory:.3f} |"
        )
    lines.extend(
        (
            "",
            "The chaining successful-search maximum absolute difference in this run is "
            f"{largest_chain_difference:.3f}; the linear unsuccessful-search maximum "
            f"absolute difference is {largest_linear_difference:.3f}. Differences from "
            "the formulas are expected-value sampling effects. At alpha=0.9, linear "
            "probing averages 36.086 miss probes against the 50.500 expected value: "
            "the 5,000 queries measure this one table, whose finite cluster layout is "
            "not the average over independently built tables. Linear probing's "
            "unsuccessful cost rises sharply as the table fills because primary "
            "clusters make long runs of occupied cells more likely; separate chaining "
            "grows approximately linearly with alpha.",
            "",
            "The SVG contains separate successful/unsuccessful panels. The one-page PDF "
            "summarizes the setup, formulas, data, and measured curves.",
            "",
        )
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _pdf_text(x: float, y: float, size: float, text: str) -> str:
    safe_text = text.encode("ascii", "replace").decode("ascii")
    safe_text = safe_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return f"BT /F1 {size:g} Tf {x:.1f} {y:.1f} Td ({safe_text}) Tj ET\n"


def _pdf_chart(
    rows: list[ComparisonRow],
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    measured_fields: tuple[str, str],
    theory_fields: tuple[str, str],
) -> str:
    content = [_pdf_text(x, y + height - 12, 9, title)]
    left, bottom = x + 24, y + 22
    plot_width, plot_height = width - 34, height - 46
    maximum = max(
        max(getattr(row, field) for row in rows)
        for field in (*measured_fields, *theory_fields)
    )
    y_max = math.ceil(maximum * 1.08)
    content.append(f"0.2 w {left:.1f} {bottom:.1f} m {left+plot_width:.1f} {bottom:.1f} l S\n")
    content.append(f"{left:.1f} {bottom:.1f} m {left:.1f} {bottom+plot_height:.1f} l S\n")
    content.append(_pdf_text(left - 2, bottom - 12, 6, "0"))
    content.append(_pdf_text(left + plot_width - 8, bottom - 12, 6, "1.0"))
    content.append(_pdf_text(left - 18, bottom + plot_height - 2, 6, str(y_max)))

    fields = (
        (measured_fields[0], (0.09, 0.41, 0.67), False),
        (theory_fields[0], (0.09, 0.41, 0.67), True),
        (measured_fields[1], (0.82, 0.28, 0.35), False),
        (theory_fields[1], (0.82, 0.28, 0.35), True),
    )
    for field, (red, green, blue), dashed in fields:
        content.append(f"{red:.2f} {green:.2f} {blue:.2f} RG\n")
        content.append("[3 2] 0 d\n" if dashed else "[] 0 d\n")
        first = True
        for row in rows:
            px = left + row.load_factor * plot_width
            py = bottom + getattr(row, field) / y_max * plot_height
            content.append(f"{px:.1f} {py:.1f} {'m' if first else 'l'} ")
            first = False
        content.append("S\n")
    content.append("0 0 0 RG [] 0 d\n")
    content.append(_pdf_text(x + 24, y + 4, 6, "Blue: chaining; red: linear; dashed: theory"))
    return "".join(content)


def write_pdf(rows: list[ComparisonRow], path: Path) -> None:
    content = [
        _pdf_text(45, 805, 17, "Hash Table Collision Strategy Comparison"),
        _pdf_text(45, 785, 9, "Capacity 1,000; identical seeded keys; load factors 0.1 to 0.9."),
        _pdf_text(45, 771, 8, "Theory (success / miss): chaining 1+alpha/2 / alpha; linear 0.5*(1+1/(1-alpha)) / 0.5*(1+1/(1-alpha)^2)."),
    ]
    headers = ("alpha", "n", "C-S", "C-S th", "C-M", "C-M th", "L-S", "L-S th", "L-M", "L-M th")
    x_positions = (45, 90, 125, 170, 215, 260, 305, 350, 395, 440)
    header_y = 745
    for x, header in zip(x_positions, headers):
        content.append(_pdf_text(x, header_y, 7, header))
    for index, row in enumerate(rows):
        y = header_y - 15 - index * 13
        values = (
            f"{row.load_factor:.1f}",
            str(row.item_count),
            f"{row.chaining_successful:.2f}",
            f"{row.chaining_successful_theory:.2f}",
            f"{row.chaining_unsuccessful:.2f}",
            f"{row.chaining_unsuccessful_theory:.2f}",
            f"{row.linear_successful:.2f}",
            f"{row.linear_successful_theory:.2f}",
            f"{row.linear_unsuccessful:.2f}",
            f"{row.linear_unsuccessful_theory:.2f}",
        )
        for x, value in zip(x_positions, values):
            content.append(_pdf_text(x, y, 7, value))
    content.append(
        _pdf_chart(
            rows,
            45,
            285,
            245,
            185,
            "Successful searches",
            ("chaining_successful", "linear_successful"),
            ("chaining_successful_theory", "linear_successful_theory"),
        )
    )
    content.append(
        _pdf_chart(
            rows,
            310,
            285,
            245,
            185,
            "Unsuccessful searches",
            ("chaining_unsuccessful", "linear_unsuccessful"),
            ("chaining_unsuccessful_theory", "linear_unsuccessful_theory"),
        )
    )
    content.extend(
        (
            _pdf_text(45, 255, 9, "Interpretation"),
            _pdf_text(45, 239, 8, "The measurements follow the expected formulas, with finite-sample deviations. Linear-probing"),
            _pdf_text(45, 226, 8, "miss cost grows rapidly near a full table as primary clusters lengthen; chaining miss cost"),
            _pdf_text(45, 213, 8, "grows approximately with alpha. At alpha=0.9, linear miss cost is 36.1 vs 50.5 theory:"),
            _pdf_text(45, 200, 8, "queries sample one table, not the expectation across independently built tables."),
            _pdf_text(45, 187, 8, "Linear-probing counts include the terminal empty cell."),
            _pdf_text(45, 30, 7, "Generated by make experiment. Full measurements and method are in the CSV and Markdown files."),
        )
    )
    stream = "".join(content).encode("ascii")
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    )

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(pdf)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = measure_comparison()
    csv_path = RESULTS_DIR / "hash_table_comparison.csv"
    svg_path = RESULTS_DIR / "hash_table_comparison.svg"
    report_path = RESULTS_DIR / "hash_table_comparison.md"
    pdf_path = RESULTS_DIR / "hash_table_comparison.pdf"
    write_csv(rows, csv_path)
    write_svg(rows, svg_path)
    write_markdown(rows, report_path)
    write_pdf(rows, pdf_path)

    print("alpha  n    chain success  chain miss  linear success  linear miss")
    for row in rows:
        print(
            f"{row.load_factor:.1f}  {row.item_count:4d}  "
            f"{row.chaining_successful:7.3f}  {row.chaining_unsuccessful:7.3f}  "
            f"{row.linear_successful:7.3f}  {row.linear_unsuccessful:7.3f}"
        )
    for path in (csv_path, svg_path, report_path, pdf_path):
        print(f"Wrote {path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
