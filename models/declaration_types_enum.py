"""
        Допустимые значения для поля "тип декларации", используется
        при пароверке присланных значений:
            Экспорт - export_full;
            Экспорт (периодическая) - export_periodic;
            Реэкспорт - re_export;
            Временный ввоз товаров - import_temporary_storage;
            Временный вывоз товаров - export_temporary_storage;
            Импорт - import_full;
            Импорт (временная) - import_partial;
            Импорт (периодическая) - import_periodic;
            Реимпорт - re_import;
            Переработка на таможенной территории - processing_internal;
            Переработка за пределами таможенной территории - processing_external;
            Беспошлинная торговля - import_duty_free, export_duty_free;
            Отказ от товара в пользу государства - states_favour;
            Транзит товаров - transit;
            Завершение Режима (возвращение товаров) - import_released, export_released.
"""
from enum import Enum
from models.logic.pydantic_helper import auto_enum
from application.configuration_handling import settings

if settings.declaration_types_allow_list is None:
    class DeclarationTypesEnum(str, Enum):

        export_full = "ЭК10"
        export_periodic = "ЭК10П"
        re_export = "ЭК11"
        import_temporary_admitted = "ИМ31"
        export_temporary_admitted = "ЭК32"
        import_full = "ИМ40"
        import_temporary = "ИМ40В"
        import_periodic = "ИМ40П"
        re_import = "ИМ41"
        processing_internal = "ИМ51"
        processing_external = "ЭК61"
        import_duty_free = "ИМ72"
        export_duty_free = "ЭК72"
        states_favour = "ИМ75"
        transit = "ТР80"
        import_released = "ИМ00"
        export_released = "ЭК00"
else:
    # Generate from config, replacing meaningful names with transliterated ones.
    DeclarationTypesEnum = auto_enum(
        "DeclarationTypesEnum", settings.declaration_types_allow_list)
