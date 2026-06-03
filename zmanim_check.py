import datetime
from zmanim.zmanim_calendar import ZmanimCalendar
from zmanim.util.geo_location import GeoLocation

geo = GeoLocation('Lakewood', 40.0959, -74.2176, 'America/New_York', elevation=13)
cal = ZmanimCalendar(geo_location=geo, date=datetime.date(2026, 6, 3))

target = ["sof_zman", "alos", "tzais"]
for m in sorted(dir(cal)):
    if any(t in m.lower() for t in target):
        try:
            val = getattr(cal, m)()
            if val:
                print(f"{m:<45} {val.strftime('%I:%M %p')}")
        except Exception:
            pass
