
from dynaconf import Dynaconf
 
settings = Dynaconf(
    envvar_prefix="CORD",
    settings_files=[
        "./configuration_files/.secrets.ini", r".\configuration_files\.secrets.ini",
        "./configuration_files/cord.toml", r".\configuration_files\cord.toml",
        "./configuration_files/validation_config.py", r".\configuration_files\validation_config.py",
    ],
    core_loaders=[
        "INI",
        "PY",
        "TOML",
    ],

)