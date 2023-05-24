from enum import Enum
from application.configuration_handling import settings

class CRUDEnum(str, Enum):
    # THis is normaly replaced with config.
    """C.R.U.D.: create, read, update и delete -- 4 фундаментальных
        манипуляци.
    """
    create = "main"
    read = None
    update = "korrekt" # default set by CB of russia
    delete = None

if settings.declaration_crud_allow_dict is not None:
    CRUDEnum = Enum("DeclarationCRUDEnum", settings.declaration_crud_allow_dict)
