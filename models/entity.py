from pydantic import BaseModel
from typing import Union

from models.logic.pydantic_helper import reorder_fields

class Entity(BaseModel):
    """
        Описание лица указанного в документе (ИНН, Наименование, адрес).
    """
    tax_payer_id: Union[None, int, str]
    name: str
    address: str


#Cosignor/Cosignee has a different field structure for statements and we have to reflect that in the model 
StatementEntity = reorder_fields(model=Entity, order=["tax_payer_id", "name"]) 
WaybillEntity = reorder_fields(model=Entity,
                               order=[
                                   "name",
                                   "tax_payer_id",
                                   "address",
                               ]
                               )
