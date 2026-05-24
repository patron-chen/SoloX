from __future__ import annotations

from solox.public.apm import AppPerformanceMonitor, initPerformanceService
from solox.public.common import Devices, Platform


def pick_running_android_process(device_id: str) -> tuple[str, str] | None:
    devices = Devices()
    candidates = ("com.android.settings",)
    for package_name in candidates:
        processes = devices.getPid(deviceId=device_id, pkgName=package_name)
        if processes:
            pid = processes[0].split(":", 1)[0]
            return package_name, pid
    return None


def main() -> int:
    devices = Devices()
    android_devices = devices.getDeviceIds()
    print("solox service switch:", initPerformanceService.get_status())

    if not android_devices:
        print("No Android device found. Imports and helper initialization are OK.")
        return 0

    device_id = android_devices[0]
    picked = pick_running_android_process(device_id)
    if picked is None:
        print(
            f"Android device {device_id} is connected, but no demo process was found."
        )
        return 2

    package_name, pid = picked
    apm = AppPerformanceMonitor(
        pkgName=package_name,
        platform=Platform.Android,
        deviceId=device_id,
        surfaceview="auto",
        noLog=True,
        pid=pid,
        record=False,
        collect_all=False,
    )
    print("device:", device_id)
    print("package:", package_name)
    print("pid:", pid)
    print("cpu:", apm.collectCpu())
    print("memory:", apm.collectMemory())
    print("fps:", apm.collectFps())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
