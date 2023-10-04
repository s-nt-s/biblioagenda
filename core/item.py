from typing import NamedTuple, Tuple, Union
from datetime import date
from unidecode import unidecode
import re

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

    a = re.sub(r"\. (Tarde|Mañana)$", "", a)
    if t == "Club de lectura" and re.match(r"^Club de lectura[: ].*", a):
        a = a[16:].strip(' "\'')
        if a.startswith("(mañana):") or a.startswith("(tarde):"):
            a = a.split(":", 1)[1].strip(' "\'')
        return _cap(a)
    if a.count('"') == 2 and t in ("Encuentro con autor", "Presentación de libro"):
        return a.split('"')[1]
    if t == "Encuentro con autor":
        return _cap(re.sub(r"^Encuentro (literario )?con[\.\s]+", "", a))
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
        spl = map(lambda x: x.strip(), self.ubicacion.split(" - "))
        return tuple(spl)


class Item(NamedTuple):
    actividad: str
    edad: str
    tipo: str
    biblioteca: str
    hora: str
    fechas: Tuple[date]
    url: str

    @staticmethod
    def build(*args, **kwargs):
        obj = get_obj(*args, **kwargs)
        obj['fechas'] = parse_fecha(obj['fechas'])
        obj['tipo'] = parse_tipo(obj['tipo'])
        obj['actividad'] = parse_actividad(obj['actividad'], obj['tipo'])
        return Item(**obj)

    @property
    def is_cancelado(self):
        if self.actividad.startswith("CANCELADO "):
            return True
        return False

    @property
    def is_adulto(self):
        if self.edad == TODOS:
            return True
        if "adultos" in self.edad.lower().split():
            return True
        return False

    @property
    def is_tarde_o_finde(self):
        if set({5, 6}).intersection(self.dias):
            return True
        h, m = map(int, self.hora.split(":"))
        if h > 15:
            return True
        return False

    @property
    def dias(self):
        ds = set()
        for f in self.fechas:
            ds.add(f.weekday())
        return tuple(sorted(ds))

    @property
    def fecha(self):
        fechas = []
        for f in self.fechas:
            txt = f.strftime("%Y-%m-%d")
            txt = txt + "-{}".format("LMXJVSD"[f.weekday()])
            fechas.append(txt)
        return fechas

    @property
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


class Info(NamedTuple):
    events: Tuple[Item]
    biblios: Tuple[Biblio]

    @staticmethod
    def build(*args, **kwargs):
        obj = get_obj(*args, **kwargs)
        obj['events'] = tuple(map(Item.build, obj['events']))
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

    def get_biblio(self, i: Union[Item, str]) -> Biblio:
        if isinstance(i, Item):
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
