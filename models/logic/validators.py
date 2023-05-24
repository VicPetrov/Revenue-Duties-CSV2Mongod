import re
import datetime
import models.logic.pydantic_helper as pydantic_helper

def validate_id(cls, v, pattern, msg):
    m = re.match("".join(pattern), v)

    try:
        datetime.date(day=int(m.group("day")),
                      month=int(m.group("month")),
                      year=int(m.group("year"))
                      )
    except ValueError:
        raise ValueError(
            msg.format(**{"date":m.group("date"), "v":v}))
    finally:
        return v


def validate_authority(regex_match: re.Match, allow_list: list,
                       msg="Authority is not in allow list.") -> None:
    if regex_match.group("authority") not in allow_list:
        raise ValueError("".join(msg))


def date_check(regex_match: re.Match, msg: str):
    try:
        return pydantic_helper.date_validation(day=int(regex_match.group("day")),
                                               month=int(
                                                   regex_match.group("month")),
                                               year=int(regex_match.group("year")))
    except ValueError:
        raise ValueError(msg)
