# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
    copy_metadata,
)

block_cipher = None

datas = []
binaries = []
hiddenimports = [
    # GUI
    'customtkinter',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',

    # Audio & Speech
    'speech_recognition',
    'pyaudio',
    'sounddevice',
    'soundfile',
    '_sounddevice_data',
    '_soundfile_data',
    'sherpa_onnx',
    'sherpa_onnx_core',
    'pythaitts',
    'vachanatts',
    'pythainlp',
    'pythainlp.tokenize',
    'pythainlp.corpus',
    'pythainlp.tools',
    'onnxruntime',

    # ML & Torch
    'torch',
    'torchvision',
    'torchaudio',
    'whisper',
    'sentence_transformers',
    'sentence_transformers.models',
    'sentence_transformers.models.Transformer',
    'sentence_transformers.models.Pooling',
    'transformers',
    'transformers.models.whisper',
    'transformers.models.whisper.tokenization_whisper',
    'transformers.models.whisper.processing_whisper',
    'transformers.models.whisper.modeling_whisper',
    'transformers.models.vits',
    'transformers.models.vits.tokenization_vits',
    'transformers.models.vits.modeling_vits',
    'transformers.models.auto',
    'scipy',
    'scipy.spatial.transform._rotation_groups',
    'scipy.special.cython_special',
    'sklearn',
    'sklearn.utils._typedefs',
    'sklearn.neighbors._typedefs',
    'sklearn.metrics.pairwise',
    'numpy',
    'sqlite3',
    'unittest',
    'unittest.mock',
    'gui',
    'chat',
    'models',
    'dictionary',
]

# Collect all resources for packages that require explicit data collection
packages_to_collect = [
    'customtkinter',
    'whisper',
    'sherpa_onnx',
    '_sounddevice_data',
    '_soundfile_data',
    'vachanatts',
    'pythaitts',
    'ssg',
    'onnxruntime',
]

for pkg in packages_to_collect:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as e:
        print(f"Warning: failed to collect_all({pkg}): {e}")

# Collect data files for pythainlp without triggering unwanted corpus downloads
datas += collect_data_files('pythainlp')

# Ensure Torch dynamic libraries (.dll) are collected
binaries += collect_dynamic_libs('torch')

# Copy metadata for essential packages
metadata_packages = [
    'transformers',
    'huggingface_hub',
    'sentence_transformers',
    'tokenizers',
    'safetensors',
    'tqdm',
    'regex',
    'requests',
    'filelock',
    'packaging',
    'numpy',
    'torch',
    'openai-whisper',
    'pythainlp',
    'scikit-learn',
    'scipy',
]

for meta in metadata_packages:
    try:
        datas += copy_metadata(meta)
    except Exception as e:
        print(f"Warning: failed to copy_metadata({meta}): {e}")

# Icon file
icon_file = os.path.abspath('assets/image/app_icon.ico')
if not os.path.exists(icon_file):
    icon_file = None

a = Analysis(
    ['src/main.py'],
    pathex=['src', '.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter.test',
        'pytest',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DJOP_DEMO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DJOP_DEMO',
)
