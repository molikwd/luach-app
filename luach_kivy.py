"""
luach_kivy.py  —  Luach Android app (Kivy)
Reuses zmanim_core.py for all halachic time calculations.
Build: see colab_build.ipynb
"""
from __future__ import annotations
import os, json, datetime, calendar
from pathlib import Path

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.image import Image as KvImage
from kivy.metrics import dp, sp
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle

_HEBREW_FONT = "Roboto"

def _init_fonts():
    global _HEBREW_FONT
    p = resource_find("NotoSansHebrew.ttf")
    if p:
        try:
            LabelBase.register("NotoHebrew", fn_regular=p)
            _HEBREW_FONT = "NotoHebrew"
        except Exception:
            pass

try:
    from bidi.algorithm import get_display as _bidi
    def _hb(t: str) -> str:
        return _bidi(t) if t else t
except ImportError:
    def _hb(t: str) -> str:
        return t

import traceback as _tb
_IMPORT_ERROR: str | None = None
try:
    from zmanim_core import CITIES, compute_day, ZMAN_FIELDS
    from zmanim.hebrew_calendar.jewish_calendar import JewishCalendar
except Exception:
    _IMPORT_ERROR = _tb.format_exc()
    CITIES, ZMAN_FIELDS = {}, []          # type: ignore
    def compute_day(*a, **kw):            # type: ignore
        raise RuntimeError("import failed")
    class JewishCalendar:                 # type: ignore
        def __init__(self, *a): pass
        def significant_day(self): return None


# ── Global state ──────────────────────────────────────────────────────────
class _St:
    hebrew:   bool          = False
    city_key: str           = "lakewood"
    year:     int           = datetime.date.today().year
    month:    int           = datetime.date.today().month
    sel_date: datetime.date = datetime.date.today()

ST = _St()

# ── Constants ─────────────────────────────────────────────────────────────
WEEKDAYS_EN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Shab"]
WEEKDAYS_HE = ["א׳", "ב׳", "ג׳", "ד׳", "ה׳", "ו׳", "שבת"]

ZMAN_EN = [lbl for lbl, _ in ZMAN_FIELDS]
ZMAN_HE = [
    "עלות השחר", "נץ החמה", 'סו"ז ק"ש מג"א', 'סו"ז ק"ש גר"א',
    'סו"ז תפילה מג"א', 'סו"ז תפילה גר"א', "חצות", "מנחה גדולה",
    "מנחה קטנה", "פלג המנחה", "שקיעה", "צאת הכוכבים", 'צאת 72 / ר"ת',
]

C_HEADER  = (0.172, 0.243, 0.478, 1)
C_SUBHDR  = (0.90,  0.91,  0.97,  1)
C_PANEL   = (0.95,  0.96,  1.00,  1)
C_SHAB    = (0.91,  0.94,  0.99,  1)
C_YOMTOV  = (1.00,  0.98,  0.90,  1)
C_ROSHCH  = (0.93,  0.98,  0.93,  1)
C_TODAY   = (1.00,  0.88,  0.20,  1)
C_SEL     = (0.70,  0.82,  1.00,  1)
C_WHITE   = (1.00,  1.00,  1.00,  1)
C_ROW_A   = (0.96,  0.97,  1.00,  1)
C_ROW_B   = (1.00,  1.00,  1.00,  1)
C_SHAB_B  = (0.88,  0.92,  1.00,  1)
C_NOTES   = (0.97,  0.97,  0.97,  1)


def _fmt(dt) -> str:
    if not dt:
        return "—"
    return dt.strftime("%I:%M %p").lstrip("0") or dt.strftime("%I:%M %p")


def _cell_color(date: datetime.date) -> tuple:
    if date == datetime.date.today():
        return C_TODAY
    if date.weekday() == 5:  # Saturday
        return C_SHAB
    try:
        sig = JewishCalendar(date).significant_day()
        if sig:
            return C_ROSHCH if sig == "rosh_chodesh" else C_YOMTOV
    except Exception:
        pass
    return C_WHITE


def _bg(widget, color):
    with widget.canvas.before:
        c = Color(*color)
        r = Rectangle(pos=widget.pos, size=widget.size)
    def _upd(*_):
        r.pos = widget.pos
        r.size = widget.size
    widget.bind(pos=_upd, size=_upd)


# ── Notes ─────────────────────────────────────────────────────────────────
_notes: dict[str, str] = {}
_notes_file: Path | None = None


def _notes_load():
    global _notes, _notes_file
    app = App.get_running_app()
    base = Path(app.user_data_dir) if app else Path(os.path.expanduser("~")) / ".luach"
    base.mkdir(parents=True, exist_ok=True)
    _notes_file = base / "notes.json"
    if _notes_file.exists():
        try:
            _notes = json.loads(_notes_file.read_text("utf-8"))
        except Exception:
            _notes = {}


def _notes_save():
    if _notes_file:
        _notes_file.write_text(
            json.dumps(_notes, ensure_ascii=False, indent=2), "utf-8"
        )


# ══════════════════════════════════════════════════════════════════════════
# MONTH SCREEN
# ══════════════════════════════════════════════════════════════════════════
class MonthScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._cells: list[tuple[datetime.date, Button]] = []
        self._sel_btn: Button | None = None
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        _bg(root, C_WHITE)

        # Nav bar
        nav = BoxLayout(size_hint_y=None, height=dp(50),
                        padding=[dp(4)] * 4, spacing=dp(4))
        _bg(nav, C_HEADER)

        # Logo (left side)
        logo_src = resource_find("logo.png")
        if logo_src:
            logo_w = KvImage(source=logo_src, size_hint=(None, 1), width=dp(56),
                             allow_stretch=True, keep_ratio=True)
            nav.add_widget(logo_w)

        self._heb_btn = Button(
            text="עב", size_hint=(None, 1), width=dp(46),
            font_size=sp(15), font_name=_HEBREW_FONT,
            background_normal="",
            background_color=(0.28, 0.38, 0.68, 1), color=(1, 1, 1, 1),
        )
        self._heb_btn.bind(on_press=self._toggle_heb)

        btn_prev = Button(
            text="<", size_hint=(None, 1), width=dp(42),
            font_size=sp(16), background_normal="",
            background_color=(0.28, 0.38, 0.68, 1), color=(1, 1, 1, 1),
        )
        btn_prev.bind(on_press=lambda *_: self._shift_month(-1))

        self._month_lbl = Label(text="", font_size=sp(15), bold=True, color=(1, 1, 1, 1))

        btn_next = Button(
            text=">", size_hint=(None, 1), width=dp(42),
            font_size=sp(16), background_normal="",
            background_color=(0.28, 0.38, 0.68, 1), color=(1, 1, 1, 1),
        )
        btn_next.bind(on_press=lambda *_: self._shift_month(1))

        for w in (self._heb_btn, btn_prev, self._month_lbl, btn_next):
            nav.add_widget(w)
        root.add_widget(nav)

        # City spinner
        city_bar = BoxLayout(size_hint_y=None, height=dp(42),
                             padding=[dp(6), dp(4), dp(6), dp(4)])
        _bg(city_bar, C_SUBHDR)
        self._city_sp = Spinner(
            text=CITIES[ST.city_key].name,
            values=[c.name for c in CITIES.values()],
            font_size=sp(13),
            background_normal="", background_down="",
            background_color=(1, 1, 1, 1), color=(0.1, 0.1, 0.4, 1),
        )
        self._city_sp.bind(text=self._on_city)
        city_bar.add_widget(self._city_sp)
        root.add_widget(city_bar)

        # Weekday headers
        self._hdr_grid = GridLayout(cols=7, size_hint_y=None, height=dp(28))
        _bg(self._hdr_grid, (0.85, 0.88, 0.96, 1))
        self._hdr_lbls: list[Label] = []
        for day in WEEKDAYS_EN:
            lbl = Label(text=day, font_size=sp(11), bold=True, color=(0.2, 0.2, 0.5, 1))
            self._hdr_lbls.append(lbl)
            self._hdr_grid.add_widget(lbl)
        root.add_widget(self._hdr_grid)

        # Calendar grid
        self._grid = GridLayout(cols=7, size_hint_y=1, spacing=1)
        _bg(self._grid, (0.72, 0.72, 0.78, 1))
        root.add_widget(self._grid)

        # Day info panel
        panel = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(120),
                          padding=[dp(8), dp(4), dp(8), dp(4)], spacing=dp(2))
        _bg(panel, C_PANEL)

        self._p_date  = Label(text="", font_size=sp(13), bold=True,
                               color=(0.1, 0.1, 0.4, 1), halign="left",
                               size_hint_x=1, text_size=(None, None))
        self._p_hdate = Label(text="", font_size=sp(11), color=(0.3, 0.3, 0.6, 1),
                               font_name=_HEBREW_FONT,
                               halign="left", size_hint_x=1, text_size=(None, None))
        self._p_times = Label(text="", font_size=sp(11), color=(0.15, 0.15, 0.15, 1),
                               halign="left", size_hint_x=1, text_size=(None, None))
        self._p_daf   = Label(text="", font_size=sp(11), color=(0.25, 0.12, 0.0, 1),
                               font_name=_HEBREW_FONT,
                               halign="left", size_hint_x=1, text_size=(None, None))

        btn_row = BoxLayout(size_hint_y=None, height=dp(32))
        btn_row.add_widget(Widget())
        detail_btn = Button(
            text="Details ▶", size_hint=(None, 1), width=dp(100),
            font_size=sp(12), background_normal="",
            background_color=C_HEADER, color=(1, 1, 1, 1),
        )
        detail_btn.bind(on_press=self._go_day)
        btn_row.add_widget(detail_btn)

        for w in (self._p_date, self._p_hdate, self._p_times, self._p_daf, btn_row):
            panel.add_widget(w)
        root.add_widget(panel)

        self.add_widget(root)

    def on_enter(self):
        self._render()

    def _render(self):
        d = datetime.date(ST.year, ST.month, 1)
        self._month_lbl.text = d.strftime("%B %Y")
        self._heb_btn.text = "EN" if ST.hebrew else "עב"
        self._heb_btn.font_name = _HEBREW_FONT
        days = WEEKDAYS_HE if ST.hebrew else WEEKDAYS_EN
        for lbl, day in zip(self._hdr_lbls, days):
            lbl.text = _hb(day) if ST.hebrew else day
            lbl.font_name = _HEBREW_FONT if ST.hebrew else "Roboto"
        self._build_grid()
        self._update_panel()

    def _build_grid(self):
        self._grid.clear_widgets()
        self._cells.clear()
        self._sel_btn = None

        first = datetime.date(ST.year, ST.month, 1)
        start_col = (first.weekday() + 1) % 7  # Sun=0 in our grid
        for _ in range(start_col):
            self._grid.add_widget(Widget())

        _, n = calendar.monthrange(ST.year, ST.month)
        for day in range(1, n + 1):
            d = datetime.date(ST.year, ST.month, day)
            base = _cell_color(d)
            has_note = bool(_notes.get(str(d)))

            cell = Button(
                text=str(day) + (" *" if has_note else ""),
                font_size=sp(12),
                background_normal="",
                background_color=C_SEL if d == ST.sel_date else base,
                color=(0.1, 0.1, 0.1, 1),
                halign="center",
            )
            cell._date = d        # type: ignore
            cell._base = base     # type: ignore
            cell.bind(on_press=self._tap)
            if d == ST.sel_date:
                self._sel_btn = cell
            self._cells.append((d, cell))
            self._grid.add_widget(cell)

    def _tap(self, cell):
        if self._sel_btn and self._sel_btn is not cell:
            self._sel_btn.background_color = self._sel_btn._base  # type: ignore
        cell.background_color = C_SEL
        self._sel_btn = cell
        ST.sel_date = cell._date  # type: ignore
        self._update_panel()

    def _update_panel(self):
        d = ST.sel_date
        try:
            dz = compute_day(ST.city_key, d)
        except Exception as e:
            self._p_date.text = f"{d} — error"
            return

        self._p_date.text = f"{d.strftime('%A, %B')} {d.day}, {d.year}"

        hd = _hb(dz.hebrew_date) if ST.hebrew else dz.hebrew_date
        sig = dz.significant_day or ""
        self._p_hdate.text = hd + (f"  • {sig}" if sig else "")

        tf = dz.formatted()
        sr = tf.get("Netz (Sunrise)", "—")
        ss = tf.get("Shkiah (Sunset)", "—")
        self._p_times.text = f"Netz: {sr}  •  Shkiah: {ss}"

        parts = []
        parsha = dz.parsha_he if ST.hebrew else dz.parsha_en
        if parsha:
            parts.append(("פרשת " if ST.hebrew else "Parshas ") +
                         (_hb(parsha) if ST.hebrew else parsha))
        parts.append(_hb(dz.daf_he) if ST.hebrew else dz.daf_en)
        self._p_daf.text = "  •  ".join(parts)

    def _toggle_heb(self, *_):
        ST.hebrew = not ST.hebrew
        self._render()

    def _shift_month(self, delta: int):
        m, y = ST.month + delta, ST.year
        while m > 12: m -= 12; y += 1
        while m < 1:  m += 12; y -= 1
        ST.month, ST.year = m, y
        self._render()

    def _on_city(self, _sp, value):
        for k, c in CITIES.items():
            if c.name == value:
                ST.city_key = k
                break
        self._update_panel()

    def _go_day(self, *_):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.get_screen("day").load(ST.sel_date)
        self.manager.current = "day"


# ══════════════════════════════════════════════════════════════════════════
# DAY SCREEN
# ══════════════════════════════════════════════════════════════════════════
class DayScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._date = datetime.date.today()
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        _bg(root, C_WHITE)

        # Nav bar
        nav = BoxLayout(size_hint_y=None, height=dp(50),
                        padding=[dp(4)] * 4, spacing=dp(4))
        _bg(nav, C_HEADER)

        btn_back = Button(
            text="< Back", size_hint=(None, 1), width=dp(80),
            font_size=sp(13), background_normal="",
            background_color=(0.28, 0.38, 0.68, 1), color=(1, 1, 1, 1),
        )
        btn_back.bind(on_press=self._go_back)

        self._date_lbl = Label(text="", font_size=sp(13), bold=True, color=(1, 1, 1, 1))

        btn_p = Button(text="<", size_hint=(None, 1), width=dp(40),
                       font_size=sp(14), background_normal="",
                       background_color=(0.28, 0.38, 0.68, 1), color=(1, 1, 1, 1))
        btn_p.bind(on_press=lambda *_: self._shift(-1))
        btn_n = Button(text=">", size_hint=(None, 1), width=dp(40),
                       font_size=sp(14), background_normal="",
                       background_color=(0.28, 0.38, 0.68, 1), color=(1, 1, 1, 1))
        btn_n.bind(on_press=lambda *_: self._shift(1))

        for w in (btn_back, self._date_lbl, btn_p, btn_n):
            nav.add_widget(w)
        root.add_widget(nav)

        # Hebrew date bar
        hdate_bar = BoxLayout(size_hint_y=None, height=dp(30),
                              padding=[dp(8), dp(2), dp(8), dp(2)])
        _bg(hdate_bar, C_SUBHDR)
        self._hdate_lbl = Label(text="", font_size=sp(12), color=(0.3, 0.3, 0.6, 1),
                                font_name=_HEBREW_FONT)
        hdate_bar.add_widget(self._hdate_lbl)
        root.add_widget(hdate_bar)

        # Shabbos bar (shown Fri/Sat only)
        self._shab_bar = BoxLayout(size_hint_y=None, height=0,
                                    padding=[dp(8), dp(2), dp(8), dp(2)])
        _bg(self._shab_bar, C_SHAB_B)
        self._shab_lbl = Label(text="", font_size=sp(12), bold=True,
                                color=(0.2, 0.2, 0.6, 1))
        self._shab_bar.add_widget(self._shab_lbl)
        root.add_widget(self._shab_bar)

        # Parsha / Daf bar
        pd_bar = BoxLayout(size_hint_y=None, height=dp(28),
                           padding=[dp(8), dp(2), dp(8), dp(2)])
        _bg(pd_bar, (1.0, 0.98, 0.90, 1))
        self._pd_lbl = Label(text="", font_size=sp(11), color=(0.25, 0.12, 0.0, 1),
                             font_name=_HEBREW_FONT)
        pd_bar.add_widget(self._pd_lbl)
        root.add_widget(pd_bar)

        # Zmanim scrollable list
        scroll = ScrollView(size_hint=(1, 1))
        self._zman_layout = GridLayout(cols=2, size_hint_y=None, spacing=1,
                                        padding=[2, 2, 2, 2])
        self._zman_layout.bind(minimum_height=self._zman_layout.setter("height"))
        scroll.add_widget(self._zman_layout)
        root.add_widget(scroll)

        # Notes
        notes_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(120),
                              padding=[dp(8), dp(4), dp(8), dp(4)], spacing=dp(4))
        _bg(notes_box, C_NOTES)

        hdr = BoxLayout(size_hint_y=None, height=dp(28))
        hdr.add_widget(Label(text="Notes:", font_size=sp(12), bold=True,
                             color=(0.2, 0.2, 0.2, 1), halign="left",
                             size_hint_x=1, text_size=(None, None)))
        save_btn = Button(
            text="Save", size_hint=(None, 1), width=dp(60),
            font_size=sp(11), background_normal="",
            background_color=C_HEADER, color=(1, 1, 1, 1),
        )
        save_btn.bind(on_press=self._save_note)
        hdr.add_widget(save_btn)

        self._note_in = TextInput(
            hint_text="Add a note for this date...",
            font_size=sp(12), multiline=True, size_hint_y=1,
        )
        notes_box.add_widget(hdr)
        notes_box.add_widget(self._note_in)
        root.add_widget(notes_box)

        self.add_widget(root)

    def load(self, date: datetime.date):
        self._date = date
        self._render()

    def _render(self):
        d = self._date
        try:
            dz = compute_day(ST.city_key, d)
        except Exception as e:
            self._date_lbl.text = f"Error: {e}"
            return

        self._date_lbl.text = f"{d.strftime('%b')} {d.day}, {d.year}"

        hd = _hb(dz.hebrew_date) if ST.hebrew else dz.hebrew_date
        sig = dz.significant_day or ""
        self._hdate_lbl.text = hd + (f"  • {sig}" if sig else "")

        tf = dz.formatted()
        dow = d.weekday()  # 0=Mon..6=Sun; 4=Fri, 5=Sat
        if dow == 4 and dz.candle_lighting:
            self._shab_lbl.text = f"  Candle Lighting: {_fmt(dz.candle_lighting)}"
            self._shab_bar.height = dp(34)
        elif dow == 5:
            hav = tf.get("Tzeis Hakochavim", "—")
            rt  = tf.get("Tzeis 72 / R'T", "—")
            self._shab_lbl.text = f"  Havdalah: {hav}  •  Rabbeinu Tam: {rt}"
            self._shab_bar.height = dp(34)
        else:
            self._shab_lbl.text = ""
            self._shab_bar.height = 0

        parts = []
        parsha = dz.parsha_he if ST.hebrew else dz.parsha_en
        if parsha:
            pref = "פרשת " if ST.hebrew else "Parshas "
            parts.append(pref + (_hb(parsha) if ST.hebrew else parsha))
        parts.append(_hb(dz.daf_he) if ST.hebrew else dz.daf_en)
        self._pd_lbl.text = "  •  ".join(parts)

        self._zman_layout.clear_widgets()
        for i, (en, he) in enumerate(zip(ZMAN_EN, ZMAN_HE)):
            lbl_txt  = _hb(he) if ST.hebrew else en
            time_txt = tf.get(en, "—")
            bg = C_ROW_A if i % 2 == 0 else C_ROW_B

            lw = Button(text=lbl_txt, font_size=sp(11),
                        font_name=_HEBREW_FONT if ST.hebrew else "Roboto",
                        background_normal="", background_color=bg,
                        color=(0.2, 0.2, 0.4, 1),
                        size_hint_y=None, height=dp(36),
                        halign="left", text_size=(None, dp(36)),
                        valign="center", padding_x=dp(8))
            tw = Button(text=time_txt, font_size=sp(12), bold=True,
                        background_normal="", background_color=bg,
                        color=(0.0, 0.35, 0.1, 1),
                        size_hint_y=None, height=dp(36),
                        halign="right", text_size=(None, dp(36)),
                        valign="center", padding_x=dp(8))
            self._zman_layout.add_widget(lw)
            self._zman_layout.add_widget(tw)

        self._note_in.text = _notes.get(str(d), "")

    def _save_note(self, *_):
        text = self._note_in.text.strip()
        if text:
            _notes[str(self._date)] = text
        else:
            _notes.pop(str(self._date), None)
        _notes_save()

    def _shift(self, delta: int):
        self._date += datetime.timedelta(days=delta)
        self._render()

    def _go_back(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        ST.month = self._date.month
        ST.year  = self._date.year
        self.manager.get_screen("month")._render()
        self.manager.current = "month"


# ── App ───────────────────────────────────────────────────────────────────
def _err_screen(msg: str):
    sv = ScrollView()
    lbl = Label(text=msg, font_size=sp(9), halign="left", valign="top",
                size_hint_y=None, text_size=(Window.width, None))
    lbl.bind(texture_size=lambda w, s: setattr(w, "height", s[1]))
    sv.add_widget(lbl)
    return sv


class LuachApp(App):
    def build(self):
        if _IMPORT_ERROR:
            return _err_screen("IMPORT ERROR:\n" + _IMPORT_ERROR)
        try:
            _init_fonts()
            Window.clearcolor = C_WHITE
            _notes_load()
            sm = ScreenManager()
            sm.add_widget(MonthScreen(name="month"))
            sm.add_widget(DayScreen(name="day"))
            return sm
        except Exception:
            return _err_screen("BUILD ERROR:\n" + _tb.format_exc())

    def on_pause(self):
        return True   # keep alive when Android home-buttons

    def on_resume(self):
        pass


if __name__ == "__main__":
    LuachApp().run()
