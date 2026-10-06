import struct
import os
import sys

def patch_elf(filepath, patches):
    """Apply binary patches to ELF file"""
    with open(filepath, 'rb') as f:
        data = bytearray(f.read())
    
    applied = 0
    for offset, original, replacement, comment in patches:
        if offset + len(replacement) > len(data):
            print(f"  SKIP (out of bounds): offset 0x{offset:x}")
            continue
        
        current = bytes(data[offset:offset+len(original)])
        if current == original:
            data[offset:offset+len(replacement)] = replacement
            print(f"  PATCHED: 0x{offset:08x} — {comment}")
            applied += 1
        elif current == replacement:
            print(f"  ALREADY: 0x{offset:08x} — {comment}")
            applied += 1
        else:
            print(f"  MISMATCH: 0x{offset:08x} — expected {original.hex()}, got {current.hex()}")
    
    with open(filepath, 'wb') as f:
        f.write(data)
    
    return applied

def find_function_by_string(data, search_str, max_results=10):
    """Find string in binary and return offsets"""
    results = []
    target = search_str.encode() if isinstance(search_str, str) else search_str
    pos = 0
    while len(results) < max_results:
        idx = data.find(target, pos)
        if idx == -1:
            break
        results.append(idx)
        pos = idx + 1
    return results

def patch_libanogs(input_path, output_path):
    """Patch libanogs.so — neutralize anticheat"""
    print("=" * 60)
    print("PATCHING libanogs.so — ANTICHEAT NEUTRALIZATION")
    print("=" * 60)
    
    with open(input_path, 'rb') as f:
        data = f.read()
    
    print(f"Original size: {len(data)} bytes")
    
    patches = []
    
    # ARM64 instruction encodings
    # MOV X0, #0 ; RET = 00 00 80 D2 C0 03 5F D6
    RET_ZERO = bytes([0x00, 0x00, 0x80, 0xD2, 0xC0, 0x03, 0x5F, 0xD6])
    # MOV W0, #1 ; RET (return true)
    RET_ONE = bytes([0x20, 0x00, 0x80, 0x52, 0xC0, 0x03, 0x5F, 0xD6])
    # NOP
    NOP = bytes([0x1F, 0x20, 0x03, 0xD5])
    # RET alone
    RET = bytes([0xC0, 0x03, 0x5F, 0xD6])
    
    # Стратегия: найти ключевые строки → найти ссылки на них → патчить функции
    
    # 1. Root detection strings
    root_strings = [
        b'/system/bin/su',
        b'/system/xbin/su', 
        b'/sbin/su',
        b'/system/app/Superuser.apk',
        b'/system/app/SuperSU',
        b'magisk',
        b'Superuser',
        b'daemon/su',
    ]
    
    print("\n[1] Root detection strings found:")
    for s in root_strings:
        offsets = find_function_by_string(data, s, 3)
        if offsets:
            print(f"  '{s.decode(errors='replace')}': {len(offsets)} locations")
            for off in offsets:
                print(f"    -> 0x{off:08x}")
    
    # 2. Frida/Hook detection
    hook_strings = [
        b'frida',
        b'LIBFRIDA',
        b'xposed',
        b'Substrate',
        b'/proc/self/maps',
        b'/proc/self/status',
        b'TracerPid',
        b'ptrace',
    ]
    
    print("\n[2] Hook/Frida detection strings:")
    for s in hook_strings:
        offsets = find_function_by_string(data, s, 3)
        if offsets:
            print(f"  '{s.decode(errors='replace')}': {len(offsets)} locations")
            for off in offsets:
                print(f"    -> 0x{off:08x}")
    
    # 3. Emulator detection
    emulator_strings = [
        b'goldfish',
        b'qemu',
        b'vbox',
        b'genymotion',
        b'x86',
        b'LD_LIBRARY_PATH',
    ]
    
    print("\n[3] Emulator detection strings:")
    for s in emulator_strings:
        offsets = find_function_by_string(data, s, 3)
        if offsets:
            print(f"  '{s.decode(errors='replace')}': {len(offsets)} locations")
    
    # 4. Integrity check strings
    integrity_strings = [
        b'signature',
        b'CRC32',
        b'MD5',
        b'SHA1',
        b'tamper',
        b'modified',
        b'integrity',
    ]
    
    print("\n[4] Integrity check strings:")
    for s in integrity_strings:
        offsets = find_function_by_string(data, s, 3)
        if offsets:
            print(f"  '{s.decode(errors='replace')}': {len(offsets)} locations")
    
    # 5. Telegram/C2 communication
    report_strings = [
        b'http://',
        b'https://',
        b'report',
        b'upload',
        b'send_data',
        b'tlog',
    ]
    
    print("\n[5] Report/C2 strings:")
    for s in report_strings:
        offsets = find_function_by_string(data, s, 3)
        if offsets:
            print(f"  '{s.decode(errors='replace')}': {len(offsets)} locations")
    
    # Теперь — основной патч
    # Ищем JNI_OnLoad — главная точка входа библиотеки
    # Патчим его чтобы вернуть JNI_VERSION_1_6 без инициализации проверок
    
    print("\n[6] Applying patches...")
    
    # JNI_OnLoad — обычно экспортирована, найдём через dynsym
    # Пока применяем generic патчи — NOP на областях сравнения строк
    
    # Патчим все строки детекции на пустые — детектор ничего не найдёт
    for s in root_strings + hook_strings + emulator_strings:
        offsets = find_function_by_string(data, s, 50)
        for off in offsets:
            # Заменяем первый байт на 0x00 — строка станет пустой
            # Это безопаснее чем NOP-ing код
            patches.append((off, s[:1], b'\x00', f"Blank string: {s[:20]}"))
    
    applied = patch_elf(output_path, patches)
    print(f"\nApplied {applied} patches")
    
    print("\n" + "="*60)
    print("ANTICHEAT PATCHING PHASE 1 COMPLETE")
    print("="*60)


def patch_libue4(input_path, output_path):
    """Patch libUE4.so — engine modifications"""
    print("=" * 60)
    print("PATCHING libUE4.so — ENGINE MODIFICATIONS")
    print("=" * 60)
    
    with open(input_path, 'rb') as f:
        data = f.read()
    
    print(f"Original size: {len(data)} bytes ({len(data)/1024/1024:.1f} MB)")
    
    patches = []
    
    # ARM64 encodings
    NOP = bytes([0x1F, 0x20, 0x03, 0xD5])
    RET = bytes([0xC0, 0x03, 0x5F, 0xD6])
    
    # 1. AntiCheat component strings — патчим报警ные строки
    ac_strings = [
        b'AntiCheatMovementRawData',
        b'AntiCheatRandValue3',
        b'AntiCheatRandValue4',
        b'AntiCheatRandValue5',
        b'AntiCheatRandValue6',
        b'CatchReportAntiCheatDetailData',
        b'AntiCheatSetup',
        b'AntiCheatMaxOmega',
    ]
    
    print("\n[1] Neutralizing AntiCheat component references:")
    for s in ac_strings:
        offsets = find_function_by_string(data, s, 20)
        print(f"  '{s.decode()}': {len(offsets)} references")
        for off in offsets:
            # Blank the string — движок не найдёт компонент
            patches.append((off, s[:1], b'\x00', f"Blank AC ref: {s[:30]}"))
    
    # 2. Speed/Position validation strings
    validation_strings = [
        b'MoveAntiCheat',
        b'SpeedHack',
        b'Teleport',
        b'InvalidMovement',
    ]
    
    print("\n[2] Movement validation strings:")
    for s in validation_strings:
        offsets = find_function_by_string(data, s, 20)
        if offsets:
            print(f"  '{s.decode()}': {len(offsets)} references")
            for off in offsets:
                patches.append((off, s[:1], b'\x00', f"Blank: {s}"))
    
    applied = patch_elf(output_path, patches)
    print(f"\nApplied {applied} patches")
    
    print("\n" + "="*60)
    print("ENGINE PATCHING PHASE 1 COMPLETE")
    print("="*60)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 patch_all.py <libs_directory>")
        sys.exit(1)
    
    libs_dir = sys.argv[1]
    
    # libanogs.so
    anogs_input = os.path.join(libs_dir, 'libanogs.so')
    anogs_output = os.path.join(libs_dir, 'libanogs.so.patched')
    if os.path.exists(anogs_input):
        patch_libanogs(anogs_input, anogs_output)
        os.replace(anogs_output, anogs_input)
        print(f"\nlibanogs.so patched → {anogs_input}")
    
    # libUE4.so
    ue4_input = os.path.join(libs_dir, 'libUE4.so')
    ue4_output = os.path.join(libs_dir, 'libUE4.so.patched')
    if os.path.exists(ue4_input):
        patch_libue4(ue4_input, ue4_output)
        os.replace(ue4_output, ue4_input)
        print(f"\nlibUE4.so patched → {ue4_input}")
    
    # Удаляем анорт (helper античита)
    anort = os.path.join(libs_dir, 'libanort.so')
    if os.path.exists(anort):
        os.remove(anort)
        print(f"\nlibanort.so REMOVED")
    
    print("\nALL PATCHES APPLIED")
