from re import match

from pydantic import BaseModel, validator, Field
from models.logic.pydantic_helper import reorder_fields

from application.configuration_handling import settings

class Country(BaseModel):
    name: str = Field(title="Name")
    code: str = Field(title="alpha-2 country code")

    @validator("code")
    def code_check(cls, v):
        if (match(settings.alpha2_regex, v) is None) and (v is not None) and (v != ""):
            raise ValueError(str(settings.alpha2_does_not_match_msg).format(**{"v":v}))
        if (v not in list(settings.alpha2_codes)) and (v is not None) and (v != ""):
            raise ValueError(settings.alpha2_not_found_msg.format(**{"v":v}))
        return v

CountryOfTrade = reorder_fields(model=Country, order=["code"])
CountryOfOrigin = reorder_fields(model=Country, order=["name"])



