# simple-iptv
A simple, no nonsense IPTV manager using mpv.exe to play iptv channels. I  created this as I wanted something lightweight and quick to just launch some TV.
![simple-iptv screenshot](https://github.com/tugbaot/simple-iptv/blob/main/Screenshot.png)

### Install
To install, just download the zip and uninstall wherever you like. Most things are configurable, e.g. size, font, theme, app name and icon.
It uses mpv.exe as the player, you just need to add the path to mpv.exe in confix.txt.

Run with ```py simple-iptv.py``` 

Requires:
- pip install pyside6 qtawesome configparser
- mpv.exe (just add in config.txt where it's installed)

### Basic features
- Open M3U: to open a m3u file
- Load URL: to load an online m3u from an IPTV provider
- Rename: to rename a highlighted channel
- Play: or double click to play
- Reorder the channels by dragging the TV icons

You can change many things, see:
- config.txt for various changes to the layout
- config.txt to add your IPTV provider url
- theme.xml for the colorscheme

### Tips
- If your IPTV provider has a lot (thousands) of channels, **simple-iptv** doesn't (yet) allow you to create favourites and filter the channels. For this I use the brilliant [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr)

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

playlist_icon = mdi.television-classic
# icon used in the playlist

app_theme = theme.xml
# default is theme.xml, but you can add your own or use those from qt_material (see below for the full list)

row_height: 24
# for the spacing between playlist items

app_font = Century Gothic
app_font_size = 13px
# can be any font you have installed

m3u_url = http://192.168.1.2:9191/output/m3u
# url of your online provider
# TIP: where an online provider has thousands of channels, you can use Dispatcharr to rationalise these.

mpv_path = mpv.exe
# the path to mpv.exe. the default is 'mpv.exe' where it's on PATH

list_name = playlist.json
# the filename used to save your playlist
```

### To do
- Search for channels
- Favourites
- Filter
  
(all currently handled by [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr))
