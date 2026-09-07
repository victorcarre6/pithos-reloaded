"""Rédaction d'une structure : une liste de motifs nommée, une seule fonction publique."""

from typing import Any

# motifs de nom de champ, normalisés sans séparateur ni casse
SECRET_NAMES = frozenset({
    "authorization", "authtoken", "credential", "credentials",
    "password", "passphrase", "privatekey", "secret", "token",
})
SECRET_SUFFIXES = (
    "apikey", "accesskey", "clientsecret", "credential", "credentials",
    "password", "passphrase", "privatekey", "secret", "secretkey", "token",
)
REDACTED = "***REDACTED***"


def _is_secret_name(name: str) -> bool:
    "Vrai si le nom de champ désigne un secret, séparateurs et casse ignorés."

    normalized = name.lower().replace("_", "").replace("-", "")

    return normalized in SECRET_NAMES or normalized.endswith(SECRET_SUFFIXES)


def _walk(value: Any, path: str, redacted_paths: list[str]) -> Any:
    "Reconstruit la valeur en remplaçant tout champ dont le nom désigne un secret."

    if isinstance(value, dict):
        projection = {}
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if _is_secret_name(str(key)):
                redacted_paths.append(child_path)
                projection[key] = REDACTED
            else:
                projection[key] = _walk(item, child_path, redacted_paths)

        return projection

    if isinstance(value, (list, tuple)):
        return [_walk(item, f"{path}[{index}]", redacted_paths) for index, item in enumerate(value)]

    return value


def redact(value: Any) -> tuple[Any, list[str]]:
    """Rend la valeur rédigée et la liste des chemins rédigés, notés `$.a[0].b`.

    La liste est vide quand rien n'a été rédigé, jamais `None` : l'appelant sait toujours ce qui a
    été retiré de ce qu'il persiste.
    """

    redacted_paths: list[str] = []
    projection = _walk(value, "$", redacted_paths)

    return projection, redacted_paths
