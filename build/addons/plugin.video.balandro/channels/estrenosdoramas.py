# -*- coding: utf-8 -*-

import re, time, struct, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, servertools, tmdb


host = 'https://www23.estrenosdoramas.net/'


GLBPLAYER = 'TEST'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar dorama ...', action = 'search', search_type = 'all', text_color = 'firebrick' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'category/peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'En latino', action = 'list_all', url = host + 'category/latino/', doblado=True, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'category/doramas-online/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'En latino', action = 'list_all', url = host + 'category/latino/', doblado=True, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos capítulos', action = 'last_episodes', url = host + 'category/ultimos-capitulos-online/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    genres = [
       ['accion', 'Acción'],
       ['boyslove', 'Boys love'],
       ['comedia', 'Comedia'],
       ['drama', 'Drama'],
       ['escolar', 'Escolares'],
       ['fantasia', 'Fantasía'],
       ['ficcion', 'Ficción'],
       ['historico', 'Histórico'],
       ['misterio', 'Misterio'],
       ['romance', 'Romance']
       ]

    for genero in genres:
        url = host + 'category/' + genero[0]

        itemlist.append(item.clone( title = genero[1], action = 'list_all', url = url ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Resultados<(.*?)>AVISO LEGAL<')

    matches = re.compile('<div class="" id="post-(.*?)</div>').findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"').strip()
        if not title: title = scrapertools.find_single_match(match, 'alt="(.*?)"').strip()

        if not url or not title: continue

        if '/search/' in item.url:
            if 'Capitulo' in title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        lang = ''
        if item.doblado: lang = 'Lat'

        tipo = 'movie' if '/peliculas/' in match else 'tvshow'

        if tipo == 'tvshow':
           if 'Pelicula' in title:
               tipo = 'movie'
               title = title.replace('Pelicula', '').strip()
        else:
           if 'Capitulo' in title:
               tipo = 'tvshow'
               title = title.replace('Capitulo', '').strip()

        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, languages = lang, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))
        else:
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, languages = lang, fmt_sufijo=sufijo, 
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if "<div class='wp-pagenavi'" in data:
            next_url = scrapertools.find_single_match(data, "class='current'>" + '.*?href="(.*?)"')
            if next_url:
                if '/page/' in next_url:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_url, action = 'list_all', text_color = 'coral' ))

    return itemlist


def last_episodes(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Resultados<(.*?)>AVISO LEGAL<')

    matches = re.compile('<div class="" id="post-(.*?)</div>').findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"').strip()
        if not title: title = scrapertools.find_single_match(match, 'alt="(.*?)"').strip()

        if not url or not title: continue
        elif 'Pelicula' in title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        season = 1
        epis = scrapertools.find_single_match(title, 'Capitulo(.*?)$').strip()
        if not epis: epis = 0

        title_serie = scrapertools.find_single_match(title, '(.*?)Capitulo').strip()
        titulo = str(season) + 'x' + str(epis) + ' ' + title_serie

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, 
                                    contentType = 'tvshow', contentSerieName = title_serie, contentSeason = season, contentEpisodeNumber = epis,
                                    infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if "<div class='wp-pagenavi'" in data:
            next_url = scrapertools.find_single_match(data, "class='current'>" + '.*?href="(.*?)"')
            if next_url:
                if '/page/' in next_url:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_url, action = 'last_episodes', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    title = 'Sin temporadas'

    platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#039;', "'").replace('&#8217;', "'"), '[COLOR tan]' + title + '[/COLOR]')
    item.page = 0
    item.contentType = 'season'
    item.contentSeason = 1
    itemlist = episodios(item)
    return itemlist


def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Lista de capítulos!<(.*?)</ul></div>')

    patron = '<a href="(.*?)">(.*?)</a>'

    matches = re.compile(patron, re.DOTALL).findall(bloque)

    if item.page == 0:
        sum_parts = len(matches)
        if sum_parts > 250:
            if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#039;', "'").replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos?'):
                platformtools.dialog_notification('EstrenosDoramas', '[COLOR cyan]Cargando elementos[/COLOR]')
                item.perpage = 250

    for url, title in matches[item.page * item.perpage:]:
        if not 'Capitulo' in title: continue

        epis = scrapertools.find_single_match(title, 'Capitulo(.*?)$').strip()

        if not epis: continue

        title = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName

        itemlist.append(item.clone( action='findvideos', url = url, title = title,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            break

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'Latino': 'Lat', 'Vose': 'Vose', 'VO': 'VO'}

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<div id="tab(.*?)"(.*?)</div>', re.DOTALL).findall(data)

    ses = 0

    for opt, resto in matches:
        url = scrapertools.find_single_match(resto, 'src="(.*?)"')

        if not url: continue

        ses += 1

        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url: continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if item.languages: lang = str(item.languages)
        else: lang = ''

        other = ''
        if servidor == 'directo':
            other = scrapertools.find_single_match(data, '<ul class="tabs">.*?<a href="#tab' + str(opt) + '">.*?<b>(.*?)</b>')
            other = other.replace('(', '').replace(')', '')

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                              other = other, language = IDIOMAS.get(lang, lang) ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.server == 'directo':
        if '.php' in item.url:
            headers = dict()
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            headers['X-Requested-With'] = 'XMLHttpRequest'
            headers['Origin'] = 'https://repro3.estrenosdoramas.us'

            data = httptools.downloadpage(item.url).data

            if 'pi76823.php' in item.url:
                matches = re.compile('post\( "(.*?)", { key: \'(.*?)\'', re.DOTALL).findall(data)

                for _page, _key in matches:
                    _base = item.url.rsplit('/', 1)[0] + '/'
                    headers["Origin"] = _base
                    _url = _base + _page

                    token_get = str(int(round(time.time())))
                    _token = base64.b64encode(token_get.encode("utf-8"))

                    _result = httptools.downloadpage(_url, post = 'key=' + _key + '&token=' + str(_token), headers = headers).data
                    _json = jsontools.load(_result)

                    if _json["link"]:
                        url = base64.b64decode(_json['link'])

                        if url.startswith('//') == True: url = 'https:' + url

                        servidor = servertools.get_server_from_url(url)
                        servidor = servertools.corregir_servidor(servidor)

                        url = servertools.normalize_url(servidor, url)

                        itemlist.append(item.clone(server = servidor, url = url))

                return itemlist

            elif 'pi7.php' in item.url:
                global GLBPLAYER

                GLBPLAYER = ''

                decrypt(data)

                if GLBPLAYER:
                    matches = re.compile('post\(\s?"(.*?)",\s?{\s?key: \'(.*?)\'', re.DOTALL).findall(GLBPLAYER)

                    for _page, _key in matches:
                        _base = item.url.rsplit('/', 1)[0] + '/'
                        headers["Origin"] = _base
                        _url = _base + _page

                        token_get = str(int(round(time.time())))
                        _token = base64.b64encode(token_get.encode("utf-8"))

                        _result = httptools.downloadpage(_url, post = 'key=' + _key + '&token=' + str(_token), headers = headers).data
                        _json = jsontools.load(_result)

                        if _json["link"]:
                            url = base64.b64decode(_json["link"])

                            if url.startswith('//') == True: url = 'https:' + url

                            servidor = servertools.get_server_from_url(url)
                            servidor = servertools.corregir_servidor(servidor)

                            url = servertools.normalize_url(servidor, url)

                            itemlist.append(item.clone(server = servidor, url = url))

                    return itemlist

            elif 'reproducir120.php' in item.url:
                _id = scrapertools.find_single_match(data, 'var videoidn = \'(.*?)\';')
                _token = scrapertools.find_single_match(data, 'var tokensn = \'(.*?)\';')

                matches = re.compile('post\( "(.*?)", { acc: "(.*?)"', re.DOTALL).findall(data)

                for _page, _acc in matches:
                    _url = item.url[0:item.url.find("reproducir120.php")] + _page

                    _result = httptools.downloadpage(_url, post = 'acc=' + _acc + '&id=' + _id + '&tk=' + _token, headers = headers)

                    if _result.code == 200:
                        _json = jsontools.load(_result.data)

                        urlremoto_matches = re.compile("file:'(.*?)'", re.DOTALL).findall(_json['urlremoto'])

                        if len(urlremoto_matches) == 1:
                            url = urlremoto_matches[0]

                            if url.startswith('//') == True: url = 'https:' + url

                            servidor = servertools.get_server_from_url(url)
                            servidor = servertools.corregir_servidor(servidor)

                            url = servertools.normalize_url(servidor, url)

                            itemlist.append(item.clone(server = servidor, url = url))

                return itemlist

            elif 'reproducir14.php' in item.url:
                matches = re.compile('<div id="player-contenido" vid="(.*?)" name="(.*?)"', re.DOTALL).findall(data)

                _id = matches[0][0]
                _token = matches[0][1]

                matches = re.compile('post\( "(.*?)", { acc: "(.*?)"', re.DOTALL).findall(data)

                for _page, _acc in matches:
                    _url = item.url[0:item.url.find("reproducir14.php")] + _page

                    _result = httptools.downloadpage(_url, post='acc=' + _acc + '&id=' + _id + '&tk=' + _token, headers = headers)

                    if _result.code == 200:
                        _json = jsontools.load(_result.data)

                        if _json['urlremoto']:
                            url = _json['urlremoto']

                            if url.startswith('//') == True: url = 'https:' + url

                            servidor = servertools.get_server_from_url(url)
                            servidor = servertools.corregir_servidor(servidor)

                            url = servertools.normalize_url(servidor, url)

                            itemlist.append(item.clone(server = servidor, url = url))

                return itemlist

    if url:
        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        if url.startswith('//') == True: url = 'https:' + url

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'search/' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# ~ Tools for player
# -*- By the BDamian (Based on channels from Alfa Develop Group) -*-

def set_player(secret):
    global GLBPLAYER
    GLBPLAYER = secret


def decrypt(data, index=0):
    index += 1

    matches = re.compile("\('([^']+)','([^\']?(?:\\.|[^\'])*)','([^\']?(?:\\.|[^\'])*)','([^\']?(?:\\.|[^\'])*)'", re.DOTALL) .findall(str(data))

    if len(matches) > 0:
        for w,i,s,e in matches:
            if not i and not s and not e: secret = decodeone(w)
            else:
               secret = decode(w,i,s,e)
               if "jwplayer" in secret:
                   secret = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", secret)
                   set_player(secret)

            decrypt(secret, index)

    return


def utf16_decimals(char):
    encoded_char = char.encode('utf-16-be')

    decimals = []

    for i in range(0, len(encoded_char), 2):
        chunk = encoded_char[i:i+2]
        decimals.append(struct.unpack('>H', chunk)[0])

    return decimals


def decode(w, i, s, e):
    lIll = 0
    ll1I = 0
    Il1l = 0

    ll1l = []
    l1lI = []

    while len(w) + len(i) + len(s) + len(e) != len(ll1l) + len(l1lI) + len(e):
        if lIll < 5: l1lI.append(w[lIll])
        elif lIll < len(w): ll1l.append(w[lIll])

        lIll += 1

        if ll1I < 5: l1lI.append(i[ll1I])
        elif ll1I < len(i): ll1l.append(i[ll1I])

        ll1I += 1

        if Il1l < 5: l1lI.append(s[Il1l])
        elif Il1l < len(s): ll1l.append(s[Il1l])

        Il1l += 1

    lI1l = ''.join(ll1l)
    I1lI = ''.join(l1lI)

    ll1I = 0

    l1ll = []

    for i in range(0,len(ll1l),2):
        lIll = i
        ll11 = -1

        nchar = utf16_decimals(I1lI[ll1I])[0]

        if nchar % 2: ll11 = 1

        l1ll.append( str(chr(int(lI1l[lIll:lIll+2], 36) - ll11)) )
        ll1I += 1

        if ll1I == len(l1lI): ll1I = 0

    return ''.join(l1ll)


def decodeone(w):
    i = ''

    for s in range(0,len(w),2):
        i +=  str(chr(int(w[s:s+2], 36)))

    return i
