"""Comprobador de slugify(). No modificar.
Imprime los casos que fallan y, en la última línea, "n/total".
Código de salida 0 solo si pasan todos."""
import sys
from slug import slugify

CASOS = [
    ("Hola Mundo", "hola-mundo"),
    ("  Hola   Mundo  ", "hola-mundo"),
    ("Canción Fácil", "cancion-facil"),
    ("¡Año Nuevo!", "ano-nuevo"),
    ("Python 3.12", "python-3-12"),
    ("a" * 25, "a" * 20),
    ("Un título muy largo para cortar", "un-titulo-muy-largo"),
    ("", "n-a"),
    ("!!!", "n-a"),
    ("ya-es-slug", "ya-es-slug"),
]

ok = 0
for entrada, esperado in CASOS:
    try:
        obtenido = slugify(entrada)
    except Exception as e:
        obtenido = f"<{type(e).__name__}>"
    if obtenido == esperado:
        ok += 1
    else:
        print(f"FALLA slugify({entrada!r}): obtenido {obtenido!r}, esperado {esperado!r}")
print(f"{ok}/{len(CASOS)}")
sys.exit(0 if ok == len(CASOS) else 1)
