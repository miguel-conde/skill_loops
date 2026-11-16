# Subagentes en el loop

Este documento define cómo se instruye a cada rol y qué debe devolver. Guarda cada brief como `subagents/<rol>-<n>.brief.md` y cada respuesta como `subagents/<rol>-<n>.result.md` dentro de la carpeta de la iteración.

## Contenido

1. Reglas comunes
2. Planificador
3. Ejecutor
4. Verificador
5. Paralelismo y dependencias
6. Fallos

---

## 1. Reglas comunes

Un buen brief permite que alguien sin ningún contexto haga el trabajo bien a la primera. Debe incluir siempre:

- **Objetivo de la tarea** en una frase.
- **Contexto mínimo necesario**, o rutas a los archivos donde está. Nada de "como hablamos antes".
- **Criterio de hecho**: cómo sabrá el subagente que ha terminado.
- **Restricciones**: qué no debe tocar, qué acciones tiene prohibidas, dónde puede escribir.
- **Formato de salida** exacto (ver cada rol).
- **Dónde dejar los artefactos**: normalmente `iter_<nnn>/` o el área de trabajo acordada en `loop.md`.

Los subagentes nunca deciden la terminación del loop ni ejecutan acciones marcadas como "con confirmación" en `loop.md`. Si creen necesitarlas, lo indican en su respuesta y el orquestador pregunta al usuario.

---

## 2. Planificador

**Recibe:** `loop.md`, `state.json` y el `verification.md` más reciente.

**Plantilla de brief:**

```markdown
# Brief: planificador, iteración <n>

## Objetivo del loop
<copiado de loop.md>

## Estado actual
- Criterios cumplidos: <lista>
- Criterios pendientes: <lista con valor actual y umbral>
- Hipótesis descartadas: <lista>
- Errores repetidos: <firma y número de veces>
- Reflexión de la iteración anterior: <qué cambiar>

## Tu tarea
Propón las tareas de esta iteración. Prioriza lo que más acerque a los criterios pendientes.
No repitas hipótesis descartadas. Si un error se ha repetido, propón una estrategia distinta.
Máximo <k> tareas. Si crees que el loop está bloqueado o que el objetivo es inalcanzable, dilo y explica por qué.

## Formato de salida
Devuelve exactamente la estructura de plan.md descrita abajo.
```

**Devuelve (`plan.md`):**

```markdown
# Plan iteración <n>

## Enfoque
<1-3 frases: qué se intenta y por qué difiere de la iteración anterior>

## Tareas
| id | tarea | criterio de hecho | depende de | criterio de éxito al que apunta |
|----|-------|-------------------|------------|---------------------------------|
| T1 | ...   | ...               | -          | C2                              |

## Riesgos o bloqueos detectados
<o "ninguno">
```

---

## 3. Ejecutor

**Recibe:** un brief por tarea. No recibe el plan completo salvo que la tarea lo requiera.

**Plantilla de brief:**

```markdown
# Brief: ejecutor <id-tarea>, iteración <n>

## Tarea
<descripción concreta>

## Contexto
<lo imprescindible, o rutas a archivos>

## Criterio de hecho
<cómo saber que has terminado>

## Restricciones
- Escribe solo en: <rutas>
- No hagas: <acciones prohibidas o que requieren confirmación>

## Formato de salida
Devuelve la estructura de resultado de ejecutor. Los detalles largos (logs, diffs, tablas) van a archivos; en la respuesta, solo la ruta.
```

**Devuelve:**

```markdown
# Resultado <id-tarea>

- Estado: completada | parcial | fallida
- Qué hice: <3-6 líneas>
- Artefactos: <rutas>
- Evidencia: <comando ejecutado y resultado resumido, o ruta a la salida>
- Problemas: <errores con su mensaje exacto, o "ninguno">
- Necesito confirmación para: <acción, o "nada">
```

---

## 4. Verificador

El verificador es la pieza más importante del loop: es lo que impide declarar éxito sin pruebas.

**Recibe:** los criterios de `loop.md` con su método de verificación, las rutas a los artefactos y el `verification.md` anterior (para medir progreso). **No recibe** el razonamiento de los ejecutores ni sus afirmaciones de éxito, solo las rutas.

**Plantilla de brief:**

```markdown
# Brief: verificador, iteración <n>

## Criterios
| id | criterio | método de verificación | umbral |
|----|----------|------------------------|--------|

## Artefactos disponibles
<rutas>

## Resultado anterior
<ruta a verification.md anterior>

## Tu tarea
Comprueba cada criterio ejecutando su método de verificación. No te fíes de afirmaciones;
basa cada veredicto en una evidencia que puedas citar (salida de comando, valor medido, línea de archivo).
Indica si hubo progreso respecto al resultado anterior. Una mejora dentro del ruido no cuenta como progreso.
Si el loop define un indicador secundario (ver `loop.md`), mídelo y repórtalo aparte: no interviene en el veredicto de ningún criterio.
```

**Devuelve (`verification.md`):**

```markdown
# Verificación iteración <n>

| id | cumplido | valor actual | valor anterior | evidencia |
|----|----------|--------------|----------------|-----------|
| C1 | sí       | ...          | ...            | ...       |

- Todos cumplidos: sí | no
- Progreso respecto a la iteración anterior: sí | no — <qué mejoró>
- Indicador secundario (solo si el loop lo define): <valor actual> (anterior: <valor>) — mejora: sí | no
- Errores observados (firma corta): <lista o "ninguno">
- Observaciones: <problemas en el propio método de verificación, si los hay>
```

La "firma" de un error es una etiqueta corta y estable que permite reconocerlo si se repite, por ejemplo `ImportError:pandas` o `test_fechas:assert`. Se pasa a `loop.py iter-end --error`.

---

## 5. Paralelismo y dependencias

- Lanza en paralelo las tareas sin dependencias entre sí, hasta `limites.max_subagentes_paralelos`.
- Si dos tareas escriben en el mismo archivo, no son independientes aunque lo parezcan: van en secuencia.
- El verificador siempre va después de todos los ejecutores de la iteración.
- Profundidad 1: los subagentes no lanzan otros subagentes. Si una tarea es demasiado grande para uno, el planificador debe partirla.

---

## 6. Fallos

- **Sin respuesta o respuesta inutilizable:** reintenta una vez con un brief más concreto (más contexto, criterio de hecho más claro).
- **Segundo fallo:** marca la tarea como fallida en `log.md` con el motivo. El planificador la reconsiderará en la siguiente iteración.
- **El subagente pide confirmación:** el orquestador pregunta al usuario. Mientras tanto, la tarea queda pendiente y el resto de la iteración continúa si no depende de ella.
