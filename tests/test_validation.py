from itertools import repeat
import pytest
import datetime
from devtools import debug
from sys import path
import os, pathlib
from models.waybill import Waybill
from models.statement import ClearanceStatement
from models.declaration import Declaration
from models.invoice_amount import InvoiceAmount
from models.item import Item

import application.configuration_handling

def construct_declaration(_file: pathlib.Path = pathlib.Path() / "test_line.txt") -> dict:
    opened_file = open(_file, "r", encoding="utf-8")
    test_line = [x.replace("\n", "") for x in opened_file]
    return dict(zip(Declaration.__fields__, Declaration.group_nested(test_line)))

@pytest.fixture
def decl_test_line() -> dict:
    return construct_declaration(_file= list(pathlib.Path().glob("**/test_line.txt"))[0]  )

@pytest.fixture
def statement_test_line() -> dict:
    clearence_test_line = """700010000/2021/000165^12.05.2021^3049710804^ФЛП ЛАВРУШКО ЮЛИЯ АЛЕКСАНДРОВНА^ДНР 83017, город Донецк, Калининский район, улица Герцена, дом 75^^ООО "Юг Карго Дон"^Импорт^Графический планшет One by Wacom medium, Кол-во-   5 шт.; Графический планшет One by Wacom small, Кол-во – 5 шт.;Графический планшет Wacom Intuos S Black цветчерный, Кол-во – 3 шт.;Графический планшет Wacom Intuos S BluetoothBlack цвет черный, Кол-во – 2 шт.^84^70975.74^RUB^71475.74^8.75^от 10.08.2020г. до 30.12.2021 г.; № 10/08-2020^CMR от 27.04.2021 г. № 13;^от 27.04.2021 г.  № 13^Упаковочный лист № 13 от 27.04.2021г.; Дополнительное соглашение № 1 от 08,12,2020 г.; Спецификация № 1 от 23.04.2021 г.; Платежное поручение № 32 от 08.04.2021 г.; Справка о транспортных расходах № б/н от 06.05.2021г.; Карточка аккредитации № 200259 от 10.06.2020г..; Учетная карточка № 700010002/2020/1/003941 от 01.07.2020г; Свидетельство о регистрации  № 02 01 51 038611 от 12.03.2020 г.; ЭК №10323010/290421/0072480 от 29.04.2021г.; Квитанция об оплате единого сбора № 265874 от 06.05.2021 г.; Провозная ведомость №700020100/2/21/19177 от 06.05.2021г.; Лицензия ЛБ № 0045 от 31.08.2018 г., Договор поручения № 0708/20-БР от 07.08.2020 г., Трудовой договор №101201901431/3 от 20.03.2019 г.; ИНН 3355906474 от 02.07.2003 г.,^2021-05-12 16:16:30^
"""
    return dict(zip(ClearanceStatement.__fields__, ClearanceStatement.group_nested(
                                 clearence_test_line.split("^"))))
@pytest.fixture
def waybill_test_line():
    wbtline = """1744^22.06.2022^Реализация^22.06.2022^84/21 от 10.12.2021^8 от 23.05.2022^Общество с ограниченной ответственностью  "СЕЛЬХОЗПРОДУКТ"^86221 ДНР, Шахтерский район, село Розовка улица Степная 2А^50009602^51000050^Общество с ограниченной ответственностью  "СЕЛЬХОЗПРОДУКТ"^86221 ДНР, Шахтерский район, село Розовка, ул.Степная 2А^50009602^ООО ПЕРЕВАЛЬСК-АГРО^61802707^Перевальский район, пгт. Селезневка, ул. Полевая 1^61102720^ООО "ПЕРЕВАЛЬСК-АГРО"^61802707^Перевальский район, пгт. Селезневка, ул. Полевая , 1^RUB^Корм ПК 6-6 (комбикорм - страна производства ДНР)^2309^661200^297200^^D09CD094D0A12DD0AE2D3137303632323532383635393530303039363032^"""
    return dict(zip(Waybill.__fields__, Waybill.group_nested(wbtline.split("^"))))

def test_sparta_declaration():
    values = list(
        repeat("sparta"+"".join(repeat("a", (2 ** 16) - len("spartaa"))), 42))
    e = False
    d = None
    try:
        d = Declaration(**dict(zip(Declaration.__fields__, values)))
    except ValueError as er:
        debug(er)
        e = True
    assert e == True and d is None, ("Declaration Object is initialised with "
                                     "errorneous data.")

def test_empty_constructor():
    e = False
    d = None
    try:
        d = Declaration()
    except:
        e = True
    assert e == True and d is None, ("Empty \"Declaration\" constructor did not"
                                     " raise an exception! Or Declaration object"
                                     " initialised with errorneous data")


def test_proper_declaration(decl_test_line):
    try:
        d = Declaration(**decl_test_line)
        Item(**decl_test_line["item"])
    except Exception as e:
        assert False, str(e) + "\n"+ str(debug.format(decl_test_line))
    else:
        assert True, str(debug.format(decl_test_line))
                                        # ("Perfectly splendid constructor"
                                        #   "(loaded from test_line.txt) failed"
                                        #   "(raised exceptions), indicates change"
                                        #   " in schema or errors waiting for you to"
                                        #   " fix them!")


def test_declaration_id(decl_test_line, test_value="700WRONGCODE/WRONG0/CODE00"):
    err = None
    try:
        t = decl_test_line.copy()
        t["declaration_id"] = test_value
        Declaration(**t)
    except ValueError as e:
        err = e
    assert err is not None, (f"Supplied code({test_value})"
                             " didn't raise a ValueError."
                             )
    inst = err = None
    try:
        t = decl_test_line.copy()
        date = datetime.datetime.now(tz=None).date()
        t["declaration_id"] = (r"700000000/"
                               + f"{date.day:02d}{date.month:02d}{date.year%100:02d}"
                               + r"/000001")
        # Putting a :02d after the year value
        # is very ambitious.
        # Assuming this test will last a century >.<
        inst = Declaration(**t)
    except ValueError as e:
        err = e
    assert inst is not None and err is None, "Date format changed(2nd part of the Declaration ID)"

def test_declaratin_no_end_date(decl_test_line, test_value=""):
    err = None
    try:
        t = decl_test_line.copy()
        t["item"]["documents"]["date_ended"] = test_value
        Declaration(**t)
    except ValueError as e:
        err = e
    assert err is None

def test_currency_code(decl_test_line, e=False, a="invoice_value", b="currency_alpha3"):
    try:
        if a not in Declaration.__fields__ or b not in InvoiceAmount.__fields__:
            raise KeyError("invoice_value is not one of the fields")
        decl_test_line[a][b] = "PPP"
        Declaration(**decl_test_line)
    except ValueError as e:
        assert e is not None, "Wrong currency code didn't raise an exception!"

def test_end_gt_start(decl_test_line):
    a = decl_test_line.copy()
    a["item"]["documents"] = {
                'document_code': None,
                'document': '2019/02/26',
                'date_started': '26/02/19',
                'date_ended': '31/12/21',
            }
    Declaration.parse_obj(a)
        # from document import Document
        # Document(**{
        #         'document_code': 'NONE',
        #         'document': '2019/02/26',
        #         'date_started': '26/02/19',
        #         'date_ended': '31/12/21',
        #     })
    

from devtools import Debug

def test_statement(statement_test_line):
    try:
        ClearanceStatement(**statement_test_line)
    except Exception as e: 
        assert False, str(e)
    else:
        assert True

def test_waybill(waybill_test_line):
    try:
        Waybill(**waybill_test_line)
    except Exception as e:
        assert False, str(e) + str(Debug.format(waybill_test_line))
    else:
        assert True


def squared_digits(number: int, _ret: int = 0) -> int:
    for decimal_place, digit in enumerate([number % 10]):
        _ret+=10**decimal_place*(digit<<2)
    return _ret

