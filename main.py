""" 
        Waybill-Declaration Parsing application using Pydantic
        Suitable for use w/ FastAPI/Django
"""
import pathlib, os, re, smbclient, concurrent.futures, asyncio, csv, numpy
import bsonjs, bson
import motor.motor_asyncio
import polars as pd
import base64
from bson.objectid import ObjectId
from bson.raw_bson import RawBSONDocument
from datetime import datetime, timedelta
from application.configuration_handling import settings
from pydantic import create_model
from models.waybill import Waybill 
from models.paper import Paper, PaperCollection 
from models.declaration import Declaration
from models.statement import ClearanceStatement 
from config.validation_config import validation_logger

try:
    smbclient.ClientConfig(encrypt=True,
                           auth_protocol="kerberos",  
                           domain_controller=settings.SMB_DOMAIN_CONTROLLER)
except:
    smbclient = os
    pass

DeclarationUpdates = create_model(
    Declaration.__name__ + "Updates",
    __base__=Declaration,
    __validators__ = dict()
)

def files_to_load():
    path = pathlib.Path(settings.input_files_path) # type: ignore # type: ignore
    for file_ in smbclient.listdir(str(path)):
        if file_.endswith(".old.old"):
            try:
                smbclient.listdir(path / "old")
            except:
                smbclient.mkdir(path / "old")
            finally:
                smbclient.rename(path / file_, path / "old" / file_[:-8])

        elif file_.endswith(".old"):
                smbclient.rename(path / file_, path / str(file_+".old"))
        else: 
            if re.match(settings.input_files_regex, file_): # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore # type: ignore
                if re.match(settings.re_updates, file_): # type: ignore # type: ignore
                    cls = DeclarationUpdates
                elif re.match(settings.re_statement, file_): # type: ignore # type: ignore
                    cls = ClearanceStatement
                elif re.match(settings.re_declaration, file_): # type: ignore # type: ignore
                    cls = Declaration
                elif re.match(".*ttn.*", file_):
                    cls = Waybill
                else:
                    cls = None
                validation_logger.info(f"file {file_} is submitted to validation.")
                yield file_, cls


def validate_rows(df: pd.DataFrame, fd, cls) -> PaperCollection:

    pc = list()

    for index, data in df.iterrows(): # type: ignore
            data = data.to_list()
            if cls is not None and issubclass(cls, Paper):
                rw = dict(
                    zip(
                        cls.__fields__,
                        cls.group_nested(data)
                    )
                )
                try:
                    t = cls(**rw)
                except ValueError as e:
                    validation_logger.error(f"\n\t\tОшибки в строке номер {index + 1} файла \"{fd}\":\n\n\t{e}\nКонтекст:\n{rw}")
                else:
                    try:
                        pc.append(t)
                    except KeyError:
                        pc = list()
    return pc # type: ignore # type: ignore

def load_file(fd, cls):
    with smbclient.open_file(pathlib.Path(settings.input_files_path) / fd, mode="r", encoding="utf-8") as smb_io: # type: ignore
        dialect = csv.Sniffer().sniff(sample=smb_io.readline(), delimiters=settings.csv_delimiters) # type: ignore
        smb_io.seek(0)
        df = pd.read_csv(smb_io, header=0, index_col=False, na_filter=False, parse_dates=False, engine="c", dialect=dialect, memory_map=True) # type: ignore
        print(fd, end=": \n")
    pc = list()

    with concurrent.futures.ThreadPoolExecutor(thread_name_prefix="RowValidationProcess") as val_exec: #ONLY WORKS WELL WHEN COMPILED WITH NUITKA
        future_to_chunk_name = {
            val_exec.submit(validate_rows, df=x, fd=fd, cls=cls):
            "#".join([str(fd),str(i)])
            for i, x in enumerate(numpy.array_split(df.copy(), os.cpu_count())) # type: ignore
        }
        concurrent.futures.wait(future_to_chunk_name)
        for future in concurrent.futures.as_completed(future_to_chunk_name):
            print(".", end="\t")
            chunk_name = future_to_chunk_name[future]
            try:
                pc += future.result()
                print(f"{chunk_name}:{len(pc)}/{len(df)}")
                validation_logger.info(
                    f"chunk({chunk_name})" 
                    f" validation returned {len(pc)}/{len(df)}"
                )
            except Exception as e:
                raise ValueError(f"{e} \nError occured in chunk {chunk_name}") from e
    validation_logger.info(f"\"{fd}\" — is exhausted.")
    fpath = str(pathlib.Path(settings.input_files_path) / fd) # type: ignore
    smbclient.rename(fpath, fpath+".old") # rename exhausted file
    return pc

result = list()
async def insert_documents(cls_name):
    result.append(await cord_db[cls_name.lower()].insert_many(all_files_dict[cls_name]))

all_files_pc = PaperCollection(paper_list=list(), received_timestamp=None)
start_from_objectid = None
documents_to_sort = dict()

with concurrent.futures.ThreadPoolExecutor(thread_name_prefix="LoadFileThread") as executor:
    future_to_papercol = {executor.submit(
        load_file, *(f, c)): f for f, c in files_to_load() if c is not None}
    for future in concurrent.futures.as_completed(future_to_papercol):
        source_file = future_to_papercol[future]
        try:
            all_files_pc.paper_list += future.result()
        except Exception as e:
            validation_logger.error(
                f"File \"{source_file}\" raised exception {str(e)}")
        else:
            validation_logger.info(
                f"parsing of \"{source_file}\" is finished.\n{str(' ' * 43)} - "
                f"loaded total of {len(all_files_pc.paper_list)} records.")
          
mongod_client = None
if len(all_files_pc.paper_list) > 0:
        try:
            mongod_client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongod_connection_link, serverSelectionTimeoutMS=5000) #settings from vault 
            cord_db = mongod_client["cord"]

            db_to_cls = list()      
            async def test(dbl):
               dbl = list(await mongod_client.list_database_names())
            asyncio.get_event_loop().run_until_complete(test(db_to_cls))
        except Exception as e:
            with open(pathlib.Path(f"./output_{datetime.now().ctime().replace(':', '-')}.json"), mode="wt", encoding="utf-8") as s:
                all_files_pc.paper_list = [{"_id": str(ObjectId())} | v.dict() for v in all_files_pc.paper_list] #type:ignore
                all_files_pc.received_timestamp = datetime.now() #type:ignore
                s.write(all_files_pc.json(ensure_ascii=False))
            
            validation_logger.error(f"При попытке подключения к базе данных произошла ошибка: \n\t\t{e}\n\n" #type:ignore
                                    f"{base64.b64decode('MTk4OSBUaWFuYW5tZW4gU3F1YXJlIHByb3Rlc3RzIGFuZCBtYXNzYWNyZQo=').decode('utf-8')}\n"
                                    f"{base64.b64decode(err).decode('utf-8').ljust(80)}" #type:ignore
            )
        else:
            updates = [all_files_pc.paper_list.pop(i)
                        for i, v in enumerate(all_files_pc.paper_list)
                                    if type(v).__name__ == "DeclarationUpdates"]
            all_files_dict = dict()

            for paper_v in all_files_pc.paper_list:
                try:
                    all_files_dict[str(type(paper_v).__name__).lower()].append(
                        RawBSONDocument(bsonjs.loads(paper_v.json()))
                    )
                except KeyError:
                    all_files_dict[str(type(paper_v).__name__).lower(
                    )] = [RawBSONDocument(bsonjs.loads(paper_v.json()))]
            
            loop = asyncio.get_event_loop()

            for cls in all_files_dict.keys():
                loop.run_until_complete(insert_documents(cls_name=cls))
else:
    print("warning: V41-P4553d\t\"N0n3-C4m3-0u7\"")
    validation_logger.warning("No new records.") #type:ignore

del all_files_pc
print("Sorting...")
OUT_EXPORT = 0
OUT_IMPORT = 1
OUT_BOTH = 2
ret = {OUT_EXPORT: dict(),
       OUT_IMPORT: dict(),
       OUT_BOTH: dict(),
}


documents_to_sort = dict()
updates = None

async def find_documents(cls, objid, out_var_name:str ):
    cursor = cord_db[cls.lower()].find({'_id': {'$gt': objid}})
    out = globals()[out_var_name]
    for document in await cursor.to_list(length=2**16):
        if cls in out.keys():
            out[cls].append(document)
        else:
            out[cls] = [document]
    return out

if mongod_client is not None:
    db_to_cls = {
        Declaration.__name__.lower(): Declaration,
        ClearanceStatement.__name__.lower(): ClearanceStatement,
        DeclarationUpdates.__name__.lower(): DeclarationUpdates,
        Waybill.__name__.lower(): Waybill
    }
    start_from_objectid = ObjectId().from_datetime(datetime.utcnow() - timedelta(days=int(settings.days_to_fetch))) #type:ignore
    for db in db_to_cls.keys():
        result = loop.run_until_complete(find_documents(cls=db, #type:ignore
                                                    out_var_name=[i for i, a in locals().items() if id(a) == id(documents_to_sort)][0],
                                                   objid=start_from_objectid)
        )
    for cls, doc_list in documents_to_sort.copy().items():
        documents_to_sort[cls] = pd.DataFrame().from_records(#type:ignore
            [db_to_cls[cls].construct(**x).flat_values() for x in doc_list if x.pop("_id") is not None],
            columns=db_to_cls[cls].construct(**doc_list[0]).flat_keys()
        )


    for cls in documents_to_sort.keys():
        if cls == ClearanceStatement.__name__.lower():
            column = "mode_of_operation"
        elif cls == Declaration.__name__.lower() or cls == DeclarationUpdates.__name__.lower():
            column = "op_type"
        elif cls == Waybill.__name__.lower():
            column = "stated_goal"
        # COMMON
        pattern = settings.re_for_both
        df = documents_to_sort[cls][
            documents_to_sort[cls][column].apply( #type:ignore
                lambda x: True if re.search(pattern, x) else False #type:ignore
            )
        ]
        try:
            ret[OUT_BOTH].update({cls: df})
        except KeyError: 
            ret[OUT_BOTH][cls] = df
        #import
        pattern = settings.re_for_impdiv or re.Pattern()
        df = documents_to_sort[cls][
            documents_to_sort[cls][column].apply(
                lambda x: True if re.search(pattern, x) else False #type:ignore
            )
        ]
        try:
            ret[OUT_IMPORT].update({cls: df})
        except KeyError:
            ret[OUT_IMPORT][cls] = df
        #export
        pattern = settings.re_for_expdiv
        df = documents_to_sort[cls][
            documents_to_sort[cls][column].apply(
                lambda x: True if re.search(pattern, x) else False
            )
        ]
        try:
            ret[OUT_EXPORT].update({cls: df})
        except KeyError:
            ret[OUT_EXPORT][cls] = df
        pattern = settings.re_for_expdiv
        df = documents_to_sort[cls][
            documents_to_sort[cls][column].apply(
                lambda x: True if re.search(pattern, x) else False
            )
        ]
        try:
            ret[OUT_EXPORT].update({cls: df})
        except KeyError:
            ret[OUT_EXPORT][cls] = df
        

date_format = r"%d-%m-%Y"
date = [(datetime.utcnow() - timedelta(days=int(settings.days_to_fetch))
         ).strftime(date_format), datetime.utcnow().strftime(date_format)]
cls_to_filename = {
              Declaration.__name__.lower():settings.declaration_output_filename.format(date[0], date[1]),
              DeclarationUpdates.__name__.lower():settings.declaration_updates_output_filename.format(date[0], date[1]),
              ClearanceStatement.__name__.lower():settings.clearance_statement_output_filename.format(date[0], date[1]),
              Waybill.__name__.lower(): f"ttn {date[0]} - {date[1]}"
}

out_key_to_path = {OUT_BOTH: pathlib.Path(settings.xlsx_path_common),
                   OUT_EXPORT: pathlib.Path(settings.xlsx_path_expdiv),
                   OUT_IMPORT: pathlib.Path(settings.xlsx_path_impdiv)
}
    
for folder in ret.keys():
    for cls in ret[folder].keys():
        if not cls.startswith("__"):
            with open(mode="wb", file=str(out_key_to_path[folder] / cls_to_filename[cls]) + ".xlsx") as o_file:
                ret[folder][cls].to_excel(o_file, sheet_name=date[1],index=False)

print("Supplying the logs...")
import smbclient.shutil
for log in pathlib.Path().glob("**/*.log"):
    for folder in out_key_to_path.values():
        smbclient.shutil.copyfile(log, pathlib.Path(folder) / log.name)
if "__CLEAR__" in smbclient.listdir(settings.input_files_path):
    for log in pathlib.Path().glob("**/*.log"):
        with open(log, mode="w") as l:
            l.truncate()