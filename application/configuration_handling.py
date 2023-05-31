
from dynaconf import Dynaconf
 
settings = Dynaconf(
    envvar_prefix="CORD",
    settings_files=[
            "validation_config.py",
            "cord.toml",
            ".secrets.ini",
    ],
    core_loaders=[
        "PY",
        "TOML",
        "INI",
    ],

)
assert settings.FEACN_LENGTH is not None