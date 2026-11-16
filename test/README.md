# Proyecto de prueba de `agentic-loop`

Fixture para validar el skill [agentic-loop](../.github/skills/agentic-loop/SKILL.md): un `slugify()` con 5 defectos que el loop debe corregir uno por iteración.

## Contenido

| Fichero | Qué es |
|---|---|
| `slug.py` | `slugify()` con defectos (acentos, grupos de guiones, guiones en los extremos, recorte, resultado vacío). Es lo que el loop modifica. |
| `check.py` | Comprobador de 10 casos. No se modifica. Imprime `n/10` y sale con código 0 solo si pasan todos. |

## Ejecutar la prueba

1. Abre la **raíz del repo** en VS Code, con Copilot Chat en modo Agent.
2. Comprueba el estado inicial: `cd test && python check.py` → `4/10`, código de salida 1.
3. Lanza el prompt `/test_skill` ([.github/prompts/test_skill.prompt.md](../.github/prompts/test_skill.prompt.md)); incluye la checklist de qué comprobar al terminar.
4. Resultado esperado: `python check.py` → `10/10`, código 0, `check.py` sin modificar, y un registro en `loops/<fecha>-<slug>/` (en la raíz del repo, ignorado por git) con `loop.md`, `state.json`, una carpeta por iteración y `report.md`.

## Volver a empezar

`slug.py` debe estar en su versión con defectos para que la prueba sea repetible. Después de una ejecución:

```bash
git restore test/slug.py
```
