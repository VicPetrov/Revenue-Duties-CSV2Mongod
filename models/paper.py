import polars as pd

from typing import (
                    Any,
                    List,
                    Union,
                    Optional
                    )

from pydantic import BaseModel
from models.logic.pydantic_helper import (find_references,
                                          find_definitions,
                                          pop_into_dict
                                         )
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
            _ = cls._reference_indices_dict[cls.__name__]
        except KeyError:
            cls.parse_schema(cls.schema(ref_template="{model}"))
            return cls.group_nested(l)
        attrs = None
        for index in Paper._reference_indices_dict[cls.__name__]:
            try:
                attrs = cls._reference_shape_dict[cls._reference_indices_dict[cls.__name__][index]]
            except KeyError:
                continue
            l.insert(index, pop_into_dict(attrs, l=l, i=index)) # type: ignore
        return l

    def flat_values(self, diction: Union[dict, None] = None) -> Any:
        if(diction is None): # R.I.P. Viction
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
    received_timestamp: Optional[float]

    def to_dataframe(self, diction: Union[dict, None] = None) -> pd.DataFrame:
        return pd.from_records( # type: ignore
            [x.flat_values() for x in self.paper_list], schema=list(self.paper_list[1].flat_keys())
        )
