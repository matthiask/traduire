import requests


class TranslationError(Exception):
    pass


def translate_by_deepl(text, to_language, auth_key):
    # Copied 1:1 from django-rosetta, thanks!
    if auth_key.lower().endswith(":fx"):
        endpoint = "https://api-free.deepl.com"
    else:
        endpoint = "https://api.deepl.com"

    r = requests.post(
        f"{endpoint}/v2/translate",
        headers={"Authorization": f"DeepL-Auth-Key {auth_key}"},
        data={
            "target_lang": to_language.upper(),
            "text": text,
        },
        timeout=5,
    )
    if r.status_code != 200:
        raise TranslationError(
            f"Deepl response is {r.status_code}. Please check your API key or try again later."
        )
    try:
        return r.json().get("translations")[0].get("text")
    except Exception as exc:
        raise TranslationError(
            "Deepl returned a non-JSON or unexpected response."
        ) from exc
