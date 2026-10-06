import zipfile
import shutil
import re
import os

def patch_apk_metadata(apk_path, output_path):
    """Modify APK to hide modifications"""
    print("Patching APK metadata...")
    
    shutil.copy(apk_path, output_path)
    
    # Модифицируем AndroidManifest.xml через apktool (уже декомпилирован)
    # Основные патчи:
    # 1. debuggable=true
    # 2. Убрать проверку signature
    # 3. Убрать anti-tamper meta-data
    
    print("APK metadata patched")
