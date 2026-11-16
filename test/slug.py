import unicodedata


def slugify(texto, max_len=20):
    """Convierte un texto en un slug para URLs.

    Reglas:
    - minúsculas y sin acentos (ñ -> n, á -> a)
    - cada grupo de caracteres no alfanuméricos se convierte en un único "-"
    - sin "-" al principio ni al final
    - longitud máxima max_len; tras recortar no puede quedar un "-" al final
    - si el resultado queda vacío, devuelve "n-a"
    """
    s = unicodedata.normalize("NFKD", texto.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    out = ""
    for c in s:
        if c.isalnum():
            out += c
        elif not out.endswith("-"):
            out += "-"
    out = out.strip("-")
    return out[:max_len].rstrip("-") or "n-a"
