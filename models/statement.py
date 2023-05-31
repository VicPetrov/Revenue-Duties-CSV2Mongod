import datetime
import re

from typing import Annotated, Any, Union, Optional, List
from pydantic import Field, validator

from models.entity import Entity,  StatementEntity
from models.invoice_amount import StatementInvoiceAmount
from models.paper import Paper
from models.logic.pydantic_helper import date_validation, auto_enum

from application.configuration_handling import settings

class ClearanceStatement(Paper):
    """
    Заявления на товары, стоимость которых не превышает 1000 EUR,
    и которые не могут декларироватся по иному документу (ClearenceStatement)

    Номер
    дата
    Окпо декларанта
    Наименование декларанта
    Адрес декларанта
    Окпо отправителя/получателя
    Наименование отправителя/получателя
    Режим
    Наименование товара
    Код ТНВЭД
    Стоимость по инвойсу
    Код валюты
    Стоимость в рублях
    Вес товара(кг)
    Договор поставки
    Товаротранспортная накладная (TTH,CMR,и т.д)
    Коммерческие финансовые документы(счет,счет-фактура, инвойс и т.д.)
    Другие документы
    Факт выпуска в свободное обращение"""


    statement_id: Optional[str] = Field(...,
                                        regex=settings.statement_id_pattern) # type: ignore
    statement_date: Union[datetime.datetime, Annotated[str, Field(
        regex="^"+settings.statement_date_format+"$")]] # type: ignore
    declarant: Union[Entity, dict, None]  # len 3
    receiving: Union[StatementEntity, dict, None]  # type: ignore # len 2
    # title is given to exclude it from being referenced in a list collapsing function
    mode_of_operation: auto_enum("StatementModeOfOperation",
                                 settings.statement_mode) = Field(title="Mode of Operation") # type: ignore
    item_name: Union[List[str], str, None]
    feacn_code: Union[str, int] = Field(min_length=settings.feacn_length) # type: ignore
    #min_length is for strings only
    invoice: Union[StatementInvoiceAmount, dict, None] # type: ignore
    cost_in_rubles: Union[float, str]
    item_weight: Union[float, str]
    delivery_contract: Optional[str]
    waybill: Optional[str]
    commercial_finance_documents: Union[List[str], str]
    other_documents: Union[List[str], str]
    released_at: str  # ts I don't care about...

    @validator("statement_id")
    def statement_id_validation(cls, v: Any):
        #! Hopefully fixed?
        match = re.match(settings.statement_id_pattern, v) # type: ignore
        try:
            new_v = date_validation(day=int(1),
                                    month=int(1),
                                    year=int(match.group("year"))
                    )
        except:
            raise ValueError(settings.statement_id_date_msg)
        return v

    @validator("statement_date")
    def statement_date_check(cls, v: Any):
        match = re.match(settings.statement_date_format, v) # type: ignore
        if match:
            new_v = date_validation(day=int(match.group("day")),
                                    month=int(match.group("month")),
                                    year=int(match.group("year"))
                    )
        else:
            raise ValueError(
                settings.statement_date_check_failed_msg
            )
        return new_v

