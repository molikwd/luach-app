"""
zmanim_core.py  —  halachic time computation engine
"""
from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from typing import Optional

from zmanim.util.geo_location import GeoLocation
from zmanim.zmanim_calendar import ZmanimCalendar
from zmanim.hebrew_calendar.jewish_calendar import JewishCalendar

try:
    from pyluach import dates as _pydates, parshios as _pyparsh
    _PYLUACH = True
except ImportError:
    _PYLUACH = False


# ── Cities ────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class City:
    name: str
    name_he: str
    latitude: float
    longitude: float
    timezone: str
    elevation: float = 0.0


CITIES: dict[str, City] = {
    "lakewood":    City("Lakewood, NJ",    "ליקוואוד",    40.0959,  -74.2176, "America/New_York",    13),
    "brooklyn":    City("Brooklyn, NY",    "ברוקלין",     40.6782,  -73.9442, "America/New_York",    10),
    "monsey":      City("Monsey, NY",      "מאנסי",       41.1112,  -74.0682, "America/New_York",   146),
    "jerusalem":   City("Jerusalem",       "ירושלים",     31.7683,   35.2137, "Asia/Jerusalem",     754),
    "bneibrak":    City("Bnei Brak",       "בני ברק",     32.0807,   34.8338, "Asia/Jerusalem",      38),
    "los_angeles": City("Los Angeles, CA", "לוס אנגלס",   34.0522, -118.2437, "America/Los_Angeles", 71),
    "toronto":     City("Toronto, ON",     "טורונטו",     43.6532,  -79.3832, "America/Toronto",     76),
    "london":      City("London",          "לונדון",      51.5074,   -0.1278, "Europe/London",       11),
    "manchester":  City("Manchester",      "מנצ'סטר",     53.4808,   -2.2426, "Europe/London",       38),
    "antwerp":     City("Antwerp",         "אנטוורפן",    51.2194,    4.4025, "Europe/Brussels",      7),
    "stamford_ny": City("The Zone Boys Camp", "זון בויז קאמפ", 42.3338,  -74.6426, "America/New_York",   691),
    "gilboa_ny":   City("The Zone Girls Camp","זון גירלז קאמפ",42.3951,  -74.4934, "America/New_York",   538),
}


# ── Zmanim fields ─────────────────────────────────────────────────────────
ZMAN_FIELDS = [
    ("Alos Hashachar",       "alos"),       # degrees-based (M"A / 16.1°)
    ("Netz (Sunrise)",       "sunrise"),
    ("Sof Zman Shma MGA",    "sof_zman_shma_mga"),    # overridden below
    ("Sof Zman Shma GRA",    "sof_zman_shma_gra"),
    ("Sof Zman Tefilla MGA", "sof_zman_tfila_mga"),   # overridden below
    ("Sof Zman Tefilla GRA", "sof_zman_tfila_gra"),
    ("Chatzos",              "chatzos"),
    ("Mincha Gedola",        "mincha_gedola"),
    ("Mincha Ketana",        "mincha_ketana"),
    ("Plag HaMincha",        "plag_hamincha"),
    ("Shkiah (Sunset)",      "sunset"),
    ("Tzeis Hakochavim",     "tzais"),
    ("Tzeis 72 / R'T",       "tzais_72"),
]


# ── Daf Yomi ──────────────────────────────────────────────────────────────
_DAF_CYCLE_14_START = datetime.date(2020, 1, 5)   # 14th cycle: Berachos 2

_DAF_SCHEDULE = [
    # (name_en,          name_he,          num_dafim, start_daf)
    ("Berachos",          "ברכות",           63,  2),
    ("Shabbos",           "שבת",            156,  2),
    ("Eruvin",            "עירובין",         104,  2),
    ("Pesachim",          "פסחים",           120,  2),
    ("Shekalim",          "שקלים",            21,  2),
    ("Yoma",              "יומא",             87,  2),
    ("Sukkah",            "סוכה",             55,  2),
    ("Beitzah",           "ביצה",             39,  2),
    ("Rosh Hashana",      "ראש השנה",         34,  2),
    ("Taanis",            "תענית",            30,  2),
    ("Megillah",          "מגילה",            31,  2),
    ("Moed Katan",        "מועד קטן",         28,  2),
    ("Chagigah",          "חגיגה",            26,  2),
    ("Yevamos",           "יבמות",           121,  2),
    ("Kesubos",           "כתובות",          111,  2),
    ("Nedarim",           "נדרים",            90,  2),
    ("Nazir",             "נזיר",             65,  2),
    ("Sotah",             "סוטה",             48,  2),
    ("Gittin",            "גיטין",            89,  2),
    ("Kiddushin",         "קידושין",          81,  2),
    ("Bava Kamma",        "בבא קמא",         118,  2),
    ("Bava Metzia",       "בבא מציעא",        118,  2),
    ("Bava Basra",        "בבא בתרא",        175,  2),
    ("Sanhedrin",         "סנהדרין",         112,  2),
    ("Makkos",            "מכות",             23,  2),
    ("Shevuos",           "שבועות",           48,  2),
    ("Avodah Zarah",      "עבודה זרה",        75,  2),
    ("Horayos",           "הוריות",           13,  2),
    ("Zevachim",          "זבחים",           119,  2),
    ("Menachos",          "מנחות",           109,  2),
    ("Chullin",           "חולין",           141,  2),
    ("Bechoros",          "בכורות",           60,  2),
    ("Arachin",           "ערכין",            33,  2),
    ("Temurah",           "תמורה",            33,  2),
    ("Kereisos",          "כריתות",           27,  2),
    ("Meilah/Kinnim",     "מעילה/קנים",       24,  2),
    ("Tamid",             "תמיד",              9, 25),
    ("Niddah",            "נדה",              72,  2),
]

# Build cumulative offset array
_DAF_CUMULATIVE: list[int] = []
_total = 0
for _en, _he, _n, _s in _DAF_SCHEDULE:
    _DAF_CUMULATIVE.append(_total)
    _total += _n
_DAF_TOTAL = _total   # ≈ 2711


def get_daf_yomi(date: datetime.date) -> tuple[str, str]:
    """Return (english_str, hebrew_str) for date's Daf Yomi, e.g. ('Chullin 34', 'חולין 34')."""
    day_num = (date - _DAF_CYCLE_14_START).days % _DAF_TOTAL
    if day_num < 0:
        day_num += _DAF_TOTAL
    # Find masechta
    idx = 0
    for i in range(len(_DAF_CUMULATIVE) - 1, -1, -1):
        if day_num >= _DAF_CUMULATIVE[i]:
            idx = i
            break
    en, he, num_daf, start_daf = _DAF_SCHEDULE[idx]
    daf_num = start_daf + (day_num - _DAF_CUMULATIVE[idx])
    return f"{en} {daf_num}", f"{he} {daf_num}"


# ── Parsha ────────────────────────────────────────────────────────────────
def get_parsha(date: datetime.date, hebrew: bool = False) -> Optional[str]:
    """Return parsha name for the week containing `date`, or None on Yom Tov."""
    if not _PYLUACH:
        return None
    try:
        d = _pydates.HebrewDate.from_pydate(date)
        return _pyparsh.getparsha_string(d, israel=False, hebrew=hebrew)
    except Exception:
        return None


# ── DayZmanim ─────────────────────────────────────────────────────────────
@dataclass
class DayZmanim:
    city: City
    date: datetime.date
    hebrew_date: str
    significant_day: Optional[str]
    times: dict[str, Optional[datetime.datetime]]
    candle_lighting: Optional[datetime.datetime] = None
    parsha_en: Optional[str] = None
    parsha_he: Optional[str] = None
    daf_en: str = ""
    daf_he: str = ""

    def formatted(self, fmt: str = "%I:%M %p") -> dict[str, str]:
        out = {}
        for label, dt in self.times.items():
            if dt:
                s = dt.strftime(fmt).lstrip("0") or dt.strftime(fmt)
                out[label] = s
            else:
                out[label] = "—"
        return out

    def fmt_time(self, dt: Optional[datetime.datetime], fmt: str = "%I:%M %p") -> str:
        if not dt:
            return "—"
        return dt.strftime(fmt).lstrip("0") or dt.strftime(fmt)


# ── Hebrew date ───────────────────────────────────────────────────────────
_HEB_MONTHS = {
    1:"ניסן", 2:"אייר", 3:"סיון", 4:"תמוז", 5:"אב", 6:"אלול",
    7:"תשרי", 8:"חשון", 9:"כסלו", 10:"טבת", 11:"שבט", 12:"אדר", 13:"אדר ב׳",
}


def _hebrew_date_str(jc: JewishCalendar) -> str:
    d = jc.jewish_day
    m = jc.jewish_month
    y = jc.jewish_year
    name = _HEB_MONTHS.get(m, str(m))
    if m == 12 and jc.is_jewish_leap_year():
        name = "אדר א׳"
    return f"{d} {name} {y}"


# ── Main computation ──────────────────────────────────────────────────────
def compute_day(city_key: str, date: datetime.date) -> DayZmanim:
    if city_key not in CITIES:
        raise KeyError(f"Unknown city '{city_key}'")
    city = CITIES[city_key]

    geo = GeoLocation(city.name, city.latitude, city.longitude,
                      city.timezone, elevation=city.elevation)
    cal = ZmanimCalendar(geo_location=geo, date=date)

    times: dict[str, Optional[datetime.datetime]] = {}
    for label, method in ZMAN_FIELDS:
        fn = getattr(cal, method, None)
        try:
            times[label] = fn() if fn else None
        except Exception:
            times[label] = None

    # Recompute MGA times using degrees-based alos + symmetrical tzais.
    # The library's sof_zman_shma_mga uses fixed 72-min alos/tzais which gives
    # a different result (~8:36) from the standard luach (8:20). The OU and
    # most printed luachos use: alos=16.1° degrees, tzais=sunset+(sunrise−alos).
    try:
        alos_dt    = times.get("Alos Hashachar")
        sunrise_dt = times.get("Netz (Sunrise)")
        sunset_dt  = times.get("Shkiah (Sunset)")
        if alos_dt and sunrise_dt and sunset_dt:
            pre_dawn  = sunrise_dt - alos_dt            # e.g. ~104 min in June
            tzais_mga = sunset_dt + pre_dawn             # symmetrical end-of-day
            shaah_mga = (tzais_mga - alos_dt) / 12
            times["Sof Zman Shma MGA"]    = alos_dt + 3 * shaah_mga
            times["Sof Zman Tefilla MGA"] = alos_dt + 4 * shaah_mga
    except Exception:
        pass

    candle_lighting = None
    try:
        candle_lighting = cal.candle_lighting()
    except Exception:
        pass

    jc = JewishCalendar(date)
    hd = _hebrew_date_str(jc)
    sig = jc.significant_day()
    sig_str = sig.replace("_", " ").title() if sig else None

    daf_en, daf_he = get_daf_yomi(date)
    parsha_en = get_parsha(date, hebrew=False)
    parsha_he = get_parsha(date, hebrew=True)

    return DayZmanim(
        city=city, date=date, hebrew_date=hd,
        significant_day=sig_str, times=times,
        candle_lighting=candle_lighting,
        parsha_en=parsha_en, parsha_he=parsha_he,
        daf_en=daf_en, daf_he=daf_he,
    )
