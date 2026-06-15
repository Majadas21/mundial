# ⚽ Quiniela Mundial 2026

App de quinielas para el Mundial para jugar con amigos, alojada gratis en GitHub Pages.

## 🚀 Cómo publicarla en GitHub Pages (5 minutos)

### Paso 1 — Crea un repositorio en GitHub
1. Ve a [github.com/new](https://github.com/new)
2. Nómbralo `mundial-quiniela` (o como quieras)
3. Márcalo como **público**
4. Haz clic en **Create repository**

### Paso 2 — Sube el archivo
```bash
# Opción A: desde la web
# Arrastra index.html directamente en la página del repositorio

# Opción B: desde terminal
git init
git add index.html
git commit -m "Quiniela Mundial 🏆"
git remote add origin https://github.com/TU_USUARIO/mundial-quiniela.git
git push -u origin main
```

### Paso 3 — Activa GitHub Pages
1. En tu repositorio → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / `root`
4. Guarda → en 1-2 minutos tendrás la URL: `https://TU_USUARIO.github.io/mundial-quiniela/`

### Paso 4 — Comparte la URL con tus amigos 🎉

---

## ⚠️ Limitación importante: datos compartidos

Actualmente la app guarda los votos en `localStorage` del navegador de cada uno.
Esto significa que **cada amigo ve solo sus propios votos**, no los del resto.

### Opciones para compartir votos entre amigos:

#### Opción A — Gist de GitHub (recomendada, gratis)
Necesitas crear un GitHub Gist para actuar como mini base de datos compartida:

1. Ve a [gist.github.com](https://gist.github.com)
2. Crea un Gist público llamado `mundial_votes.json` con contenido `{}`
3. Copia el **ID del Gist** (los caracteres al final de la URL)
4. Crea un **Personal Access Token** con permiso `gist` en GitHub Settings → Developer settings → Tokens
5. En `index.html` rellena:
   ```javascript
   const GIST_TOKEN = 'ghp_tutoken...';
   const GIST_ID = 'el_id_del_gist';
   ```

> ⚠️ **Importante**: con esta opción el token es visible en el código. Solo funciona para grupos de confianza (amigos). No lo uses para apps públicas.

#### Opción B — Google Sheets como backend (más seguro)
Puedes usar Google Apps Script como API gratuita. Más complejo de configurar pero sin exponer tokens.

#### Opción C — Firebase Realtime Database (gratis hasta cierto límite)
Firebase ofrece una base de datos en tiempo real gratuita. Ideal si quieres escalarlo.

---

## 📋 Cómo cargar los partidos automáticamente (API)

La app usa [football-data.org](https://www.football-data.org/) para cargar los partidos del día. El token **nunca aparece en el HTML** — lo guarda GitHub como secret y solo lo usa el Action en servidor.

### Paso 1 — Consigue el token de la API
1. Regístrate gratis en [football-data.org/client/register](https://www.football-data.org/client/register)
2. Te llega el token por email

### Paso 2 — Añade el token como GitHub Secret
1. En tu repositorio → **Settings** → **Secrets and variables** → **Actions**
2. Clic en **New repository secret**
3. Nombre: `FOOTBALL_API_TOKEN` (exactamente así)
4. Valor: tu token de football-data.org
5. Guardar

### Paso 3 — Lanza el Action por primera vez
1. Ve a la pestaña **Actions** de tu repositorio
2. Selecciona **"Actualizar partidos del día"**
3. Clic en **Run workflow** → **Run workflow**

A partir de ahí se ejecuta solo cada noche a medianoche (hora Madrid) y genera `matches.json` automáticamente. La app lee ese fichero — sin ningún token en el código público.

Sin configurar el secret, la app carga **partidos de demo** para que puedas probarla.

## 📋 Cómo registrar resultados manualmente (sin API)

En la consola del navegador (F12), escribe:

```javascript
let d = JSON.parse(localStorage.getItem('mundialData_v1'));
d.matches.find(m => m.id === 'm1').result = { home: 2, away: 1 };
localStorage.setItem('mundialData_v1', JSON.stringify(d));
location.reload();
```

---

## 🏆 Sistema de puntuación

| Acierto | Puntos |
|---------|--------|
| Ganador correcto (1, X, 2) | 50 pts |
| + Goles equipo local exactos | +25 pts |
| + Goles equipo visitante exactos | +25 pts |
| **Resultado exacto** | **100 pts** |

---

## 🌍 Banderas incluidas
España, Alemania, Francia, Brasil, Argentina, Portugal, Inglaterra, Italia,
Países Bajos, Bélgica, Croacia, Uruguay, México, Marruecos, Senegal, Japón,
Corea del Sur, Australia, Estados Unidos, Canadá, y muchos más.
