# plugin.audio.addict

Kodi audio add-on for the AudioAddict radio networks:

- [DigitallyImported](https://www.di.fm)
- [RadioTunes](https://www.radiotunes.com)
- [RockRadio](https://www.rockradio.com)
- [JazzRadio](https://www.jazzradio.com)
- [ClassicalRadio](https://www.classicalradio.com)
- [ZenRadio](https://www.zenradio.com)

Requires a **premium** AudioAddict account and your **Listen Key**.

Current version: **0.8.9** (Kodi Omega / Android Shield compatible).

## Features

- Browse networks and channels, then play live premium streams
- Music/internet-stream tagging for Kodi 19–21
- Optional `inputstream.ffmpegdirect` for more stable live MP3 playback
- Background service that updates artist, title, and artwork from the AudioAddict now-playing API
- HTTPS API / artwork / referer handling

## Install

This add-on is installed from a zip file.

1. Build or download `plugin.audio.addict.zip`
2. In Kodi: **Add-ons → Install from zip file**
3. Fully quit and restart Kodi after install/upgrade
4. Open **AudioAddict** settings and paste your **Listen Key**
5. Pick quality and enable the networks you want

### Build the install zip (Windows)

From the project folder:

```powershell
python build_zip.py
```

That creates `plugin.audio.addict.zip` next to the project folder, with the layout Kodi expects (`plugin.audio.addict/addon.xml` as the root content).

### Listen Key

Find it in your network account settings, for example:

https://www.di.fm/settings

One premium account works across the AudioAddict networks.

## Settings

- **Listen Key** — required
- **Quality** — `low` / `moderate` / `medium` / `high`
- **Networks** — enable/disable DI, RadioTunes, RockRadio, JazzRadio, ClassicalRadio, ZenRadio

## Notes

- Do **not** commit your Listen Key or Kodi `addon_data` settings into git
- A second stream connection with the same Listen Key can disconnect playback; this add-on avoids that
- Artist Slideshow and skin now-playing views use the metadata the service pushes into Kodi’s player

## License

GNU General Public License v3

## Credits

Original add-on by Samuel Sapalski (@leas), Fritz Capell, wanilton. Logo by Rantanplan-1 (forum.kodi.tv).
