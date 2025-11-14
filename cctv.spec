# cctv.spec
# Adjust "cctv.py" to your filename

block_cipher = None

a = Analysis(
    ['cctv.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ffmpeg/ffmpeg.exe', 'ffmpeg'),
        ('ffmpeg/ffprobe.exe', 'ffmpeg'),
        ('ffmpeg/ffplay.exe', 'ffmpeg'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[]
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='cctv',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='cctv'
)
