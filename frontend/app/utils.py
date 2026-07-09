"""Utilitaires de parsing/validation partagés entre les pages.

Centralise la conversion des champs numériques saisis par l'utilisateur,
qui doit tolérer les formats courants en français (espace ou espace
insécable comme séparateur de milliers, virgule comme séparateur décimal)
plutôt que de planter sur `float("3 800")`.
"""


class FieldValidationError(ValueError):
    """Erreur de validation destinée à être affichée telle quelle à
    l'utilisateur (message déjà en français, prêt pour show_snackbar)."""


def parse_float(
    value,
    field_name: str = "Ce champ",
    required: bool = True,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float | None:
    """Convertit une saisie utilisateur en float, tolérante aux espaces
    (séparateur de milliers, y compris l'espace insécable) et à la virgule
    décimale française.

    - `required=True` (par défaut) : lève FieldValidationError si vide.
    - `required=False` : retourne None si vide (champ optionnel).
    - `min_value`/`max_value` : bornes optionnelles (ex: latitude -90..90).

    Lève toujours FieldValidationError (jamais ValueError brut) en cas de
    saisie invalide, avec un message prêt à afficher à l'utilisateur.
    """
    if value is None or not str(value).strip():
        if required:
            raise FieldValidationError(f"{field_name} est obligatoire.")
        return None

    cleaned = str(value).strip()
    # Retire les espaces normaux et insécables utilisés comme séparateur de
    # milliers (ex: "3 800", "3\u202f800", "3\xa0800").
    for space_char in (" ", "\u202f", "\xa0"):
        cleaned = cleaned.replace(space_char, "")
    # Convertit la virgule décimale française en point.
    cleaned = cleaned.replace(",", ".")

    try:
        result = float(cleaned)
    except ValueError:
        raise FieldValidationError(
            f"{field_name} doit être un nombre valide (ex: 3800 ou 3800,50)."
        )

    if min_value is not None and result < min_value:
        raise FieldValidationError(f"{field_name} doit être supérieur ou égal à {min_value}.")
    if max_value is not None and result > max_value:
        raise FieldValidationError(f"{field_name} doit être inférieur ou égal à {max_value}.")

    return result


def parse_positive_float(value, field_name: str = "Ce champ", required: bool = True) -> float | None:
    """Comme parse_float, mais rejette aussi les nombres négatifs ou nuls
    quand une valeur strictement positive est attendue (montants, superficies)."""
    result = parse_float(value, field_name, required)
    if result is not None and result <= 0:
        raise FieldValidationError(f"{field_name} doit être un nombre supérieur à zéro.")
    return result
