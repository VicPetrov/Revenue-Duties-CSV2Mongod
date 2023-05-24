from typing import Union
from pydantic import BaseModel


class Bank(BaseModel):
    """
    ```
    Bank(
    sort_code = int | str, — МФО
    name = str,
    classifier = str) — Код ОКПО
    ```
    """
    sort_code: Union[int, str]
    name: str
    classifier: str
