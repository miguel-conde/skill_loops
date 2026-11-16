# Loop: {{titulo}}

- ID: {{loop_id}}
- Creado: {{creado}}

## Objetivo
<Una frase orientada a resultado.>

## Criterios de éxito
| id | criterio | método de verificación | umbral |
|----|----------|------------------------|--------|
| C1 |          |                        |        |

## Indicador secundario de progreso (opcional)
{{secundario}}
<Solo si el criterio es «todo o nada» y puede tardar varias iteraciones en moverse. Medida comprobable + cómo se mide. No cuenta para el éxito y no se cambia durante el loop. Si no aplica: "ninguno".>

## Condiciones de terminación
- éxito: el verificador confirma todos los criterios.
- fallo: <cuándo se considera inalcanzable>
- presupuesto: {{max_iter}} iteraciones como máximo.
- estancamiento: {{stall}} iteraciones seguidas sin progreso.
- bloqueado: se necesita decisión, permiso o dato del usuario.

## Límites
- Iteraciones máximas: {{max_iter}}
- Estancamiento: {{stall}}
- Repeticiones del mismo error: 3
- Subagentes en paralelo: 3
- Profundidad de subagentes: 1

## Acciones
### Libres
- 

### Con confirmación del usuario
- 

## Recursos
| recurso | ubicación | comprobado |
|---------|-----------|------------|
|         |           |            |

## Rollback
<Cómo volver al estado inicial, o "no aplica".>

## Cambios
<Cambios acordados con el usuario durante el loop, con fecha.>
