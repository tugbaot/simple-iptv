#!/usr/bin/python
# Created: 02/02/2026 
# Simple IPTV thing
# github.com/tugbaot/simple-iptv
##################################
# TO DO
# why do some buttons retain focus for focus sake
##################################

import sys
import os
import json
import subprocess
import configparser
import requests
from time import sleep
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from fake_useragent import UserAgent
from pyxtream import XTream

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QFileDialog, QGridLayout,
    QVBoxLayout, QHBoxLayout, QInputDialog, QMessageBox,
    QLineEdit, QListView, QStyledItemDelegate, QAbstractItemView,
    QStatusBar, QStyle, QDialog, QLabel
)
from PySide6.QtCore import Qt, QSize, QSortFilterProxyModel, QRect, QEvent, QModelIndex, QAbstractListModel, QMimeData, QByteArray, QDataStream, QIODevice, QTimer
from PySide6.QtGui import QIcon, QPainter, QTextOption

from qt_material import apply_stylesheet
import qtawesome as qta

# ------- Use script path -----------------------
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# ------- Read config ---------------------------
config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
config.read('config.txt')

# ------- Configuration -------------------------
MPV_PATH         = config.get('config', 'mpv_path', fallback='mpv.exe') 
MPV_ARGS         = config.get('config', 'mpv_args', fallback='').strip().split()
STATE_FILE       = config.get('config', 'list_name', fallback='playlist_state.json')
APP_NAME         = config.get('config', 'app_name', fallback='Simple IPTV')
APP_ICON         = config.get('config', 'app_icon', fallback='mdi.television')
APP_ICON_COLOR   = config.get('config', 'app_icon_color', fallback='white')
PLAYLIST_ICON    = config.get('config', 'playlist_icon', fallback='mdi.television-guide')
APP_THEME        = config.get('config', 'app_theme', fallback='charcoal.xml')
APP_FONT         = config.get('config', 'app_font', fallback='Segoe UI')
APP_FONT_SIZE    = config.get('config', 'app_font_size', fallback='9pt')
FLAT             = config.getboolean('config', 'flat_buttons', fallback=False)
ROW_HEIGHT       = config.getint('config', 'row_height', fallback=38)
APP_HEIGHT       = config.getint('config', 'app_height', fallback=600)
APP_WIDTH        = config.getint('config', 'app_width', fallback=480)
FULLSCREEN       = config.getboolean('config', 'fullscreen', fallback=False)
MINIMISE         = config.getboolean('config', 'minimise', fallback=False)

# Star colors – loaded dynamically can be refreshed
STAR_COLOR = None
STAR_EMPTY_COLOR = None
def reload_star_colors():
    global STAR_COLOR, STAR_EMPTY_COLOR
    theme_key = APP_THEME.replace('.xml', '') if APP_THEME.endswith('.xml') else APP_THEME
    STAR_COLOR = config.get('themes', theme_key, fallback='#FFCA28')
    STAR_EMPTY_COLOR = config.get('config', 'star_empty_color', fallback='#757575')

reload_star_colors()  # Initial load

# ------- Xtream config -------------------------
IPTV_NAME        = config.get('xtream', 'IPTV_NAME')
IPTV_URL         = config.get('xtream', 'IPTV_URL')
IPTV_USER        = config.get('xtream', 'IPTV_USER')
IPTV_PASS        = config.get('xtream', 'IPTV_PASS')

# ------- Button style --------------------------
BUTTON_STYLE = (
    "text-align: left; padding-left: 4px; font-size: 8pt; "
    "font-weight: normal; border-width: 0.5px"
)

# ------- Info popup ----------------------------
INFO = """A simple, lightweight IPTV manager using mpv to play channels.

Features:
• Search channels
• Favourites (toggle view / star items)
• Open local M3U
• Load from URL (m3u or Xstream)
• Save m3u playlist (all or favourites only)
• Save json (playlist and favs)
• Drag to reorder
• Clear list
• Theme selection

Customize via config.txt and theme.xml

⛬ https://github.com/tugbaot/simple-iptv"""

# ------- Custom Model --------------------------
class PlaylistModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    UrlRole  = Qt.UserRole + 2
    FavRole  = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._playlist = []  # [name: str, url: str, favourite: bool]

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._playlist)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._playlist[index.row()]
        if role in (Qt.DisplayRole, self.NameRole):
            return item[0]
        if role == self.UrlRole:
            return item[1]
        if role == self.FavRole:
            return item[2]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        row = index.row()
        changed = False
        if role == self.FavRole:
            self._playlist[row][2] = bool(value)
            changed = True
        elif role == self.NameRole:
            self._playlist[row][0] = str(value).strip()
            changed = True
        if changed:
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def flags(self, index):
        default = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDropEnabled
        if index.isValid():
            default |= Qt.ItemIsDragEnabled | Qt.ItemIsEditable
        return default

    def supportedDragActions(self):
        return Qt.MoveAction

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ["application/x-qabstractitemmodeldatalist"]

    def mimeData(self, indexes):
        mime = QMimeData()
        encoded = QByteArray()
        stream = QDataStream(encoded, QIODevice.WriteOnly)

        rows = sorted(set(i.row() for i in indexes))
        stream.writeInt32(len(rows))
        for row in rows:
            stream.writeInt32(row)

        mime.setData("application/x-qabstractitemmodeldatalist", encoded)
        return mime

    def dropMimeData(self, data, action, row, column, parent):
        if action != Qt.MoveAction or not data.hasFormat("application/x-qabstractitemmodeldatalist"):
            return False

        if row == -1:
            if parent.isValid():
                row = parent.row()
            else:
                row = self.rowCount()

        encoded = data.data("application/x-qabstractitemmodeldatalist")
        stream = QDataStream(encoded, QIODevice.ReadOnly)
        count = stream.readInt32()
        source_rows = []
        for _ in range(count):
            source_rows.append(stream.readInt32())

        source_rows.sort(reverse=True)

        dest_row = row

        self.beginResetModel()  # safe for small-medium lists
        for src_row in source_rows:
            item = self._playlist.pop(src_row)
            if src_row < dest_row:
                dest_row -= 1
            self._playlist.insert(dest_row, item)
        self.endResetModel()

        return True

    def append_items(self, items):
        if not items:
            return
        first = len(self._playlist)
        last = first + len(items) - 1
        self.beginInsertRows(QModelIndex(), first, last)
        self._playlist.extend(items)
        self.endInsertRows()

    def clear(self):
        if not self._playlist:
            return
        self.beginRemoveRows(QModelIndex(), 0, len(self._playlist) - 1)
        self._playlist.clear()
        self.endRemoveRows()

    def get_playlist_copy(self):
        return [item[:] for item in self._playlist]

# ------- Custom Proxy for Favourites -----------
class FavouriteFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._show_only_favourites = False

    @property
    def show_only_favourites(self):
        return self._show_only_favourites

    @show_only_favourites.setter
    def show_only_favourites(self, value: bool):
        if value != self._show_only_favourites:
            self._show_only_favourites = value
            self.invalidate()

    def filterAcceptsRow(self, source_row, source_parent):

        if not super().filterAcceptsRow(source_row, source_parent):
            return False

        if not self._show_only_favourites:
            return True

        idx = self.sourceModel().index(source_row, 0, source_parent)
        return self.sourceModel().data(idx, PlaylistModel.FavRole) is True

# ------- Custom Delegate -----------------------
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

        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())

        icon_size = 20
        margin = 8

        icon_rect = QRect(rect.left() + margin,
                          rect.top() + (rect.height() - icon_size) // 2,
                          icon_size, icon_size)
        self.icon.paint(painter, icon_rect)

        star_rect = QRect(rect.right() - 30,
                          rect.top() + (rect.height() - icon_size) // 2,
                          icon_size, icon_size)
        fav = index.data(PlaylistModel.FavRole)
        (self.star_on if fav else self.star_off).paint(painter, star_rect)

        text_rect = QRect(icon_rect.right() + 8, rect.top() + 4,
                          rect.width() - 80, rect.height() - 8)
        text = index.data(Qt.DisplayRole) or ""
        search = self._get_search_text(index)

        painter.setClipRect(text_rect)

        if not search:
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.TextWordWrap, text)
        else:
            lower_text = text.lower()
            lower_search = search.lower()

            x = text_rect.left()
            y = text_rect.top()

            fm = painter.fontMetrics()

            i = 0
            while i < len(text):
                match_index = lower_text.find(lower_search, i)

                if match_index == -1:
                    chunk = text[i:]
                    painter.drawText(x, y + fm.ascent() + 2, chunk)
                    break

                before = text[i:match_index]
                painter.drawText(x, y + fm.ascent() + 2, before)
                x += fm.horizontalAdvance(before)

                match = text[match_index:match_index + len(search)]

                highlight_rect = QRect(
                    x,
                    y + 2,
                    fm.horizontalAdvance(match),
                    fm.height()
                )

                painter.fillRect(highlight_rect, option.palette.highlight())
                painter.setPen(option.palette.highlightedText().color())
                painter.drawText(x, y + fm.ascent() + 2, match)
                painter.setPen(option.palette.text().color())

                x += fm.horizontalAdvance(match)
                i = match_index + len(search)

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            star_rect = QRect(option.rect.right() - 30,
                              option.rect.top() + (option.rect.height() - 20) // 2,
                              20, 20)
            if star_rect.contains(event.pos()):
                fav = index.data(PlaylistModel.FavRole)
                model.setData(index, not fav, PlaylistModel.FavRole)
                return True
        return super().editorEvent(event, model, option, index)

    def _get_search_text(self, index):
        view = self.parent()
        if not view:
            return ""
        proxy = view.model()
        if not proxy:
            return ""
        return proxy.filterRegularExpression().pattern()

# ------- Main Window ---------------------------
class M3UPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(qta.icon(APP_ICON, color=APP_ICON_COLOR))
        self.resize(APP_WIDTH, APP_HEIGHT)
        if FULLSCREEN:
            self.showMaximized()

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.model = PlaylistModel()

        self.proxy_model = FavouriteFilterProxy()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterRole(PlaylistModel.NameRole)

        self.show_favourites = False

        self.init_ui()
        self.load_state()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QHBoxLayout(central)
        main.setContentsMargins(12, 12, 12, 12)

        left = QVBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search channels…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.proxy_model.setFilterFixedString)
        left.addWidget(self.search)

        self.list_view = QListView()
        self.list_view.setModel(self.proxy_model)
        self.list_view.doubleClicked.connect(self.play_selected)
        self.search.textChanged.connect(self.list_view.viewport().update)
        self.list_view.setDragDropMode(QListView.InternalMove)
        self.list_view.setDefaultDropAction(Qt.MoveAction)
        self.list_view.setDropIndicatorShown(True)
        self.list_view.setDragEnabled(True)
        self.list_view.setAcceptDrops(True)
        self.list_view.viewport().setAcceptDrops(True)
        self.list_view.setDragDropOverwriteMode(False)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_view.setItemDelegate(
            PlaylistDelegate(ROW_HEIGHT, qta.icon(PLAYLIST_ICON), self.list_view)
        )
        self.list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        left.addWidget(self.list_view, 1)
        main.addLayout(left, 1)

        controls = QVBoxLayout()
        controls.setSpacing(8)

        btn_search    = self.make_button(" Search", "mdi.magnify", self.toggle_search)
        self.btn_fav  = self.make_button(" Favourites", "mdi.star-outline", self.toggle_favourites)
        btn_open      = self.make_button(" Open M3U", "mdi.folder-open", self.open_m3u)
        btn_url       = self.make_button(" M3U URL", "mdi.link", self.load_m3u)
        btn_xtream    = self.make_button(" Xtreme", "mdi.television", self.get_xtream)
        btn_savem3u   = self.make_button(" Save M3U", "mdi.content-save-outline", self.save_m3u)
        btn_savejson  = self.make_button(" Save json", "mdi.code-json", self.save_json)
        btn_clear     = self.make_button(" Clear list", "mdi.delete-outline", self.clearlist)
        btn_theme     = self.make_button(" Theme", "mdi.palette-outline", self.theme)
        btn_info      = self.make_button(" Info", "mdi.information", self.show_info)
        btn_quit      = self.make_button(" Quit", "mdi.exit-to-app", self.close)
        
        controls.addWidget(btn_search)
        controls.addWidget(self.btn_fav)
        controls.addWidget(btn_open)
        controls.addWidget(btn_url)
        controls.addWidget(btn_xtream)
        controls.addWidget(btn_savem3u)
        controls.addWidget(btn_savejson)
        controls.addWidget(btn_clear)
        controls.addWidget(btn_theme)
        controls.addStretch()

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(4)

        btn_info.setMinimumWidth(40) 
        btn_info.setMaximumWidth(120)

        btn_quit.setMinimumWidth(40)
        btn_quit.setMaximumWidth(120)
        btn_quit.setIconSize(QSize(18, 18))
        bottom_row.addWidget(btn_info)
        bottom_row.addWidget(btn_quit)

        if FLAT:
            buttons = [btn_search, self.btn_fav, btn_open, btn_url, btn_xtream, btn_savem3u, btn_savejson, btn_clear, btn_theme, btn_info, btn_quit]
            for i, button in enumerate(buttons):
                button.setFlat(True)

        controls.addLayout(bottom_row)

        main.addLayout(controls)

    def make_button(self, text, icon_name, callback):
        btn = QPushButton(text)
        btn.setIcon(qta.icon(icon_name))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumWidth(140)
        btn.setIconSize(QSize(20, 20))
        btn.setStyleSheet(BUTTON_STYLE)
        def wrapped_callback(checked=False):
            callback()
            QTimer.singleShot(0, self.setFocus)  # or self.list_view.setFocus()

        btn.clicked.connect(wrapped_callback)
        return btn

    def toggle_favourites(self):
        self.show_favourites = not self.show_favourites
        self.proxy_model.show_only_favourites = self.show_favourites

        self.update_fav_button_icon()

        self.proxy_model.invalidate()

    def update_fav_button_icon(self):
        if self.show_favourites:
            self.btn_fav.setIcon(qta.icon("mdi.star", color=STAR_COLOR))
            self.btn_fav.setToolTip("Showing favourites only — click to show all")
        else:
            self.btn_fav.setIcon(qta.icon("mdi.star-outline", color=STAR_EMPTY_COLOR))
            self.btn_fav.setToolTip("Click to show favourites only")

    def toggle_search(self):
        if self.search.isVisible():
            self.search.clear()
            self.search.hide()
        else:
            self.search.show()
            self.search.setFocus()

    def update_star_icons(self):
        delegate = self.list_view.itemDelegate()
        if isinstance(delegate, PlaylistDelegate):
            delegate.star_on = qta.icon("mdi.star", color=STAR_COLOR)
            delegate.star_off = qta.icon("mdi.star-outline", color=STAR_EMPTY_COLOR)
            self.list_view.viewport().update()

    def _parse_m3u_content(self, lines: list[str]) -> list:
        playlist = []
        name = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#EXTM3U"):
                continue
            if line.startswith("#EXTINF"):
                name = line.split(",", 1)[-1].strip()
            else:
                display = name if name else os.path.basename(line or "Untitled")
                playlist.append([display, line, False])
                name = None
        return playlist

    def open_m3u(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open M3U", "", "M3U Files (*.m3u *.m3u8)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                items = self._parse_m3u_content(f.readlines())
            self.model.clear()
            self.model.append_items(items)
            self.statusBar.showMessage(f"Loaded {len(items)} channels from file", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        self.setFocus()

    def load_m3u(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Load M3U URL")
        dialog.setLabelText("Enter playlist URL:")
        dialog.setOkButtonText("Load")
        dialog.setCancelButtonText("Cancel")
        dialog.resize(400, 120)

        for btn in dialog.findChildren(QPushButton):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumWidth(100)
            btn.setIconSize(QSize(20, 20))
            btn.setStyleSheet(
                "text-align: left; padding-left: 12px; font-size: 8pt; "
                "font-weight: normal; border-width: 1px;"
            )

        if dialog.exec():
            url = dialog.textValue().strip()
        else:
            return

        try:
            self.statusBar.showMessage(f"Loading, please wait...", 4000)
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            items = self._parse_m3u_content(r.text.splitlines())
            self.model.clear()
            self.model.append_items(items)
            self.statusBar.showMessage(f"Loaded {len(items)} channels from URL", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load:\n{e}")
        self.setFocus()

    def get_xtream(self):
        global IPTV_NAME, IPTV_URL, IPTV_USER, IPTV_PASS

        msg = QMessageBox(self)
        msg.setWindowTitle("Load IPTV Xtream")
        msg.setText(f"This will remove all current channels and favs, and reload from your IPTV provider.\n\n"
                    f"Provider: {IPTV_NAME}\nURL: {IPTV_URL}\nUsername: {IPTV_USER}\nPassword: ************")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        for btn in msg.findChildren(QPushButton):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumWidth(100)
            btn.setIconSize(QSize(20, 20))
            btn.setStyleSheet(BUTTON_STYLE)
            if "Yes" in btn.text():
                btn.setIcon(qta.icon("mdi.check-circle-outline"))
            if "No" in btn.text():
                btn.setIcon(qta.icon("mdi.close-circle-outline"))
            if FLAT:
                btn.setFlat(True)

        reply = msg.exec()

        if reply == QMessageBox.Yes:
            try:
                self.statusBar.showMessage("Connecting to Xtream…", 3000)
                xt = XTream(IPTV_NAME, IPTV_USER, IPTV_PASS, IPTV_URL)
                xt.authenticate()

                if not xt.authorization:
                    QMessageBox.critical(self, "Xtream Error", "Login failed.")
                    return

                xt.load_iptv()
                items = []

                for ch in xt.channels:
                    try:
                        name = getattr(ch, "name", None)
                        stream_id = getattr(ch, "stream_id", None) or getattr(ch, "streamId", None) or getattr(ch, "id", None)
                        if not name or not stream_id:
                            continue
                        url = f"{IPTV_URL}/live/{IPTV_USER}/{IPTV_PASS}/{stream_id}.ts"
                        items.append([name, url, False])
                    except Exception as e:
                        print("Skipped:", e)

                if not items:
                    QMessageBox.warning(self, "Xtream", "No channels found.")
                    return

                self.model.clear()
                self.model.append_items(items)
                QMessageBox.information(self, "Complete", "Xtream channels loaded.")
            except Exception as e:
                QMessageBox.critical(self, "Xtream Error", str(e))
        self.setFocus()

    def save_m3u(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save playlist", "playlist.m3u", "M3U Files (*.m3u)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for item in self.model.get_playlist_copy():
                    name, url, _ = item
                    f.write(f"#EXTINF:-1,{name}\n{url}\n")
            self.statusBar.showMessage("Playlist saved", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save json file", "playlist.json", "json files (*.json)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "playlist": self.model.get_playlist_copy(),
                    "show_favourites": self.show_favourites,
                }, f, indent=2)
            self.statusBar.showMessage("json saved", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        self.setFocus()

    def clearlist(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Clear")
        msg.setText("Are you sure you want to clear the list?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)

        for btn in msg.findChildren(QPushButton):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumWidth(100)
            btn.setIconSize(QSize(20, 20))
            btn.setStyleSheet(BUTTON_STYLE)
            if "OK" in btn.text():
                btn.setIcon(qta.icon("mdi.check-circle-outline"))
            if "Cancel" in btn.text():
                btn.setIcon(qta.icon("mdi.close-circle-outline"))
            if FLAT:
                btn.setFlat(True)

        reply = msg.exec()

        if reply == QMessageBox.Ok:
            self.model.clear()
            self.statusBar.showMessage("List cleared", 3000)
        self.setFocus()

    def theme(self):
        global APP_THEME

        dialog = QDialog(self)
        dialog.setWindowTitle("Theme")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        current_without_ext = APP_THEME.replace('.xml', '') if APP_THEME.endswith('.xml') else APP_THEME
        layout.addWidget(QLabel(f"The current theme is <b>{current_without_ext}</b><br><br>Pick your poison: <br>"))

        grid = QGridLayout()

        theme_names = ["amaranth", "charcoal", "ebony", "granite", "grape", "gunmetal", "plum", "sapphire"]

        selected_theme = [None]

        def on_theme_selected(name):
            selected_theme[0] = name
            dialog.accept()

        for i, name in enumerate(theme_names):
            btn = QPushButton(name)
            btn.setMinimumSize(130, 48)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(qta.icon("mdi6.palette-outline"))
            btn.setStyleSheet(BUTTON_STYLE)

            if name == current_without_ext:
                btn.setAutoDefault(True)
                btn.setDefault(True)
                btn.setFocus()          # optional: give it initial keyboard focus too
            else:
                btn.setAutoDefault(False)
                btn.setDefault(False)

            btn.clicked.connect(lambda checked=False, n=name: on_theme_selected(n))
            grid.addWidget(btn, i // 4, i % 4)

        layout.addLayout(grid)

        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(BUTTON_STYLE)
        cancel.setIcon(qta.icon("mdi.close"))
        cancel.clicked.connect(dialog.reject)
        layout.addWidget(cancel, alignment=Qt.AlignRight)

        if dialog.exec() == QDialog.Accepted and selected_theme[0]:
            chosen_name = selected_theme[0]
            chosen = chosen_name + ".xml"

            apply_stylesheet(
                QApplication.instance(),
                theme=f"themes/{chosen}",
                extra={"font_family": APP_FONT, "font_size": APP_FONT_SIZE}
            )
            QApplication.instance().setStyle(QApplication.style())
            self.style().polish(self)

            APP_THEME = chosen

            reload_star_colors()
            self.update_star_icons()
            self.update_fav_button_icon()

            self.list_view.viewport().update()
            self.update()

            self.statusBar.showMessage(f"Theme changed to {chosen_name}", 8000)

            config.set('config', 'app_theme', chosen_name)
            with open('config.txt', 'w') as cfgfile:
                config.write(cfgfile)

        else:
            ""

        self.setFocus()

    def play_selected(self):
        idx = self.list_view.currentIndex()
        if not idx.isValid():
            return
        src_idx = self.proxy_model.mapToSource(idx)
        url = self.model.data(src_idx, PlaylistModel.UrlRole)
        try:
            if os.name == "nt":
                subprocess.Popen([MPV_PATH, *MPV_ARGS, url])
            else:
                subprocess.Popen(["mpv", *MPV_ARGS, url])
            if MINIMISE:
                sleep(5)
                self.showMinimized()
        except FileNotFoundError:
            QMessageBox.critical(self, "mpv not found", f"Check MPV_PATH\nCurrently: {MPV_PATH}")

    def show_info(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Info")
        msg.setText(INFO)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        for btn in msg.findChildren(QPushButton):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumWidth(100)
            btn.setIconSize(QSize(20, 20))
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setIcon(qta.icon("mdi.check-circle-outline"))
            if FLAT:
                btn.setFlat(True)
        msg.exec()

    def load_state(self):
        path = Path(STATE_FILE)
        if not path.exists():
            return
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                items = [[n, u, False] for n, u in data]
            else:
                items = data.get("playlist", [])
                self.show_favourites = data.get("show_favourites", False)
            self.model.append_items(items)
            self.proxy_model.show_only_favourites = self.show_favourites
            self.update_fav_button_icon()
            self.statusBar.showMessage(f"Restored {len(items)} channels", 4000)
        except Exception as e:
            print("State load failed:", e)

    def update_config(self):
        cfgfile = open('config.txt', 'w')
        config.set("config", "app_height", str(self.height()))
        config.set("config", "app_width", str(self.width()))
        config.write(cfgfile)
        cfgfile.close()  

    def closeEvent(self, event):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "playlist": self.model.get_playlist_copy(),
                    "show_favourites": self.show_favourites,
                }, f, indent=2)
        except Exception:
            pass

        self.update_config()
        super().closeEvent(event)

# ---------- Entry Point ------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(
        app,
        theme="themes/" + APP_THEME + ".xml",
        extra={"font_family": APP_FONT, "font_size": APP_FONT_SIZE}
    )
    window = M3UPlayer()
    window.show()
    sys.exit(app.exec())