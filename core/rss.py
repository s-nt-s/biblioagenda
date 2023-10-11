import rfeed
from datetime import datetime
from textwrap import dedent
from xml.dom.minidom import parseString as parseXml
import re
import os


from .item import Info

re_last_modified = re.compile(
    r'^\s*<lastBuildDate>[^>]+</lastBuildDate>\s*$',
    flags=re.MULTILINE
)


class AgendaRss:
    def __init__(
            self,
            destino,
            root: str,
            info: Info,
            title="Biblio Agenda",
            description="Agenda de las bibliotecas de la Comunidad de Madrid"
    ):
        self.root = root
        self.info = info
        self.destino = destino
        self.title = title
        self.description = description

    def save(self, out: str):
        feed = rfeed.Feed(
            title=self.title,
            link=self.root+'/'+out,
            description=self.description,
            language="es-ES",
            lastBuildDate=datetime.now(),
            items=list(self.iter_items())
        )

        destino = self.destino + out
        directorio = os.path.dirname(destino)

        if not os.path.exists(directorio):
            os.makedirs(directorio)

        rss = self.__get_rss(feed)
        if self.__is_changed(destino, rss):
            with open(destino, "w") as f:
                f.write(rss)

    def __is_changed(self, destino, new_rss):
        if not os.path.isfile(destino):
            return True
        with open(destino, "r") as f:
            old_rss = f.read()
        new_rss = re_last_modified.sub("", new_rss)
        old_rss = re_last_modified.sub("", old_rss)
        if old_rss == new_rss:
            return False
        return True

    def __get_rss(self, feed: rfeed.Feed):
        def bkline(s, i):
            return s.split("\n", 1)[i]
        rss = feed.rss()
        dom = parseXml(rss)
        prt = dom.toprettyxml()
        rss = bkline(rss, 0)+'\n'+bkline(prt, 1)
        return rss

    def iter_items(self):
        for p in self.info.events:
            b = self.info.kwbiblio[p.biblioteca]
            yield rfeed.Item(
                title=f'{p.tipoactividad}',
                link=p.url,
                description='<p>'+dedent(f'''
                    {p.hora} - {' - '.join(p.fecha)}.
                    {b.zona} - <a href="{b.mapa or b.url}">{p.biblioteca}</a>.
                ''').strip().replace("\n", "<br/>")+'</p>'+p.body,
                guid=rfeed.Guid(p.url),
                # pubDate=datetime(*map(int, p.fecha.split("-"))),
                categories=rfeed.Category(p.tipo)
            )
