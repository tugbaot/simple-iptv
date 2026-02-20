# simple-iptv
A lightweight & customisable IPTV manager using mpv.exe to play iptv channels. I  created this as I wanted something simple and quick to just launch some TV. Works on Windows and Linux.
![simple-iptv screenshot](https://github.com/tugbaot/simple-iptv/blob/main/screenshots/screenshot.png)

### Install
To install, just clone or download the zip and uninstall wherever you like. Most things are configurable, e.g. size, font, theme, app name and icon.
It uses mpv as the player, so you need to have this installed:
- Windows: install and add the path to mpv.exe in confix.txt.
- Linux: just install `sudo apt install mpv` and the app will find it

Also requires:
- pip install -r requirements.txt

Run with ```python3 simple-iptv.py``` or see Tips below if you just want a normal shortcut.

### Theming

Pretty flexible to make it look how you want with a nice selection of inbuilt themes.
![themese](https://github.com/tugbaot/simple-iptv/blob/main/screenshots/themes.png)

### Basic features
- Search: search box to filter & search for channels
- Favourites: toggle view only favs or all channels
- Open M3U: to open a m3u file
- Load URL: to load an online m3u/XStream from an IPTV provider
- Save M3U: to save the current playlist (all or favs only) as an m3u file
- Save json: saves the full state, all channels and favourites.
- Clear list: clear current channels
- Double click to play
- Reorder the channels by dragging the TV icons

You can change many things, see:
- config.txt for various changes to the look & layout
- theme.xml for the colorscheme

### Tips
- If you don't want to run from the command line:
  - For Windows you can create a normal desktop shortcut with the following as target: ```C:\<path to>\pythonw.exe "C:\<path to>\simple-iptv.py"```
  - If you're using Linux you know this stuff.
- To try out some IPTV, you can try this url [https://iptv-org.github.io/iptv/index.m3u](https://iptv-org.github.io/iptv/index.m3u) which has a curated list of free channels from across the world. You can find more IPTV providers here [https://github.com/iptv-org/awesome-iptv](https://github.com/iptv-org/awesome-iptv?tab=readme-ov-file#providers)

### Config
```
[config]
app_name = Simple IPTV
# the name in the title bar
app_icon = mdi.television-classic
# the icon in the title bar using mdi icons, see https = //pictogrammers.com/library/mdi/
app_icon_color = #292623
# the icon color in the title bar, can be text or rgb
app_height = 533
app_width = 870
# the size of the application window
fullscreen = false
# if true, overrides the app_height and app_width
playlist_icon = mdi.television-classic
# icon used in the playlist
app_theme = dark_teal.xml
# default is theme.xml, but you can add your own or use those from qt_material (see below for the full list)
star_empty_color = #777777
# the color of the empty favourites star icon
row_height = 24
# for the spacing between playlist items
app_font = Century Gothic
app_font_size = 13px
# can be any font you have installed
mpv_path = mpv.exe
# the path to mpv.exe. the default is 'mpv.exe' where it's on path
list_name = playlist.json
# the filename used to save your playlist

[themes]
# alternate themes ###################
# associated color is for the fav star
theme.xml = #bd95b8
dark_amber.xml = #ffd740
dark_blue.xml = #448aff
dark_cyan.xml = #4dd0e1
dark_lightgreen.xml = #8bc34a
dark_pink.xml = #ff4081
dark_purple.xml = #ab47bc
dark_red.xml = #ff1744
dark_teal.xml = #1de9b6
dark_yellow.xml = #ffff00
light_amber.xml = #ffc400
light_blue.xml = #2979ff
light_blue_500.xml = #03a9f4
light_cyan.xml = #00e5ff
light_cyan_500.xml = #00bcd4
light_lightgreen.xml = #64dd17
light_lightgreen_500.xml = #8bc34a
light_orange.xml = #ff3d00
light_pink.xml = #ff4081
light_pink_500.xml = #e91e63
light_purple.xml = #e040fb
light_purple_500.xml = #9c27b0
light_red.xml = #ff1744
light_red_500.xml = #f44336
light_teal.xml = #1de9b6
light_teal_500.xml = #009688
light_yellow.xml = #ffea00

```



