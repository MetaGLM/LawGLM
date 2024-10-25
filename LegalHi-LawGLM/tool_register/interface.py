from dataclasses import dataclass
from typing import Any, Union


@dataclass
class ToolObservation:
    content_type: str
    text: str
    image_url: Union[str, None] = None
    role_metadata: Union[str, None] = None
    metadata: Any = None
