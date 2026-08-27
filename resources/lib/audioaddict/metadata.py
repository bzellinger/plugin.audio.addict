"""
    audioaddict.metadata
    Now-playing track metadata for live streams.
"""

import json
import os
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from audioaddict.api import AudioAddictApi

STATE_FILENAME = 'nowplaying.json'
POLL_SECONDS = 5
FAST_POLL_SECONDS = 2
END_WINDOW_SECONDS = 45


def _profile_path():
    addon = xbmcaddon.Addon()
    return xbmcvfs.translatePath(addon.getAddonInfo('profile'))


def _state_path():
    return os.path.join(_profile_path(), STATE_FILENAME)


def save_playback_state(network_key, channel, stream_url=None, headers=None):
    path = _state_path()
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder)

    state = {
        'network_key': network_key,
        'channel_id': channel.id,
        'channel_key': channel.key,
        'channel_name': channel.name,
        'channel_art': channel.image_default(),
    }
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(state, handle)


def load_playback_state():
    path = _state_path()
    if not os.path.exists(path):
        return None

    try:
        with open(path, 'r', encoding='utf-8') as handle:
            return json.load(handle)
    except (IOError, ValueError, TypeError):
        return None


def clear_playback_state():
    path = _state_path()
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def next_poll_seconds(track):
    if not track:
        return FAST_POLL_SECONDS

    ends_at = track.get('ends_at')
    if not ends_at:
        return POLL_SECONDS

    remaining = float(ends_at) - time.time()
    if remaining <= END_WINDOW_SECONDS:
        return FAST_POLL_SECONDS

    return max(FAST_POLL_SECONDS, min(POLL_SECONDS, remaining - END_WINDOW_SECONDS))


def apply_track_to_listitem(list_item, channel, track=None):
    title = channel.name
    artist = ''
    album = channel.name
    art = {'thumb': channel.image_default()}

    if track:
        if track.get('title'):
            title = track['title']
        if track.get('artist'):
            artist = track['artist']
        if track.get('art_url'):
            art['thumb'] = track['art_url']
            art['fanart'] = track['art_url']

    list_item.setArt(art)
    _set_music_tags(list_item, title, artist, album)


def update_player_from_track(channel_name, channel_art, track):
    """Update Kodi's active player item in-place (needed for skins/AS)."""
    if not track:
        return

    player = xbmc.Player()
    if not player.isPlaying():
        return

    title = track.get('title') or channel_name
    artist = track.get('artist') or ''
    art_url = track.get('art_url') or channel_art or ''

    list_item = None
    if hasattr(player, 'getPlayingItem'):
        try:
            list_item = player.getPlayingItem()
        except Exception:
            list_item = None

    if list_item is None:
        list_item = xbmcgui.ListItem()

    art = {}
    if art_url:
        art['thumb'] = art_url
        art['fanart'] = art_url
    if art:
        list_item.setArt(art)

    _set_music_tags(list_item, title, artist, channel_name)

    # Window properties help Artist Slideshow / skins notice changes quickly.
    home = xbmcgui.Window(10000)
    home.setProperty('AudioAddict.Artist', artist)
    home.setProperty('AudioAddict.Title', title)
    home.setProperty('AudioAddict.Album', channel_name)
    if art_url:
        home.setProperty('AudioAddict.Art', art_url)

    if hasattr(player, 'updateInfoTag'):
        try:
            player.updateInfoTag(list_item)
        except Exception as exc:  # pylint: disable=broad-except
            xbmc.log('AudioAddict metadata update failed: %s' % exc,
                     xbmc.LOGWARNING)


def _set_music_tags(list_item, title, artist, album):
    if hasattr(list_item, 'getMusicInfoTag'):
        tag = list_item.getMusicInfoTag()
        tag.setTitle(title)
        tag.setAlbum(album)
        tag.setMediaType('song')
        if artist:
            if hasattr(tag, 'setArtists'):
                tag.setArtists([artist])
            if hasattr(tag, 'setArtist'):
                try:
                    tag.setArtist(artist)
                except Exception:
                    pass
    else:
        info = {
            'title': title,
            'album': album,
            'mediatype': 'song',
        }
        if artist:
            info['artist'] = artist
        list_item.setInfo('music', info)


def fetch_current_track(network_key, channel_id, include_art=True):
    try:
        api = AudioAddictApi(network_key)
        track = api.current_track(channel_id)
        if track and include_art and not track.get('art_url'):
            track['art_url'] = api.track_art_url(track.get('track_id'))
        return track
    except Exception as exc:  # pylint: disable=broad-except
        xbmc.log('AudioAddict track lookup failed: %s' % exc, xbmc.LOGDEBUG)
        return None


def enrich_icy_track(network_key, channel_id, icy_track):
    """Deprecated helper kept for compatibility; prefer fetch_current_track."""
    if not icy_track:
        return None

    track = {
        'artist': icy_track.get('artist') or '',
        'title': icy_track.get('title') or '',
        'art_url': '',
        'track_id': None,
        'source': 'icy',
    }

    api_track = fetch_current_track(network_key, channel_id, include_art=True)
    if api_track:
        track['art_url'] = api_track.get('art_url') or ''
        track['track_id'] = api_track.get('track_id')
        track['ends_at'] = api_track.get('ends_at')
        track['duration'] = api_track.get('duration')
        if not track.get('artist'):
            track['artist'] = api_track.get('artist') or ''
        if not track.get('title'):
            track['title'] = api_track.get('title') or ''

    return track
