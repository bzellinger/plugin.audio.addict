"""
    audioaddict.play
    Functionality triggered if the user starts/plays a channel.
"""

import urllib.parse

import requests
import xbmc
import xbmcaddon
import xbmcplugin

from audioaddict.api import AudioAddictApi
from audioaddict.channels import create_list_item
from audioaddict.exceptions import NoStreamingServerOnlineError
from audioaddict.metadata import fetch_current_track, save_playback_state


def play_stream(addon, settings):
    network_key = addon.args['network_key']
    channel_key = addon.args['channel_key']

    network = settings.get_network(network_key)

    listen_key = addon.getSetting('listen_key')
    quality_key = addon.getSetting('quality')
    stream_key = network.get_stream_key(quality_key)

    api = AudioAddictApi(network_key)
    playlist = api.playlist(stream_key, channel_key, listen_key)
    channel = api.channel_by_key(channel_key)

    headers = _stream_headers(settings, network)
    channel_url = get_valid_channel_url(playlist, headers)

    track = fetch_current_track(network_key, channel.id)
    list_item = create_list_item(channel, track=track)
    _configure_stream_list_item(list_item, channel_url, settings, network)

    save_playback_state(network_key, channel, channel_url, headers)

    xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
    xbmcplugin.setResolvedUrl(addon.handle, True, list_item)


def _stream_headers(settings, network):
    return {
        'User-Agent': settings.user_agent,
        'Referer': network.referer,
        'Icy-MetaData': '1',
    }


def _append_stream_options(channel_url, settings, network):
    options = urllib.parse.urlencode({
        'User-Agent': settings.user_agent,
        'Referer': network.referer,
        'Icy-MetaData': '1',
    })
    return '%s|%s' % (channel_url, options)


def _configure_stream_list_item(list_item, channel_url, settings, network):
    list_item.setMimeType('audio/mpeg')
    list_item.setPath(_append_stream_options(channel_url, settings, network))

    if _ffmpegdirect_available():
        list_item.setProperty('inputstream', 'inputstream.ffmpegdirect')
        list_item.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
        list_item.setProperty('inputstream.ffmpegdirect.open_mode', 'ffmpeg')


def _ffmpegdirect_available():
    try:
        xbmcaddon.Addon('inputstream.ffmpegdirect')
        return True
    except RuntimeError:
        return False


def get_valid_channel_url(playlist, headers):
    fallback = None

    for channel_url in playlist:
        if fallback is None:
            fallback = channel_url

        if stream_reachable(channel_url, headers):
            return channel_url

    if fallback:
        return fallback

    raise NoStreamingServerOnlineError()


def stream_reachable(channel_url, headers):
    try:
        with requests.get(channel_url,
                          headers=headers,
                          stream=True,
                          timeout=(5, 5)) as response:
            if response.status_code >= 400:
                return False

            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    return True
    except requests.exceptions.RequestException:
        return False

    return False
