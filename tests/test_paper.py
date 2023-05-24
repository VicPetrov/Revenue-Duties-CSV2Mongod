import pandas as pd

from sys import path
import os, pathlib
os.environ["PYTHONUTF8"] = "1"
for py in pathlib.Path().glob("**/*.py"):
    path.insert(1, str(py.parent))


from paper import Paper, PaperCollection


class ClassOne(Paper):
    id: int
    p: str

class ClassTwo(Paper):
    one: ClassOne
    name: str

t = ClassTwo(one=ClassOne(id=1, p="One"), name="Two")

def test_flattening():
    counter = 0; 
    for value in t.flat_values():
        print(value)
        counter+=1
    assert counter == 3

def test_key_flattening():
    counter = 0;
    for key in t.flat_keys():
        print(key)
        counter+=1
    assert counter == 3

def test_paper_collection():
    l = list([t for _ in range(0, 10)])
    print(l)
    coll = PaperCollection(paper_list=l)
    print (coll.to_dataframe())
    
