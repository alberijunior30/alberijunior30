"""Gera um SVG animado: uma borracha passa pelo gráfico de contribuições e apaga os commits."""
import json
import os
import random
import sys
import urllib.request

USERNAME = os.environ.get("USERNAME", "alberijunior30")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUTPUT = os.environ.get("OUTPUT_PATH", "profile/eraser-commits.svg")

# Paleta azul, combinando com o resto do perfil
COLORS = {
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#0369a1",
    "SECOND_QUARTILE": "#0284c7",
    "THIRD_QUARTILE": "#38bdf8",
    "FOURTH_QUARTILE": "#00BFFF",
}

CELL, GAP = 11, 3
STEP = CELL + GAP
PAD_X, PAD_Y = 40, 20
DURATION = 10  # segundos por ciclo
SWEEP_START, SWEEP_END = 10, 70  # % do ciclo em que a borracha atravessa o gráfico
RETURN_START, RETURN_END = 82, 95  # % em que os commits reaparecem

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionLevel weekday } }
      }
    }
  }
}
"""


def fetch_weeks():
    body = json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    if "errors" in data:
        sys.exit(f"Erro da API do GitHub: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def fake_weeks():
    """Dados aleatórios para testar localmente sem token."""
    levels = list(COLORS)
    return [
        {"contributionDays": [{"weekday": d, "contributionLevel": random.choice(levels)} for d in range(7)]}
        for _ in range(53)
    ]


def build_svg(weeks):
    n = len(weeks)
    grid_w = n * STEP - GAP
    grid_h = 7 * STEP - GAP
    width = grid_w + PAD_X * 2
    height = grid_h + PAD_Y * 2 + 20

    eraser_w, eraser_h = 30, grid_h + 24
    eraser_y = PAD_Y - 12
    # Posição da borda direita (a que apaga) no início e no fim da varredura
    x_start = PAD_X - 4 - eraser_w
    x_end = PAD_X + grid_w + 4 - eraser_w

    css = [
        f".cell{{animation-duration:{DURATION}s;animation-iteration-count:infinite;animation-timing-function:linear}}",
        f".eraser{{animation:sweep {DURATION}s linear infinite}}",
        "@keyframes sweep{"
        f"0%{{transform:translate({x_start - 60}px,0);opacity:0}}"
        f"5%{{transform:translate({x_start - 60}px,0);opacity:0}}"
        f"{SWEEP_START}%{{transform:translate({x_start}px,0);opacity:1}}"
        f"{SWEEP_END}%{{transform:translate({x_end}px,0);opacity:1}}"
        f"{SWEEP_END + 6}%{{transform:translate({x_end + 60}px,0);opacity:0}}"
        f"100%{{transform:translate({x_end + 60}px,0);opacity:0}}}}",
    ]

    cells_bg, cells_fg = [], []
    for i, week in enumerate(weeks):
        x = PAD_X + i * STEP
        # Momento em que a borda da borracha passa pelo centro desta coluna
        p = SWEEP_START + (SWEEP_END - SWEEP_START) * (i * STEP + CELL / 2 + 4) / (grid_w + 8)
        css.append(
            f"@keyframes e{i}{{0%,{p:.2f}%{{opacity:1}}{p + 1.2:.2f}%,{RETURN_START}%{{opacity:0}}"
            f"{RETURN_END}%,100%{{opacity:1}}}}"
        )
        for day in week["contributionDays"]:
            y = PAD_Y + day["weekday"] * STEP
            cells_bg.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{COLORS["NONE"]}"/>')
            level = day["contributionLevel"]
            if level != "NONE":
                cells_fg.append(
                    f'<rect class="cell" style="animation-name:e{i}" x="{x}" y="{y}" '
                    f'width="{CELL}" height="{CELL}" rx="2" fill="{COLORS[level]}"/>'
                )

    eraser = (
        f'<g class="eraser">'
        f'<rect x="0" y="{eraser_y}" width="{eraser_w}" height="{eraser_h}" rx="5" fill="#f9a8d4"/>'
        f'<rect x="0" y="{eraser_y}" width="{eraser_w // 2}" height="{eraser_h}" rx="5" fill="#1e3a8a"/>'
        f'<rect x="{eraser_w // 2 - 3}" y="{eraser_y}" width="6" height="{eraser_h}" fill="#1e3a8a"/>'
        f'<rect x="{eraser_w - 4}" y="{eraser_y + 4}" width="2" height="{eraser_h - 8}" rx="1" fill="#fce7f3" opacity="0.7"/>'
        f"</g>"
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'
        f"<style>{''.join(css)}</style>"
        f"{''.join(cells_bg)}{''.join(cells_fg)}{eraser}"
        f"</svg>"
    )


if __name__ == "__main__":
    weeks = fake_weeks() if "--demo" in sys.argv else fetch_weeks()
    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(build_svg(weeks))
    print(f"SVG salvo em {OUTPUT}")
