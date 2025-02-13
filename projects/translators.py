import requests


class TranslationError(Exception):
    pass


def translate_by_deepl(text, to_language, auth_key):
    # Copied 1:1 from django-rosetta, thanks!
    if auth_key.lower().endswith(":fx"):
        endpoint = "https://api-free.deepl.com"
    else:
        endpoint = "https://api.deepl.com"

    try:
        r = requests.post(
            f"{endpoint}/v2/translate",
            headers={"Authorization": f"DeepL-Auth-Key {auth_key}"},
            data={
                "target_lang": to_language.upper(),
                "text": text,
            },
            timeout=5,
        )
    except requests.Timeout as exc:
        raise TranslationError(
            "The Deepl request timed out. Please try again later."
        ) from exc

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


def fix_nls(in_, out_):
    # Thanks, django-rosetta!
    """Fixes submitted translations by filtering carriage returns and pairing
    newlines at the begging and end of the translated string with the original
    """
    if len(in_) == 0 or len(out_) == 0:
        return out_

    if "\r" in out_ and "\r" not in in_:
        out_ = out_.replace("\r", "")

    if in_[0] == "\n" and out_[0] != "\n":
        out_ = "\n" + out_
    elif in_[0] != "\n" and out_[0] == "\n":
        out_ = out_.lstrip()
    if len(out_) == 0:
        pass
    elif in_[-1] == "\n" and out_[-1] != "\n":
        out_ = out_ + "\n"
    elif in_[-1] != "\n" and out_[-1] == "\n":
        out_ = out_.rstrip()
    return out_
