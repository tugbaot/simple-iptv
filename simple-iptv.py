#!/usr/bin/python 
# Created: 02/02/2026
# Simple IPTV manager thing
# ##########################

import sys
import os
import json
import subprocess
import configparser
import requests

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QStyle, QInputDialog, QMessageBox,
    QLineEdit, QLabel, QListView, QStyledItemDelegate, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize, QSortFilterProxyModel, QStringListModel, QRect, QEvent
from PySide6.QtGui import QIcon, QPainter, QTextOption

from qt_material import apply_stylesheet
import qtawesome as qta

# ------- Use script path -----------
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# ------- Read config ---------------
config = configparser.ConfigParser()
config.read(r'config.txt')   

# ------- Configuration -------------
MPV_PATH = config.get('config', 'mpv_path')
STATE_FILE = config.get('config', 'list_name')
APP_NAME = config.get('config', 'app_name')
APP_ICON = config.get('config', 'app_icon')
APP_ICON_COLOR = config.get('config', 'app_icon_color')
PLAYLIST_ICON = config.get('config', 'playlist_icon')
APP_THEME = config.get('config', 'app_theme')
APP_FONT = config.get('config', 'app_font')
APP_FONT_SIZE = config.get('config', 'app_font_size')
STAR_COLOR = config.get('config', 'star_color')
STAR_EMPTY_COLOR = config.get('config', 'star_empty_color')
ROW_HEIGHT = int(config.get('config', 'row_height'))
APP_HEIGHT = int(config.get('config', 'app_height'))
APP_WIDTH = int(config.get('config', 'app_width'))
BUTTON_STYLE = (
    "text-align: left; padding-left: 12px; font-size: 8pt; "
    "font-weight: normal; border-width: 1px;"
)
INFO = "A simple, lightweight IPTV manager using mpv.exe to play iptv channels. I created this as I wanted something simple and quick to just launch some TV.\n\nFeatures:\n• Search: to search channel list\n• Favourites: toggle view only favs or all channels\n• Open M3U: to open a m3u file\n• Save M3U: to save the current playlist (all or favs only)\n• Load URL: to load an online m3u from an IPTV provider\n• Rename: to rename a highlighted channel\n• Clear list: clear all channels\n• Play: or double click to play\n• Reorder the channels by dragging the TV icons\n\nYou can tweak many things: \n• config.txt for various changes to the layout\n• config.txt to add your IPTV provider url\n• theme.xml for the colorscheme\n\n🌐 https://github.com/tugbaot/simple-iptv"

# ------- Right then ---------------
class PlaylistDelegate(QStyledItemDelegate):
    def __init__(self, height, icon, parent=None):
        super().__init__(parent)
        self.height = height
        self.icon = icon
        self.star_on = qta.icon("mdi.star", color=STAR_COLOR)
        self.star_off = qta.icon("mdi.star-outline", color=STAR_EMPTY_COLOR)

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), self.height)

    def paint(self, painter, option, index):
        painter.save()

        rect = option.rect
        text = index.data(Qt.DisplayRole)

        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())

        icon_size = 20
        margin = 8

        icon_rect = QRect(rect.left()+margin,
                          rect.top()+(rect.height()-icon_size)//2,
                          icon_size, icon_size)
        self.icon.paint(painter, icon_rect)

        star_rect = QRect(rect.right()-30,
                          rect.top()+(rect.height()-icon_size)//2,
                          icon_size, icon_size)

        main = self.parent().window()
        source_index = main.proxy_model.mapToSource(index)
        playlist_row = main.visible_rows[source_index.row()]
        fav = main.playlist[playlist_row][2]

        (self.star_on if fav else self.star_off).paint(painter, star_rect)

        text_rect = QRect(icon_rect.right()+8, rect.top()+4,
                          rect.width()-80, rect.height()-8)

        opt = QTextOption()
        opt.setWrapMode(QTextOption.WordWrap)

        painter.drawText(text_rect, text, opt)
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            rect = option.rect
            star_rect = QRect(rect.right()-30,
                              rect.top()+(rect.height()-20)//2,
                              20, 20)

            if star_rect.contains(event.pos()):
                main = self.parent().window()
                source_index = main.proxy_model.mapToSource(index)
                playlist_row = main.visible_rows[source_index.row()]
                main.playlist[playlist_row][2] = not main.playlist[playlist_row][2]
                main.refresh_list()
                return True
        return False


class M3UPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(qta.icon(APP_ICON,color=APP_ICON_COLOR))
        self.resize(APP_WIDTH, APP_HEIGHT)

        self.playlist = []
        self.show_favourites = False
        self.fav_icon_on = qta.icon("mdi.star", color=STAR_COLOR)
        self.fav_icon_off = qta.icon("mdi.star-outline", color=STAR_EMPTY_COLOR)

        self.init_ui()
        self.load_state()

    # ---------- UI ----------
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main = QHBoxLayout(central)
        main.setContentsMargins(12, 12, 12, 12)

        # Playlist
        # Search box
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search channels…")
        self.search.textChanged.connect(self.filter_changed)
        #self.search.hide() # uncomment if you want search to be hidden unless clicked
        self.search.setFocus(Qt.ShortcutFocusReason)
        self.search.selectAll()
        self.search.setClearButtonEnabled(True)


        main_left = QVBoxLayout()
        main_left.addWidget(self.search)

        # Base model
        self.model = QStringListModel()

        # Proxy model
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)

        # View
        self.list_view = QListView()
        self.list_view.setModel(self.proxy_model)
        self.list_view.doubleClicked.connect(self.play_selected)
        self.list_view.setDragDropMode(QListView.InternalMove)
        self.list_view.setDefaultDropAction(Qt.MoveAction)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        playlist_icon = qta.icon(PLAYLIST_ICON)

        self.list_view.setItemDelegate(
            PlaylistDelegate(ROW_HEIGHT, playlist_icon, self.list_view)
        )
        self.list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_left.addWidget(self.list_view, 1)
        main.addLayout(main_left, 1)

        # Controls
        controls = QVBoxLayout()
        controls.setSpacing(8)

        btn_search = self.make_button(" Search", "mdi.magnify", self.toggle_search) 
        btn_open = self.make_button(" Open M3U", "mdi.folder-open", self.load_m3u)
        btn_url = self.make_button(" Load URL", "mdi.link", self.load_url)
        btn_save = self.make_button(" Save M3U", "mdi.link", self.save_m3u)
        btn_rename = self.make_button(" Rename", "mdi.pencil", self.rename_item)
        btn_clear = self.make_button(" Clear list", "mdi.delete-outline", self.clearlist)
        btn_play = self.make_button(" Play", "mdi.play-circle", self.play_selected)
        btn_info = self.make_button(" Info", "mdi.information", self.info)
        btn_quit = self.make_button(" Quit", "mdi.exit-to-app", self.quit)
        self.btn_fav = self.make_button(" Favourites", "mdi.star-outline", self.toggle_favourites)
        self.btn_fav.setToolTip("Show favourites only")

        controls.insertWidget(0, btn_search) # comment out if you don't want to toggle the search bar
        controls.insertWidget(1, self.btn_fav)
        controls.addWidget(btn_open)
        controls.addWidget(btn_url)
        controls.addWidget(btn_save)
        controls.addWidget(btn_rename)
        controls.addWidget(btn_clear)
        controls.addStretch()
        controls.addWidget(btn_play)
        controls.addWidget(btn_info)
        controls.addWidget(btn_quit)

        main.addLayout(controls)

    # ---------- Buttons -----------
    def make_button(self, text, icon_name, callback):
        btn = QPushButton(text)
        btn.setIcon(qta.icon(icon_name))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumWidth(140)
        btn.setIconSize(QSize(20, 20))
        btn.setStyleSheet(BUTTON_STYLE)
        btn.clicked.connect(callback)
        return btn

    # ---------- Playlist ----------
    def toggle_favourites(self):
        self.show_favourites = not self.show_favourites

        if self.show_favourites:
            self.btn_fav.setIcon(self.fav_icon_on)
            self.btn_fav.setToolTip("Showing favourites — click to show ALL channels")
        else:
            self.btn_fav.setIcon(self.fav_icon_off)
            self.btn_fav.setToolTip("Show favourites only")

        self.refresh_list()

    def refresh_list(self):
        names = []
        self.visible_rows = []  # maps view row → playlist row

        for i, item in enumerate(self.playlist):
            if not self.show_favourites or item[2]:
                names.append(item[0])
                self.visible_rows.append(i)

        self.model.setStringList(names)

    def filter_changed(self, text):
        self.proxy_model.setFilterFixedString(text)

    # ---------- Toggle Search ---------
    def toggle_search(self):
        if self.search.isVisible():
            self.clear_search()
        else:
            self.search.show()
            self.search.setFocus()

    def clear_search(self):
        self.search.clear()
        self.search.hide()
        self.proxy_model.setFilterFixedString("")
        self.update_drag_state()

    def update_drag_state(self):
        searching = bool(self.search.text().strip())

        self.list_view.setDragEnabled(not searching)
        self.list_view.setAcceptDrops(not searching)
        self.list_view.setDropIndicatorShown(not searching)

    # ---------- Load M3U ---------
    def load_m3u(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open M3U", "", "M3U Files (*.m3u)"
        )
        if not path:
            return

        self.playlist.clear()

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                name = None
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#EXTM3U"):
                        continue
                    if line.startswith("#EXTINF"):
                        name = line.split(",", 1)[-1]
                    else:
                        display = name if name else os.path.basename(line)
                        self.playlist.append([display, line, False])
                        name = None

            self.refresh_list()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# ---------- Load URL ---------
    def load_url(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Load URL")
        dialog.setLabelText("Enter playlist URL:")
        dialog.setOkButtonText("Load")
        dialog.setCancelButtonText("Cancel")
        dialog.resize(400, 120)

        for btn in dialog.findChildren(QPushButton):
            btn.setStyleSheet(BUTTON_STYLE)

        buttons = dialog.findChildren(QPushButton)

        for btn in buttons:
            if "Load" in btn.text():
                btn.setIcon(qta.icon("mdi.link"))
            elif "Cancel" in btn.text():
                btn.setIcon(qta.icon("mdi.close"))

        if dialog.exec():
            url = dialog.textValue().strip()
        else:
            return

        if not url:
            return

        response = requests.get(url)
        m3u = response.text
        with open("loaded.m3u", "w", encoding="utf-8") as m:
            m.write(m3u)

        self.playlist.clear()

        try:
            with open("loaded.m3u", "r", encoding="utf-8", errors="ignore") as f:
                name = None
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#EXTM3U"):
                        continue
                    if line.startswith("#EXTINF"):
                        name = line.split(",", 1)[-1]
                    else:
                        display = name if name else os.path.basename(line)
                        self.playlist.append([display, line, False])
                        name = None

            self.refresh_list()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# ---------- Save M3U ---------
    def save_m3u(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save playlist",
            "playlist.m3u",
            "M3U Files (*.m3u)"
        )

        if not path:
            return

        try:
            model = self.model  # source model (NOT proxy)

            with open(path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")

                for row in range(model.rowCount()):
                    index = model.index(row, 0)
                    name = model.data(index).strip()

                    # find matching URL in playlist
                    for item in self.playlist:
                        display, url = item[0], item[1]
                        if display == name:
                            f.write(f"#EXTINF:-1,{display}\n")
                            f.write(f"{url}\n")
                            break

            QMessageBox.information(self, "Saved", "Playlist saved successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e)) 


    # ---------- Clear ---------
    def clearlist(self):
        self.playlist.clear()
        self.refresh_list()

    # ---------- Info box ---------
    def info(self):
        ret = QMessageBox.about(self,"Info",INFO)

    # ---------- Quit -------------
    def quit(self):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "playlist": self.playlist,
                "show_favourites": self.show_favourites
            }, f, indent=2)
        sys.exit()

    # ---------- Renaming ---------
    def rename_item(self):
        index = self.list_view.currentIndex()
        if not index.isValid():
            return

        source_index = self.proxy_model.mapToSource(index)
        row = source_index.row()

        current = self.playlist[row][0]
        text, ok = QInputDialog.getText(
            self, "Rename Item", "New name:", text=current
        )

        if ok and text:
            self.playlist[row][0] = text
            self.refresh_list()

    # ---------- Playback ----------
    def play_selected(self):
        index = self.list_view.currentIndex()
        if not index.isValid():
            return

        # Map proxy → source
        source_index = self.proxy_model.mapToSource(index)
        row = source_index.row()

        media_path = self.playlist[row][1]
        print(MPV_PATH)
        print(media_path)

        try:
            subprocess.Popen([MPV_PATH, media_path])
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "mpv not found",
                "mpv.exe not found.\nCheck MPV_PATH in config.txt.",
            )

    # ---------- Persistence ----------
    def load_state(self):
        if not os.path.exists(STATE_FILE):
            return

        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Support old save format
                if isinstance(data, list):
                    self.playlist = data
                    self.show_favourites = False
                else:
                    self.playlist = data.get("playlist", [])
                    self.show_favourites = data.get("show_favourites", False)

                for item in self.playlist:
                    if len(item) == 2:
                        item.append(False)
            # Update favourites button icon/state
                if self.show_favourites:
                    self.btn_fav.setIcon(self.fav_icon_on)
                    self.btn_fav.setToolTip("Showing favourites — click to show ALL channels")
                else:
                    self.btn_fav.setIcon(self.fav_icon_off)
                    self.btn_fav.setToolTip("Show favourites only")

                self.refresh_list()
        except Exception:
            pass

    # ---------- Closing ----------
    def closeEvent(self, event):

        # Only reorder if showing FULL unfiltered list
        if not self.show_favourites and not self.search.text().strip():

            new_order = []
            model = self.model

            for row in range(model.rowCount()):
                index = model.index(row, 0)
                name = model.data(index).strip()

                for entry in self.playlist:
                    if entry[0] == name:
                        new_order.append(entry)
                        break

            self.playlist = new_order

        # Always save full playlist
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "playlist": self.playlist,
                    "show_favourites": self.show_favourites
                }, f, indent=2)
        except Exception as e:
            print("Failed to save state:", e)

        event.accept()


# ---------- Entry Point ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Theme
    apply_stylesheet(
        app, 
        theme=APP_THEME,
        extra={"font_family": APP_FONT, "font_size": APP_FONT_SIZE,},
    )
    
    window = M3UPlayer()
    window.show()

    sys.exit(app.exec())

