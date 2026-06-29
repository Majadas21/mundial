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

try:
    import google.auth.transport.requests
    import google.oauth2.service_account
    FCM_AVAILABLE = True
except ImportError:
    FCM_AVAILABLE = False

PROJECT_ID = "mundial-99cdc"
FCM_URL = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"

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
    # Equipos adicionales del Mundial 2026
    "Egypt": "Egipto", "Cape Verde Islands": "Cabo Verde", "Cape Verde": "Cabo Verde",
    "New Zealand": "Nueva Zelanda", "Venezuela": "Venezuela", "Paraguay": "Paraguay",
    "Bolivia": "Bolivia", "Chile": "Chile", "Peru": "Perú",
    "Nigeria": "Nigeria", "Algeria": "Argelia", "Mali": "Mali",
    "Ivory Coast": "Costa de Marfil", "DR Congo": "RD Congo",
    "Tanzania": "Tanzania", "Guinea": "Guinea", "Burkina Faso": "Burkina Faso",
    "South Africa": "Sudáfrica", "Zambia": "Zambia", "Kenya": "Kenia",
    "Iraq": "Irak", "Jordan": "Jordania", "United Arab Emirates": "Emiratos Árabes",
    "Uzbekistan": "Uzbekistán", "Indonesia": "Indonesia", "Thailand": "Tailandia",
    "China PR": "China", "India": "India", "Vietnam": "Vietnam",
    "Panama": "Panamá", "Jamaica": "Jamaica", "Honduras": "Honduras",
    "El Salvador": "El Salvador", "Cuba": "Cuba", "Trinidad and Tobago": "Trinidad y Tobago",
    # Variantes de nombre que devuelve la API y no se traducían (faltaba la bandera)
    "South Korea": "Corea del Sur", "Czechia": "República Checa",
    "Congo DR": "RD Congo", "DR Congo": "RD Congo",
    "Haiti": "Haití", "Curacao": "Curazao", "Cape Verde": "Cabo Verde",
    "Bosnia and Herzegovina": "Bosnia y Herzegovina", "Bosnia-Herzegovina": "Bosnia y Herzegovina",
}

def to_es(name: str) -> str:
    return TEAM_ES.get(name, name)

def madrid_time(utc_str: str) -> str:
    """Convierte ISO UTC a HH:MM en hora de Madrid (UTC+2 en verano)."""
    dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    madrid = dt + timedelta(hours=2)  # CEST (verano); el Action corre a las 9am Madrid, cuando los partidos nocturnos de EEUU/México ya han terminado
    return madrid.strftime("%H:%M")

def format_group(raw: str) -> str:
    """Convierte GROUP_F → Grupo F, GROUP_STAGE → Fase de grupos, etc."""
    if not raw:
        return ""
    if raw.startswith("GROUP_"):
        letter = raw.replace("GROUP_", "")
        return f"Grupo {letter}"
    return raw.replace("_", " ").title()

OUTPUT_FILE = "matches.json"


def fetch_chunk(date_from: str, date_to: str) -> dict:
    """Pide a la API los partidos entre date_from y date_to (YYYY-MM-DD, inclusive)
    y los devuelve agrupados por su fecha real en Madrid: { "2026-06-15": [...] }."""
    url = (
        f"https://api.football-data.org/v4/competitions/{COMPETITION}/matches"
        f"?dateFrom={date_from}&dateTo={date_to}"
    )
    req = Request(url, headers={"X-Auth-Token": TOKEN})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except HTTPError as e:
        print(f"❌ Error HTTP {e.code} al llamar a la API ({date_from}→{date_to}).", file=sys.stderr)
        return {}

    days = {}
    for m in data.get("matches", []):
        kick_utc = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        kick_madrid = kick_utc + timedelta(hours=2)  # CEST

        day_key = kick_madrid.strftime("%Y-%m-%d")  # fecha real del partido en Madrid
        match = {
            "id": f"m{m['id']}",
            "home": to_es(m["homeTeam"]["name"]),
            "away": to_es(m["awayTeam"]["name"]),
            "time": kick_madrid.strftime("%H:%M"),
            "datetime": kick_madrid.strftime("%Y-%m-%dT%H:%M"),
            "group": format_group(m.get("group") or m.get("stage") or ""),
        }
        if m.get("status") == "FINISHED" and m.get("score", {}).get("fullTime"):
            ft = m["score"]["fullTime"]
            if ft.get("home") is not None and ft.get("away") is not None:
                match["result"] = {"home": ft["home"], "away": ft["away"]}
            # Ganador real (necesario en eliminatorias con prórroga/penaltis)
            winner_raw = m.get("score", {}).get("winner")
            if winner_raw == "HOME_TEAM":
                match["winner"] = "home"
            elif winner_raw == "AWAY_TEAM":
                match["winner"] = "away"
        days.setdefault(day_key, []).append(match)
    return days


def daterange_chunks(start: datetime, end: datetime, max_days: int = 9):
    """Parte [start, end] en tramos de como mucho max_days (límite del plan gratuito)."""
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=max_days - 1), end)
        yield cur.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")
        cur = chunk_end + timedelta(days=1)


def fetch_matches() -> dict:
    """Decide la ventana de fechas. Por defecto ±1 día (ejecución diaria).
    Si DATE_FROM/DATE_TO están definidos (backfill manual), usa ese rango."""
    if not TOKEN:
        print("⚠️  FOOTBALL_TOKEN no configurado — no se piden partidos.")
        return {}

    # Naive (sin tz): solo se usan para construir cadenas YYYY-MM-DD
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    env_from = os.environ.get("DATE_FROM", "").strip()
    env_to = os.environ.get("DATE_TO", "").strip()

    if env_from:
        start = datetime.strptime(env_from, "%Y-%m-%d")
        end = datetime.strptime(env_to, "%Y-%m-%d") if env_to else now
        print(f"🗓️  Backfill: {start:%Y-%m-%d} → {end:%Y-%m-%d}")
    else:
        start = now - timedelta(days=1)
        end = now + timedelta(days=1)

    fetched = {}
    for d_from, d_to in daterange_chunks(start, end):
        chunk = fetch_chunk(d_from, d_to)
        for day, matches in chunk.items():
            fetched.setdefault(day, []).extend(matches)

    total = sum(len(v) for v in fetched.values())
    print(f"✅ {total} partido(s) en {len(fetched)} día(s): {sorted(fetched.keys())}.")
    return fetched


def load_existing() -> dict:
    """Carga el matches.json actual del repo para no perder el histórico."""
    if not os.path.exists(OUTPUT_FILE):
        return {}
    try:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  No se pudo leer {OUTPUT_FILE} existente: {e}", file=sys.stderr)
        return {}


def merge(existing: dict, fetched: dict) -> dict:
    """Fusiona los partidos nuevos sobre el histórico SIN borrar días anteriores.
    Cada partido se identifica por su id dentro del día: si ya existe se actualiza
    (así un partido que terminó recibe su 'result'); si es nuevo se añade."""
    for day, matches in fetched.items():
        bucket = existing.setdefault(day, [])
        by_id = {m["id"]: i for i, m in enumerate(bucket) if "id" in m}
        for m in matches:
            if m["id"] in by_id:
                old = bucket[by_id[m["id"]]]
                # Nunca perder un resultado ya guardado si la API lo devuelve sin él
                if "result" not in m and "result" in old:
                    m["result"] = old["result"]
                bucket[by_id[m["id"]]] = m   # actualiza (puede traer resultado nuevo)
            else:
                bucket.append(m)
        bucket.sort(key=lambda x: x.get("datetime") or x.get("time", ""))

    # Reordenar los días cronológicamente
    return {day: existing[day] for day in sorted(existing.keys())}


def get_fcm_access_token(creds_json: str) -> str:
    """Obtiene un OAuth2 access token para la API de FCM v1."""
    info = json.loads(creds_json)
    creds = google.oauth2.service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/firebase.messaging"]
    )
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def send_notifications(creds_json: str, body: str):
    """Envía una notificación push a todos los tokens registrados en Firebase."""
    if not FCM_AVAILABLE:
        print("⚠️  google-auth no disponible, omitiendo notificaciones.")
        return

    # Leer tokens desde Firebase REST API
    db_url = "https://mundial-99cdc-default-rtdb.europe-west1.firebasedatabase.app/fcm_tokens.json"
    try:
        with urlopen(db_url, timeout=10) as r:
            tokens_data = json.loads(r.read()) or {}
    except Exception as e:
        print(f"⚠️  No se pudieron leer los tokens FCM: {e}", file=sys.stderr)
        return

    if not tokens_data:
        print("ℹ️  No hay tokens FCM registrados.")
        return

    access_token = get_fcm_access_token(creds_json)
    sent = 0
    for safe_token, entry in tokens_data.items():
        real_token = entry.get("token") if isinstance(entry, dict) else None
        if not real_token:
            continue
        payload = json.dumps({
            "message": {
                "token": real_token,
                "notification": {
                    "title": "⚽ Quiniela Mundial 2026",
                    "body": body,
                },
                "webpush": {
                    "fcmOptions": {"link": "https://majadas21.github.io/mundial/"}
                }
            }
        }).encode()
        req = Request(FCM_URL, data=payload, headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })
        try:
            urlopen(req, timeout=10)
            sent += 1
        except Exception as e:
            print(f"⚠️  Error enviando a token {safe_token[:20]}…: {e}", file=sys.stderr)

    print(f"🔔 Notificaciones enviadas: {sent}/{len(tokens_data)}")


if __name__ == "__main__":
    fetched = fetch_matches()
    existing = load_existing()
    merged = merge(existing, fetched)

    new_days = sorted(set(merged) - set(existing))
    if new_days:
        print(f"➕ Días añadidos: {new_days}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"📄 {OUTPUT_FILE} actualizado: {len(merged)} día(s) en total.")

    # Enviar notificación push si hay cambios y hay credenciales Firebase
    creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
    if creds_json and fetched:
        today = datetime.now(timezone.utc).strftime("%d/%m")
        send_notifications(creds_json, f"Partidos del {today} actualizados — ¡haz tu pronóstico!")
