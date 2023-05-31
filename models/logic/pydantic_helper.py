from collections import OrderedDict
from enum import Enum
import datetime
from itertools import repeat
import shortuuid
import transliterate

from typing import Union

from pydantic.main import BaseModel, create_model


def date_validation(day: int = 1, month: int = 1, year: int = 2014) -> datetime.datetime:
    try:
        return datetime.datetime(day=day % 100, month=month % 100, year=year % 10000)
    except Exception as e:
        raise ValueError(str(e))


def recursive_len(attrs_, len=0):
    for k, v in attrs_.items():
        if isinstance(v, dict):
            len += recursive_len(attrs_=v)
        if k == "title":
            len += 1
    return len


def pop_into_dict(x: dict, l: list[str], i: int = 0) -> dict:
    """helper function for feeding kwargs into single level dictionaries.
    """
    # ? this function can fit 12 eggs in its mouth
    # Got tired of perfecting this massive chain of recursive functions and
    # I have no idea on how to make it work anymore
    #! doesn't handle multiple levels of inheritance
    return_value = dict()
    for name, attr in x.items():
        if "title" in attr or "$ref" in attr:
            return_value.update({name: l.pop(i)})
        else:
            return_value.update(
                {name: dict(zip(attr.keys(), [l.pop(i) for _ in attr]))})
    return return_value


def find_references(properties, count=-1, ret=dict()) -> Union[dict, list, None]:
    """walks dict recursively, finding all object references"""
    #! wrote this by making mindless tweaks in debug mode until it worked,— there is room for optimisation!

    for key, value in properties.items():
        if isinstance(value, dict):
            if "title" in value:
                count += 1
            find_references(properties=value, ret=ret, count=count)
        elif isinstance(value, list):
            find_references(properties=dict(
                enumerate(value)), ret=ret, count=count)
        else:
            if(key == "$ref"):
                if isinstance(ret, dict):
                    ret[count] = value
                elif isinstance(ret, list):
                    ret[:2] = [count, value]
    return ret or None


def find_definitions(definitions: dict, ret: dict = dict()) -> dict:
    """walks dict recursively, finding all referenced object definitions"""
    for key, value in definitions.items():
        if isinstance(value, dict):
            if "properties" in value:
                ref = find_references(
                    properties=value["properties"], ret=list())
                if ref is not None and ref[1] in ret:
                    # we copy the properties dict, because it changes during iteration
                    for i, v in enumerate(value["properties"].copy()):
                        if i == ref[0]:
                            value["properties"][v] = dict()
                            for prop in ret[ref[1]].items():
                                value["properties"][v].update(
                                    {prop[0]: prop[1]})
                ret[key] = value["properties"]
            else:
                find_definitions(definitions=value)
        elif isinstance(value, list):
            continue
    return ret


def reorder_fields(model: BaseModel, order: list) -> BaseModel:
    new_model = create_model(model.__name__ + "_" + # type: ignore
                             shortuuid.uuid()[:4], __base__=model) # type: ignore
    original_fields = new_model.__fields__.copy()
    new_fields = OrderedDict()

    for item in order:
        new_fields[item] = original_fields.pop(item)

    new_model.__fields__ = new_fields
    return new_model


#TODO: fix naming here
# I think it's fixed now. Not sure 🤷🏻‍♂️
def auto_enum(name: str, values: list[str]) -> Enum:
    return Enum(name + "_" + shortuuid.uuid()[:4], dict(
        zip([str(transliterate.slugify(value, language_code="ru").translate( #type:ignore
            str.maketrans("-", "_"))) for value in values], values)
    )
    )
