from models.paper import Paper, PaperCollection


class ClassOne(Paper):
    id: int
    p: str

class ClassTwo(Paper):
    one: ClassOne
    name: str

t = ClassTwo(one=ClassOne(id=1, p="One"), name="Two")

def test_flattening():
    # count the # of yeilds from flat_values generator
    assert sum(1 for value in t.flat_values()) == 3

def test_key_flattening():
    # count the # of yeilds from flat_keys generator
    assert sum(1 for value in t.flat_keys()) == 3

def test_paper_collection():
    l = list([t for _ in range(0, 10)])
    print(l)
    coll = PaperCollection(paper_list=l) # type: ignore
    print (coll.to_dataframe())
    
