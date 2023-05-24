from pydantic import BaseModel, Field

from typing import Union, Optional

from models.logic.pydantic_helper import reorder_fields
from application.configuration_handling import settings #feacn_length
from models.document import Document


class Item(BaseModel):
    feacn_code: Optional[str] = Field("", title="feacn_code",  max_length=settings.FEACN_LENGTH) 
    procedure: str = Field(..., title="procedure")
    parent: Optional[str] = Field("", title="parent")
    item_price: Union[float, str, None] = Field(..., title="", alias="price")
    documents: Optional[Document] = Field(None, title="documents")

WaybillItem = reorder_fields(model=Item,
                             order=[
                                 "feacn_code",
                                 "item_price"
                             ] 
              )
        
