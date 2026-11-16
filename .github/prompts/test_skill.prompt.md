---
name: test_skill
agent: agent
description: Prueba el skill agentic-loop corrigiendo slugify() en slug.py hasta que check.py pase
---

# Prueba del skill agentic-loop en GitHub Copilot (VS Code)

## Preparación
1. Crea una carpeta de proyecto vacía y ábrela en VS Code.
2. Copia en la raíz `slug.py` y `check.py`.
3. Copia el skill (la versión parcheada) en `.github/skills/agentic-loop/`
   (también vale `.claude/skills/agentic-loop/` o `.agents/skills/agentic-loop/`).
   Debe quedar `.github/skills/agentic-loop/SKILL.md` y `scripts/loop.py`.
4. Abre Copilot Chat en **modo Agent** (necesita ejecutar comandos en el terminal).
5. Estado inicial esperado: `python check.py` → `4/10`, código de salida 1.

## Prompt para pegar
Usa el skill agentic-loop.

Objetivo: que slugify() de slug.py pase todos los casos de check.py.
Criterio de éxito: `python check.py` termina con código de salida 0 (última línea `10/10`).
Indicador secundario de progreso: el número de casos correctos que imprime check.py (n/10). No cuenta para el éxito.
Límites: máximo 7 iteraciones. Corrige UN SOLO defecto por iteración. No modifiques check.py.

Al terminar, enséñame el contenido de loops/ y el report.md.

## Qué comprobar al terminar
- [ ] Se creó `loops/<fecha>-<slug>/` con `loop.md`, `state.json`, `iter_000_*` (línea base) y una carpeta por iteración.
- [ ] La iteración 0 midió la línea base (4/10) sin tocar el código.
- [ ] Cada iteración cambió un solo defecto (hay 5: acentos, grupos de guiones, guiones en los extremos, recorte, resultado vacío).
- [ ] Cada `verification.md` tiene evidencia (salida real de `python check.py`) y no una afirmación del agente.
- [ ] `python check.py` final → `10/10`, código 0, y `check.py` sin modificar.
- [ ] `report.md` con la salida clasificada (`exito`).

## Solo si tu copia es la parcheada
- [ ] `loop.md` tiene la sección «Indicador secundario de progreso» rellena desde el pre-flight.
- [ ] `state.json` → `indicador_secundario` definido, y `historial_metricas` con el valor n por iteración.
- [ ] `python .github/skills/agentic-loop/scripts/loop.py init --help` muestra `--secondary`.
- [ ] El contador de estancamiento no sube mientras n crece, aunque el criterio siga en «no cumplido».

Si el agente no usa el skill o no encuentra `loop.py`, es un problema de carga del skill en Copilot, no del loop.