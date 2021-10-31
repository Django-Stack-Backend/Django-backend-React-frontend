def link_content(url, rel, content_type):
    return f"<{url}>; rel=\"{rel}\"; type=\"{content_type}\""


def get_string_or_evaluate(string_or_func, *args, **kwargs):
    if not string_or_func:
        return None
    if isinstance(string_or_func, str):
        return string_or_func
    return string_or_func(*args, **kwargs)
