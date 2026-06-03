"""
luach_app.py  —  Hebrew-English Jewish Calendar with Zmanim (tkinter GUI)
"""
from __future__ import annotations
import calendar
import datetime
import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from zmanim_core import compute_day, CITIES, ZMAN_FIELDS
from zmanim.hebrew_calendar.jewish_calendar import JewishCalendar

# ── Persistence ───────────────────────────────────────────────────────────
_APP_DIR   = Path(os.environ.get("APPDATA", Path.home())) / "Luach"
NOTES_FILE = _APP_DIR / "notes.json"


def _load_notes() -> dict[str, str]:
    try:
        _APP_DIR.mkdir(parents=True, exist_ok=True)
        if NOTES_FILE.exists():
            return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_notes(notes: dict[str, str]) -> None:
    try:
        _APP_DIR.mkdir(parents=True, exist_ok=True)
        NOTES_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ── Colors ────────────────────────────────────────────────────────────────
BG        = "#FFFFFF"
BG2       = "#F4F4F4"
BG3       = "#E5E5E5"
NAVY      = "#1C3A6E"
NAVY2     = "#2B5EAF"
GOLD      = "#B8860B"
RED       = "#B00000"
ORANGE    = "#C84B00"   # note dot + candle
GREEN     = "#1A6E2E"   # havdalah

TODAY_BG  = "#C8E6C9"
SEL_BG    = "#1C3A6E"
SEL_FG    = "#FFFFFF"
SHAB_BG   = "#EAF0FF"
YOMTOV_BG = "#FFFBEA"
RCHOD_BG  = "#F0F8FF"

TEXT      = "#1A1A1A"
MUTED     = "#666666"
BORDER    = "#D0D0D0"

# ── Fonts ─────────────────────────────────────────────────────────────────
F  = lambda s, b=False: ("Segoe UI", s, "bold" if b else "")
FH = lambda s, b=False: ("Arial",    s, "bold" if b else "")

# ── Calendar data ─────────────────────────────────────────────────────────
ENG_MONTHS = ["","January","February","March","April","May","June",
              "July","August","September","October","November","December"]
HEB_MONTHS = {
    1:"ניסן", 2:"אייר", 3:"סיון", 4:"תמוז", 5:"אב", 6:"אלול",
    7:"תשרי", 8:"חשון", 9:"כסלו", 10:"טבת", 11:"שבט", 12:"אדר", 13:"אדר ב׳",
}
HEB_NUMS = {
    1:"א", 2:"ב", 3:"ג", 4:"ד", 5:"ה", 6:"ו", 7:"ז", 8:"ח", 9:"ט",
    10:"י", 11:"יא", 12:"יב", 13:"יג", 14:"יד", 15:"טו", 16:"טז",
    17:"יז", 18:"יח", 19:"יט", 20:"כ", 21:"כא", 22:"כב", 23:"כג",
    24:"כד", 25:"כה", 26:"כו", 27:"כז", 28:"כח", 29:"כט", 30:"ל",
}
SIG_NAMES = {
    "rosh_hashana":"Rosh Hashana", "erev_rosh_hashana":"Erev Rosh Hashana",
    "yom_kippur":"Yom Kippur", "erev_yom_kippur":"Erev Yom Kippur",
    "succos":"Succos", "erev_succos":"Erev Succos",
    "chol_hamoed_sukkos":"Chol HaMoed Sukkos", "hoshana_rabbah":"Hoshana Rabbah",
    "shmini_atzeres":"Shmini Atzeres", "simchas_torah":"Simchas Torah",
    "chanukah":"Chanukah", "taanis_esther":"Taanis Esther",
    "purim":"Purim", "shushan_purim":"Shushan Purim",
    "erev_pesach":"Erev Pesach", "pesach":"Pesach",
    "chol_hamoed_pesach":"Chol HaMoed Pesach", "pesach_sheni":"Pesach Sheni",
    "lag_baomer":"Lag BaOmer", "shavuos":"Shavuos", "erev_shavuos":"Erev Shavuos",
    "tzom_gedaliah":"Tzom Gedaliah", "asara_betevet":"Asara BeTeives",
    "taanis_bechoros":"Taanis Bechoros", "yom_haatzmaut":"Yom Ha'atzmaut",
    "yom_yerushalayim":"Yom Yerushalayim", "tisha_beav":"Tisha B'Av",
    "shiva_asar_betamuz":"17 Tamuz", "rosh_chodesh":"Rosh Chodesh",
}
FULL_YOMTOV = {
    "rosh_hashana","yom_kippur","succos","shmini_atzeres","simchas_torah",
    "pesach","shavuos",
}
EREV_SHABBAT_OR_YT = {"erev_rosh_hashana","erev_yom_kippur","erev_succos",
                       "erev_pesach","erev_shavuos"}

WEEKDAYS_EN = ["Sun","Mon","Tue","Wed","Thu","Fri","Shab"]
WEEKDAYS_HE = ["א׳", "ב׳", "ג׳", "ד׳", "ה׳", "ו׳", "שבת"]

ZMAN_LABELS_EN = [
    "Alos Hashachar", "Netz (Sunrise)",
    "Sof Zman Shma MGA",   "Sof Zman Shma GRA",
    "Sof Zman Tefilla MGA","Sof Zman Tefilla GRA",
    "Chatzos",             "Mincha Gedola",
    "Mincha Ketana",       "Plag HaMincha",
    "Shkiah (Sunset)",     "Tzeis Hakochavim",
    "Tzeis 72 / R'T",
]
ZMAN_LABELS_HE = [
    'עלות השחר (72)',    'נץ החמה',
    'סו"ז ק"ש מג"א',    'סו"ז ק"ש גר"א',
    'סו"ז תפלה מג"א',   'סו"ז תפלה גר"א',
    'חצות',             'מנחה גדולה',
    'מנחה קטנה',        'פלג המנחה',
    'שקיעה',            'צאת הכוכבים',
    'צאת 72 / ר"ת',
]


def _fmt_date(d: datetime.date) -> str:
    return f"{d.strftime('%A, %B')} {d.day}, {d.year}"


def _heb_month_name(jc: JewishCalendar) -> str:
    m = jc.jewish_month
    name = HEB_MONTHS.get(m, "")
    if m == 12 and jc.is_jewish_leap_year():
        name = "אדר א׳"
    return name


def _is_friday(d: datetime.date) -> bool:
    return d.weekday() == 4

def _is_shabbos(d: datetime.date) -> bool:
    return d.weekday() == 5


class LuachApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Jewish Calendar / לוח יהודי")
        self.root.configure(bg=BG)
        self.root.minsize(940, 620)

        self.today         = datetime.date.today()
        self.selected_date = self.today
        self.current_month = self.today.replace(day=1)
        self.view          = "month"
        self._cache: dict  = {}
        self._notes        = _load_notes()
        self._heb_mode     = False

        self._city_keys  = list(CITIES.keys())
        self._city_names = [c.name for c in CITIES.values()]

        self._build_topbar()
        self._content = tk.Frame(self.root, bg=BG)
        self._content.pack(fill=tk.BOTH, expand=True)
        self._build_month_frame()
        self._build_day_frame()
        self._switch_view("month")

    # ── Top bar ───────────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=NAVY, padx=10, pady=7)
        bar.pack(fill=tk.X)

        tk.Label(bar, text="Jewish Calendar  |  לוח יהודי",
                 bg=NAVY, fg="white", font=F(13, True)).pack(side=tk.LEFT)

        right = tk.Frame(bar, bg=NAVY)
        right.pack(side=tk.RIGHT)
        tk.Label(right, text="City:", bg=NAVY, fg="white", font=F(10)).pack(side=tk.LEFT, padx=(0,4))
        self._city_combo = ttk.Combobox(right, values=self._city_names,
                                        width=18, font=F(10), state="readonly")
        self._city_combo.current(0)
        self._city_combo.bind("<<ComboboxSelected>>", self._on_city)
        self._city_combo.pack(side=tk.LEFT)

        mid = tk.Frame(bar, bg=NAVY)
        mid.pack(side=tk.LEFT, padx=24)

        self._btn_month = tk.Button(mid, text="Month", width=7, font=F(10),
                                    relief=tk.FLAT, cursor="hand2",
                                    command=lambda: self._switch_view("month"))
        self._btn_month.pack(side=tk.LEFT, padx=2)

        self._btn_day = tk.Button(mid, text="Day", width=7, font=F(10),
                                  relief=tk.FLAT, cursor="hand2",
                                  command=lambda: self._switch_view("day"))
        self._btn_day.pack(side=tk.LEFT, padx=2)

        tk.Frame(mid, bg="#5577AA", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        self._btn_lang = tk.Button(mid, text="עב", width=4, font=FH(10, True),
                                   relief=tk.FLAT, cursor="hand2",
                                   bg=NAVY2, fg="white",
                                   command=self._toggle_lang)
        self._btn_lang.pack(side=tk.LEFT, padx=2)

    # ── Month view ────────────────────────────────────────────────────────
    def _build_month_frame(self):
        self._mf = tk.Frame(self._content, bg=BG)

        nav = tk.Frame(self._mf, bg=BG2, pady=5)
        nav.pack(fill=tk.X)
        tk.Button(nav, text="◀", font=F(11, True), bg=BG2, relief=tk.FLAT,
                  cursor="hand2", command=self._prev_month).pack(side=tk.LEFT, padx=10)
        self._month_lbl = tk.Label(nav, text="", bg=BG2, font=F(12, True), fg=NAVY)
        self._month_lbl.pack(side=tk.LEFT, expand=True)
        tk.Button(nav, text="▶", font=F(11, True), bg=BG2, relief=tk.FLAT,
                  cursor="hand2", command=self._next_month).pack(side=tk.RIGHT, padx=10)
        tk.Button(nav, text="Today", font=F(10), bg=NAVY2, fg="white",
                  relief=tk.FLAT, cursor="hand2", padx=8,
                  command=self._go_today).pack(side=tk.RIGHT, padx=4)

        body = tk.Frame(self._mf, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        self._cal_frame = tk.Frame(body, bg=BG)
        self._cal_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Frame(body, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        self._zm_panel = tk.Frame(body, bg=BG2, width=258)
        self._zm_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self._zm_panel.pack_propagate(False)
        self._build_zmanim_panel()

    def _build_zmanim_panel(self):
        p = self._zm_panel

        # Date / Hebrew date
        self._zm_date_lbl = tk.Label(p, text="", bg=NAVY, fg="white",
                                     font=F(9, True), pady=5, padx=6,
                                     anchor="center", wraplength=248)
        self._zm_date_lbl.pack(fill=tk.X)
        self._zm_heb_lbl = tk.Label(p, text="", bg=NAVY, fg="#D4AF37",
                                    font=FH(11, True), pady=2, anchor="center")
        self._zm_heb_lbl.pack(fill=tk.X)
        self._zm_sig_lbl = tk.Label(p, text="", bg="#FFF3CD", fg="#856404",
                                    font=F(8, True), pady=2, anchor="center")

        # Parsha + Daf row
        info_f = tk.Frame(p, bg=BG3)
        info_f.pack(fill=tk.X)
        self._zm_parsha_lbl = tk.Label(info_f, text="", bg=BG3, fg=NAVY,
                                       font=F(8), padx=6, pady=2, anchor="w",
                                       wraplength=248)
        self._zm_parsha_lbl.pack(fill=tk.X)
        self._zm_daf_lbl = tk.Label(info_f, text="", bg=BG3, fg=MUTED,
                                    font=F(8), padx=6, pady=1, anchor="w")
        self._zm_daf_lbl.pack(fill=tk.X)

        # Shabbos/Candle lighting bar (hidden by default)
        self._zm_shab_bar = tk.Frame(p, bg="#E3F2FD")
        self._zm_candle_lbl  = tk.Label(self._zm_shab_bar, text="", bg="#E3F2FD",
                                        fg=ORANGE, font=F(8, True), padx=6, pady=2, anchor="w")
        self._zm_candle_lbl.pack(fill=tk.X)
        self._zm_havdala_lbl = tk.Label(self._zm_shab_bar, text="", bg="#E3F2FD",
                                        fg=GREEN, font=F(8, True), padx=6, pady=2, anchor="w")
        self._zm_havdala_lbl.pack(fill=tk.X)
        self._zm_rt_lbl      = tk.Label(self._zm_shab_bar, text="", bg="#E3F2FD",
                                        fg=GREEN, font=F(8, True), padx=6, pady=2, anchor="w")
        self._zm_rt_lbl.pack(fill=tk.X)

        # Zmanim rows
        scroll_f = tk.Frame(p, bg=BG2)
        scroll_f.pack(fill=tk.BOTH, expand=True, pady=1)
        self._zm_rows: list[tuple[tk.Label, tk.Label]] = []
        for i in range(len(ZMAN_FIELDS)):
            rb = BG if i % 2 == 0 else BG2
            row = tk.Frame(scroll_f, bg=rb)
            row.pack(fill=tk.X)
            lbl = tk.Label(row, text="", bg=rb, fg=TEXT, font=F(8),
                           anchor="w", padx=5, pady=2)
            lbl.pack(side=tk.LEFT)
            val = tk.Label(row, text="", bg=rb, fg=NAVY, font=F(8, True),
                           anchor="e", padx=5)
            val.pack(side=tk.RIGHT)
            self._zm_rows.append((lbl, val))

        # Notes
        tk.Frame(p, bg=BORDER, height=1).pack(fill=tk.X, pady=(3,0))
        note_hdr = tk.Frame(p, bg=BG3)
        note_hdr.pack(fill=tk.X)
        tk.Label(note_hdr, text="Note", bg=BG3, fg=NAVY,
                 font=F(8, True), padx=6, pady=2).pack(side=tk.LEFT)
        tk.Button(note_hdr, text="Save", font=F(8), bg=NAVY2, fg="white",
                  relief=tk.FLAT, cursor="hand2", padx=6,
                  command=lambda: self._auto_save(self._zm_note)).pack(side=tk.RIGHT, padx=4, pady=2)
        self._zm_note = tk.Text(p, height=3, font=F(8), wrap=tk.WORD,
                                relief=tk.FLAT, bd=1,
                                highlightbackground=BORDER, highlightthickness=1,
                                padx=4, pady=3)
        self._zm_note.pack(fill=tk.X, padx=4, pady=(0, 4))
        self._zm_note.bind("<FocusOut>", lambda e: self._auto_save(self._zm_note))

    # ── Day view ──────────────────────────────────────────────────────────
    def _build_day_frame(self):
        self._df = tk.Frame(self._content, bg=BG)

        nav = tk.Frame(self._df, bg=BG2, pady=5)
        nav.pack(fill=tk.X)
        tk.Button(nav, text="◀  Prev", font=F(10), bg=BG2, relief=tk.FLAT,
                  cursor="hand2", command=self._prev_day).pack(side=tk.LEFT, padx=10)
        tk.Button(nav, text="Today", font=F(10), bg=NAVY2, fg="white",
                  relief=tk.FLAT, cursor="hand2", padx=8,
                  command=self._go_today).pack(side=tk.LEFT, padx=4)
        tk.Button(nav, text="Next  ▶", font=F(10), bg=BG2, relief=tk.FLAT,
                  cursor="hand2", command=self._next_day).pack(side=tk.RIGHT, padx=10)

        hdr = tk.Frame(self._df, bg=NAVY, pady=12)
        hdr.pack(fill=tk.X)
        self._day_eng_lbl = tk.Label(hdr, text="", bg=NAVY, fg="white", font=F(18, True))
        self._day_eng_lbl.pack()
        self._day_heb_lbl = tk.Label(hdr, text="", bg=NAVY, fg="#D4AF37", font=FH(13, True))
        self._day_heb_lbl.pack()
        self._day_sig_lbl = tk.Label(hdr, text="", bg="#856404", fg="white",
                                     font=F(10, True), pady=3)
        # Parsha + Daf
        info_bar = tk.Frame(self._df, bg=BG3, padx=20, pady=4)
        info_bar.pack(fill=tk.X)
        self._day_info_bar = info_bar
        self._day_parsha_lbl = tk.Label(info_bar, text="", bg=BG3, fg=NAVY,
                                        font=F(10), anchor="w")
        self._day_parsha_lbl.pack(side=tk.LEFT, expand=True, anchor="w")
        self._day_daf_lbl = tk.Label(info_bar, text="", bg=BG3, fg=MUTED,
                                     font=F(9), anchor="e")
        self._day_daf_lbl.pack(side=tk.RIGHT, anchor="e")

        # Shabbos bar
        self._day_shab_bar = tk.Frame(self._df, bg="#E3F2FD", padx=20, pady=3)
        self._day_candle_lbl  = tk.Label(self._day_shab_bar, text="", bg="#E3F2FD",
                                         fg=ORANGE, font=F(10, True), anchor="w")
        self._day_candle_lbl.pack(side=tk.LEFT, expand=True, anchor="w")
        self._day_havdala_lbl = tk.Label(self._day_shab_bar, text="", bg="#E3F2FD",
                                         fg=GREEN, font=F(10, True), anchor="w")
        self._day_havdala_lbl.pack(side=tk.LEFT, padx=(10,0))
        self._day_rt_lbl      = tk.Label(self._day_shab_bar, text="", bg="#E3F2FD",
                                         fg=GREEN, font=F(10, True), anchor="w")
        self._day_rt_lbl.pack(side=tk.LEFT, padx=(10,0))

        # Zmanim list
        zm = tk.Frame(self._df, bg=BG)
        zm.pack(fill=tk.BOTH, expand=True, padx=30, pady=6)
        self._day_zm_rows: list[tuple[tk.Label, tk.Label]] = []
        for i in range(len(ZMAN_FIELDS)):
            rb = BG if i % 2 == 0 else BG2
            row = tk.Frame(zm, bg=rb)
            row.pack(fill=tk.X)
            lbl = tk.Label(row, text="", bg=rb, fg=TEXT, font=F(10),
                           anchor="w", padx=12, pady=4, width=24)
            lbl.pack(side=tk.LEFT)
            val = tk.Label(row, text="", bg=rb, fg=NAVY, font=F(10, True),
                           anchor="e", padx=12)
            val.pack(side=tk.RIGHT)
            self._day_zm_rows.append((lbl, val))

        # Notes
        tk.Frame(self._df, bg=BORDER, height=1).pack(fill=tk.X, padx=30, pady=(4,0))
        note_bar = tk.Frame(self._df, bg=BG2, padx=30, pady=3)
        note_bar.pack(fill=tk.X)
        tk.Label(note_bar, text="Note", bg=BG2, fg=NAVY, font=F(10, True)).pack(side=tk.LEFT)
        tk.Button(note_bar, text="Save", font=F(10), bg=NAVY2, fg="white",
                  relief=tk.FLAT, cursor="hand2", padx=8,
                  command=lambda: self._auto_save(self._day_note)).pack(side=tk.RIGHT)
        self._day_note = tk.Text(self._df, height=3, font=F(10), wrap=tk.WORD,
                                 relief=tk.FLAT, bd=1,
                                 highlightbackground=BORDER, highlightthickness=1,
                                 padx=6, pady=4)
        self._day_note.pack(fill=tk.X, padx=30, pady=(0, 8))
        self._day_note.bind("<FocusOut>", lambda e: self._auto_save(self._day_note))

    # ── View switching ────────────────────────────────────────────────────
    def _switch_view(self, mode: str):
        self.view = mode
        self._mf.pack_forget()
        self._df.pack_forget()
        if mode == "month":
            self._mf.pack(fill=tk.BOTH, expand=True)
            self._btn_month.config(bg="white", fg=NAVY,  relief=tk.SUNKEN)
            self._btn_day.config(  bg=NAVY2,  fg="white", relief=tk.FLAT)
        else:
            self._df.pack(fill=tk.BOTH, expand=True)
            self._btn_day.config(  bg="white", fg=NAVY,  relief=tk.SUNKEN)
            self._btn_month.config(bg=NAVY2,  fg="white", relief=tk.FLAT)
        self._render()

    def _toggle_lang(self):
        self._heb_mode = not self._heb_mode
        if self._heb_mode:
            self._btn_lang.config(text="EN", bg="white", fg=NAVY)
        else:
            self._btn_lang.config(text="עב", bg=NAVY2, fg="white")
        self._render()

    # ── Rendering ─────────────────────────────────────────────────────────
    def _render(self):
        if self.view == "month":
            self._render_month()
            self._update_panel(self.selected_date)
        else:
            self._render_day()

    def _zman_labels(self) -> list[str]:
        return ZMAN_LABELS_HE if self._heb_mode else ZMAN_LABELS_EN

    def _weekday_headers(self) -> list[str]:
        return WEEKDAYS_HE if self._heb_mode else WEEKDAYS_EN

    def _render_month(self):
        jc = JewishCalendar(self.current_month)
        hname = _heb_month_name(jc)
        self._month_lbl.config(
            text=f"{ENG_MONTHS[self.current_month.month]} {self.current_month.year}"
                 f"    |    {hname} {jc.jewish_year}"
        )
        for w in self._cal_frame.winfo_children():
            w.destroy()

        headers = self._weekday_headers()
        for col, wd in enumerate(headers):
            fg = RED if wd in ("Shab", "שבת", "Sun", "א׳") else TEXT
            tk.Label(self._cal_frame, text=wd, bg=BG3, fg=fg, font=F(9, True),
                     width=8, pady=4).grid(row=0, column=col, padx=1, pady=(0,1), sticky="nsew")

        days_in_month = calendar.monthrange(self.current_month.year, self.current_month.month)[1]
        first_col = (self.current_month.weekday() + 1) % 7
        row, col = 1, first_col
        for day in range(1, days_in_month + 1):
            d = self.current_month.replace(day=day)
            self._make_cell(d, row, col)
            col += 1
            if col == 7:
                col, row = 0, row + 1

        for c in range(7):
            self._cal_frame.columnconfigure(c, weight=1)
        for r in range(1, row + 2):
            self._cal_frame.rowconfigure(r, weight=1)

    def _cell_colors(self, date: datetime.date, sig_key: str | None):
        if date == self.selected_date:
            return SEL_BG, SEL_FG, SEL_FG
        if date == self.today:
            return TODAY_BG, TEXT, NAVY
        if sig_key in FULL_YOMTOV:
            return YOMTOV_BG, TEXT, GOLD
        if sig_key == "rosh_chodesh":
            return RCHOD_BG, TEXT, NAVY2
        if date.weekday() in (4, 5):   # Friday or Shabbos
            return SHAB_BG, RED if date.weekday()==5 else TEXT, RED
        if date.weekday() == 6:        # Sunday
            return BG, RED, RED
        return BG, TEXT, MUTED

    def _make_cell(self, date: datetime.date, row: int, col: int):
        jc      = JewishCalendar(date)
        sig_key = jc.significant_day()
        bg, fg, hfg = self._cell_colors(date, sig_key)
        note    = self._notes.get(date.isoformat(), "")

        cell = tk.Frame(self._cal_frame, bg=bg, relief=tk.FLAT, cursor="hand2",
                        highlightbackground=BORDER, highlightthickness=1)
        cell.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")

        # Top row: day number + Hebrew number
        top = tk.Frame(cell, bg=bg)
        top.pack(fill=tk.X)
        tk.Label(top, text=str(date.day), bg=bg, fg=fg,
                 font=F(11, True), anchor="nw", padx=3, pady=1).pack(side=tk.LEFT)
        tk.Label(top, text=HEB_NUMS.get(jc.jewish_day, ""), bg=bg, fg=hfg,
                 font=FH(9), anchor="ne", padx=3).pack(side=tk.RIGHT)

        # Parsha on Shabbos
        if _is_shabbos(date):
            z = self._get_zmanim(date)
            parsha = (z.parsha_he if self._heb_mode else z.parsha_en) if z else None
            if parsha:
                tk.Label(cell, text=parsha, bg=bg,
                         fg=NAVY if bg != SEL_BG else SEL_FG,
                         font=FH(7) if self._heb_mode else F(7),
                         wraplength=62, justify=tk.CENTER).pack(pady=(0,1))

        # Candle lighting time on Friday
        elif _is_friday(date):
            z = self._get_zmanim(date)
            if z and z.candle_lighting:
                cl = z.fmt_time(z.candle_lighting)
                tk.Label(cell, text=f"🕯 {cl}", bg=bg,
                         fg=ORANGE if bg != SEL_BG else SEL_FG,
                         font=F(7)).pack(pady=(0,1))

        # Significant day label
        elif sig_key and sig_key not in ("erev_shabbos",):
            short = SIG_NAMES.get(sig_key, sig_key.replace("_"," ").title())[:12]
            tk.Label(cell, text=short, bg=bg,
                     fg=GOLD if sig_key in FULL_YOMTOV else NAVY2,
                     font=F(7), wraplength=60, justify=tk.CENTER).pack(pady=(0,1))

        # Note text inside cell
        if note:
            first_line = note.split('\n')[0][:13]
            tk.Label(cell, text=first_line, bg=bg,
                     fg=ORANGE if bg != SEL_BG else "#FFCC80",
                     font=F(7), anchor="w", padx=3).pack(fill=tk.X, pady=(0,1))

        self._bind_cell(cell, date)

    def _bind_cell(self, cell: tk.Frame, date: datetime.date):
        cb = lambda e, d=date: self._select(d)
        for w in self._all_widgets(cell):
            try:
                w.bind("<Button-1>", cb)
            except Exception:
                pass

    def _all_widgets(self, w):
        yield w
        for child in w.winfo_children():
            yield from self._all_widgets(child)

    def _select(self, date: datetime.date):
        self.selected_date = date
        self._render_month()
        self._update_panel(date)

    def _update_panel(self, date: datetime.date):
        jc = JewishCalendar(date)
        self._zm_date_lbl.config(text=_fmt_date(date))
        self._zm_heb_lbl.config(
            text=f"{jc.jewish_day} {_heb_month_name(jc)} {jc.jewish_year}"
        )
        sig_key = jc.significant_day()
        if sig_key:
            self._zm_sig_lbl.config(text=SIG_NAMES.get(sig_key, sig_key.replace("_"," ").title()))
            self._zm_sig_lbl.pack(fill=tk.X, after=self._zm_heb_lbl)
        else:
            self._zm_sig_lbl.pack_forget()

        z = self._get_zmanim(date)
        # Parsha + Daf
        if z:
            parsha = z.parsha_he if self._heb_mode else z.parsha_en
            daf    = z.daf_he   if self._heb_mode else z.daf_en
            self._zm_parsha_lbl.config(
                text=("פרשת " + parsha if parsha else ""), fg=NAVY
            )
            daf_prefix = "דף " if self._heb_mode else "Daf: "
            self._zm_daf_lbl.config(text=daf_prefix + daf if daf else "")
        else:
            self._zm_parsha_lbl.config(text="")
            self._zm_daf_lbl.config(text="")

        # Shabbos / candle bar
        self._zm_candle_lbl.config(text="")
        self._zm_havdala_lbl.config(text="")
        self._zm_rt_lbl.config(text="")
        if z and (_is_friday(date) or sig_key in EREV_SHABBAT_OR_YT):
            cl = z.fmt_time(z.candle_lighting)
            lbl = "הדלקת נרות" if self._heb_mode else "Candle Lighting"
            self._zm_candle_lbl.config(text=f"🕯 {lbl}: {cl}")
            self._zm_shab_bar.pack(fill=tk.X, after=self._zm_daf_lbl.master)
        elif z and _is_shabbos(date):
            fmt = z.formatted()
            hav = fmt.get("Tzeis Hakochavim", "—")
            rt  = fmt.get("Tzeis 72 / R'T",   "—")
            hav_l = "הבדלה" if self._heb_mode else "Havdalah"
            rt_l  = 'ר"ת'   if self._heb_mode else "Rabbeinu Tam"
            self._zm_havdala_lbl.config(text=f"✡ {hav_l}: {hav}")
            self._zm_rt_lbl.config(     text=f"✡ {rt_l}: {rt}")
            self._zm_shab_bar.pack(fill=tk.X, after=self._zm_daf_lbl.master)
        else:
            self._zm_shab_bar.pack_forget()

        # Zmanim rows
        labels = self._zman_labels()
        fmt = z.formatted() if z else {}
        for i, ((lbl, val), (en_label, _)) in enumerate(zip(self._zm_rows, ZMAN_FIELDS)):
            anchor = "e" if self._heb_mode else "w"
            lbl.config(text=labels[i], anchor=anchor)
            val.config(text=fmt.get(en_label, "—"))

        # Note
        self._zm_note.delete("1.0", tk.END)
        note = self._notes.get(date.isoformat(), "")
        if note:
            self._zm_note.insert("1.0", note)

    def _render_day(self):
        date = self.selected_date
        jc   = JewishCalendar(date)

        self._day_eng_lbl.config(text=_fmt_date(date))
        self._day_heb_lbl.config(
            text=f"{jc.jewish_day} {_heb_month_name(jc)} {jc.jewish_year}"
        )
        sig_key = jc.significant_day()
        if sig_key:
            self._day_sig_lbl.config(text=SIG_NAMES.get(sig_key, sig_key.replace("_"," ").title()))
            self._day_sig_lbl.pack(fill=tk.X)
        else:
            self._day_sig_lbl.pack_forget()

        z = self._get_zmanim(date)
        # Parsha + Daf
        if z:
            parsha = z.parsha_he if self._heb_mode else z.parsha_en
            daf    = z.daf_he   if self._heb_mode else z.daf_en
            self._day_parsha_lbl.config(
                text=("פרשת " + parsha if parsha else ""),
                font=FH(10) if self._heb_mode else F(10)
            )
            daf_prefix = "דף " if self._heb_mode else "Daf: "
            self._day_daf_lbl.config(text=daf_prefix + daf if daf else "")
        else:
            self._day_parsha_lbl.config(text="")
            self._day_daf_lbl.config(text="")

        # Shabbos bar
        self._day_candle_lbl.config(text="")
        self._day_havdala_lbl.config(text="")
        self._day_rt_lbl.config(text="")
        if z and (_is_friday(date) or sig_key in EREV_SHABBAT_OR_YT):
            cl = z.fmt_time(z.candle_lighting)
            lbl = "הדלקת נרות" if self._heb_mode else "Candle Lighting"
            self._day_candle_lbl.config(text=f"🕯 {lbl}: {cl}")
            self._day_shab_bar.pack(fill=tk.X, after=self._day_info_bar)
        elif z and _is_shabbos(date):
            fmt = z.formatted()
            hav = fmt.get("Tzeis Hakochavim", "—")
            rt  = fmt.get("Tzeis 72 / R'T",   "—")
            hav_l = "הבדלה" if self._heb_mode else "Havdalah"
            rt_l  = 'ר"ת'   if self._heb_mode else "Rabbeinu Tam"
            self._day_havdala_lbl.config(text=f"✡ {hav_l}: {hav}")
            self._day_rt_lbl.config(     text=f"✡ {rt_l}: {rt}")
            self._day_shab_bar.pack(fill=tk.X, after=self._day_info_bar)
        else:
            self._day_shab_bar.pack_forget()

        # Zmanim rows
        labels = self._zman_labels()
        fmt = z.formatted() if z else {}
        for i, ((lbl, val), (en_label, _)) in enumerate(zip(self._day_zm_rows, ZMAN_FIELDS)):
            anchor = "e" if self._heb_mode else "w"
            lbl.config(text=labels[i], anchor=anchor,
                       font=FH(10) if self._heb_mode else F(10))
            val.config(text=fmt.get(en_label, "—"))

        # Note
        self._day_note.delete("1.0", tk.END)
        note = self._notes.get(date.isoformat(), "")
        if note:
            self._day_note.insert("1.0", note)

    # ── Notes (auto-save) ─────────────────────────────────────────────────
    def _auto_save(self, widget: tk.Text):
        text = widget.get("1.0", tk.END).strip()
        key  = self.selected_date.isoformat()
        if text:
            self._notes[key] = text
        else:
            self._notes.pop(key, None)
        _save_notes(self._notes)
        if self.view == "month":
            self._render_month()   # refresh cell display

    # ── Navigation ────────────────────────────────────────────────────────
    def _prev_month(self):
        m, y = self.current_month.month - 1, self.current_month.year
        if m == 0: m, y = 12, y - 1
        self.current_month = datetime.date(y, m, 1)
        self._render()

    def _next_month(self):
        m, y = self.current_month.month + 1, self.current_month.year
        if m == 13: m, y = 1, y + 1
        self.current_month = datetime.date(y, m, 1)
        self._render()

    def _prev_day(self):
        self.selected_date -= datetime.timedelta(days=1)
        self.current_month  = self.selected_date.replace(day=1)
        self._render()

    def _next_day(self):
        self.selected_date += datetime.timedelta(days=1)
        self.current_month  = self.selected_date.replace(day=1)
        self._render()

    def _go_today(self):
        self.selected_date = self.today
        self.current_month = self.today.replace(day=1)
        self._render()

    # ── Helpers ───────────────────────────────────────────────────────────
    def _city_key(self) -> str:
        return self._city_keys[self._city_combo.current()]

    def _on_city(self, _=None):
        self._cache.clear()
        self._render()

    def _get_zmanim(self, date: datetime.date):
        key = (self._city_key(), date)
        if key not in self._cache:
            try:
                self._cache[key] = compute_day(self._city_key(), date)
            except Exception:
                self._cache[key] = None
        return self._cache[key]


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("980x680")
    LuachApp(root)
    root.mainloop()
