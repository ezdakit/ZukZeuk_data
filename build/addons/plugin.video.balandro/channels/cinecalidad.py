# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.cinecalidad.lat/'


def item_configurar_proxies(item):
    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = 'Configurar proxies a usar ... [COLOR plum](si no hay resultados)[/COLOR]', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' )

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://www.cinecalidad.eu/', 'https://www.cinecalidad.im/', 'https://www.cinecalidad.is/', 
                 'https://www.cinecalidad.li/', 'https://www.cine-calidad.com/',
                 'https://cinecalidad.website/'
                 ]

    for ant in ant_hosts:
        url = url.replace(ant, host)

    raise_weberror = True
    if '/peliculas-por-ano/' in url: raise_weberror = False

    # ~ data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    data = httptools.downloadpage_proxy('cinecalidad', url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'En castellano:', folder=False, text_color='plum' ))
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'espana/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'En latino:', folder=False, text_color='plum' ))
    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - Estrenos', action = 'list_all', url = host + 'estrenos/', search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - Más destacadas', action = 'destacadas', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - Más populares', action = 'list_all', url = host + 'peliculas-populares/', search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - En 4K', action = 'list_all', url = host + 'genero/4k/', search_type = 'movie' ))

    itemlist.append(item.clone( title = ' - Por género', action='generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = ' - Por año', action='anios' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'serie/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'destacadas', url = host, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'series-populares/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action='generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = [
        ('accion','Acción'),
        ('animacion','Animación'),
        ('animes','Animes'),
        ('aventura','Aventura'),
        ('belica','Bélica'),
        ('biografia','Biografía'),
        ('ciencia-ficcion','Ciencia ficción'),
        ('comedia','Comedia'),
        ('crimen','Crimen'),
        ('documental','Documental'),
        ('drama','Drama'),
        ('fantasia','Fantasía'),
        ('guerra','Guerra'),
        ('historia','Historia'),
        ('infantil','Infantil'),
        ('misterio','Misterio'),
        ('musica','Música'),
        ('musical','Musical'),
        ('romance','Romance'),
        ('suspenso','Suspenso'),
        ('terror','Terror'),
        ('thriller','Thriller'),
        ('western','Western')
    ]

    for opc, tit in opciones:
        itemlist.append(item.clone( title = tit, url = host + opc + '/', action = 'list_all' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    item.url = host + 'peliculas-por-ano/'

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="yearList">(.*?)</div>')

    matches = re.compile('href="(.*?)">(.*?)</a>', re.DOTALL).findall(bloque)

    for url, title in matches:
        if url.startswith('/'): url = host[:-1] + url

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, search_type = 'movie' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    if not matches:
        bloque = scrapertools.find_single_match(data, '<div id="content">(.*?)>Destacadas<')
        matches = scrapertools.find_multiple_matches(bloque, '<div class="home_post_content">(.*?)</div></div>')

    for match in matches:
        title = scrapertools.find_single_match(match, '<h2>.*?">(.*?)</h2>')
        if not title:
            title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        url = scrapertools.find_single_match(match, ' href="(.*?)"')

        url = url.replace('\\/', '/')

        if not url or not title: continue

        plot = scrapertools.find_single_match(match, '<p>.*?">(.*?)</p>').strip()
        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        m = re.match(r"^(.*?)\((\d+)\)$", title)
        if m:
            title = m.group(1).strip()
            year = m.group(2)
        else:
            year = '-'

        tipo = 'tvshow' if '/serie/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if item.search_type == 'movie':
            if '/serie/' in url: continue
        elif item.search_type == 'tvshow':
            if not '/serie/' in url: continue

        if tipo == 'movie':
            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))

        if tipo == 'tvshow':
            itemlist.append(item.clone( action='temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title,  infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page_link = scrapertools.find_single_match(data, '<a class="next page-numbers".*?href="(.*?)"')
        if next_page_link:
            itemlist.append(item.clone( title='Siguientes ...', url = next_page_link, action = 'list_all', text_color='coral' ))

    return itemlist


def destacadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Destacadas<(.*?)>Herramientas<')

    matches = scrapertools.find_multiple_matches(bloque, '<a(.*?)</a></li>')

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        if item.search_type == 'movie':
            if '/serie/' in url: continue
        else:
            if '/ver-pelicula/' in url: continue

        thumb = scrapertools.find_single_match(match, 'alt=".*?src="(.*?)"')

        m = re.match(r"^(.*?)\((\d+)\)$", title)
        if m:
            title = m.group(1).strip()
            year = m.group(2)
        else:
            year = '-'

        if item.search_type == 'movie':
            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))
        else:
            itemlist.append(item.clone( action='temporadas', url = url, title = title, thumbnail = thumb,
                                        contentType = 'tvshow', contentSerieName = title,  infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<span data-serie="(.*?)".*?data-season="(.*?)"')

    for data_serie, tempo in matches:
        title = 'Temporada ' + tempo

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.data_serie = data_serie
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = item.url, data_serie = data_serie,
                                    contentType = 'season', contentSeason = tempo ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    post = {'action': 'action_change_episode', 'season': str(item.contentSeason), 'serie': str(item.data_serie)}

    headers = {'Referer': item.url}

    data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post, headers = headers)

    matches = scrapertools.find_multiple_matches(data, '<img(.*?)alt=.*?"episode":"(.*?)".*?"url":"(.*?)"')

    if item.page == 0:
        sum_parts = len(matches)
        if sum_parts > 250:
            if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos?'):
                platformtools.dialog_notification('CineCalidad', '[COLOR cyan]Cargando elementos[/COLOR]')
                item.perpage = 250

    for thumb, epis, url in matches[item.page * item.perpage:]:
        if not epis: epis = '0'

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName

        thumb = thumb.replace('\\/', '/')
        thumb = thumb.replace('src=\\"', '').replace('\\"', '')

        url = url.replace('\\/', '/')

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > ((item.page + 1) * item.perpage):
        itemlist.append(item.clone( title = "Siguientes ...", action = "episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'latino': 'Lat', 'castellano': 'Esp', 'subtitulado': 'Vose'}

    lang = 'Lat'

    if '/espana/' in item.url: lang = 'Esp'

    data = do_downloadpage(item.url)

    ses = 0

    if '">Ver' in data or '">VER' in data:
        if '">Ver' in data:
           bloque = scrapertools.find_single_match(data, '">Ver(.*?)</aside>')
        else:
           bloque = scrapertools.find_single_match(data, '">VER(.*?)</aside>')

        matches = scrapertools.find_multiple_matches(bloque, 'href=".*?data-src="(.*?)".*?data-lmt="(.*?)".*?data-option>(.*?)</a>')
        if not matches:
            matches = scrapertools.find_multiple_matches(bloque, 'href=".*?data-src="(.*?)".*?data-lmt="(.*?)".*?data-option.*?>(.*?)</a>')

        for data_url, data_lmt, servidor in matches:
            ses += 1

            servidor = servidor.lower().strip()

            if servidor == "trailer": continue
            elif servidor == 'veri': continue
            elif servidor == 'netu': continue
            elif servidor == 'player': continue

            elif servidor == 'gounlimited': continue
            elif servidor == 'jetload': continue
            elif servidor == '1fichier': continue
            elif servidor == 'turbobit': continue

            elif servidor == 'latmax': servidor = 'fembed'
            elif servidor == 'maxplay': servidor = 'voe'
            elif servidor == 'ccplay': servidor = 'streamsb'

            elif servidor == 'doos': servidor = 'doodstream'
            elif servidor == 'dood': servidor = 'doodstream'

            elif 'fembedhd' in servidor: servidor = 'fembed'
            elif 'doostream' in servidor: servidor = 'doodstream'
            elif 'voesx' in servidor: servidor = 'voe'

            qlty = '1080'

            itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', data_url = data_url, data_lmt = data_lmt,
                                  quality = qlty, language = lang ))

    if '">Descargar' in data or '">DESCARGAR' in data:
        if '">Descargar' in data:
            bloque = scrapertools.find_single_match(data, '">Descargar(.*?)</aside>')
        else:
            bloque = scrapertools.find_single_match(data, '">DESCARGAR(.*?)</aside>')

        matches = scrapertools.find_multiple_matches(bloque, 'href=".*?data-url="(.*?)".*?data-lmt="(.*?)".*?data-link>(.*?)</a>')
        if not matches:
            matches = scrapertools.find_multiple_matches(bloque, 'href=".*?data-url="(.*?)".*?data-lmt="(.*?)".*?data-link.*?>(.*?)</a>')

        for data_url, data_lmt, servidor in matches:
            ses += 1

            servidor = servidor.lower().strip()

            if servidor == "subtítulos" or servidor == 'subtitulos': continue
            elif servidor == 'veri': continue
            elif servidor == 'netu': continue
            elif servidor == 'gounlimited': continue
            elif servidor == 'jetload': continue
            elif servidor == '1fichier': continue
            elif servidor == 'turbobit': continue

            elif servidor == 'torrent 4k': servidor = 'torrent'
            elif servidor == 'bittorrent': servidor = 'torrent'

            elif 'bittorrent' in servidor: servidor = 'bittorrent'
            elif 'fembed' in servidor: servidor = 'fembed'
            elif 'voesx' in servidor: servidor = 'voe'

            qlty = '1080'
            if "4k" in servidor: qlty = '4K'

            itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', data_url = data_url, data_lmt = data_lmt,
                                  quality = qlty, language = lang ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = base64.b64decode(item.data_url).decode("utf-8")

    url = url.replace('&amp;', '&')

    servidor = item.server

    if url:
        if url.startswith(host):
            data = do_downloadpage(url)

            url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')
            if not url: url = scrapertools.find_single_match(data, 'id="btn_enlace">.*?<a href="(.*?)"')

            if '/hqq.' in url or '/waaw.' in url or '/netu.' in url:
                return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

            if servidor == 'mega':
               if url.startswith('#'): url = 'https://mega.nz/' + url
               elif not url.startswith('http'): url = 'https://mega.nz/file/' + url

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

    if '/protect/v.php' in url or '/protect/v2.php' in url:
        enc_url = scrapertools.find_single_match(url, "i=([^&]+)")
        url = base64.b64decode(enc_url).decode("utf-8")

        if not 'magnet' in url: url = url.replace('/file/', '/embed#!')

    if url:
        if url.endswith('.torrent'):
            if config.get_setting('proxies', item.channel, default=''):
                import os

                data = do_downloadpage(url)
                file_local = os.path.join(config.get_data_path(), "temp.torrent")
                with open(file_local, 'wb') as f: f.write(data); f.close()

                itemlist.append(item.clone( url = file_local, server = 'torrent' ))
            else:
                itemlist.append(item.clone( url = url, server = 'torrent' ))

            return itemlist

        if servidor == 'directo':
            if not url.startswith('http'): return itemlist

        itemlist.append(item.clone(url = url, servidor = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
