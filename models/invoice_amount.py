from pydantic import BaseModel, Field
from models.logic.pydantic_helper import reorder_fields, auto_enum

from typing import Union
from application.configuration_handling import settings


class InvoiceAmount(BaseModel):
    #TODO: Convert to Decimal type for all values across the validation. 
    value: Union[float, str, None] = Field(0.0, title="Incoice's Total Monetary Value")
    currency_alpha3: Union[auto_enum("Alpha3CurrencyCodeEnum",
                        list(settings.allowed_currency_codes)), str, None] = Field(None, title="Currency Alpha-3 (3 digit) Code") # type: ignore
    exchange_rate: Union[float, str, None] = Field(1.0, gt=0, ls=0)


StatementInvoiceAmount = reorder_fields(InvoiceAmount, # type: ignore
                                        ["value",
                                         "currency_alpha3"])
