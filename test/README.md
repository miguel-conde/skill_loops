# skill_loops

Skill `agentic-loop` para agentes de IA (GitHub Copilot, Claude, etc.) y un proyecto de prueba para validarlo.

## Qué es

`agentic-loop` ejecuta ciclos agénticos iterativos hasta cumplir un objetivo verificable (por ejemplo, que pasen los tests). Define objetivo, criterios de éxito, límites y salvaguardas; orquesta subagentes (planificador, ejecutores, verificador) y registra cada iteración en `loops/`.

Documentación completa: [.github/skills/agentic-loop/SKILL.md](.github/skills/agentic-loop/SKILL.md).

## Estructura

```
.github/skills/agentic-loop/
├── SKILL.md        # protocolo del skill
├── scripts/loop.py # estado y límites del loop (init, contadores, timestamps)
├── assets/         # plantillas de loop, estado, entrada, log e informe
└── references/     # registro y subagentes
check.py            # comprobador de slugify() (no modificar)
slug.py             # función slugify() con defectos a corregir
PROMPT.md           # prompt y checklist de la prueba
```

## Prueba del skill

1. Abre el proyecto en VS Code con Copilot Chat en modo Agent.
2. Estado inicial: `python check.py` devuelve `4/10` y código de salida 1.
3. Pega el prompt de [PROMPT.md](PROMPT.md).
4. Resultado esperado: `python check.py` devuelve `10/10` (código 0) y se genera `loops/<fecha>-<slug>/` con `loop.md`, `state.json`, una carpeta por iteración y `report.md`.

## Uso de `loop.py`

```bash
python .github/skills/agentic-loop/scripts/loop.py init --title "Objetivo corto" --max-iter 10 --stall 3
```
