# Registro del loop

Formato de cada archivo que vive en `loops/<id>/`. Las plantillas correspondientes están en `assets/`.

## Identificadores y timestamps

- Carpeta del loop: `<YYYYMMDD-HHMMSS>-<slug>`, con hora UTC y slug en minúsculas con guiones (por ejemplo `20261116-093012-limpiar-csv-octubre`).
- Carpeta de iteración: `iter_<nnn>_<YYYYMMDD-HHMMSS>`, con número de tres dígitos para que se ordenen bien (`iter_007_20261116-101544`). La iteración 0 es la línea base.
- Dentro de los archivos, timestamps en ISO 8601 UTC (`2026-11-16T09:30:12Z`).

## loop.md

La definición del loop. Se escribe en el pre-flight y no se modifica durante la ejecución, salvo que el usuario cambie algo (en ese caso, se anota el cambio y su fecha al final, en una sección "Cambios").

Secciones: Objetivo, Criterios de éxito (tabla con id, criterio, método de verificación, umbral), Indicador secundario de progreso (opcional; "ninguno" por defecto), Condiciones de terminación, Límites, Acciones (libres y con confirmación), Recursos, Rollback, Cambios.

## state.json

Fuente de verdad entre iteraciones. El script mantiene los campos marcados con (script); el resto los actualiza el orquestador.

```json
{
  "loop_id": "20261116-093012-limpiar-csv-octubre",       // (script)
  "titulo": "Limpiar el CSV de octubre",                   // (script)
  "creado": "2026-11-16T09:30:12Z",                        // (script)
  "estado": "preflight | en_curso | terminado",            // (script)
  "salida": null,                                          // (script) exito | fallo | presupuesto | estancado | bloqueado
  "iteracion_actual": 0,                                   // (script)
  "limites": {
    "max_iteraciones": 10,
    "max_estancamiento": 3,
    "max_repeticiones_error": 3,
    "max_subagentes_paralelos": 3,
    "max_minutos": null
  },
  "criterios": [
    {"id": "C1", "descripcion": "...", "verificacion": "...", "umbral": "...", "cumplido": false, "valor": null}
  ],
  "contador_estancamiento": 0,                             // (script)
  "errores_vistos": {"ImportError:pandas": 2},             // (script)
  "indicador_secundario": null,                           // o {"descripcion": "...", "comando": "..."}; se fija en el pre-flight
  "historial_metricas": [{"iter": 1, "C2": 0.71, "indicador_secundario": 6}],   // (script añade las --metric)
  "hecho": [],
  "pendiente": [],
  "hipotesis_descartadas": [],
  "decisiones": [],
  "iteraciones": [                                         // (script)
    {"n": 1, "carpeta": "iter_001_...", "inicio": "...", "fin": "...", "progreso": true, "progreso_secundario": null, "resumen": "..."}
  ]
}
```

(Los comentarios `//` son solo explicativos; el archivo real es JSON válido sin comentarios.)

## Carpeta de iteración

| Archivo | Contenido |
|---|---|
| `input.md` | Instrucciones de entrada: qué falta, qué se aprendió, qué no repetir. Se construye solo desde `loop.md` y `state.json`. |
| `plan.md` | Salida del planificador (ver `subagentes.md`). |
| `subagents/` | Briefs y resultados de cada subagente. |
| `verification.md` | Veredicto del verificador, criterio a criterio. |
| `log.md` | Acciones ejecutadas, estado de los recursos al terminar, resultados y reflexión. |

### log.md

```markdown
# Iteración <n>

## Acciones ejecutadas
- <timestamp> <acción> → <resultado breve>

## Estado de recursos
- <recurso>: <estado> (por ejemplo: rama loop/csv en commit abc123; proceso de entrenamiento detenido; 3 archivos temporales en tmp/)

## Resultados
- <qué cambió en los criterios, con referencia a verification.md>

## Reflexión
- Funcionó: ...
- No funcionó: ...
- Cambia en la siguiente iteración: ...
```

## report.md

Se genera en el post-flight desde `assets/report.template.md`. Debe poder leerse sin abrir nada más del loop.
