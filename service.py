"""
    plugin.audio.addict service
    Polls AudioAddict now-playing data and updates player metadata.
"""

import os
import sys

import xbmc

TOPDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TOPDIR, 'resources', 'lib'))

from audioaddict.metadata import (  # pylint: disable=wrong-import-position
    FAST_POLL_SECONDS,
    clear_playback_state,
    fetch_current_track,
    load_playback_state,
    next_poll_seconds,
    update_player_from_track,
)


class MetadataMonitor(xbmc.Monitor):
    pass


class MetadataPlayer(xbmc.Player):
    def __init__(self):
        super(MetadataPlayer, self).__init__()
        self.refresh_requested = False

    def onAVStarted(self):
        self.refresh_requested = True

    def onPlayBackStopped(self):
        clear_playback_state()

    def onPlayBackEnded(self):
        clear_playback_state()

    def onPlayBackError(self):
        clear_playback_state()


def _apply_track(state, track, last_key):
    if not track:
        return last_key, None

    key = track.get('track_id') or '%s|%s' % (
        track.get('artist') or '',
        track.get('title') or '',
    )
    if key and key == last_key:
        return last_key, track

    if not track.get('art_url'):
        track = fetch_current_track(
            state['network_key'],
            state['channel_id'],
            include_art=True,
        ) or track

    update_player_from_track(
        state.get('channel_name') or '',
        state.get('channel_art') or '',
        track,
    )
    return key, track


def run():
    monitor = MetadataMonitor()
    player = MetadataPlayer()
    last_key = None
    current_track = None

    xbmc.log('AudioAddict metadata service started', xbmc.LOGINFO)

    while not monitor.abortRequested():
        wait_seconds = FAST_POLL_SECONDS
        try:
            state = load_playback_state()
            if player.isPlaying() and state:
                if player.refresh_requested:
                    player.refresh_requested = False
                    last_key = None

                track = fetch_current_track(
                    state['network_key'],
                    state['channel_id'],
                    include_art=(last_key is None),
                )
                last_key, current_track = _apply_track(state, track, last_key)
                wait_seconds = next_poll_seconds(current_track)
            else:
                last_key = None
                current_track = None
                wait_seconds = FAST_POLL_SECONDS
        except Exception as exc:  # pylint: disable=broad-except
            xbmc.log('AudioAddict metadata service error: %s' % exc,
                     xbmc.LOGWARNING)
            current_track = None
            wait_seconds = FAST_POLL_SECONDS

        if monitor.waitForAbort(wait_seconds):
            break

    xbmc.log('AudioAddict metadata service stopped', xbmc.LOGINFO)


if __name__ == '__main__':
    run()
