import os, sys

def blank_all(data, target, cap=300):
    tb = target.encode() if isinstance(target, str) else target
    if not tb:
        return 0
    hits = 0
    pos = 0
    while hits < cap:
        idx = data.find(tb, pos)
        if idx == -1:
            break
        data[idx:idx+len(tb)] = b'\x00' * len(tb)
        hits += 1
        pos = idx + len(tb)
    return hits

def patch_file(path, targets, label):
    if not os.path.exists(path):
        print(f"  {path} skip")
        return 0
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    total = 0
    for t in targets:
        total += blank_all(data, t)
    with open(path, 'wb') as f:
        f.write(data)
    print(f"  [{label}] {os.path.basename(path)}: {total} blanked")
    return total

# Root / hook / emulator detection strings — blank in libanogs.so
DETECT = [
    '/system/bin/su', '/system/xbin/su', '/sbin/su',
    'Superuser', 'SuperSU', 'magisk', 'frida', 'xposed',
    'substrate', 'TracerPid', 'ptrace',
    '/proc/self/maps', '/proc/self/status',
    'gameguardian', 'vmos', 'goldfish', 'qemu',
    'vbox', 'genymotion', 'emulator',
]

# AntiCheat components in libUE4.so — blank so engine can't find them
AC = [
    'AntiCheatSetup', 'AntiCheatMaxOmega',
    'AntiCheatMovementRawData', 'CatchReportAntiCheatDetailData',
    'MoveAntiCheatComponent', 'PlayerAntiCheatManager',
    'AntiCheatManagerComp', 'AntiCheatData',
    'AntiCheatDetailData', 'AntiCheatRandValue',
    'AntiCheatComp',
]

# Telemetry strings
TELEMETRY = [
    'TDataMaster', 'CrashSight', 'Sentry',
    'sentry.io', 'crashreport',
]

if __name__ == '__main__':
    libs = sys.argv[1] if len(sys.argv) > 1 else 'libs'
    print("=== ANTIBAN ===")
    patch_file(os.path.join(libs, 'libanogs.so'), DETECT, "anogs-detect")
    patch_file(os.path.join(libs, 'libUE4.so'), AC, "UE4-anticheat")
    patch_file(os.path.join(libs, 'libTDataMaster.so'), DETECT + TELEMETRY, "telemetry")
    print("=== DONE ===")
