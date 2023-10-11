from .web import Web
from .item import Item, Biblio, Info
from bs4 import Tag
import re

re_sp = re.compile(r"\s+")


def get_text(n: Tag):
    t = n.get_text()
    t = re_sp.sub(" ", t)
    t = re.sub(r'[“”]', '"', t)
    return t.strip()


class PortalLector:
    AGENDA = "http://www.madrid.org/cs/Satellite?c=Page&cid=1343065588761&language=es&pagename=PortalLector%2FPage%2FPLEC_buscadorAgenda"
    REGIONAL = "http://www.madrid.org/cs/Satellite?c=Page&cid=1343065588936&language=es&pagename=PortalLector%2FPage%2FPLEC_buscadorAgenda"

    def __init__(self):
        self.w = Web()

    def get_info(self, *urls):
        if len(urls) == 0:
            urls = (
                PortalLector.AGENDA,
                PortalLector.REGIONAL
            )
        biblios = set()
        items = set()
        for url in urls:
            self.w.get(url)
            self.w.submit(
                "#pagSup0 .botonOk",
                registros=1000
            )
            for tr in self.w.soup.select("#tablaAgenda tbody tr"):
                tds = tr.findAll("td")
                txt = iter(map(get_text, tds))
                item = Item.build(
                    actividad=next(txt),
                    edad=next(txt),
                    tipo=next(txt),
                    biblioteca=next(txt),
                    hora=next(txt),
                    fechas=next(txt),
                    url=tds[0].find("a").attrs["href"]
                )
                biblios.add(Biblio(
                    nombre=item.biblioteca,
                    url=tds[3].find("a").attrs["href"]
                ))
                items.add(item)

        def visit_biblio(b: Biblio):
            self.w.get(b.url)
            for p in self.w.soup.select("p.ficha_valor"):
                txt = tuple(map(get_text, p.findAll("span")))
                if txt[0] == "Ubicación:":
                    return Biblio(
                        nombre=b.nombre,
                        url=b.url,
                        ubicacion=txt[1]
                    )
            return b

        return Info(
            events=tuple(sorted(items)),
            biblios=tuple(sorted(map(visit_biblio, biblios)))
        )


if __name__ == "__main__":
    for i in PortalLector().get_info().biblios:
        print(i.ubicacion)
