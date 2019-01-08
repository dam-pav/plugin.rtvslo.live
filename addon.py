# -*- coding: utf-8 -*-
import json
import sys
import urllib
import urllib2
import urlparse

import xbmcgui
import xbmcplugin

#######################################

# global constants

url_base = 'http://api.rtvslo.si/ava/'
client_id = '82013fb3a531d5414f478747c1aca622'


# classes

#######################################

# functions
def parseToListEntry(stream_id, _args):
    # url parameters
    url_query = {}
    url_query['client_id'] = client_id
    url_query['callback'] = 'ava_999'
    url = build_url(url_base + 'getLiveStream/' + stream_id, url_query)

    rtvsloHtml = urllib2.urlopen(url)
    rtvsloData = rtvsloHtml.read()
    rtvsloHtml.close()

    # extract json from response
    x = rtvsloData.find('({')
    y = rtvsloData.rfind('});')
    if x < 0 or y < 0:
        xbmcgui.Dialog().ok('RTV Slovenija', 'Strežnik ni posredoval seznama.')
        return

    # parse json to a list of streams
    rtvsloData = rtvsloData[x + 1:y + 1]

    j = json.loads(rtvsloData)
    j = j['response']
    if len(j) == 0:
        return

    typeOK = True
    try:
        if contentType == 'audio' and j['mediaType'] == 'video':
            typeOK = False
        if contentType == 'video' and j['mediaType'] == 'audio':
            typeOK = False
    except:
        pass

    if typeOK:
        # newer video streams usually have this format
        try:
            stream_url = j['addaptiveMedia']['hls']
        except:
            # audio streams and some older video streams have this format
            try:
                stream_url = j['mediaFiles'][0]['streamer'] + j['mediaFiles'][0]['file']
            except:
                xbmcgui.Dialog().ok('RTV Slovenija',
                                    'Naslova kanala ni mogoče ugotoviti.')
                return

    # list stream
    if stream_url:
        try:
            broadcast_title = j['onair']['current']['broadcast']['title']
            broadcast_genre = j['onair']['current']['broadcast']['slottitle']
            broadcast_plot = j['onair']['current']['broadcast']['txreq_synopsis']
        except:
            broadcast_title = j['title']
            broadcast_genre = ''
            broadcast_plot = ''

        list_item = xbmcgui.ListItem(broadcast_title, j['title'])
        list_item.setArt({'thumb': j['images'].get('orig', ''),
                          'poster': j['images'].get('orig', ''),
                          'banner': j['images'].get('orig', ''),
                          'fanart': j['images'].get('orig', ''),
                          'clearart': j['images'].get('fp1', ''),
                          'clearlogo': j['images'].get('fp2', ''),
                          'landscape': j['images'].get('wide1', ''),
                          'icon': j['images'].get('fp3', '')})

        if contentType == 'audio':
            list_item.setInfo('music', {  # 'duration': j.get('duration', '0'),
                'genre': broadcast_genre,
                # 'title': j.get('title', ''),
                # 'playcount': j.get('views', '')
            })
        elif contentType == 'video':
            list_item.setInfo('video', {  # 'duration': j.get('duration', '0'),
                'genre': broadcast_genre,
                'title': broadcast_title,
                # 'playcount': '',
                'aired': j.get('stamp_real', ''),
                'plot': broadcast_plot,
                # 'plotoutline': '',
                'tvshowtitle': broadcast_title})

        xbmcplugin.addDirectoryItem(handle=handle, url=stream_url, listitem=list_item)


def do_LiveRadio():
    liveList = ['ra.a1', 'ra.val202', 'ra.ars', 'ra.mb1', 'ra.kp', 'ra.capo', 'ra.rsi', 'ra.mmr']

    for channel in liveList:
        parseToListEntry(channel, {})


def do_LiveTV():
    liveList = ['tv.slo1', 'tv.slo2', 'tv.slo3', 'tv.kp1', 'tv.mb1', 'tv.mmctv']

    for channel in liveList:
        parseToListEntry(channel, {})


def build_url(base, query):
    return base + '?' + urllib.urlencode(query)


#######################################

# main
if __name__ == "__main__":
    try:
        # arguments
        Argv = sys.argv

        # get add-on base url
        base = str(Argv[0])

        # get add-on handle
        handle = int(Argv[1])

        # in some cases kodi returns empty sys.argv[2]
        if Argv[2] == '':
            selection = xbmcgui.Dialog().select(
                'Kodi ni posredoval informacije o vrsti vsebine.\n\nIzberi vrsto vsebine:', ['TV', 'Radio'])
            if selection == 0:
                Argv[2] = '?content_type=video'
            else:
                Argv[2] = '?content_type=audio'

        # get add-on args
        args = urlparse.parse_qs(Argv[2][1:])

        # get content type
        contentType = str(args.get('content_type')[0])
        if contentType == 'audio':
            xbmcplugin.setContent(handle, 'songs')
        elif contentType == 'video':
            xbmcplugin.setContent(handle, 'videos')

        if contentType == 'audio':
            # LIVE RADIO
            do_LiveRadio()

        elif contentType == 'video':
            # LIVE TV
            do_LiveTV()

        # write contents
        xbmcplugin.endOfDirectory(handle)

    except Exception as e:
        xbmcgui.Dialog().ok('RTV Slovenija', 'Prišlo je do napake:\n' + e.message)
