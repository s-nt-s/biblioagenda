
from datetime import date, datetime
import dataclasses
from typing import NamedTuple
from os import makedirs
from os.path import dirname
import json
import simplejson


def myconverter(o):
    if isinstance(o, (datetime, date)):
        return o.__str__()
    dct = None
    if dataclasses.is_dataclass(o):
        dct = dataclasses.asdict(o)
        for k, v in list(o.items()):
            if v is None:
                del o[k]
        return o
    if isinstance(o, NamedTuple):
        dct = o._asdict()
    if dct is None:
        return None
    for k, v in list(dct.items()):
        if v is None:
            del dct[k]
    return dct


def tmap(fnc, arr):
    return tuple(map(fnc, arr))


def tfilter(fnc, arr):
    return tuple(filter(fnc, arr))


def tsplit(s: str):
    return tuple(s.split())


def to_file(path, *args, **kwargs):
    if len(kwargs) == 0 and len(args) == 0:
        return
    if len(args) > 0 and len(kwargs) > 0:
        raise ValueError("No se puede usar args y kwargs a la vez")
    if len(args) == 1:
        args = args[0]
    dr = dirname(path)
    makedirs(dr, exist_ok=True)
    with open(path, "w") as f:
        if args:
            simplejson.dump(args, f, indent=2, default=myconverter, namedtuple_as_object=True)
        for i, (k, v) in enumerate(kwargs.items()):
            if i > 0:
                f.write(";\n")
            f.write("const " + k + " = ")
            simplejson.dump(v, f, indent=2, default=myconverter)
            f.write(";")


def flat(lst):
    arr = []
    for sublst in lst:
        for item in sublst:
            arr.append(item)
    return arr
