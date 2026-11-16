#!/usr/bin/env python3
"""Gestión determinista de loops agénticos: estructura de carpetas, contadores y límites.

Comandos:
  init        Crea loops/<YYYYMMDD-HHMMSS>-<slug>/ con loop.md y state.json
              (opcional: --secondary para fijar un indicador secundario de progreso).
  iter-start  Abre la siguiente iteración (la primera es la 000, línea base).
  iter-end    Cierra la iteración actual y actualiza estancamiento y errores repetidos
              (opcional: --metric nombre=valor, --secondary-progress yes|no).
  check       Comprueba los límites deterministas antes de abrir otra iteración.
  status      Muestra un resumen del estado.
  close       Marca el loop como terminado y genera report.md.

Solo usa la biblioteca estándar.
"""
import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SALIDAS = ["exito", "fallo", "presupuesto", "estancado", "bloqueado"]


def ahora():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def compacto(dt):
    return dt.strftime("%Y%m%d-%H%M%S")


def slugify(texto, maximo=40):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto.lower()).strip("-")
    return texto[:maximo].rstrip("-") or "loop"


def rellenar(plantilla, valores):
    texto = (ASSETS / plantilla).read_text(encoding="utf-8")
    for clave, valor in valores.items():
        texto = texto.replace("{{" + clave + "}}", str(valor))
    return texto


def cargar(carpeta):
    ruta = Path(carpeta) / "state.json"
    if not ruta.exists():
        sys.exit(f"No existe {ruta}. ¿Es la carpeta de un loop?")
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar(carpeta, estado):
    ruta = Path(carpeta) / "state.json"
    ruta.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parsear_metrica(texto):
    """'nombre=valor' -> (nombre, valor). El valor es número si se puede, texto corto si no."""
    if "=" not in texto:
        sys.exit(f"--metric espera nombre=valor, recibido: {texto!r}")
    nombre, valor = texto.split("=", 1)
    nombre, valor = nombre.strip(), valor.strip()
    if not nombre:
        sys.exit("--metric: el nombre no puede estar vacío")
    for conv in (int, float):
        try:
            return nombre, conv(valor)
        except ValueError:
            pass
    return nombre, valor


def iteracion_abierta(estado):
    if estado["iteraciones"] and estado["iteraciones"][-1].get("fin") is None:
        return estado["iteraciones"][-1]
    return None


def limites_superados(estado):
    """Devuelve (salida, motivo) si algún límite determinista impide seguir, o None."""
    lim = estado["limites"]
    siguiente = estado["iteracion_actual"] + 1
    if siguiente > lim["max_iteraciones"]:
        return "presupuesto", f"se han usado las {lim['max_iteraciones']} iteraciones permitidas"
    if estado["contador_estancamiento"] >= lim["max_estancamiento"]:
        return "estancado", f"{estado['contador_estancamiento']} iteraciones seguidas sin progreso"
    max_rep = lim.get("max_repeticiones_error", 3)
    repetidos = {k: v for k, v in estado["errores_vistos"].items() if v >= max_rep}
    if repetidos:
        detalle = ", ".join(f"{k} ×{v}" for k, v in repetidos.items())
        return "bloqueado", f"errores repetidos {max_rep} o más veces: {detalle}"
    if lim.get("max_minutos"):
        inicio = datetime.strptime(estado["creado"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        minutos = (ahora() - inicio).total_seconds() / 60
        if minutos >= lim["max_minutos"]:
            return "presupuesto", f"{minutos:.0f} minutos transcurridos (máximo {lim['max_minutos']})"
    return None


def cmd_init(a):
    momento = ahora()
    loop_id = f"{compacto(momento)}-{slugify(a.title)}"
    carpeta = Path(a.root) / loop_id
    if carpeta.exists():
        sys.exit(f"Ya existe {carpeta}")
    carpeta.mkdir(parents=True)

    estado = json.loads((ASSETS / "state.template.json").read_text(encoding="utf-8"))
    estado.update(loop_id=loop_id, titulo=a.title, creado=iso(momento))
    estado["limites"]["max_iteraciones"] = a.max_iter
    estado["limites"]["max_estancamiento"] = a.stall
    if a.max_minutes:
        estado["limites"]["max_minutos"] = a.max_minutes
    texto_secundario = "ninguno"
    if a.secondary:
        estado["indicador_secundario"] = {"descripcion": a.secondary, "comando": a.secondary_cmd}
        texto_secundario = a.secondary + (f" (se mide con: {a.secondary_cmd})" if a.secondary_cmd else "")
    elif a.secondary_cmd:
        sys.exit("--secondary-cmd requiere --secondary")
    guardar(carpeta, estado)

    (carpeta / "loop.md").write_text(
        rellenar("loop.template.md", {
            "titulo": a.title, "loop_id": loop_id, "creado": iso(momento),
            "max_iter": a.max_iter, "stall": a.stall, "secundario": texto_secundario,
        }),
        encoding="utf-8",
    )
    print(carpeta)


def cmd_iter_start(a):
    estado = cargar(a.loop)
    if estado["estado"] == "terminado":
        sys.exit(f"El loop está terminado (salida: {estado['salida']}).")
    if iteracion_abierta(estado):
        sys.exit(f"La iteración {estado['iteracion_actual']} sigue abierta. Ciérrala con iter-end.")
    bloqueo = limites_superados(estado)
    if bloqueo and not a.force:
        sys.exit(f"LIMITE: {bloqueo[0]} — {bloqueo[1]}. Pasa al post-flight (o usa --force si el usuario amplió el límite).")

    momento = ahora()
    n = estado["iteracion_actual"] + 1
    nombre = f"iter_{n:03d}_{compacto(momento)}"
    carpeta_iter = Path(a.loop) / nombre
    (carpeta_iter / "subagents").mkdir(parents=True)
    (carpeta_iter / "input.md").write_text(
        rellenar("input.template.md", {"n": n, "inicio": iso(momento)}), encoding="utf-8")
    (carpeta_iter / "log.md").write_text(
        rellenar("log.template.md", {"n": n}), encoding="utf-8")

    estado["iteracion_actual"] = n
    estado["estado"] = "en_curso"
    estado["iteraciones"].append({
        "n": n, "carpeta": nombre, "inicio": iso(momento),
        "fin": None, "progreso": None, "progreso_secundario": None, "resumen": None,
    })
    guardar(a.loop, estado)
    if n == 0:
        print(f"{carpeta_iter}  (línea base: solo verificar, no actuar)")
    else:
        print(carpeta_iter)


def cmd_iter_end(a):
    estado = cargar(a.loop)
    it = iteracion_abierta(estado)
    if not it:
        sys.exit("No hay ninguna iteración abierta.")
    progreso = a.progress == "yes"
    secundario = None
    if a.secondary_progress:
        if not estado.get("indicador_secundario"):
            sys.exit("--secondary-progress requiere un indicador secundario definido en el pre-flight "
                     "(init --secondary o state.json → indicador_secundario). No se define a mitad del loop.")
        secundario = a.secondary_progress == "yes"
    it.update(fin=iso(ahora()), progreso=progreso, progreso_secundario=secundario, resumen=a.summary)

    if a.metric:
        entrada = next((m for m in estado["historial_metricas"] if m.get("iter") == it["n"]), None)
        if entrada is None:
            entrada = {"iter": it["n"]}
            estado["historial_metricas"].append(entrada)
        for texto in a.metric:
            nombre, valor = parsear_metrica(texto)
            entrada[nombre] = valor

    # La línea base no cuenta para el estancamiento. El progreso en el criterio o en el
    # indicador secundario (si existe) evita sumar estancamiento.
    if it["n"] > 0:
        avanza = progreso or bool(secundario)
        estado["contador_estancamiento"] = 0 if avanza else estado["contador_estancamiento"] + 1
    for firma in a.error or []:
        estado["errores_vistos"][firma] = estado["errores_vistos"].get(firma, 0) + 1
    guardar(a.loop, estado)

    texto_sec = "" if secundario is None else f" (secundario: {'sí' if secundario else 'no'})"
    print(f"Iteración {it['n']} cerrada. Progreso: {'sí' if progreso else 'no'}{texto_sec}. "
          f"Estancamiento: {estado['contador_estancamiento']}/{estado['limites']['max_estancamiento']}.")
    bloqueo = limites_superados(estado)
    if bloqueo:
        print(f"LIMITE: {bloqueo[0]} — {bloqueo[1]}")


def cmd_check(a):
    estado = cargar(a.loop)
    if iteracion_abierta(estado):
        print(f"ABIERTA: la iteración {estado['iteracion_actual']} no se ha cerrado.")
        sys.exit(2)
    bloqueo = limites_superados(estado)
    if bloqueo:
        print(f"LIMITE: {bloqueo[0]} — {bloqueo[1]}")
        sys.exit(1)
    print("OK: ningún límite determinista impide seguir. Comprueba también el último veredicto del verificador.")


def cmd_status(a):
    e = cargar(a.loop)
    lim = e["limites"]
    print(f"{e['titulo']}  [{e['loop_id']}]")
    print(f"Estado: {e['estado']}" + (f" · salida: {e['salida']}" if e["salida"] else ""))
    print(f"Iteración: {e['iteracion_actual']} de {lim['max_iteraciones']} · "
          f"estancamiento {e['contador_estancamiento']}/{lim['max_estancamiento']}")
    if e.get("indicador_secundario"):
        ind = e["indicador_secundario"]
        print(f"Indicador secundario: {ind.get('descripcion')} (no cuenta para el éxito)")
    if e["criterios"]:
        hechos = sum(1 for c in e["criterios"] if c.get("cumplido"))
        print(f"Criterios: {hechos}/{len(e['criterios'])} cumplidos")
        for c in e["criterios"]:
            marca = "✓" if c.get("cumplido") else "·"
            print(f"  {marca} {c.get('id')}: {c.get('descripcion')} (valor: {c.get('valor')})")
    if e["errores_vistos"]:
        print("Errores vistos: " + ", ".join(f"{k} ×{v}" for k, v in e["errores_vistos"].items()))
    for it in e["iteraciones"][-5:]:
        prog = "línea base" if it["n"] == 0 else {True: "progreso", False: "sin progreso", None: "abierta"}[it["progreso"]]
        if it["n"] > 0 and it["progreso"] is False and it.get("progreso_secundario"):
            prog = "progreso (solo indicador secundario)"
        print(f"  iter {it['n']:>3}: {prog} — {it.get('resumen') or ''}")


def cmd_close(a):
    estado = cargar(a.loop)
    if iteracion_abierta(estado):
        sys.exit(f"La iteración {estado['iteracion_actual']} sigue abierta. Ciérrala antes con iter-end.")
    momento = ahora()
    estado.update(estado="terminado", salida=a.outcome)
    guardar(a.loop, estado)

    resumen = "\n".join(
        f"- iter {it['n']}: {'línea base' if it['n'] == 0 else ('progreso' if it['progreso'] else ('progreso (solo indicador secundario)' if it.get('progreso_secundario') else 'sin progreso'))} — {it.get('resumen') or ''}"
        for it in estado["iteraciones"]
    )
    informe = Path(a.loop) / "report.md"
    if informe.exists() and not a.force:
        print(f"{informe} ya existe; no se sobrescribe (usa --force).")
    else:
        informe.write_text(rellenar("report.template.md", {
            "titulo": estado["titulo"], "loop_id": estado["loop_id"], "salida": a.outcome,
            "iteraciones": max(estado["iteracion_actual"], 0),
            "max_iter": estado["limites"]["max_iteraciones"],
            "creado": estado["creado"], "fin": iso(momento),
            "resumen_iteraciones": resumen,
        }), encoding="utf-8")
        print(informe)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init")
    s.add_argument("--title", required=True)
    s.add_argument("--root", default="loops")
    s.add_argument("--max-iter", type=int, default=10)
    s.add_argument("--stall", type=int, default=3)
    s.add_argument("--max-minutes", type=int, default=None)
    s.add_argument("--secondary", default=None, help="descripción del indicador secundario de progreso (opcional; no cuenta para el éxito)")
    s.add_argument("--secondary-cmd", default=None, help="cómo se mide el indicador secundario")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("iter-start")
    s.add_argument("--loop", required=True)
    s.add_argument("--force", action="store_true", help="ignorar límites (solo si el usuario lo autoriza)")
    s.set_defaults(func=cmd_iter_start)

    s = sub.add_parser("iter-end")
    s.add_argument("--loop", required=True)
    s.add_argument("--progress", choices=["yes", "no"], required=True)
    s.add_argument("--summary", default="")
    s.add_argument("--error", action="append", help="firma corta de un error; se puede repetir")
    s.add_argument("--metric", action="append", help="métrica nombre=valor de esta iteración (número o texto corto); se puede repetir")
    s.add_argument("--secondary-progress", choices=["yes", "no"], default=None,
                   help="si el indicador secundario mejoró; solo con indicador definido en el pre-flight")
    s.set_defaults(func=cmd_iter_end)

    s = sub.add_parser("check")
    s.add_argument("--loop", required=True)
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("status")
    s.add_argument("--loop", required=True)
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("close")
    s.add_argument("--loop", required=True)
    s.add_argument("--outcome", choices=SALIDAS, required=True)
    s.add_argument("--force", action="store_true", help="sobrescribir report.md si existe")
    s.set_defaults(func=cmd_close)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
