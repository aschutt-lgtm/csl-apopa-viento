# CSL Apopa — Panel de Riesgo de Viento
### Activo de Grupo Logístico Mesoamérica, S.A. · Actualización automática diaria vía Open-Meteo

---

## Qué hay en este paquete

| Archivo | Descripción | Se actualiza |
|---|---|---|
| `csl_apopa_viento.html` | El dashboard — esto es lo que se ve en la web | **Diario, automático** |
| `template.html` | Plantilla base (diseño, CSS, lógica de riesgo) | Manual, solo si se cambia el diseño |
| `update_dashboard.py` | Script que consulta Open-Meteo y reconstruye el HTML | — |
| `.github/workflows/daily-update.yml` | Programación de GitHub Actions (corre el script solo) | — |

No se necesita ninguna API key. Open-Meteo es gratuito.

---

## Configuración inicial (una sola vez, ~15 minutos)

### Paso 1 — Crear una cuenta de GitHub
Entrar a [github.com](https://github.com) y registrarse (gratis).

### Paso 2 — Crear un repositorio nuevo
1. Clic en el botón **+** (arriba a la derecha) → **New repository**
2. Nombre sugerido: `csl-apopa-viento`
3. Marcar como **Public** (necesario para que GitHub Pages sea gratuito y accesible para el equipo de Diana sin login)
4. Clic en **Create repository**

### Paso 3 — Subir todos los archivos
1. En la página del repositorio, clic en **Add file → Upload files**
2. Arrastrar TODOS los archivos de esta carpeta, manteniendo la estructura:
   - `csl_apopa_viento.html`
   - `template.html`
   - `update_dashboard.py`
   - `.github/workflows/daily-update.yml`  ⚠️ debe subirse con esa ruta completa, incluyendo las carpetas `.github/workflows/`
3. Clic en **Commit changes**

> Si al arrastrar la carpeta `.github` no respeta la estructura, se puede crear manualmente: **Add file → Create new file**, escribir `.github/workflows/daily-update.yml` como nombre (GitHub crea las carpetas solo) y pegar el contenido.

### Paso 4 — Activar GitHub Pages
1. En el repositorio, ir a **Settings → Pages**
2. En "Source", seleccionar **Deploy from a branch**
3. Branch: **main**, carpeta: **/ (root)**
4. Guardar

A los 2-5 minutos, el dashboard queda accesible en:
```
https://[tu-usuario].github.io/csl-apopa-viento/csl_apopa_viento.html
```

### Paso 5 — Confirmar que la automatización diaria funciona
1. Ir a la pestaña **Actions** del repositorio
2. Debe aparecer el workflow **Daily Dashboard Update**
3. Para probarlo sin esperar al día siguiente: clic en el workflow → **Run workflow** (botón manual) → esperar ~1 minuto → refrescar la página del dashboard

Si el workflow falla (ícono rojo), revisar el log — casi siempre es Open-Meteo temporalmente no disponible; el script reintenta 5 veces con 60 segundos de espera antes de fallar, así que un fallo persistente amerita revisión.

---

## Compartir con el equipo de Diana

El link de GitHub Pages del Paso 4 es público — cualquiera con el link lo puede ver, sin necesidad de cuenta de GitHub ni de Claude. Es el link que se comparte con el equipo de Diana.

Opcional: si se quiere un link más corto/memorable, se puede configurar un dominio propio en **Settings → Pages → Custom domain** (requiere que GLM tenga un subdominio disponible, ej. `viento.grupomesoamerica.com`).

---

## Cambios pendientes de aplicar cuando estén disponibles

Estos valores viven en `template.html`, dentro del bloque `CONFIG` cerca del final del archivo:

```js
const CONFIG = {
  ...
  designWindKmh: 130,          // ← placeholder: reemplazar con la velocidad de diseño real de la cubierta
  knownIncidents: []           // ← agregar aquí los 3 percances históricos cuando se tengan las fechas
};
```

Cuando se instale el anemómetro físico en sitio, ese es un cambio más grande (agregar una fuente de datos en tiempo real al script), y con gusto lo armamos cuando llegue ese momento.

---

## Fuentes de datos

- Pronóstico y clima histórico: [Open-Meteo](https://open-meteo.com) (modelos ECMWF IFS / GFS, gratuito, sin API key)
- Alertas regionales oficiales de referencia: Dirección General del Observatorio de Amenazas de El Salvador ([snet.gob.sv](https://www.snet.gob.sv)) y NOAA/NHC para sistemas del Pacífico
