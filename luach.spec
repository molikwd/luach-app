# luach.spec
block_cipher = None

a = Analysis(
    ['luach_app.py'],
    pathex=['C:\\luach_app'],
    binaries=[],
    datas=[
        ('C:\\k4k_env\\Lib\\site-packages\\zmanim', 'zmanim'),
        ('C:\\k4k_env\\Lib\\site-packages\\pyluach', 'pyluach'),
        ('logo.png', '.'),
    ],
    hiddenimports=[
        'zmanim',
        'zmanim.hebrew_calendar',
        'zmanim.hebrew_calendar.jewish_calendar',
        'zmanim.util',
        'zmanim.util.geo_location',
        'zmanim.zmanim_calendar',
        'pytz',
        'julian',
        'memoization',
        'pyluach',
        'pyluach.dates',
        'pyluach.parshios',
        'tkinter',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pygame'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Luach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
