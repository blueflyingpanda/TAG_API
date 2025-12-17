import pycountry


def validate_language_alpha2(v: str | None) -> str | None:
    """Validate compliance with ISO 639-1 alpha-2 codes ('en', 'ru' ...)"""
    if v is None:
        return None
    lang = v.lower()
    try:
        pycountry.languages.get(alpha_2=lang)
        return lang
    except (KeyError, AttributeError) as e:
        raise ValueError(f'Invalid ISO 639-1 language code: {lang}') from e
