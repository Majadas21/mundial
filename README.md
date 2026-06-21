# ⚽ Quiniela Mundial 2026

App de quinielas para el Mundial 2026 para jugar con amigos. Alojada en GitHub Pages, con Firebase como base de datos en tiempo real y actualización automática de partidos vía GitHub Actions.

## ¿Cómo funciona?

### Partidos
Los partidos se obtienen de la API de [football-data.org](https://www.football-data.org/) mediante una GitHub Action que se ejecuta cada noche. El resultado se guarda en `matches.json`, que es el fichero que lee la app. De esta forma el token de la API nunca aparece en el código público.

### Pronósticos
Cada jugador elige su nombre en la app y vota el resultado de cada partido antes de que empiece. Los votos se guardan en **Firebase Realtime Database** en tiempo real, de forma que todos los participantes ven los pronósticos del resto en cuanto el partido comienza.

### Puntuación
| Acierto | Puntos |
|---------|--------|
| Signo correcto (1, X, 2) | 50 pts |
| + Goles local exactos | +25 pts |
| + Goles visitante exactos | +25 pts |
| **Resultado exacto** | **100 pts** |

Si no votas un partido antes de que empiece, obtienes 0 puntos en ese partido.

### Pestañas
- **Partidos** — pronósticos del día, navegables por fecha
- **Grupos** — clasificación en tiempo real de la fase de grupos
- **Clasificación** — ranking de participantes con evolución histórica

---

## Tecnología

- **Frontend**: HTML + CSS + JavaScript vanilla, sin frameworks
- **Base de datos**: Firebase Realtime Database (plan gratuito)
- **Datos de partidos**: [football-data.org](https://www.football-data.org/) API v4
- **Automatización**: GitHub Actions (cron diario a las 9:00h Madrid)
- **Hosting**: GitHub Pages

---

## Sistema de puntuación detallado

- Pronóstico **exacto** (p. ej. 2-1 cuando el resultado es 2-1): **100 pts**
- Pronóstico con **ganador correcto** pero marcador incorrecto:
  - 50 pts base por el signo
  - +25 pts si los goles del local son exactos
  - +25 pts si los goles del visitante son exactos
- Si el partido empezó y no votaste: **0 pts**
