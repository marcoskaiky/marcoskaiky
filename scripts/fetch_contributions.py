"""Le o calendario real de contribuicoes -- sem token, sem GraphQL.

O GitHub publica o calendario como HTML publico em
`https://github.com/users/<user>/contributions`, o mesmo fragmento que a
pagina de perfil consome. Basta buscar, parsear e derivar as estatisticas.

Saida: data/contributions.json
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

from config import DATA, USERNAME

URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = DATA / "contributions.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (profile-art; +https://github.com/{})".format(USERNAME),
    "Accept": "text/html",
    "X-Requested-With": "XMLHttpRequest",
}

COUNT_RE = re.compile(r"^\s*(No|[\d,]+)\s+contribution", re.I)
TOTAL_RE = re.compile(r"([\d,]+)\s+contributions?\s+in\s+the\s+last", re.I)


def sunday_index(d: date) -> int:
    """0 = domingo ... 6 = sabado (a grade do GitHub comeca no domingo)."""
    return (d.weekday() + 1) % 7


def parse_count(text: str) -> int | None:
    m = COUNT_RE.match(text or "")
    if not m:
        return None
    raw = m.group(1)
    return 0 if raw.lower() == "no" else int(raw.replace(",", ""))


def scrape() -> tuple[list[dict], str | None]:
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # As contagens vivem em <tool-tip for="<id do td>">N contributions on ...</tool-tip>
    tips: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        count = parse_count(tip.get_text(strip=True))
        if target and count is not None:
            tips[target] = count

    days: list[dict] = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        iso = cell.get("data-date")
        if not iso:
            continue
        # ordem de preferencia: tooltip -> data-count (markup antigo) -> aria-label
        count = tips.get(cell.get("id", ""))
        if count is None and cell.get("data-count") is not None:
            count = int(cell["data-count"])
        if count is None:
            count = parse_count(cell.get("aria-label", "")) or 0
        days.append({
            "date": iso,
            "count": int(count),
            "level": int(cell.get("data-level") or 0),
        })

    if not days:
        raise SystemExit(
            "nenhum dia encontrado -- o markup do GitHub mudou ou o perfil e privado"
        )

    heading = soup.find(string=TOTAL_RE)
    label = " ".join(heading.split()) if heading else None
    return sorted(days, key=lambda d: d["date"]), label


def streaks(days: list[dict], today: date) -> tuple[dict, dict]:
    """Sequencia atual e maior sequencia, ignorando dias no futuro.

    Se hoje ainda esta zerado, a sequencia atual conta a partir de ontem --
    caso contrario ela zeraria toda madrugada.
    """
    past = [d for d in days if date.fromisoformat(d["date"]) <= today]

    best = {"length": 0, "start": None, "end": None}
    run = 0
    for i, day in enumerate(past):
        if day["count"] > 0:
            run += 1
            if run > best["length"]:
                best = {
                    "length": run,
                    "start": past[i - run + 1]["date"],
                    "end": day["date"],
                }
        else:
            run = 0

    tail = past[:-1] if past and past[-1]["count"] == 0 else past
    current = {"length": 0, "start": None, "end": None}
    for day in reversed(tail):
        if day["count"] == 0:
            break
        current["length"] += 1
        current["start"] = day["date"]
        current["end"] = current["end"] or day["date"]

    return current, best


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    days, label = scrape()
    today = datetime.now(timezone.utc).date()

    past = [d for d in days if date.fromisoformat(d["date"]) <= today]
    total = sum(d["count"] for d in past)
    current, best = streaks(days, today)
    top = max(past, key=lambda d: d["count"])

    monthly: dict[str, int] = defaultdict(int)
    for day in past:
        monthly[day["date"][:7]] += day["count"]

    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": total,
        "total_label": label or f"{total:,} contributions in the last year",
        "days": days,
        "stats": {
            "current_streak": current,
            "longest_streak": best,
            "best_day": {"date": top["date"], "count": top["count"]},
            "active_days": sum(1 for d in past if d["count"] > 0),
            "tracked_days": len(past),
            "monthly": dict(sorted(monthly.items())),
        },
    }

    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"  -> {OUT.name}  {total:,} contribuicoes, "
        f"{len(days)} dias, streak {current['length']}d (recorde {best['length']}d)"
    )


if __name__ == "__main__":
    main()
