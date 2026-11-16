---
name: "agentic-loop"
description: Ejecuta loops o ciclos agénticos iterativos para completar tareas que necesitan varios intentos hasta cumplir un objetivo verificable, como iterar hasta que pasen los tests, refinar un modelo hasta alcanzar una métrica, investigar hasta responder una pregunta o corregir hasta que no queden errores. Define objetivo, criterios de éxito, límites y salvaguardas, orquesta subagentes (planificador, ejecutores, verificador) en cada iteración y registra cada iteración en la carpeta loops/. Úsalo siempre que el usuario diga "itera hasta", "repite hasta que", "haz un loop", "ciclo agéntico", "sigue intentando hasta", "optimiza hasta llegar a X", o pida cualquier tarea larga de prueba y error, aunque no use la palabra "loop".
---

# Loop agéntico

Un loop agéntico se define por tres cosas: el **objetivo** que se quiere alcanzar, las **condiciones** que deciden si se continúa o se para, y las **acciones** que se ejecutan en cada vuelta. Este skill añade lo que hace que un loop sea fiable en la práctica: criterios de éxito comprobables, límites que impiden iterar sin fin, un verificador independiente, estado en disco para poder reanudar y un registro completo de cada iteración.

## Principios

Estos cinco principios explican el resto del protocolo. Cuando una situación no esté cubierta, decide según ellos.

1. **El orquestador decide, los subagentes ejecutan.** Solo el loop principal decide si se continúa o se termina. Un subagente que "cree que ya ha terminado" informa; no cierra el loop.
2. **El éxito lo comprueba quien no ejecutó.** Quien hizo el trabajo tiende a darlo por bueno. La verificación la hace un verificador con contexto limpio, a partir de evidencias (salidas de comandos, métricas, archivos), no de lo que el ejecutor dice haber hecho.
3. **El estado vive en disco, no en el contexto.** Cada iteración arranca leyendo `loop.md` y `state.json`, no el historial completo de la conversación. Así el loop sobrevive a interrupciones y no se ahoga en su propio contexto.
4. **Todo loop tiene límites.** Máximo de iteraciones, detección de estancamiento y detección de errores repetidos. Un loop sin límites acaba gastando presupuesto en dar vueltas.
5. **Lo irreversible requiere permiso.** Borrar, enviar, desplegar, publicar o gastar dinero se confirma con el usuario aunque el loop esté en marcha.

## Estructura de registro

```
loops/
└── <YYYYMMDD-HHMMSS>-<slug>/
    ├── loop.md                     # definición: objetivo, criterios, límites, acciones, permisos
    ├── state.json                  # estado vivo del loop (fuente de verdad entre iteraciones)
    ├── iter_000_<timestamp>/       # línea base: medición inicial antes de actuar
    ├── iter_001_<timestamp>/
    │   ├── input.md                # instrucciones de entrada a la iteración
    │   ├── plan.md                 # tareas de esta iteración
    │   ├── subagents/              # <rol>-<n>.brief.md y <rol>-<n>.result.md
    │   ├── verification.md         # veredicto del verificador, criterio a criterio
    │   └── log.md                  # acciones ejecutadas, estado de recursos, resultados, reflexión
    └── report.md                   # informe final (post-flight)
```

El script `scripts/loop.py` crea esta estructura y gestiona la parte determinista del estado (contadores, límites, timestamps). Úsalo siempre que haya Python disponible, porque evita errores de bookkeeping:

```bash
python <skill>/scripts/loop.py init --title "Objetivo corto" [--root loops] [--max-iter 10] [--stall 3] [--secondary "descripción" [--secondary-cmd "comando"]]
python <skill>/scripts/loop.py iter-start --loop <carpeta>
python <skill>/scripts/loop.py iter-end   --loop <carpeta> --progress yes|no --summary "..." [--error "firma"] [--metric nombre=valor] [--secondary-progress yes|no]
python <skill>/scripts/loop.py check      --loop <carpeta>   # ¿salta algún límite?
python <skill>/scripts/loop.py status     --loop <carpeta>
python <skill>/scripts/loop.py close      --loop <carpeta> --outcome exito|fallo|presupuesto|estancado|bloqueado
```

El formato detallado de cada archivo está en `references/registro.md`. Las plantillas están en `assets/`.

---

## Fase 1: pre-flight

No empieces a iterar hasta que `loop.md` esté completo. La mayoría de loops que fallan lo hacen por un objetivo vago o un criterio de éxito que no se puede comprobar, y eso se arregla aquí, no a mitad del loop.

1. **Crea el loop** con `loop.py init`. Esto genera `loop.md` y `state.json` desde las plantillas.

2. **Objetivo.** Una frase orientada a resultado ("el pipeline de ingesta procesa el CSV de octubre sin errores"), no a actividad ("trabajar en el pipeline").

3. **Criterios de éxito verificables.** Cada criterio lleva su método de comprobación: un comando cuyo resultado se pueda leer, una métrica con umbral, o una checklist con evidencia concreta. Si un criterio no se puede comprobar, conviértelo en algo comprobable o pregunta al usuario. Regístralos en `state.json → criterios`. Si el objetivo se puede partir en varios criterios independientes (C1, C2, C3...), hazlo: el progreso por criterio ya es una señal clara y no necesitas nada más.

   **Indicador secundario de progreso (opcional).** Solo cuando el criterio venga fijado y sea del tipo «todo o nada», de modo que el trabajo pueda avanzar varias iteraciones sin que el criterio cambie (por ejemplo, un umbral que solo se cruza al resolver varios problemas independientes). Un indicador secundario es cualquier medida comprobable que avanza cuando el trabajo avanza aunque el criterio aún no se mueva: subpreguntas con fuente verificada, comentarios de revisión resueltos, una métrica intermedia continua, comprobaciones parciales superadas. Defínelo ahora, con su método de medición, en `loop.md → Indicador secundario` y en `state.json → indicador_secundario`, y muéstraselo al usuario. Reglas: (a) **nunca cuenta para declarar `exito`**: el éxito lo deciden solo los criterios; (b) **no se cambia a mitad del loop**: si resulta inadecuado, es un `bloqueado`; (c) si el criterio ya se mueve en cada iteración, no definas ninguno.

4. **Condiciones de terminación.** Hay cinco salidas posibles, y cada una se trata de forma distinta en el post-flight:

   | Salida | Cuándo |
   |---|---|
   | `exito` | El verificador confirma todos los criterios. |
   | `fallo` | El objetivo es inalcanzable por una razón identificada (requisito imposible, recurso inexistente). |
   | `presupuesto` | Se alcanza el máximo de iteraciones o de tiempo. |
   | `estancado` | N iteraciones seguidas sin progreso (por defecto 3). |
   | `bloqueado` | Hace falta una decisión, un permiso o un dato del usuario. |

5. **Límites.** Valores por defecto razonables: 10 iteraciones, estancamiento a las 3 sin progreso, 3 subagentes en paralelo, profundidad de subagentes 1 (sin subagentes de subagentes). Ajústalos a la tarea y anótalos en `state.json → limites`.

6. **Acciones y permisos.** Lista qué tipos de acción puede ejecutar el loop y clasifícalas en *libres* (leer, escribir dentro de su carpeta o del área de trabajo acordada, ejecutar tests) y *con confirmación* (borrar, sobrescribir originales, enviar, desplegar, gastar). Si el loop va a modificar algo valioso, define un punto de rollback (copia, rama de git, snapshot) antes de empezar.

7. **Recursos.** Comprueba que existe lo necesario: archivos, herramientas, credenciales, conectores, entorno. Un recurso que falta es un `bloqueado` en la iteración 1 que pudo evitarse aquí.

8. **Línea base (iteración 0).** Abre la iteración 0 con `loop.py iter-start`, ejecuta solo la verificación (sin actuar), guarda el resultado en su `verification.md` y ciérrala con `loop.py iter-end --progress no --summary "línea base"` (no cuenta para el estancamiento). Así sabes de dónde partes y puedes medir progreso real, y además compruebas que el método de verificación funciona.

9. **Pregunta lo que falte.** Si el objetivo, los criterios o los límites no están claros, pregunta al usuario antes de arrancar. No inventes criterios de éxito: un criterio inventado convierte el loop en una forma elaborada de hacer lo que ya ibas a hacer. Si el loop es largo o tiene efectos fuera de su carpeta, muestra un resumen de `loop.md` y pide confirmación.

---

## Fase 2: ejecución

Cada iteración sigue los mismos pasos, en este orden.

1. **Comprobar terminación** antes de abrir nada. Primero `loop.py check` (límites deterministas: iteraciones, tiempo, estancamiento, errores repetidos). Después mira el último `verification.md`: si ya se cumplen todos los criterios, o hay un bloqueo pendiente de respuesta del usuario, también se sale. Si salta cualquier condición, pasa al post-flight.

2. **Abrir.** `loop.py iter-start` crea `iter_<nnn>_<ts>/`. Rellena `input.md` a partir de `loop.md` y `state.json` únicamente: qué criterios faltan, qué se aprendió en la iteración anterior, qué no repetir.

3. **Planificar.** El planificador produce `plan.md`: las tareas de esta iteración, cada una con su criterio de hecho y sus dependencias. Una iteración debe atacar lo que más acerque al objetivo, no todo a la vez; planes más pequeños dan señales de progreso más claras.

4. **Ejecutar.** Lanza un ejecutor por tarea. Las tareas independientes van en paralelo (hasta el límite); las dependientes, en secuencia. Antes de cualquier acción con confirmación, para y pregunta.

5. **Verificar.** El verificador comprueba cada criterio contra evidencias y escribe `verification.md`: criterio, resultado, evidencia, y si hubo progreso respecto a la iteración anterior.

6. **Actualizar estado.** Actualiza en `state.json` los criterios, `historial_metricas`, `hecho`, `pendiente`, `hipotesis_descartadas` y `decisiones`.

7. **Reflexionar.** Al final de `log.md`, tres líneas como mínimo: qué funcionó, qué no, qué cambia en la siguiente iteración. Sin este paso el loop repite en lugar de aprender. Si un mismo error aparece por segunda vez, la siguiente iteración debe cambiar de estrategia, no reintentar lo mismo.

8. **Cerrar.** `loop.py iter-end` con `--progress yes|no` (hubo progreso si mejoró al menos un criterio por encima del ruido) y `--error` si hubo un error con firma reconocible. Si el loop tiene indicador secundario, añade `--metric nombre=valor` con su medición y `--secondary-progress yes|no` según haya mejorado (por encima del ruido) respecto a la iteración anterior. El script actualiza el contador de estancamiento y de errores repetidos: el progreso en cualquiera de los dos (criterio o indicador secundario) pone el contador a cero; las iteraciones seguidas sin mejora en ninguno de los dos cuentan como estancamiento (límite `max_estancamiento`). `--secondary-progress yes` solo se acepta si el indicador se definió en el pre-flight.

9. **Informar.** Da al usuario una línea por iteración: número, qué se hizo, estado de los criterios. Sin volcar logs.

### Qué no hacer durante el loop

- **No cambies los criterios de éxito para "pasar".** Si un criterio resulta estar mal planteado, es un `bloqueado`: se para y se consulta al usuario.
- **No amplíes el alcance.** Las mejoras que descubras fuera del objetivo se anotan como propuestas en `state.json → decisiones` y se mencionan en el informe final.
- **No cargues el historial completo.** Si necesitas algo de una iteración antigua, lee su `log.md` concreto.
- **No declares éxito sin verificación.** Aunque el ejecutor diga que todo funciona.
- **No uses el indicador secundario para decidir el éxito, ni lo cambies durante el loop.** Sirve para medir avance y evitar falsos estancamientos; si empieza a divergir del objetivo real (mejora el indicador pero no se acerca a los criterios), anótalo en la reflexión y trátalo como `bloqueado`.

---

## Subagentes

Cada iteración usa hasta tres roles. Lee `references/subagentes.md` antes de lanzar el primero: contiene la plantilla de brief y el formato de respuesta de cada rol.

| Rol | Qué hace | Qué recibe | Qué devuelve |
|---|---|---|---|
| Planificador | Decide las tareas de la iteración | `loop.md`, `state.json`, último `verification.md` | `plan.md` con tareas, criterio de hecho y dependencias |
| Ejecutor | Realiza una tarea concreta | Brief autocontenido de su tarea | Resumen estructurado: qué hizo, artefactos, problemas |
| Verificador | Comprueba criterios contra evidencias | Criterios de `loop.md` y rutas a artefactos, **no** el razonamiento del ejecutor | `verification.md` criterio a criterio |

Reglas:

- **Briefs autocontenidos.** Un subagente no ve la conversación ni a otros subagentes. Todo lo que necesite va en su brief o en archivos que el brief referencia.
- **Respuestas resumidas.** Los subagentes devuelven resúmenes estructurados, no logs crudos. Los detalles largos van a archivos y la respuesta da la ruta. Esto protege el contexto del orquestador.
- **Todo se registra.** Guarda cada brief y cada respuesta en `iter_<nnn>/subagents/`.
- **Fallos de subagentes.** Si un subagente no responde o devuelve algo inutilizable, reintenta una vez con un brief más concreto. Si vuelve a fallar, marca la tarea como fallida en `log.md` y deja que el planificador decida en la siguiente iteración.

**Si no hay herramienta de subagentes** (por ejemplo en claude.ai), ejecuta los roles en secuencia tú mismo, pero conserva la separación: escribe igualmente el brief y el resultado en archivos, y al hacer de verificador juzga solo a partir de las evidencias en disco, volviendo a ejecutar las comprobaciones en lugar de fiarte de lo que hiciste como ejecutor.

---

## Fase 3: post-flight

1. **Verificación final.** Ejecuta de nuevo todos los criterios con el verificador, aunque la última iteración ya los diera por cumplidos. Lo que se entrega es lo que se comprueba al final.

2. **Clasifica la salida** y cierra con `loop.py close --outcome <salida>`.

3. **Libera recursos.** Para procesos lanzados, borra temporales, cierra lo abierto. Si la salida no es `exito` y se definió rollback, pregunta al usuario si quiere restaurar el estado anterior; no lo hagas por tu cuenta.

4. **Escribe `report.md`** desde la plantilla `assets/report.template.md`: resultado, criterios uno a uno con evidencia, iteraciones usadas, artefactos producidos, propuestas fuera de alcance, lecciones para futuros loops y siguientes pasos recomendados.

5. **Comunica al usuario** el resultado en pocas líneas y enlaza el informe y los artefactos. Si la salida es `bloqueado`, termina con la pregunta concreta que desbloquea el loop; el loop se puede reanudar con `iter-start` sobre la misma carpeta.

---

## Pseudocódigo de referencia

```
pre_flight()                          # objetivo, criterios, límites, permisos, rollback
ultimo_veredicto = verificar()        # iteración 0: línea base
estado = cargar_estado()

while True:
    salida = comprobar_terminacion(estado, ultimo_veredicto)
    if salida:                        # exito | fallo | presupuesto | estancado | bloqueado
        break
    iter = abrir_iteracion(estado)

    plan       = planificador(loop, estado, ultimo_veredicto)
    resultados = ejecutar(plan)       # paralelo si son independientes; confirmar lo irreversible
    ultimo_veredicto = verificador(criterios, artefactos)
    estado     = actualizar(estado, resultados, ultimo_veredicto)
    reflexionar(iter)
    cerrar_iteracion(iter, progreso=ultimo_veredicto.progreso)

post_flight(salida, estado)           # verificación final, limpieza, informe
```
