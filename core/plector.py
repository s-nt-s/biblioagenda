from .web import Web
from .item import Item, Biblio, Info
from bs4 import Tag
import re
from typing import NamedTuple, Tuple, Set

re_sp = re.compile(r"\s+")


def get_text(n: Tag):
    t = n.get_text()
    t = re_sp.sub(" ", t)
    t = re.sub(r'[“”]', '"', t)
    return t.strip()


def get_href(n: Tag):
    if n is None:
        return None
    if n.name == "a":
        return n.attrs.get("href")
    return get_href(n.find("a"))


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
    txt: Tuple[str]
    hrf: Tuple[str]


class PortalLector:
    AGENDA = "http://www.madrid.org/cs/Satellite?c=Page&cid=1343065588761&language=es&pagename=PortalLector%2FPage%2FPLEC_buscadorAgenda"
    REGIONAL = "http://www.madrid.org/cs/Satellite?c=Page&cid=1343065588936&language=es&pagename=PortalLector%2FPage%2FPLEC_buscadorAgenda"

    def __init__(self):
        self.w = Web()

    def get_info(self, *urls):
        biblios = set()
        items = set()
        for row in self.__get_rows(*urls):
            txt = iter(row.txt)
            item = Item(
                actividad=next(txt),
                edad=next(txt),
                tipo=next(txt),
                biblioteca=next(txt),
                hora=next(txt),
                fechas=next(txt),
                url=row.hrf[0]
            )
            biblios.add(Biblio(
                nombre=item.biblioteca,
                url=row.hrf[3]
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
                rows.add(Row(
                    txt=tuple(map(get_text, tds)),
                    hrf=tuple(map(get_href, tds))
                ))

        return rows


if __name__ == "__main__":
    for i in PortalLector().get_info().biblios:
        print(i.ubicacion)
