#!/usr/bin/python 
# Created: 02/02/2026
# Simple IPTV manager thing
# ##########################
# TO DO
# Double click is iffy
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
from PySide6.QtCore import Qt, QSize, QSortFilterProxyModel, QStringListModel, QRect
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
M3U_URL = config.get('config', 'm3u_url')
APP_NAME = config.get('config', 'app_name')
APP_ICON = config.get('config', 'app_icon')
APP_ICON_COLOR = config.get('config', 'app_icon_color')
PLAYLIST_ICON = config.get('config', 'playlist_icon')
APP_THEME = config.get('config', 'app_theme')
APP_FONT = config.get('config', 'app_font')
APP_FONT_SIZE = config.get('config', 'app_font_size')
ROW_HEIGHT = int(config.get('config', 'row_height'))
APP_HEIGHT = int(config.get('config', 'app_height'))
APP_WIDTH = int(config.get('config', 'app_height'))
INFO = "A simple, no nonsense IPTV manager using mpv.exe to play iptv channels. I created this as I wanted something lightweight and quick to just launch some TV.\n\nBasic features:\n• Search: to search channel list\n• Open M3U: to open a m3u file\n• Load URL: to load an online m3u from an IPTV provider\n• Rename: to rename a highlighted channel\n• Clear list: clear all channels\n• Play: or double click to play\n• Reorder the channels by dragging the TV icons\n\nYou can tweak many things: \n• config.txt for various changes to the layout\n• config.txt to add your IPTV provider url\n• theme.xml for the colorscheme\n\n🌐 https://github.com/tugbaot/simple-iptv"

# ------- Right then ---------------
class PlaylistDelegate(QStyledItemDelegate):
    def __init__(self, height, icon, parent=None):
        super().__init__(parent)
        self.height = height
        self.icon = icon

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), self.height)

    def paint(self, painter, option, index):
        painter.save()

        rect = option.rect
        text = index.data(Qt.DisplayRole)

        # ---- Background (hover / selection handled by style)
        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())
        #elif option.state & QStyle.State_MouseOver:
        #    painter.fillRect(rect, option.palette.base().color().lighter(105))
        # -- this seems to cause a bug where a black highlight bar might appear on prev selection 

        # ---- Icon
        icon_size = 20
        icon_margin = 8

        icon_rect = QRect(
            rect.left() + icon_margin,
            rect.top() + (rect.height() - icon_size) // 2,
            icon_size,
            icon_size
        )
        self.icon.paint(painter, icon_rect)

        # ---- Text (multi-line, word wrap)
        text_rect = QRect(
            icon_rect.right() + 8,
            rect.top() + 4,
            rect.width() - icon_rect.width() - 24,
            rect.height() - 8
        )

        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WordWrap)

        painter.setPen(option.palette.text().color())
        painter.drawText(text_rect, text, text_option)

        painter.restore()

class M3UPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(qta.icon(APP_ICON,color=APP_ICON_COLOR))
        self.resize(APP_WIDTH, APP_HEIGHT)

        self.playlist = [] 

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
        btn_rename = self.make_button(" Rename", "mdi.pencil", self.rename_item)
        btn_clear = self.make_button(" Clear list", "mdi.delete-outline", self.clearlist)
        btn_play = self.make_button(" Play", "mdi.play-circle", self.play_selected)
        btn_info = self.make_button(" Info", "mdi.information", self.info)
        btn_quit = self.make_button(" Quit", "mdi.exit-to-app", self.quit)

        controls.insertWidget(0, btn_search) # comment out if you don't want to toggle the search bar
        controls.addWidget(btn_open)
        controls.addWidget(btn_url)
        controls.addWidget(btn_rename)
        controls.addWidget(btn_clear)
        controls.addStretch()
        controls.addWidget(btn_play)
        controls.addWidget(btn_info)
        controls.addWidget(btn_quit)

        main.addLayout(controls)

    def make_button(self, text, icon_name, callback):
        btn = QPushButton(text)
        btn.setIcon(qta.icon(icon_name))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumWidth(140)
        btn.setIconSize(QSize(20, 20))
        btn.setStyleSheet("text-align: left; padding-left: 12px; font-size: 8pt; font-weight: normal; border-width: 1px;")
        btn.clicked.connect(callback)
        return btn

    # ---------- Playlist ----------
    def refresh_list(self):
        names = [name for name, _ in self.playlist]
        self.model.setStringList(names)

    def filter_changed(self, text):
        self.proxy.setFilterFixedString(text)

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
        self.proxy.setFilterFixedString("")
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
                        self.playlist.append([display, line])
                        name = None

            self.refresh_list()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# ---------- Load URL ---------
    def load_url(self):
        response = requests.get(M3U_URL)
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
                        self.playlist.append([display, line])
                        name = None

            self.refresh_list()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# ---------- Load URL ---------
    def clearlist(self):
        self.playlist.clear()
        self.refresh_list()


    # ---------- Info box ---------
    def info(self):
        ret = QMessageBox.about(self,"Info",INFO)

    # ---------- Quit -------------
    def quit(quit):
        sys.exit()

    # ---------- Renaming ---------
    def rename_item(self):
        index = self.list_view.currentIndex()
        if not index.isValid():
            return

        source_index = self.proxy.mapToSource(index)
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
                self.playlist = json.load(f)
            self.refresh_list()
        except Exception:
            pass

    def closeEvent(self, event):
        # Sync order from UI (important after drag & drop)
        new_order = []
        for i in range(self.list_view.count()):
            name = self.list_view.item(i).text().strip()
            for entry in self.playlist:
                if entry[0] == name:
                    new_order.append(entry)
                    break
        self.playlist = new_order

        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.playlist, f, indent=2)
        except Exception:
            pass

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

