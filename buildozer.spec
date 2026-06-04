[app]

title = Luach
package.name = luach
package.domain = org.jewish

source.dir = .
source.include_exts = py,json,ttf,png
source.include_patterns = luach_kivy.py,zmanim_core.py,logo.png

version = 1.0

# Pure-Python requirements — all work on Android
requirements = python3==3.10.0,kivy==2.3.0,zmanim,pyluach,pytz,julian,memoization,python-bidi,Pillow

orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png

[android]
android.permissions = WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.release_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
