import json
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
_cache = {}


def bl(en: str, zh: str) -> str:
    return f"{en} / {zh}"


def _load_locale(lang: str) -> dict:
    if lang not in _cache:
        with open(LOCALES_DIR / f"{lang}.json", encoding="utf-8") as f:
            _cache[lang] = json.load(f)
    return _cache[lang]


def t(key: str) -> str:
    en = _load_locale("en")
    zh = _load_locale("zh")
    parts = key.split(".")
    ev = en
    zv = zh
    for p in parts:
        ev = ev.get(p, key)
        zv = zv.get(p, key)
    if isinstance(ev, dict) or isinstance(zv, dict):
        return key
    return bl(str(ev), str(zv))
