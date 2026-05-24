from __future__ import annotations

import threading
import time
from typing import Literal

from solox.public.adb import adb
from solox.public.apm import AppPerformanceMonitor
from solox.public.common import Devices, Platform


DEVICE_ID = "I76XGQ5D7T5LBQVC"
PACKAGE_NAME = "com.android.settings"


def make_monitor(
    pid: str, surfaceview: Literal["true", "false", "auto"]
) -> AppPerformanceMonitor:
    return AppPerformanceMonitor(
        pkgName=PACKAGE_NAME,
        platform=Platform.Android,
        deviceId=DEVICE_ID,
        surfaceview=surfaceview,
        noLog=True,
        pid=pid,
        record=False,
        collect_all=False,
    )


def swipe_for(seconds: float) -> threading.Thread:
    def worker() -> None:
        end_at = time.time() + seconds
        while time.time() < end_at:
            adb.shell("input swipe 800 2100 800 800 250", DEVICE_ID)
            time.sleep(0.1)
            adb.shell("input swipe 800 800 800 2100 250", DEVICE_ID)
            time.sleep(0.1)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread


def main() -> int:
    devices = Devices()
    pids = devices.getPid(DEVICE_ID, PACKAGE_NAME)
    main_pid = [item for item in pids if item.endswith(":" + PACKAGE_NAME)][0].split(
        ":", 1
    )[0]

    print("device", DEVICE_ID)
    print("package", PACKAGE_NAME)
    print("pid", main_pid)
    print("current_activity", devices.getCurrentActivity(DEVICE_ID))

    apm = make_monitor(main_pid, surfaceview='auto')

    checks = [
        ("cpu", lambda: apm.collectCpu()),
        ("memory", lambda: apm.collectMemory()),
        ("memory_detail", lambda: apm.collectMemoryDetail()),
        ("network_wifi", lambda: apm.collectNetwork(wifi=True)),
        ("fps_gfxinfo_static", lambda: apm.collectFps()),
        ("battery", lambda: apm.collectBattery()),
        ("disk", lambda: apm.collectDisk()),
        ("thermal", lambda: apm.collectThermal()),
        ("gpu", lambda: apm.collectGpu()),
    ]

    try:
        for name, func in checks:
            print()
            try:
                print(name, func())
            except Exception as exc:
                print(name, "ERROR", type(exc).__name__, str(exc))
            print()
    finally:
        adb.shell("dumpsys battery reset", DEVICE_ID)
        print("battery_reset done")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
