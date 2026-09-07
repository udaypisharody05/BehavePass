"""Small dependency-free SVG plotting helpers for review artifacts."""

from __future__ import annotations

import html
import math
from pathlib import Path


def _save(path: Path, title: str, body: str, width: int = 900, height: int = 560) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="white"/>
<style>text{{font-family:Arial,sans-serif;fill:#172033}} .title{{font-size:22px;font-weight:bold}} .axis{{font-size:12px}} .label{{font-size:13px}}</style>
<text x="{width/2}" y="32" text-anchor="middle" class="title">{html.escape(title)}</text>{body}</svg>'''
    path.write_text(svg, encoding="utf-8")


def histogram(path: Path, values: list[float], title: str, x_label: str, bins: int = 25) -> None:
    low, high = min(values), max(values)
    width = (high - low) / bins or 1
    counts = [0] * bins
    for value in values:
        counts[min(bins - 1, int((value - low) / width))] += 1
    peak = max(counts) or 1
    parts = ['<line x1="75" y1="490" x2="860" y2="490" stroke="#334155"/>']
    bar_width = 780 / bins
    for index, count in enumerate(counts):
        height = 400 * count / peak
        parts.append(f'<rect x="{78 + index*bar_width:.1f}" y="{490-height:.1f}" width="{bar_width-2:.1f}" height="{height:.1f}" fill="#2563eb"/>')
    parts += [
        f'<text x="75" y="515" class="axis">{low:.2f}</text>',
        f'<text x="860" y="515" text-anchor="end" class="axis">{high:.2f}</text>',
        f'<text x="470" y="545" text-anchor="middle" class="label">{html.escape(x_label)}</text>',
        '<text x="20" y="280" transform="rotate(-90 20 280)" text-anchor="middle" class="label">Session count</text>',
    ]
    _save(path, title, "".join(parts))


def heatmap(path: Path, labels: list[str], matrix: list[list[float]], title: str) -> None:
    count = len(labels)
    cell = min(50, 400 / count)
    left, top = 330, 75
    parts = []
    for row in range(count):
        parts.append(f'<text x="{left-8}" y="{top+(row+.7)*cell:.1f}" text-anchor="end" class="axis">{html.escape(labels[row])}</text>')
        for column in range(count):
            value = matrix[row][column]
            strength = int(70 + 160 * abs(value))
            color = f'rgb({255-strength if value>=0 else 245},{245-strength//2},{255-strength if value<0 else 245})'
            parts.append(f'<rect x="{left+column*cell:.1f}" y="{top+row*cell:.1f}" width="{cell:.1f}" height="{cell:.1f}" fill="{color}" stroke="white"/>')
    for column, label in enumerate(labels):
        x = left + (column + .55) * cell
        parts.append(f'<text x="{x:.1f}" y="{top-8}" transform="rotate(-55 {x:.1f} {top-8})" text-anchor="start" class="axis">{html.escape(label)}</text>')
    _save(path, title, "".join(parts), 1000, 650)


def bars(path: Path, labels: list[str], values: list[float], title: str, y_label: str) -> None:
    maximum = max(values) or 1
    parts = ['<line x1="90" y1="485" x2="860" y2="485" stroke="#334155"/>']
    slot = 740 / len(values)
    for index, (label, value) in enumerate(zip(labels, values)):
        height = 380 * value / maximum
        x = 105 + index * slot
        parts.append(f'<rect x="{x:.1f}" y="{485-height:.1f}" width="{slot*.62:.1f}" height="{height:.1f}" fill="#0f766e"/>')
        parts.append(f'<text x="{x+slot*.31:.1f}" y="{475-height:.1f}" text-anchor="middle" class="axis">{value:.3f}</text>')
        parts.append(f'<text x="{x+slot*.31:.1f}" y="505" transform="rotate(25 {x+slot*.31:.1f} 505)" text-anchor="start" class="axis">{html.escape(label)}</text>')
    parts.append(f'<text x="25" y="280" transform="rotate(-90 25 280)" text-anchor="middle" class="label">{html.escape(y_label)}</text>')
    _save(path, title, "".join(parts), 900, 620)


def scatter(path: Path, actual: list[float], predicted: list[float], title: str) -> None:
    low = min(actual + predicted)
    high = max(actual + predicted)
    span = high - low or 1
    parts = ['<line x1="80" y1="490" x2="860" y2="490" stroke="#334155"/>', '<line x1="80" y1="60" x2="80" y2="490" stroke="#334155"/>']
    parts.append('<line x1="80" y1="490" x2="860" y2="60" stroke="#dc2626" stroke-dasharray="6 5"/>')
    step = max(1, len(actual) // 900)
    for observed, estimate in zip(actual[::step], predicted[::step]):
        x = 80 + 780 * (observed - low) / span
        y = 490 - 430 * (estimate - low) / span
        if math.isfinite(x) and math.isfinite(y):
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.1" fill="#2563eb" opacity="0.45"/>')
    parts += [
        '<text x="470" y="540" text-anchor="middle" class="label">Actual log10 estimated guesses</text>',
        '<text x="22" y="275" transform="rotate(-90 22 275)" text-anchor="middle" class="label">Predicted log10 estimated guesses</text>',
    ]
    _save(path, title, "".join(parts))


def lines(path: Path, series: dict[str, list[float]], title: str, y_label: str) -> None:
    all_values = [value for values in series.values() for value in values]
    low, high = min(all_values), max(all_values)
    span = high - low or 1
    colors = ["#2563eb", "#dc2626", "#0f766e", "#7c3aed", "#ea580c", "#0891b2"]
    parts = [
        '<line x1="80" y1="490" x2="860" y2="490" stroke="#334155"/>',
        '<line x1="80" y1="60" x2="80" y2="490" stroke="#334155"/>',
    ]
    maximum_length = max(len(values) for values in series.values())
    for series_index, (label, values) in enumerate(series.items()):
        color = colors[series_index % len(colors)]
        points = []
        for index, value in enumerate(values):
            x = 80 + 780 * index / max(1, maximum_length - 1)
            y = 490 - 410 * (value - low) / span
            points.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<rect x="{630}" y="{65+series_index*20}" width="12" height="12" fill="{color}"/><text x="648" y="{76+series_index*20}" class="axis">{html.escape(label)}</text>')
    parts += [
        '<text x="470" y="540" text-anchor="middle" class="label">Epoch</text>',
        f'<text x="22" y="275" transform="rotate(-90 22 275)" text-anchor="middle" class="label">{html.escape(y_label)}</text>',
    ]
    _save(path, title, "".join(parts))
