# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cctv.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ffmpeg/*', 'ffmpeg'),
    ],
    hiddenimports=[],
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='cctv',
    console=False,
)
