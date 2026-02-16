# simple-iptv
A lightweight & customisable IPTV manager using mpv.exe to play iptv channels. I  created this as I wanted something simple and quick to just launch some TV.
![simple-iptv screenshot](https://github.com/tugbaot/simple-iptv/blob/main/screenshots/screenshot.png)

### Install
To install, just clone or download the zip and uninstall wherever you like. Most things are configurable, e.g. size, font, theme, app name and icon.
It uses mpv.exe as the player, you just need to add the path to mpv.exe in confix.txt.

Run with ```py simple-iptv.py``` or see Tips below if you just want a normal shortcut.

Requires:
- pip install pyside6 qtawesome configparser
- mpv.exe (just add in config.txt where it's installed)

### Theming

Pretty flexible to make it look how you want with a nice selection of inbuilt themes.
![themese](https://github.com/tugbaot/simple-iptv/blob/main/screenshots/themes.png)

### Basic features
- Search: search box to filter & search for channels
- Favourites: toggle view only favs or all channels
- Open M3U: to open a m3u file
- Load URL: to load an online m3u/XStream from an IPTV provider
- Save M3U: to save the current playlist (all or favs only) as an m3u file
- Rename: to rename a highlighted channel
- Clear list: clear current channels
- Play: or double click to play
- Reorder the channels by dragging the TV icons

You can change many things, see:
- config.txt for various changes to the look & layout
- theme.xml for the colorscheme

### Tips
- If you don't want to run from the command line, you can create a normal desktop shortcut with the following as target: ```C:\<path to>\pythonw.exe "C:\<path to>\simple-iptv.py"```
- To try out some IPTV, you can try this url [https://iptv-org.github.io/iptv/index.m3u](https://iptv-org.github.io/iptv/index.m3u) which has a curated list of free channels from across the world. You can find more IPTV providers here [https://github.com/iptv-org/awesome-iptv](https://github.com/iptv-org/awesome-iptv?tab=readme-ov-file#providers)

### Config
```
# ----------------------------------------
# simple-iptv config for some basic stuff
# ----------------------------------------

[config]
app_name = Simple IPTV
# the name in the title bar

app_icon = mdi.television-classic
# the icon in the title bar using mdi icons, see https://pictogrammers.com/library/mdi/ 

app_icon_color = #292623
# the icon color in the title bar, can be text or RGB

app_height: 560
app_width: 800
# the size of the application window

fullscreen = false
# if True, overrides the app_height and app_width

playlist_icon = mdi.television-classic
# icon used in the playlist

app_theme = theme.xml
# default is theme.xml, but you can modify, add your own or use those from qt_material (see below for the full list)

row_height: 24
# for the spacing between playlist items

app_font = Century Gothic
app_font_size = 13px
# can be any font you have installed

mpv_path = mpv.exe
# the path to mpv.exe. the default is 'mpv.exe' where it's on PATH

list_name = playlist.json
# the filename used to save your playlist
```



