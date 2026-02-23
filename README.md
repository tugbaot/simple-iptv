# simple-iptv
A lightweight & customisable IPTV manager using MPV to play iptv channels for Windows and Linux.

I created this as I wanted something simple and quick to just launch some TV.
![simple-iptv screenshot](https://github.com/tugbaot/simple-iptv/blob/main/screenshots/screenshot.png)

### Install
To install, just clone or download the zip and uninstall wherever you like. Most things are configurable, e.g. size, font, theme, app name and icon.
It uses mpv as the player, so you need to have this installed:
- Windows: install and add the path to mpv.exe in confix.txt.
- Linux: just install `sudo apt install mpv` and the app will find it

Also requires:
- `pip install -r requirements.txt`

Run with `python3 simple-iptv.py` or see Tips below if you just want a normal shortcut.

### Theming

Pretty flexible so you can make it look how you want with a nice selection of inbuilt themes you can use or create your own.

You can change many things, see:
- config.txt for various changes to the look & layout
- change the theme to any in the themes folder or add your own

![themese](https://github.com/tugbaot/simple-iptv/blob/main/screenshots/themes.png)

### Basic features
- Search: search box to filter & search for channels
- Favourites: toggle view only favs or all channels
- Open M3U: to open a m3u file
- Load URL: to load an online m3u/XStream from an IPTV provider
- Save M3U: to save the current playlist (all or favs only) as an m3u file
- Xtream: Load from your Xtream IPTV provider
- Save json: saves the full state, all channels and favourites.
- Clear list: clear current channels
- Double click to play
- Reorder the channels by dragging the TV icons

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
minimise = True
# whether the app minimises after play starts
playlist_icon = mdi.television-classic
# icon used in the playlist
app_theme = ebony.xml
# pick any from the list below or make you're own
star_empty_color = #777777
# the color of the empty favourites star icon
row_height = 24
# for the spacing between playlist items
app_font = Century Gothic
app_font_size = 13px
# can be any font you have installed
mpv_path = mpv.exe
# for Windows, the path to mpv.exe. the default is 'mpv.exe' where it's on path
list_name = playlist.json
# the filename used to save your playlist

[xtream]
iptv_name = TEST IPTV
iptv_url = http://test.iptv
iptv_user = test
iptv_pass = test
# your iptv login info

[themes]
# alternate themes ###################
# associated color is for the fav star which is applied based on your theme choice
charcoal-blue.xml = #E76F51
vintage-grape.xml = #ce4257
sapphire.xml = #B9D6F2
amaranth.xml = #2CE6C0
chocolate-plum.xml = #40C9A2
granite.xml = #59C9A5
gunmetal.xml = #A2999E
ebony.xml = #E3DC95


```



