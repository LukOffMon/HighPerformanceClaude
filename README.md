# ⚡ High-Performance Claude

**Una skill para Claude que le pone la disciplina de un ingeniero staff:** gasta menos tokens, se equivoca menos, sopesa opciones antes de decidir y comprueba que lo que hizo funciona antes de decirte que está listo.

Sirve para cualquier lenguaje o stack y para cualquier tarea: vibecoding (de una idea a un producto que funciona), features, bugs, refactors, code review, decisiones de arquitectura, migraciones y sesiones largas en modo agente.

```
/plugin marketplace add LukOffMon/HighPerformanceClaude
/plugin install hpc@high-performance-claude
```

---

## Qué cambia en la práctica

| Sin la skill | Con High-Performance Claude |
|---|---|
| Lee archivos enteros para encontrar una función | Primero busca, luego lee solo el rango que importa; un solo `repo_brief.py` sustituye decenas de lecturas exploratorias |
| El mismo proceso pesado para un typo que para una migración | **Triage T0/T1/T2**: el nivel de proceso depende del riesgo de la tarea |
| Usa APIs de memoria (de otra versión) | Comprueba la versión instalada y lee los tipos o la doc antes de usar una API |
| Elige la librería que le suena | Compara 2–3 opciones con criterios explícitos, hace un pre-mortem y te da una recomendación |
| "Ya debería funcionar" | **Escalera de verificación**: diff → typecheck → lint → tests → ejecutarlo de verdad → revisión adversarial. Lo que no se comprobó, se dice |
| Repite el mismo arreglo fallido en bucle | **Cortacircuitos**: tras 2 intentos fallidos para y busca evidencia nueva; tras 3, cambia de enfoque o te pregunta |
| Borra o debilita tests para ponerlos en verde | Prohibido |
| En sesiones largas pierde el hilo al compactar el contexto | Archivos de handoff y memoria del proyecto (`CLAUDE.md`) |
| Muros de texto | El resultado primero, luego la evidencia y los riesgos, en tu idioma |

---

## Instalación

### Opción A — Plugin de Claude Code (recomendada)

Dentro de Claude Code:

```
/plugin marketplace add LukOffMon/HighPerformanceClaude
/plugin install hpc@high-performance-claude
```

En versiones recientes de Claude Code también funciona en un solo paso:

```
/plugin install hpc --marketplace LukOffMon/HighPerformanceClaude
```

Incluye la skill, los scripts, los 2 agentes y los 9 comandos (`/hpc:ship`, `/hpc:vibe`…). Para actualizar: `/plugin marketplace update high-performance-claude`.

### Opción B — Instalador manual (sin sistema de plugins)

```bash
git clone https://github.com/LukOffMon/HighPerformanceClaude.git
cd HighPerformanceClaude
./install.sh                         # para tu usuario (~/.claude)
./install.sh --project ../mi-app     # solo para un proyecto (mi-app/.claude)
./install.sh --uninstall             # desinstalar
```

O en una línea: `curl -fsSL https://raw.githubusercontent.com/LukOffMon/HighPerformanceClaude/main/install.sh | bash`

Con esta opción los comandos se llaman `/hpc-ship`, `/hpc-vibe`, etc.

### Opción C — claude.ai (web o app de escritorio)

1. Descarga [`dist/high-performance.zip`](dist/high-performance.zip).
2. En claude.ai ve a **Settings → Capabilities → Skills** y súbelo (hace falta tener activada la ejecución de código).
3. La skill se carga sola en las tareas de programación. En claude.ai no hay agentes ni comandos slash, pero la skill y sus scripts funcionan igual.

### Opción D — Adjuntando este repo

Si adjuntas este repositorio a una sesión o a un proyecto, el `CLAUDE.md` de la raíz le dice a Claude que aplique la skill a todo el trabajo de esa sesión.

---

## 🧊 Iceberg

Escribe **`Iceberg`** antes de tu tarea (o usa `/hpc:iceberg <tarea>`). Claude baja por la petición antes de tocar nada, con la profundidad que pide la tarea: una errata no lleva brief, un cambio normal lleva 3 líneas y una app nueva lleva el descenso completo.

1. **Memoria** — si conectaste Obsidian, lee tu perfil, la nota del proyecto y las lecciones recientes (resumen con límite de líneas).
2. **Superficie** — qué pediste, en una frase, y qué se entrega.
3. **Línea de flotación** — lo que quisiste decir: requisitos implícitos, restricciones del repo, ambigüedades resueltas con evidencia.
4. **Profundidades** — riesgos, puntos donde es fácil equivocarse, áreas de mejora y opciones comparadas.
5. **Herramientas** — en tareas grandes, revisa qué servidores MCP, plugins y permisos le faltan a este proyecto.
6. **Lecho** — reescribe tu prompt como un `ICEBERG BRIEF` de ≤15 líneas con criterios comprobables, presupuesto de tokens y plan por partes.

Luego ejecuta parte por parte, verificando cada una, sin repetir lo que falla y sin declarar "listo" lo que no vio funcionar. Al terminar guarda el brief y las lecciones en tu vault.

### Conectar Obsidian (`/hpc:obsidian`)

Crea en tu vault una carpeta `Claude/` y te pregunta lo justo para rellenar tu perfil:

```
Claude/
├── README.md        qué es cada cosa
├── Profile.md       idioma, stack, estilo (Claude lo lee en cada tarea; ≤40 líneas)
├── Lessons.md       una línea por error que no debe repetirse
├── Projects/        una nota por proyecto: stack, comandos, decisiones, trampas
├── Briefs/          cada ICEBERG BRIEF con su resultado + Index.md
└── Templates/       plantillas Brief / Project / Lesson (plugin Templates de Obsidian)
```

Encuentra el vault solo, leyendo la configuración de Obsidian (macOS, Windows, Linux, Flatpak y Snap); también puedes indicarlo con `OBSIDIAN_VAULT=/ruta`. Nunca sobrescribe notas existentes ni escribe fuera de `Claude/`, salvo `.obsidian/templates.json` si no existe. Para ahorrar tokens, Claude nunca recorre el vault: usa `vault.py context` (resumen con límite) y `vault.py recall` (las mejores coincidencias, 3 líneas cada una).

### Herramientas y permisos (`/hpc:setup`)

Detecta tu stack y lo que ya tienes instalado, y recomienda solo lo que falta para ese proyecto: Context7 (documentación de la versión instalada), Playwright (ver y probar la interfaz), GitHub, Supabase, Sentry, Stripe, con su comando de instalación. Propone además una lista de permisos seguros (git de solo lectura, búsquedas, y los scripts de build, lint y test del proyecto) y bloquea leer `.env`, el force-push y `git reset --hard`. No instala ni escribe nada sin tu sí.

Sitio explicativo (iceberg animado en el Antártico): https://lukoffmon.github.io/HighPerformanceClaude/ — fuente en `site/iceberg.html`, publicado desde `docs/` con GitHub Pages.

## 🧻 Toilet Bamboo Paper GeekMcON

Una **app de escritorio** (Windows, macOS, Linux) que le da memoria a Claude: un cajón (*çekmece* en turco) de notas Markdown que Claude ordena solo, con un cajón por proyecto, paquetes de memoria con tope de tokens, búsqueda con ranking, compatibilidad con Obsidian y **Rollito**, un asistente pixel art que narra todo lo que pasa. Se conecta a Claude Code por MCP: pide permiso una vez y desde entonces es automático.

**Descargar:** [Windows (.exe)](https://github.com/LukOffMon/HighPerformanceClaude/releases/latest/download/Cekmecon-Setup-Windows.exe) · [macOS (.dmg)](https://github.com/LukOffMon/HighPerformanceClaude/releases/latest/download/Cekmecon-macOS.dmg) · [Linux (.tar.gz)](https://github.com/LukOffMon/HighPerformanceClaude/releases/latest/download/Cekmecon-Linux-x86_64.tar.gz) — programa normal, sin Python; al abrirlo se conecta solo a Claude Code.

Sitio (el rollo que se desenrolla): https://lukoffmon.github.io/HighPerformanceClaude/cekmecon/ — detalles en [`apps/cekmecon/README.md`](apps/cekmecon/README.md). La skill `cekmecon` del plugin le enseña a Claude a usarla.

---

## Uso

**Automático.** La skill se activa sola en cualquier tarea de programación. No tienes que hacer nada.

**Comandos** (nombre del plugin; con `install.sh` cambia `hpc:` por `hpc-`):

| Comando | Para qué |
|---|---|
| `/hpc:brief` | Radiografía del repo en una llamada: stack, comandos, estructura, CI, archivos grandes, estado de git |
| `/hpc:plan <tarea>` | Plan antes de tocar código: nivel, criterios de aceptación, opciones, fases, riesgos |
| `/hpc:options <decisión>` | Matriz de decisión con 2–4 opciones puntuadas, pre-mortem y recomendación |
| `/hpc:ship <tarea>` | El ciclo completo de principio a fin, con verificación y reporte con evidencia |
| `/hpc:vibe <idea>` | Modo vibecoding: idea → producto completo, pulido y funcionando, con capturas |
| `/hpc:debug <síntoma>` | Depuración científica: reproducir → aislar → hipótesis → causa raíz → arreglo → test de regresión |
| `/hpc:review [objetivo]` | Revisión del diff con hallazgos verificados por gravedad (con `path:línea`) |
| `/hpc:iceberg <tarea>` | Modo Iceberg: descenso adaptado a la tarea → brief → construcción verificada por partes |
| `/hpc:obsidian` | Conecta tu vault de Obsidian como memoria de Claude (perfil, proyectos, briefs, lecciones) |
| `/hpc:setup` | Revisa qué MCP, plugins y permisos le faltan al proyecto y los propone |
| `/hpc:handoff` | Guarda el estado de la sesión para retomarla tras una compactación o en otra sesión |
| `/hpc:memory` | Crea o ajusta un `CLAUDE.md` mínimo para que las próximas sesiones arranquen rápido |

**Agentes:**
- `hpc-scout`: exploración barata y de solo lectura (modelo rápido). Hace las búsquedas amplias sin llenar tu contexto y devuelve solo conclusiones con `archivo:línea`.
- `hpc-critic`: revisor adversarial con ojos frescos (tu mismo modelo). Intenta romper el cambio antes de que lo hagan tus usuarios.

**Ejemplos:**

```
/hpc:vibe un tracker de hábitos con rachas, modo oscuro y que guarde en local
/hpc:debug el checkout falla con 500 cuando el carrito tiene un cupón
/hpc:options ¿Supabase o Postgres propio con Drizzle para este proyecto?
/hpc:ship añade exportación a CSV en la página de reportes
```

---

## Cómo funciona

```
SKILL.md (siempre cargado, ~1.6k palabras ≈ 2.5k tokens)
├─ 0. Directivas: evidencia > memoria · cambio mínimo · verificar antes de afirmar · decidir con criterio
├─ 1. Triage T0 / T1 / T2: el proceso escala con el riesgo
├─ 2. Ciclo: Orientar → Definir "hecho" → Decidir → Construir en fases → Verificar → Reportar
├─ 3. Economía de tokens (reglas duras)
├─ 4. Prevención de errores + cortacircuitos
├─ 5. Modos → cargan su referencia solo cuando hace falta
└─ 6. Autochequeo final

references/  (se cargan bajo demanda: 0 tokens hasta que se necesitan)
  token-economy · decisions · verification · debugging · vibecoding
  failure-modes · stack-traps · review · delegation · context-and-memory · communication

scripts/  (Python, solo biblioteca estándar, no ejecutan nada del proyecto salvo en checks.py --run)
  repo_brief.py  → orientación completa en ~60 líneas
  checks.py      → detecta y ejecuta typecheck/lint/test/build; muestra solo las líneas que importan
```

**Divulgación progresiva:** solo `SKILL.md` ocupa contexto siempre. Las referencias se leen cuando el modo lo necesita, y los scripts se ejecutan sin cargar su código en el contexto. Así la skill añade capacidad sin cobrarte tokens por lo que no usas.

**¿Por qué la skill está en inglés?** El inglés gasta menos tokens que el español y los modelos siguen mejor las instrucciones en inglés. Claude te responde siempre en tu idioma; es una de sus reglas.

### Ejemplo de `repo_brief.py`

```
# Repo brief: mi-app
Languages: TypeScript 142f/18,204L, CSS 12f/900L
## Stack
- JS package manager: pnpm
- JS stack: Next.js 15.1.0, React 19.0.0, Prisma, Tailwind, Zod, Vitest
## Commands
- Verification ladder (scripts/checks.py --run):
    typecheck pnpm typecheck   [package.json:typecheck]
    lint      pnpm lint        [package.json:lint]
    test      pnpm test        [package.json:test]
## Large text files (grep, don't read whole)
- src/generated/schema.ts  412KB
## Git
- branch: feat/csv; uncommitted changes: 3
```

---

## Lo que esta skill puede y no puede hacer

Una skill no le da a un modelo conocimientos que no tiene. Lo que sí hace es quitar las causas más comunes de malos resultados: falta de contexto, sobrarle contexto, decisiones precipitadas, no verificar, bucles y comunicación confusa. Esas causas explican la mayoría de los fallos del día a día al programar con IA, y ahí es donde esta skill marca la diferencia.

En [`evals/scenarios.md`](evals/scenarios.md) hay 12 escenarios para comparar sesiones con y sin la skill.

---

## Desarrollo

```bash
python3 tools/validate.py     # valida frontmatter, límites, enlaces, manifiestos, agentes, comandos, zip
python3 tools/package.py      # regenera dist/*.zip, uno por skill (determinista)
python3 tools/build_site.py   # regenera docs/ (iceberg y cekmecon) desde site/
python3 -m unittest discover -s apps/cekmecon/tests   # pruebas de la app GeekMcON
python3 tools/token_report.py # coste en tokens: siempre cargado / al activarse / bajo demanda
claude plugin validate .      # validación oficial de Claude Code
```

La CI (`.github/workflows/validate.yml`) ejecuta todo esto en cada push. Reglas para editar la skill: [`CLAUDE.md`](CLAUDE.md).

```
.
├── .claude-plugin/        plugin.json · marketplace.json · icon.png
├── apps/cekmecon/         app de escritorio GeekMcON (Python stdlib, UI web, puente MCP, instaladores)
├── skills/cekmecon/       cómo usa Claude la app
├── skills/iceberg/
│   ├── SKILL.md
│   ├── references/        depth-probes.md · toolbelt.md
│   └── scripts/           vault.py (Obsidian) · toolbelt.py (herramientas y permisos)
├── skills/high-performance/
│   ├── SKILL.md
│   ├── references/        11 guías bajo demanda
│   └── scripts/           repo_brief.py · checks.py · hpc_detect.py
├── agents/                hpc-scout.md · hpc-critic.md
├── commands/              12 comandos
├── tools/                 validate.py · package.py · build_site.py · token_report.py
├── evals/                 scenarios.md
├── site/ · docs/          sitios del iceberg y de GeekMcON (fuente · GitHub Pages)
├── dist/                  high-performance.zip · iceberg.zip · cekmecon.zip (para claude.ai)
├── install.sh
└── CLAUDE.md
```

Licencia MIT.
