import datetime
import re
from typing import Union

from pydantic import Field, validator

from models.logic.pydantic_helper import reorder_fields
from application.configuration_handling import settings
from models.paper import Paper
from models.entity import Entity
from models.item import WaybillItem

class Waybill(Paper):
    id: str = Field(..., title="Waybill Registration Number")
    registration: Union[datetime.datetime, datetime.date] = Field(title="Registration Date")
    stated_goal: str = Field(...,title="Waybill Stated Transportation Goal")
    crossed_at: Union[datetime.datetime, datetime.date, None] = Field(title="Date of crossing the border")
    contract: str = Field("", title="Purchase contract")
    specification: str = Field("", title="Item Specifications")
    seller: reorder_fields(model=Entity, order=["name","address", "tax_payer_id"]) = Field(title="Seller Entity")#3
    seller_bank: str = Field("", title="Seller's Bank")
    sender_name: str = Field("", title="Sneder's Name")
    sender_tax_payer_id: str = Field("", title="Sender's Tax Payer ID")
    sender_cargo_handling_terminal: str = Field("", title="Sender's Terminal")
    buyer: reorder_fields(model=Entity, order=["name", "tax_payer_id", "address"]) = Field(title="Buyer Entitiy")#3
    buyer_bank: str = Field(title="Buyer's Bank")
    reciever_name: str = Field(title="Reciever's Name")
    reciever_tax_payer_id: str = Field(title="Reciever's Tax Payer ID")
    reciever_cargo_handling_terminal: str = Field(title="Reciever's Terminal")
    currency: str = Field(title="Currency of Contract")
    item_name: str = Field(title="Name of Item")
    item: WaybillItem = Field(title="Item object") #2
    price_in_national_currency: Union[str, float, None] = Field(None, title="Price in Roubles")
    correction_date: Union[datetime.date, datetime.datetime, None] = Field(None, title="Date of Correction")
    global_unique_identifier: str = Field(title="GUID")

    @validator('registration', pre=True)
    def registration_date_conversion(cls, v):
        if v == "":
            return None
        try:
            d, m, y = re.match(settings.WAYBILL_REGISTRATION_DATE_REGEX, v).groupdict().values()
        except Exception as e:
            raise ValueError(settings.waybill_registration_date_failed_msg.format(**{"v":v})+f"\tОписание ошибки: \n\n{e}")
        return datetime.datetime(
            day=int(d),
            month=int(m),
            year=int(y)
        )
    @validator("crossed_at", pre=True)
    def crossed_at_conversion(cls, v):
        return cls.registration_date_conversion(v=v)

    @validator("correction_date", pre=True)
    def correction_date_conversion(cls, v):
        return cls.registration_date_conversion(v=v)
        

 
