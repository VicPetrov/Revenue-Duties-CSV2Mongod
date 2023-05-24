from datetime import datetime
from pathlib import Path
#import pandas as pd
import polars as pd

from typing import (
                    Any,
                    List,
                    Union,
                    Optional
                    )

from pydantic import BaseModel
from os import chdir
from pathlib import Path
from application.configuration_handling import settings
from models.logic.pydantic_helper import (find_references,
                             find_definitions,
                             pop_into_dict)
#import smbclient
#import pathlib

class Paper(BaseModel):

    _reference_indices_dict = dict()
    _reference_shape_dict = dict()

    @classmethod
    def parse_schema(cls, m):
        cls._reference_indices_dict[cls.__name__] = find_references(
            properties=m["properties"], ret=dict())
        cls._reference_shape_dict.update(find_definitions(
            definitions=m["definitions"]))

    @classmethod
    def group_nested(cls, l: list[str]) -> list[str]:
        """ Group nested classes into separate dictionaries.
        e.g. if slice [1:4] contains attributes `a`, `b`, `c` - described
        in a nested class:
        ```
        1: 1                  >      1: {"a": 1,
        2: "value2"           >          "b": "value2",
        3: "value-enigma"     >          "c": "value-enigma"}                         
        4: "value4"           >      2: "value4"   

        ```
        """
        # Enumerators have to be annotated with "Union", or "Annotated", so that they count because of how schema works.
        try:
            ln = cls._reference_indices_dict[cls.__name__]
        except KeyError:
            cls.parse_schema(cls.schema(ref_template="{model}"))
            return cls.group_nested(l)
        attrs = None
        for index in Paper._reference_indices_dict[cls.__name__]:
            try:
                attrs = cls._reference_shape_dict[cls._reference_indices_dict[cls.__name__][index]]
            except KeyError:
                continue
            l.insert(index, pop_into_dict(attrs, l=l, i=index))
        return l

    def flat_values(self, diction: Union[dict, None] = None) -> Any:
        if(diction is None):
            diction = self.dict()
        for v in diction.values():
            if isinstance(v, dict):
                for x in self.flat_values(diction=v):
                    yield x
            else:
                yield v

    def flat_keys(self, diction: Union[dict, None] = None) -> Any:
        if(diction is None):
            diction = self.dict()
        for k, v in diction.items():
            if isinstance(v, dict):
                for x in self.flat_keys(diction=v):
                    yield f"{k} {x}"
            else:
                yield k


class PaperCollection(BaseModel):
    paper_list: List[Paper]
    recieved_timestamp: Optional[float]

    # def smb_write(self, destination: Path, filename: str):
    #     smb_io = None
    #     try:
    #         smb_io = smbclient.open_file(pathlib.Path(destination) / filename)
    #     except (AttributeError, NameError):
    #         smbclient.ClientConfig(username=settings.smb_login,
    #                                password=settings.smb_pw,
    #                                encrypt=True)
    #         smb_io = smbclient.open_file(pathlib.Path(destination) / filename)
    #     with smb_io as f:
    #         if str(filename).endswith("json"):
    #             f.write(self.json())
    #         elif str(filename).endswith("xlsx"):
    #             self.to_dataframe().to_excel(io=f, header=True)

    def to_dataframe(self, diction: Union[dict, None] = None) -> pd.DataFrame:
        return pd.DataFrame.from_records(
            [x.flat_values() for x in self.paper_list], columns=self.paper_list[1].flat_keys()
        )
