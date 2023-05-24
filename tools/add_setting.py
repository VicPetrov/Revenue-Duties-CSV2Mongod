import argparse
from ast import alias
from enum import Enum
import re
from typing import Counter, List
from devtools import debug
from os.path import basename, abspath
from pathlib import Path


STR_SNIPPET = (
"""
{name} = custom_get(option="{option}", 
                    section= "Validation",
                    fallback= {fallback},
                    apply={apply}
         )
""")
REGEX_SNIPPET = STR_SNIPPET

INT_SNIPPET = (
"""
{name} = config.getint(option="{option}", 
                       section= "Validation",
                       fallback= {fallback})
""")
usage_string = """py add_setting.py \"setting1 = value1; setting2 = value2\" [--str|--regex|--float|--int] [--apply lambda x: x.split(';')] `
[--ini-file="/mnt/c/some/file/path/file.ini"](по умолчанию ищет validation.ini) [--py-file="/mnt/c/some/file/path/file.py"](по умолчанию ищет validation_config.py)
"""

def parse():
    parser = argparse.ArgumentParser(prog="py " + basename(__file__),
                                     description=("Добавить настройки в файлы"
                                                  " конфигурации *.ini и генерировать"
                                                  " код их чтения в *.py."), usage=usage_string)

    parser.add_argument("setting",
                        nargs="*",
                        metavar="N",
                        help=("опция до первого \"=\" с последующим указанием значения. Допускается множество значений"
                              " Допускаются конец строки (через \"`\" в PowerShell), пробелы - "
                              " (Пробелы изымаются из конечного результата)"))

    parser.add_argument("--ini-file", nargs="?",
                        default=next(Path().glob("**/validation.ini")),
                        help="\tпуть к файлу *.ini")
    parser.add_argument("--py-file",
                        nargs="?", default=next(Path().glob("**/validation_config.py")),
                        help="\tпуть к *.py файлу")

    parser.add_argument("--regex", action="store_true", help="Устанавливаемое значение — регулярное выражение.")
    parser.add_argument("--int", action="store_true", help="Устанавливаемое значение — целое число.")
    parser.add_argument("--str", action="store_true", help="Устанавливаемое значение — строка.")
    parser.add_argument("--float", action="store_true", help="Устанавливаемое значение — число с плавающей точкой.")

    parser.add_argument("--verbose", action="store_true", help="вывод на экран всех операций записи")
    parser.add_argument("--apply", dest="apply", nargs="?", default="DO_NOTHING", help="Функция единственны аргументом которой будет строка значения.")
    parser.add_argument("--split", default=";", metavar="C", help="Символ разбития на подстроки в предоставленной строке.(; по умолчанию)")
    return parser.parse_args()
def arguments_valid(n: argparse.Namespace) -> bool:
    type_counter = Counter([n.regex, n.int, n.str, n.float])
    if type_counter[True] > 1:
        return False
    else: 
        return True

def write(n: argparse.Namespace):
    settings = dict()

    try:
        for s in re.finditer(r"(?P<key>.*?)\s*=\s*(?P<value>.*)", " ".join(n.setting)):
            split_value = s.group("value").split(n.split)
            if len(split_value) > 1:
                settings[s.group("key")] =  split_value
            else:
                settings[s.group("key")] =  split_value[0]

    except AttributeError:
        print("attr_ERROR")
    with open(abspath(n.ini_file), encoding="utf-8") as ini_file:
        for line in ini_file:
            for k in settings.copy().keys():
                if re.match(f"(?i)({k})", line):
                    print(k+" already exists in "+ basename(n.ini_file) + ". Setting addition aborted.")
                    del settings[k]
    with open(abspath(n.py_file), encoding="utf-8") as py_file:
        for line in py_file:
            for k in settings.copy().keys():
                if re.match("(?i)({k})", line):
                    print(k+" already exists in "+ basename(n.py_file)+ ". Setting addition aborted.")
                    del settings[k]
    with open(abspath(n.ini_file), encoding="utf-8", mode="at") as ini_file_at:
        for k, v in settings.items():
            if ini_file_at.writable():
                if isinstance(v, list):  
                    first_line = f"{k}: {v[0]}"
                else:
                    first_line = f"{k}: {v}"
                ini_file_at.write("\n"+first_line)
                if n.verbose:
                    print("FILE:\n\n")
                    debug(ini_file_at)
                    print("WROTE:\n\n")
                    print(first_line)
                first_line = first_line.find(":")
                if isinstance(v, list):
                    for element in v[1:]:
                        ini_file_at.write("\n"+(" " * (first_line+2))+element)
                        if n.verbose:
                            print((" " * (first_line+2))+element)
            else: 
                print("Файл не доступен для записи.")
            
    with open(abspath(n.py_file), encoding="utf-8", mode="at") as py_file_at:
        for k, v in settings.items():
            if py_file_at.writable():
                if n.str or n.regex or not(n.str or n.int or n.regex):
                    new_line = STR_SNIPPET.format(**{"name": k.upper(),
                                                     "option": k,
                                                     "fallback":
                                                     repr(v),
                                                     "apply":str(n.apply)})
                    py_file_at.write(new_line)
                    if n.verbose: 
                        debug(py_file_at, new_line)
                if n.int:
                    new_line = INT_SNIPPET.format(**{"name": k.upper(),
                                                     "option": k,
                                                     "fallback":
                                                     str(v)})
                    py_file_at.write(new_line)
                    if n.verbose: 
                        debug(py_file_at, new_line)
            else: 
                print("Файл не доступен для записи.")

if __name__ == "__main__":
    n = parse()
    if arguments_valid(n):
        write(n)
    else:
        print("Опция может иметь лишь один тип.")


