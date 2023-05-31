import re

from pydantic import Field, validator, root_validator
from typing import Union, Optional

from models.bank import Bank
from models.crud_enum import CRUDEnum
from models.paper import Paper
from models.entity import Entity
from models.country import Country, CountryOfOrigin, CountryOfTrade
from models.item import Item
from models.declaration_types_enum import DeclarationTypesEnum
from models.invoice_amount import InvoiceAmount
from application.configuration_handling import settings
import models.logic.validators as validators


class Declaration(Paper):
    """
    #### Модель данных грузовой таможенной декларации
     Описывает типы данных и методы их проверки при разборке.

    Аттрибуты(Keyword Arguments):

        Таможенный режим;
        Номер ГТД;
        Отправитель\Доп;
        Получатель\Доп;
        Oтв. за фин урег.\Доп;
        Торгующая страна;
        Таможенная стоимость;
        Страна отправления\экспорта, ее код;
        Страна происхождения;
        Сумма по счету(графа 22);
        Валюта;
        Курс;
        МФО Банка;
        Наименование банка;
        ОКПО банка;
        ТНВЭД;
        Процедура;
        Общая декларация/предшествующий документ;
        Цена товара;
        Код документа,;
        Документ;
        Дата начала;
        Дата конца;
        Отметка D/J;
    """


    #   Thought of moving common fields to Paper superclass,
    #   Terrible idea, all of the fields are in different order nothing is standardised.   
    
      
    crud_type: Union[CRUDEnum, str] = Field("", title="CRUD Type")

    op_type: Union[DeclarationTypesEnum, str] = Field("", title="Operation Type")

    declaration_id: str = Field(...,
                                regex=settings.declaration_id_pattern, # type: ignore
                                title="Declaration ID")

    sender: Optional[Entity] = Field(None, title="Sender Entity")
    sender_additional: Optional[Entity] = Field(None, title="Additional Sender Entity")

    receiver: Optional[Entity] = Field(None, title="Receiver Entitty")
    receiver_additional: Optional[Entity] =  Field(None, title="Additional Receiver Entitty")

    financially_responsibe: Optional[Entity] =  Field(None, title="Financially-responsible Entity")
    financially_responsibe_additional: Optional[Entity] = Field(None, title="Additional Financially-responsible Entity")

    country_of_trade: Optional[CountryOfTrade] = Field(None, title="Country of Trade")  # type: ignore
    value_in_rub: Union [float, str, None] = Field(None, regex=settings.decimal_places_regex, title="Value in Roubles") # type: ignore
    country_of_departure: Optional[Country] = Field(None, title="Country of Departure")
    country_of_origin: Optional[CountryOfOrigin] = Field(None, title="Country of Origin") # type: ignore
    invoice_value: Optional[InvoiceAmount] = Field(None, title="Total Invoice Amount")

    banking_information: Optional[Bank] = Field(None, title="Banking Information")
    
    item: Optional[Item] = Field(None, title="Item")       
    timestamp: Optional[str] = Field(None, title="Item release timestamp")

    @validator("crud_type")
    def validate_crud_type(cls, v):
        if v.startswith("m"):
            return v
        else:
            for sk, dv in settings.declaration_crud_allow_dict.items(): # type: ignore (*.py configuration)
                if v in dv:
                    return sk
        raise ValueError()

    @validator("declaration_id")
    def validate_id(cls, v):
        m = re.search(pattern="".join(settings.declaration_id_pattern), # type: ignore
                     string=v)
        if m is not None:
            validators.validate_authority(regex_match=m,
                                          allow_list=settings.authority_allow_list, # type: ignore
                                          msg="".join(settings.validate_id_authority_msg # type: ignore
                                                      ).format(
                                              **{"authority": m.group("authority"),
                                                 "v": v
                                                 }
                                          )
                                          )
        else:
            raise ValueError(settings.declaration_id_pattern_message)
        try:
            validators.date_check(regex_match=m, msg=settings.validate_id_msg.format(**{"date":".".join([m.group("day"), m.group("month"), m.group("year")]), "v":v})) # type: ignore
        finally:
            return v

    @validator("sender_additional")
    def sender_is_none(cls, v, values):
        if v is not None and values["sender"] is None:
            raise ValueError(settings.sender_is_none_msg
            )
        return v

    @validator("receiver_additional")
    def receiver_is_none(cls, v, values):
        if v is not None and values["receiver"] is None:
            raise ValueError(settings.receiver_is_none_msg
            )
        return v
        
    @validator("financially_responsibe_additional")
    def fin_responsible_is_none(cls, v, values):
        if v is not None and values["financially_responsibe"] is None:
            raise ValueError(settings.fin_responsible_is_none_msg
            )
        return v

    @validator("item")
    def parse_item(cls, v):
        if isinstance(v, dict):
            return Item(**v)
        elif isinstance(v, Item):
            return v
    @root_validator(pre=True)
    def decl_root(cls, values):
        try:
            if isinstance(values["country_of_departure"], dict):
                try:
                    values["country_of_departure"] = Country(**values["country_of_departure"])
                except Exception as e:
                    raise ValueError( "Страна отправления: \n\t\t" + str(e))
            if isinstance(values["country_of_trade"], dict):
                try:
                    values["country_of_trade"] = CountryOfTrade(**values["country_of_trade"]) # type: ignore
                except Exception as e: 
                    raise ValueError("Страна продавец: \n\t\t"+str(e))
            if isinstance(values["country_of_origin"], dict):
                try:
                    values["country_of_origin"] = CountryOfOrigin(**values["country_of_origin"]) # type: ignore
                except Exception as e:
                    raise ValueError("Страна произхождения: \n\t\t" + str(e))
        except Exception as e:
            raise ValueError("Отсутствуют страны: \n\n\n\t" + str(e))
        return values
