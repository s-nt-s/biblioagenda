from .web import Web
from .item import Item, Biblio, Info
from bs4 import Tag
import re
from typing import NamedTuple, Set

re_sp = re.compile(r"\s+")


def get_text(n: Tag):
    t = n.get_text()
    t = re_sp.sub(" ", t)
    t = re.sub(r'[“”]', '"', t)
    return t.strip()


def visit_biblio(b: Biblio):
    obj = {}
    soup = Web().get(b.url)
    a = soup.find("a", text="Mapa Localización")
    if a is not None:
        obj["mapa"] = a.attrs["href"]
    for p in soup.select("p.ficha_valor"):
        txt = tuple(map(get_text, p.findAll("span")))
        if txt[0] == "Ubicación:":
            obj["ubicacion"] = txt[1]
    return Biblio(
        nombre=b.nombre,
        url=b.url,
        **obj
    )


class Row(NamedTuple):
    actividad: str
    edad: str
    tipo: str
    hora: str
    fechas: str
    url: str
    biblio_nombre: str
    biblio_url: str


class PortalLector:
    AGENDA = "http://www.madrid.org/cs/Satellite?c=Page&cid=1343065588761&language=es&pagename=PortalLector%2FPage%2FPLEC_buscadorAgenda"
    REGIONAL = "http://www.madrid.org/cs/Satellite?c=Page&cid=1343065588936&language=es&pagename=PortalLector%2FPage%2FPLEC_buscadorAgenda"

    def __init__(self):
        self.w = Web()

    def get_info(self, *urls):
        biblios = set()
        items = set()
        for row in self.__get_rows(*urls):
            item = Item(
                actividad=row.actividad,
                edad=row.edad,
                tipo=row.tipo,
                biblioteca=row.biblio_nombre,
                hora=row.hora,
                fechas=row.fechas,
                url=row.url
            )
            biblios.add(Biblio(
                nombre=item.biblioteca,
                url=row.biblio_url
            ))
            items.add(item)

        return Info(
            events=tuple(sorted(items)),
            biblios=tuple(sorted(map(visit_biblio, biblios)))
        )

    def __get_rows(self, *urls):
        if len(urls) == 0:
            urls = (
                PortalLector.AGENDA,
                PortalLector.REGIONAL
            )
        rows: Set[Row] = set()
        for url in urls:
            self.w.get(url)
            self.w.submit(
                "#pagSup0 .botonOk",
                registros=1000
            )
            for tr in self.w.soup.select("#tablaAgenda tbody tr"):
                tds: list[Tag] = tr.findAll("td")
                txt = iter(map(get_text, tds))
                rows.add(Row(
                    actividad=next(txt),
                    edad=next(txt),
                    tipo=next(txt),
                    biblio_nombre=next(txt),
                    hora=next(txt),
                    fechas=next(txt),
                    url=tds[0].find("a").attrs["href"],
                    biblio_url=tds[3].find("a").attrs["href"]
                ))

        return rows


if __name__ == "__main__":
    for i in PortalLector().get_info().biblios:
        print(i.ubicacion)
