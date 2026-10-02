import json
from fastapi.templating import Jinja2Templates


def from_json_filter(value: str):
    """Jinja2 filter to parse JSON string in templates."""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


templates = Jinja2Templates(directory="app/templates")
templates.env.filters["from_json"] = from_json_filter
