#!/usr/bin/env python3
"""
Llama a football-data.org con el token guardado como GitHub Secret
y genera matches.json en la raíz del repo para que lo lea index.html.
El token NUNCA toca el HTML público.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

TOKEN = os.environ.get("FOOTBALL_TOKEN", "")
COMPETITION = "WC"  # Copa del Mundo FIFA

TEAM_ES = {
    "Spain": "España", "Germany": "Alemania", "France": "Francia",
    "Brazil": "Brasil", "Argentina": "Argentina", "Portugal": "Portugal",
    "England": "Inglaterra", "Italy": "Italia", "Netherlands": "Países Bajos",
    "Belgium": "Bélgica", "Croatia": "Croacia", "Uruguay": "Uruguay",
    "Mexico": "México", "Morocco": "Marruecos", "Senegal": "Senegal",
    "Japan": "Japón", "Korea Republic": "Corea del Sur", "Australia": "Australia",
    "United States": "Estados Unidos", "Canada": "Canadá", "Ecuador": "Ecuador",
    "Colombia": "Colombia", "Ghana": "Ghana", "Switzerland": "Suiza",
    "Poland": "Polonia", "Serbia": "Serbia", "Denmark": "Dinamarca",
    "Cameroon": "Camerún", "Tunisia": "Túnez", "Saudi Arabia": "Arabia Saudí",
    "Costa Rica": "Costa Rica", "Iran": "Irán", "Wales": "Gales",
    "Sweden": "Suecia", "Norway": "Noruega", "Turkey": "Turquía",
    "Austria": "Austria", "Greece": "Grecia", "Romania": "Rumanía",
    "Slovakia": "Eslovaquia", "Ukraine": "Ucrania", "Hungary": "Hungría",
    "Scotland": "Escocia", "Albania": "Albania", "Georgia": "Georgia",
    "Slovenia": "Eslovenia", "Czech Republic": "República Checa", "Qatar": "Qatar",
}

def to_es(name: str) -> str:
    return TEAM_ES.get(name, name)

def madrid_time(utc_str: str) -> str:
    """Convierte ISO UTC a HH:MM en hora de Madrid (UTC+2 en verano)."""
    dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    madrid = dt + timedelta(hours=2)  # CEST (verano); el Action corre a las 9am Madrid, cuando los partidos nocturnos de EEUU/México ya han terminado
    return madrid.strftime("%H:%M")

def fetch_today() -> list:
    if not TOKEN:
        print("⚠️  FOOTBALL_TOKEN no configurado — generando matches.json vacío.")
        return []

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = (
        f"https://api.football-data.org/v4/competitions/{COMPETITION}/matches"
        f"?dateFrom={today}&dateTo={today}"
    )
    req = Request(url, headers={"X-Auth-Token": TOKEN})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except HTTPError as e:
        print(f"❌ Error HTTP {e.code} al llamar a la API.", file=sys.stderr)
        return []

    matches = []
    for m in data.get("matches", []):
        home = to_es(m["homeTeam"]["name"])
        away = to_es(m["awayTeam"]["name"])
        match = {
            "id": f"m{m['id']}",
            "home": home,
            "away": away,
            "time": madrid_time(m["utcDate"]),
            "group": m.get("group") or m.get("stage") or "",
        }
        if m.get("status") == "FINISHED" and m.get("score", {}).get("fullTime"):
            match["result"] = {
                "home": m["score"]["fullTime"]["home"],
                "away": m["score"]["fullTime"]["away"],
            }
        matches.append(match)

    print(f"✅ {len(matches)} partido(s) encontrados para hoy ({today}).")
    return matches

if __name__ == "__main__":
    matches = fetch_today()
    output = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "matches": matches,
    }
    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("📄 matches.json generado correctamente.")
