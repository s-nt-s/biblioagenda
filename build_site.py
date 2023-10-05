#!/usr/bin/env python3
from bs4 import BeautifulSoup, Tag
from core.j2 import Jnj2, simplify
from core.plector import PortalLector
from core.rss import AgendaRss
from core.web import get_text
from core.item import Info, Item, Biblio
from datetime import datetime
import json


def clean(html, **kwargs):
    n: Tag
    soup = BeautifulSoup(html, "lxml")
    for n in soup.findAll(["th", "td", "span", "code", "li"]):
        txt = get_text(n)
        if n.name == "li" and "None" in txt:
            n.extract()
            continue
        if len(n.select(":scope *")) > 0:
            continue
        if txt not in (None, "None"):
            continue
        if n.name in ("span", "code"):
            n.extract()
        else:
            n.string = ""
    return str(soup)


def readjs(path: str, **kwargs) -> Info:
    with open(path, "r") as f:
        return Info.build(**json.load(f))


def readhtml(path: str):
    with open(path, "r") as f:
        return f.read()


def fltr(i: Item, b: Biblio):
    return i.is_adulto and i.is_tarde_o_finde and not i.is_cancelado


INFO = readjs("docs/agenda.json").filter(fltr)

now = datetime.now()
j = Jnj2(origen="_template", destino="docs/", post=clean)
j.save(
    "index.html",
    "index.html",
    info=INFO,
    now=now,
    favicon="📅",
    url=dict(
        agenda=PortalLector.AGENDA,
        regional=PortalLector.REGIONAL
    )
)

AgendaRss(
    destino="docs/",
    root="https://s-nt-s.github.io/biblioagenda",
    info=INFO
).save("agenda.rss")


AgendaRss(
    destino="docs/agenda/",
    root="https://s-nt-s.github.io/biblioagenda",
    info=INFO.filter(lambda i, b: b.is_madrid),
    title="Biblio Agenda (Madrid)",
    description="Agenda de las bibliotecas de Madrid"
).save("madrid.rss")

for zona in INFO.get_zonas():
    def zfltr(i: Item, b: Biblio):
        return b.zona == zona
    AgendaRss(
        destino="docs/agenda/",
        root="https://s-nt-s.github.io/biblioagenda",
        info=INFO.filter(zfltr),
        title=f"Biblio Agenda ({zona})",
        description="Agenda de las bibliotecas de "+zona
    ).save(simplify(zona)+".rss")
