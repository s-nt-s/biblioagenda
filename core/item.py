from typing import NamedTuple, Tuple, Union
from datetime import date
from unidecode import unidecode
import re
from urllib.parse import urlparse, parse_qs, quote
from dataclasses import dataclass, field, fields
from functools import cached_property
from .web import Web
from bs4 import BeautifulSoup

from .util import flat

re_sp = re.compile(r"\s+")
TODOS = "Para todos los públicos"


def parse_fecha(dt: Union[date, str, tuple, list]):
    if isinstance(dt, (list, tuple)):
        return tuple(flat(map(parse_fecha, dt)))
    if isinstance(dt, date):
        return (dt, )
    if not isinstance(dt, str):
        return ValueError()
    dt = dt.strip()
    if re.match(r"^\d\d\d\d-\d\d-\d\d$", dt):
        return (date(*map(int, dt.split("-"))), )
    today = date.today()
    fechas = []
    for f in dt.split(" / "):
        f = f.strip().lower()
        w, d, m = map(unidecode, f.split())
        d = int(d)
        w = [
                "lunes", "martes", "miercoles", "jueves",
                "viernes", "sabado", "domingo"
            ].index(w)
        m = [
                "enero", "febrero", "marzo", "abril", "mayo",
                "junio", "julio", "agosto", "septiembre", "octubre",
                "noviembre", "diciembre"
            ].index(m)+1
        f = date(today.year, m, d)
        if f.weekday() != w:
            f = date(today.year+1, m, d)
        fechas.append(f)
    return tuple(fechas)


def parse_tipo(t: str):
    if t == "Clubes de lectura":
        return "Club de lectura"
    if t == "Conciertos":
        return "Concierto"
    if t == "Concursos":
        return "Concurso"
    if t == "Conferencias y mesas redondas":
        return "Conferencia o mesa redonda"
    if t == "Encuentros con autores":
        return "Encuentro con autor"
    if t == "Espectáculos":
        return "Espectáculo"
    if t == "Exposiciones":
        return "Exposición"
    if t == "Itinerarios culturales":
        return "Itinerario cultural"
    if t == "Jornadas":
        return "Jornada"
    if t == "Presentaciones de libros":
        return "Presentación de libro"
    if t == "Proyecciones":
        return "Proyección"
    if t == "Recitales y lecturas en público":
        return "Recital o lectura en público"
    if t == "Talleres":
        return "Taller"
    if t == "Talleres de escritura":
        return "Taller de escritura"
    if t == "Visitas a la biblioteca":
        return "Visita a la biblioteca"
    return t


def parse_actividad(a: str, t: str):
    def _cap(s: str):
        return s[0].upper()+s[1:]

    t = parse_tipo(t)
    a = re.sub(r"\. (Tarde|Mañana)$", "", a)
    if t == "Club de lectura" and re.match(r"^Club de lectura[: ].*", a):
        a = a[16:].strip(' "\'')
        if a.startswith("(mañana):") or a.startswith("(tarde):"):
            a = a.split(":", 1)[1].strip(' "\'')
        return _cap(a)
    if a.count('"') == 2 and t in ("Encuentro con autor", "Presentación de libro"):
        return a.split('"')[1]
    if t == "Encuentro con autor":
        return _cap(re.sub(r"^Encuentro ((literario|virtual) )?con[\.\s]+", "", a))
    if t.startswith("Taller"):
        return _cap(re.sub(r"^Taller( de|:)\s+", "", a))
    if t == "Proyección":
        return re.sub(r"^(Día del cine español|Proyección de la película)[: ]+", "", a)
    if a.count('"') == 2 and a[0] == '"' and a[-1] == '"':
        return a[1:-1]
    return a


def get_obj(*args, **kwargs) -> dict:
    if len(args) != 0 and len(kwargs) != 0:
        raise ValueError()
    if len(args) > 1:
        raise ValueError()
    if len(args) == 0:
        return kwargs
    obj = args[0]
    if not isinstance(obj, (dict, list)):
        raise ValueError()
    return obj


class Biblio(NamedTuple):
    nombre: str
    url: str
    ubicacion: str = None
    mapa: str = None

    @staticmethod
    def build(*args, **kwargs):
        obj = get_obj(*args, **kwargs)
        return Biblio(**obj)

    @property
    def is_madrid(self):
        if len(self.tpubicacion) == 0:
            return False
        if self.tpubicacion[0] != "Madrid":
            return False
        return True

    @property
    def zona(self):
        if len(self.tpubicacion) == 0:
            return None
        if self.is_madrid:
            return self.tpubicacion[1]
        return self.tpubicacion[0]

    @property
    def zonas(self):
        if len(self.tpubicacion) == 0:
            return tuple()
        if self.is_madrid:
            return self.tpubicacion[1:]
        return self.tpubicacion

    @property
    def tpubicacion(self):
        if self.ubicacion is None:
            return tuple()
        arr = []
        for i in self.ubicacion.split(" - "):
            i = i.strip()
            i = re.sub("^Barrio de\s+", "", i)
            if len(i):
                arr.append(i)
        return tuple(arr)


@dataclass(frozen=True, order=True)
class Event:
    id: int = field(init=False, repr=False, compare=True, hash=True)
    actividad: str = field(compare=False, hash=False)
    edad: str = field(compare=False, hash=False)
    tipo: str = field(compare=False, hash=False)
    biblioteca: str = field(compare=False, hash=False)
    hora: str = field(compare=False, hash=False)
    fechas: Tuple[date] = field(compare=False, hash=False)
    url: str = field(compare=False, hash=False)

    @classmethod
    def build(cls, *args, **kwargs):
        flds = tuple(n.name for n in fields(cls) if n.init)
        obj = get_obj(*args, **kwargs)
        for k in list(obj.keys()):
            if k not in flds:
                del obj[k]
        return Event(**obj)

    def __post_init__(self):
        for fld, conv in self.__iter_post_init():
            object.__setattr__(self, fld, conv())

    def __iter_post_init(self):
        for fld in fields(self):
            conv = getattr(self, "".join([
                    "_",
                    self.__class__.__name__,
                    "__post_init__",
                    fld.name
                ]), None)
            if callable(conv):
                yield fld.name, conv

    def __post_init__url(self):
        pr = urlparse(self.url)
        qr = {k: quote(v[0], safe='') for k, v in parse_qs(pr.query).items()}
        url = self.url.split("?")[0]
        return url + '?c={c}&pagename={pagename}&cid={cid}'.format(**qr)

    def __post_init__id(self):
        purl = urlparse(self.url)
        id = parse_qs(purl.query)['cid'][0]
        return int(id)

    def __post_init__fechas(self):
        return parse_fecha(self.fechas)

    def __post_init__tipo(self):
        return parse_tipo(self.tipo)

    def __post_init__actividad(self):
        return parse_actividad(self.actividad, self.tipo)

    @cached_property
    def is_cancelado(self):
        if self.actividad.startswith("CANCELADO "):
            return True
        return False

    @cached_property
    def is_adulto(self):
        if self.edad == TODOS:
            return True
        if "adultos" in self.edad.lower().split():
            return True
        return False

    @cached_property
    def is_tarde_o_finde(self):
        if set({5, 6}).intersection(self.dias):
            return True
        h, m = map(int, self.hora.split(":"))
        if h >= 14:
            return True
        return False

    @cached_property
    def dias(self):
        ds = set()
        for f in self.fechas:
            ds.add(f.weekday())
        return tuple(sorted(ds))

    @cached_property
    def fecha(self):
        fechas = []
        for f in self.fechas:
            txt = f.strftime("%Y-%m-%d")
            txt = txt + "-{}".format("LMXJVSD"[f.weekday()])
            fechas.append(txt)
        return tuple(fechas)

    @cached_property
    def lugar(self):
        lugar = str(self.biblioteca)
        if lugar == "Unidad Central de Bibliotecas Públicas (Comunidad de Madrid)":
            return "Unidad Central de BP"
        for k, v in {
            "Biblioteca Pública": "BP",
            "Biblioteca Municipal": "BM",
            "Biblioteca Central": "BC",
            "Centro de Lectura": "CL",
            "Biblioteca Regional": "BR"
        }.items():
            if lugar.startswith(k):
                lugar = lugar[len(k)+1:]
                if lugar.startswith("de "):
                    lugar = lugar.split(None, 1)[1]
                return v + ' ' + lugar
        return lugar

    @cached_property
    def tipoactividad(self):
        a = self.actividad.lower()
        if a.split()[0] in "club taller visita itinerario debate jornada".split():
            return self.actividad
        if self.tipo == self.actividad:
            return self.actividad
        tipo = self.tipo.split(" o ")[0]
        return tipo+': '+self.actividad

    @cached_property
    def html(self):
        soup = Web().get(self.url)
        return str(soup)

    def get_soup(self):
        return BeautifulSoup(self.html, "lxml")

    @cached_property
    def body(self):
        soup = self.get_soup()
        body = soup.select_one("#textoCuerpo")
        body.attrs.clear()
        for n in body.findAll(['span']):
            n.unwrap()
        for n in body.select(":scope *"):
            txt = n.get_text().strip()
            chl = n.select(":scope > *")
            if tuple(map(len, (txt, chl))) == (0, 0):
                n.extract()
        p = body.find(text=True)
        if p.parent == body:
            p.wrap(soup.new_tag("p"))
        return str(body)

    @cached_property
    def hora_fin(self):
        soup = self.get_soup()
        n = soup.select("div[id='datoHora']")[-1]
        return n.get_text().strip()

    @cached_property
    def tema(self):
        soup = self.get_soup()
        n = soup.select_one("div[id='temaActividad']")
        for x in n.select(":scope *"):
            x.extract()
        return n.get_text().strip()


class Info(NamedTuple):
    events: Tuple[Event]
    biblios: Tuple[Biblio]

    @staticmethod
    def build(*args, **kwargs):
        obj = get_obj(*args, **kwargs)
        obj['events'] = tuple(map(Event.build, obj['events']))
        obj['biblios'] = tuple(map(Biblio.build, obj['biblios']))
        return Info(**obj)

    def filter(self, func):
        biblios = {b.nombre: b for b in self.biblios}
        ok_events = []
        ok_biblios = []
        for i in self.events:
            b = biblios[i.biblioteca]
            if func(i, b):
                ok_events.append(i)
                if b not in ok_biblios:
                    ok_biblios.append(b)
        return Info(
            events=tuple(ok_events),
            biblios=tuple(ok_biblios)
        )

    @property
    def kwbiblio(self):
        kw = {b.nombre: b for b in self.biblios}
        return kw

    def get_biblio(self, i: Union[Event, str]) -> Biblio:
        if isinstance(i, Event):
            i = i.biblioteca
        return self.kwbiblio[i]

    def get_zonas(self):
        zonas = set()
        for b in self.biblios:
            zonas.add(b.zona)
        return tuple(sorted(zonas))

    def get_events_zona(self, lugar):
        events = []
        for e in self.events:
            lg = self.get_biblio(e).zona
            if lg == lugar:
                events.append(e)
        return tuple(events)
