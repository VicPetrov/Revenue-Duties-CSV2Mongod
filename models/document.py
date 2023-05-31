import datetime
import re
from pydantic import (
                        BaseModel,
                         root_validator,
                     )
from typing import (
                    Optional,
                    Union,
                    )
from application.configuration_handling import settings   



class Document(BaseModel):
    document_code: Optional[str]
    document: Optional[str]
    date_started: Union[datetime.datetime,
                        str,
                        None]
    date_ended: Union[datetime.datetime,
                      str,
                      None]

    def doc_string_date_2_datetime(self, v):
        if isinstance(v, str):
            captured_day, captured_month, captured_year = 0, 0, 0
            for match in re.finditer(settings.document_date_format, v): # type: ignore
                captured_day = int(match.group("day"))
                captured_month = int(match.group("month"))
                captured_year = int(match.group("year"))
            if (captured_day == 0 or captured_month == 0 or captured_year == 0):
                return None
            else:
                return datetime.datetime(day=captured_day, month=captured_month, year=captured_year)
        else:
            return v
        
    @root_validator(pre=True)
    def dates_check(cls, values):
        try:
            _date_started = values["date_started"]
            _date_ended = values["date_ended"]
        except KeyError:
            ...
        else:
            _date_ended = cls.doc_string_date_2_datetime(v=_date_ended)
            _date_started = cls.doc_string_date_2_datetime(v=_date_started)
            if _date_ended is not None and _date_started is not None and (_date_started > _date_ended):
                raise ValueError(settings.document_date_check_failed_msg.format(**{"ds":_date_started, "de":_date_ended})) # type: ignore
            else:
                values["date_started"] = _date_started
                values["date_ended"] = _date_ended
        return values
