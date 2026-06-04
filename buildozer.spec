[app]

title = Luach
package.name = luach
package.domain = org.jewish

source.dir = .
source.include_exts = py,json,ttf,png
source.include_patterns = luach_kivy.py,zmanim_core.py,logo.png

version = 1.0

requirements = python3==3.11.4,hostpython3==3.11.4,kivy==2.3.0,zmanim,pyluach,pytz,julian,memoization,python-bidi

orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/logo.png

android.permissions = WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a
android.allow_backup = True
android.release_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
