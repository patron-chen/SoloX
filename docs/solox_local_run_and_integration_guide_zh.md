# SoloX 本地源码运行与集成指南

## 1. 背景与目标

本文记录如何在本机 conda 环境 `testing_metrics` 中，基于当前 clone 下来的 SoloX 源码完成安装、UI 启动、Python API 调用验证，以及后续集成建议。

本文不使用 `pip install solox` 安装 PyPI 发布版。所有安装与运行均基于当前目录源码：

```bash
/Users/qingyun/Code/game_test/SoloX
```

## 2. 当前项目结构概览

已实际检查的关键文件：

```bash
README.md
README.zh.md
FAQ.md
DocForAndroid.md
setup.py
setup.cfg
MANIFEST.in
solox/__main__.py
solox/web.py
solox/view/apis.py
solox/view/pages.py
solox/public/apm.py
solox/public/common.py
solox/public/adb.py
```

源码确认结果：

- Python 包名是 `solox`，当前版本在 `solox/__init__.py` 中为 `2.9.3`。
- 默认 UI 入口是 `python -m solox`。
- `solox/__main__.py` 使用 `fire.Fire(main)` 调用 `solox.web.main`。
- Web UI 使用 Flask，入口对象在 `solox/web.py` 中：
  - `app = Flask(...)`
  - 注册 `solox.view.apis.api`
  - 注册 `solox.view.pages.page`
- Python API 主要在：
  - `solox.public.apm.AppPerformanceMonitor`
  - `solox.public.common.Devices`
  - `solox.public.common.Platform`
- 服务 API 入口主要在 `solox/view/apis.py`，例如：
  - `/device/info`
  - `/package/pids`
  - `/apm/initialize`
  - `/apm/collect`
- 当前仓库没有 `requirements.txt`、`requirements-dev.txt`、`pyproject.toml`。
- 依赖声明在 `setup.py` 的 `install_requires` 中。
- `setup.cfg` 中写了 `console_scripts = solox = solox.__main__:main`，但当前 `setup.py` 未读取该配置。本次安装后实际验证 `solox --help` 不可用，因此应使用 `python -m solox`。

## 3. Conda 环境准备

已实际验证当前 shell 激活的是 `base`，不是 `testing_metrics`：

```bash
conda info --envs
```

输出中 `base` 带 `*`，同时存在目标环境：

```text
testing_metrics        /opt/homebrew/Caskroom/miniconda/base/envs/testing_metrics
```

如果需要手动激活环境，使用：

```bash
conda activate testing_metrics
```

本文实际执行命令时主要使用 `conda run`，避免依赖当前 shell 激活状态：

```bash
conda run -n testing_metrics python --version
```

已实际验证 Python 版本：

```text
Python 3.11.15
```

项目 `setup.py` 声明：

```python
python_requires=">=3.10"
```

因此 `testing_metrics` 的 Python 3.11.15 满足要求。

## 4. 基于当前源码安装 solox

当前仓库没有 requirements 文件，应直接从当前源码 editable install：

```bash
conda run -n testing_metrics python -m pip install -e .
```

第一次在沙箱内执行时失败，根因是网络受限，pip 无法下载构建依赖 `setuptools>=40.8.0`：

```text
Failed to establish a new connection
No matching distribution found for setuptools>=40.8.0
```

放开网络后重新执行同一命令，已实际安装成功。安装结果包含：

```text
Successfully installed ... solox-2.9.3 ...
```

验证当前安装指向本地源码：

```bash
conda run -n testing_metrics python -c "import solox, sys; print(solox.__version__); print(solox.__file__); print(sys.version)"
```

已实际输出：

```text
2.9.3
/Users/qingyun/Code/game_test/SoloX/solox/__init__.py
3.11.15 ...
```

验证 pip editable location：

```bash
conda run -n testing_metrics python -m pip show solox
```

已实际确认：

```text
Name: solox
Version: 2.9.3
Editable project location: /Users/qingyun/Code/game_test/SoloX
```

## 5. 默认 UI 启动与验证

源码确认的默认 UI 启动方式：

```bash
conda run -n testing_metrics python -m solox
```

建议本地调试时显式绑定 localhost 和端口：

```bash
conda run -n testing_metrics python -m solox --host=127.0.0.1 --port=50003
```

已实际用上述命令启动 UI，并通过 HTTP 验证：

```bash
conda run -n testing_metrics python -c "import requests; r=requests.get('http://127.0.0.1:50003/?platform=Android&lan=en', timeout=5); print(r.status_code); print(r.url); print(r.text[:160].replace('\n',' '))"
```

已实际输出：

```text
200
http://127.0.0.1:50003/?platform=Android&lan=en
<!doctype html> ...
```

访问地址：

```text
http://127.0.0.1:50003/?platform=Android&lan=en
```

注意事项：

- UI 服务本身可以启动。
- Android/iOS 设备相关功能依赖外部设备连接。
- 在受限沙箱中，ADB daemon 监听 `tcp:5037` 会被系统拒绝，错误形如 `could not install *smartsocket* listener: Operation not permitted`。在非沙箱/放权命令下，本机可以识别 Android 设备。
- `python -m solox` 会尝试打开浏览器；服务验证更可靠的方式是请求本地 HTTP 地址。

已实际验证服务 API：

```bash
conda run -n testing_metrics python -c "import requests; r=requests.get('http://127.0.0.1:50003/apm/initialize', timeout=10); print(r.status_code); print(r.text)"
```

输出：

```text
200
{"msg":"initialize env success","status":1}
```

Android 设备信息接口已实际验证。本机当前连接到一台 Android 设备：

```text
I76XGQ5D7T5LBQVC(PKB110)
```

iOS 设备信息接口已实际验证，当前无 iOS 设备：

```text
{"msg":"no devices","status":0}
```

## 6. Python API 调用方式

源码确认的主要 Python API：

```python
from solox.public.apm import AppPerformanceMonitor
from solox.public.common import Devices, Platform
```

关键行为：

- `Devices().getDeviceIds()` 获取 Android 设备 ID。
- `Devices().getPid(deviceId, pkgName)` 获取 Android 包名对应进程。
- `AppPerformanceMonitor(...)` 初始化时会立即调用 `devicesCheck`。
- 因此真实采集必须满足：
  - Android 设备已连接并授权 ADB；
  - 目标 app 已安装；
  - 对 CPU、Memory、Network、FPS 等指标，目标 app 进程需要存活；
  - iOS 设备需要 tidevice 能识别，且部分 iOS 能力受系统版本和开发者镜像影响。

已实际验证 Python API 对 Android 设备采集 CPU 和 Memory：

```bash
conda run -n testing_metrics python -c "from solox.public.apm import AppPerformanceMonitor; apm=AppPerformanceMonitor(pkgName='com.android.systemui', platform='Android', deviceId='I76XGQ5D7T5LBQVC', surfaceview=True, noLog=True, pid='3264', record=False, collect_all=False); print('cpu', apm.collectCpu()); print('memory', apm.collectMemory())"
```

已实际输出示例：

```text
cpu {'appCpuRate': 0.91, 'systemCpuRate': 40.8}
memory {'total': 786.56, 'swap': 225.16}
```

服务 API `/apm/collect` 也已实际验证：

```bash
conda run -n testing_metrics python -c "import requests; params={'platform':'Android','deviceid':'I76XGQ5D7T5LBQVC','pkgname':'com.android.systemui','target':'cpu'}; r=requests.get('http://127.0.0.1:50003/apm/collect', params=params, timeout=15); print(r.status_code); print(r.text)"
```

输出：

```text
200
{"appCpuRate":0.66,"status":1,"systemCpuRate":10.58}
```

## 7. 最小 API 示例代码

已新增示例脚本：

```bash
examples/solox_api_minimal_demo.py
```

运行方式：

```bash
conda run -n testing_metrics python examples/solox_api_minimal_demo.py
```

脚本行为：

- 导入当前源码安装的 `solox` API。
- 自动查找 Android 设备。
- 优先选择常见常驻进程：
  - `com.android.systemui`
  - `com.android.settings`
  - `com.coloros.assistantscreen`
- 找到进程后采集 CPU 和 Memory。
- 如果没有 Android 设备，则只验证 import 和 helper 初始化，然后正常退出。

已实际运行成功，输出示例：

```text
solox service switch: on
device: I76XGQ5D7T5LBQVC
package: com.android.systemui
pid: 3264
cpu: {'appCpuRate': 1.0, 'systemCpuRate': 8.3}
memory: {'total': 741.41, 'swap': 222.17}
```

## 8. 设备与系统依赖要求

根据 README、FAQ 和源码确认：

- Python：`>=3.10`。
- Android：
  - 需要 ADB。
  - SoloX 包内带有 `solox/public/adb/...`，但 FAQ 明确建议自行安装 Android Platform Tools 并配置环境变量，因为内置 adb 不一定适配所有电脑。
  - 本机实际检测到 `/opt/homebrew/bin/adb`。
  - Android 指标采集要求设备已连接、已授权 USB 调试。
- iOS：
  - 依赖 `tidevice==0.9.7`。
  - README/FAQ 说明 Windows 测 iOS 需要 iTunes。
  - FAQ 说明不支持 iOS 17，且 tidevice 兼容性可能受设备和支持包影响。
- FPS：
  - Android 支持 SurfaceView 和 gfxinfo 两种方式。
  - gfxinfo 方式需要手机开发者选项中启用 GPU 渲染相关配置。
- GPU：
  - Android 只支持部分高通芯片设备。
  - 本次连接设备 `PKB110` 的硬件平台为 `mt6991`，`/sys/class/devfreq` 下暴露的是 `48000000.mali`，不是高通 KGSL。
  - SoloX 当前 Android GPU 实现只读取 `/sys/class/kgsl/kgsl-3d0/gpubusy`，因此这台设备 GPU 指标无法采集。
- 录屏：
  - Android 录屏依赖 scrcpy。
  - FAQ 建议 macOS 可自行安装 `scrcpy`。

不要盲目安装系统依赖。建议先用以下命令检查：

```bash
adb devices
conda run -n testing_metrics python -m tidevice list
scrcpy --version
```

## 9. 常见问题与排查

### `solox --help` 不可用

已实际验证：

```text
solox: command not found
```

原因：`setup.cfg` 声明了 console script，但当前 `setup.py` 没读取该配置。使用：

```bash
conda run -n testing_metrics python -m solox --host=127.0.0.1 --port=50003
```

### pip 安装失败，提示无法下载 setuptools

原因是网络受限，不是项目源码问题。需要允许 pip 访问包索引后重试：

```bash
conda run -n testing_metrics python -m pip install -e .
```

### ADB 报 `Operation not permitted`

在受限沙箱中，ADB daemon 不能监听本地端口 `5037`。在普通终端或已放权命令中重新验证：

```bash
adb devices
conda run -n testing_metrics python -c "from solox.public.common import Devices; print(Devices().getDeviceIds())"
```

### UI 能启动，但页面没有设备

检查：

```bash
adb devices
```

Android 设备必须显示为 `device` 状态。如果是 `unauthorized`，需要在手机上确认 USB 调试授权。

### API 初始化失败或提示 no process found

`AppPerformanceMonitor` 初始化时会检查设备和进程。CPU、Memory、Network、FPS 等指标需要目标 app 进程正在运行。

先查进程：

```bash
conda run -n testing_metrics python -c "from solox.public.common import Devices; d=Devices(); device=d.getDeviceIds()[0]; print(d.getPid(device, 'com.android.systemui'))"
```

### FPS 自动选择模式

本次用 `com.android.settings` 复现并定位：

- 当前前台不是目标应用时，FPS 很容易为 0。先把目标应用拉到前台。
- `surfaceview=True` 适合 SurfaceView/BLAST 场景；`com.android.settings` 是普通 Activity，本次验证强制 true 返回 `{"fps": 0, "jank": 0}`。
- `surfaceview=False` 走 `dumpsys gfxinfo <pkg> framestats`，本次对 Settings 可返回非 0，例如 `{"fps": 120, "jank": 0}`。
- 已将 Python API 和 `/apm/fps` 的默认 FPS 模式改为 `auto`：先尝试 `surfaceview=True`，如果没有有效 FPS，再自动回退到 `surfaceview=False`。
- 已修复 `/apm/fps` 路由内部 `FPS.getObject()` 缓存复用问题：Android FPS 缓存现在按 `pkgName/deviceId/platform/surfaceview` 区分，避免 `surv=true` 与 `surv=false` 切换时复用错误对象。
- 已修复 `solox.public.android_fps.collect_fps/collect_jank` 全局值复用问题：每次 FPSMonitor 启动前会清零，避免失败路径沿用上一次采集结果。

推荐 Settings 验证方式：

```bash
adb -s I76XGQ5D7T5LBQVC shell monkey -p com.android.settings -c android.intent.category.LAUNCHER 1
conda run -n testing_metrics python examples/solox_validate_settings_metrics.py
```

如果需要强制指定 FPS 路径，可以显式传参：

```text
/apm/fps?...&surv=auto
/apm/fps?...&surv=true
/apm/fps?...&surv=false
```

本次还用 `com.tencent.tmgp.pubgmhd` 验证了游戏 SurfaceView 场景。Android 16 / BLAST SurfaceView 的 `dumpsys SurfaceFlinger --list` 输出形如：

```text
RequestedLayerState{b3b1ac SurfaceView[com.tencent.tmgp.pubgmhd/com.epicgames.ue4.GameActivity](BLAST)#1055656 ...}
```

旧逻辑只匹配 `line.startswith('SurfaceView')`，会选到普通 Activity layer，latency 数据全为 0。已增强 `solox/public/android_fps.py`：

- 兼容 `RequestedLayerState{...}` 包裹格式。
- 优先选择包含 `SurfaceView` 且包含 `(BLAST)` 的 layer。
- 对候选 layer 先执行 `dumpsys SurfaceFlinger --latency`，只使用有有效帧时间戳的 layer。
- 对包含空格、方括号、括号的 layer 使用更安全的 adb shell quoting，避免 layer 名称被 shell 拆开。

已实际验证 PUBG FPS：

```text
/apm/fps?...pkgname=com.tencent.tmgp.pubgmhd
{"fps":30,"jank":0,"status":1}

/apm/fps?...pkgname=com.tencent.tmgp.pubgmhd&surv=true
{"fps":30,"jank":0,"status":1}

/apm/fps?...pkgname=com.tencent.tmgp.pubgmhd&surv=false
{"fps":0,"jank":4,"status":1}
```

已实际验证 Settings FPS：

```text
/apm/fps?...pkgname=com.android.settings
{"fps":20,"jank":1,"status":1}

/apm/fps?...pkgname=com.android.settings&surv=true
{"fps":0,"jank":0,"status":1}

/apm/fps?...pkgname=com.android.settings&surv=false
{"fps":20,"jank":1,"status":1}
```

### GPU 始终无数据

本次用 `PKB110` 设备定位到根因是设备不支持当前 SoloX Android GPU 采集路径：

```bash
adb -s I76XGQ5D7T5LBQVC shell 'ls -l /sys/class/kgsl /sys/class/kgsl/kgsl-3d0/gpubusy /sys/class/devfreq 2>&1 | head -80'
```

已实际输出关键信息：

```text
ls: /sys/class/kgsl: No such file or directory
ls: /sys/class/kgsl/kgsl-3d0/gpubusy: No such file or directory
/sys/class/devfreq/48000000.mali -> .../48000000.mali
```

SoloX 当前源码：

```python
cmd = 'cat /sys/class/kgsl/kgsl-3d0/gpubusy'
```

因此高通 KGSL 以外的 GPU，例如本机这台 MTK/Mali 设备，不会有 GPU 数据。`/apm/gpu` 接口会捕获异常并返回 `{"gpu":0,"status":1}`，Python API 直接调用会抛出 `ValueError: invalid literal for int() with base 10: ''`。

### Thermal 返回 None

本次设备存在 `thermal_zone`，但普通 adb shell 读取 `type/temp` 被拒绝：

```bash
adb -s I76XGQ5D7T5LBQVC shell 'cat /sys/class/thermal/thermal_zone0/type 2>&1; cat /sys/class/thermal/thermal_zone0/temp 2>&1'
```

已实际输出：

```text
cat: /sys/class/thermal/thermal_zone0/type: Permission denied
cat: /sys/class/thermal/thermal_zone0/temp: Permission denied
```

所以 `collectThermal()` 返回 `None`，这是设备权限限制，不是 conda 环境安装问题。

### iOS 无设备

本次实际验证 iOS 返回：

```text
{"msg":"no devices","status":0}
```

后续需要连接 iOS 设备后再验证：

```bash
conda run -n testing_metrics python -m tidevice list
```

## 10. 集成到自有项目的推荐方案

推荐方案：先作为本地 path dependency 或 git submodule 集成，再在自有项目中封装一层内部 metrics 模块。

推荐原因：

- SoloX 当前 API 与设备、ADB、tidevice、报告目录、全局配置文件耦合较强。
- 直接复制源码不利于后续同步上游修复。
- 直接依赖 PyPI 发布版不符合当前目标，也不便于调试本地源码。
- 封装内部 service 可以隔离 SoloX 的外部依赖和不稳定细节。

建议目录组织：

```text
your-project/
  third_party/
    SoloX/                  # git submodule 或固定源码目录
  your_project/
    metrics/
      solox_client.py       # 封装 AppPerformanceMonitor 或 HTTP API
      device_probe.py       # 统一设备发现与校验
      config.py             # 设备、包名、输出路径配置
  reports/
    solox/
```

依赖隔离建议：

- 为 metrics 采集单独使用 conda env 或 virtualenv。
- 使用 `pip install -e ./third_party/SoloX` 安装本地源码。
- 锁定 `setup.py` 中的关键依赖版本，尤其是：
  - `Flask-SocketIO==4.3.1`
  - `python-engineio==3.13.2`
  - `python-socketio==4.6.0`
  - `Werkzeug==2.0.3`
  - `Jinja2==3.0.1`
  - `tidevice==0.9.7`

在自有项目中 import：

```python
from solox.public.apm import AppPerformanceMonitor
from solox.public.common import Devices, Platform
```

推荐封装方式：

- 对外只暴露 `collect_cpu`、`collect_memory`、`collect_network` 等业务函数。
- 在封装层中处理设备 ID、包名、进程选择、异常和重试。
- 不要让业务代码直接依赖 SoloX 内部类过多细节。
- 将输出目录、报告目录、目标 app 包名写入自有项目配置。
- CI/CD 中把 ADB/tidevice/scrcpy 检查作为前置步骤。

## 11. 后续改造建议

根据源码和本次验证，建议后续小步改造：

- 修正 packaging 配置，让 `setup.cfg` 的 console script 生效，或在 `setup.py` 中显式声明 `entry_points`。
- 为 `AppPerformanceMonitor` 增加可选的 lazy device check，便于无设备环境做 import 和配置验证。
- 将报告目录从 `os.getcwd()/report` 改为可配置参数，方便集成项目管理输出。
- 将 ADB 探测从 import 阶段延迟到实际调用阶段，减少无设备环境或受限环境下的副作用。
- 为 `/apm/collect` 的 GPU 分支补测试；源码中 `GPU(pkgname=pkgname)` 与 `GPU.__init__(pkgName, deviceId, platform=...)` 参数名不一致，可能存在运行问题。
- 增加最小单元测试覆盖 `Devices`、`AppPerformanceMonitor` 参数校验和 Flask API 空设备返回。

## 12. 已验证命令清单

环境检查：

```bash
conda info --envs
conda run -n testing_metrics python --version
conda run -n testing_metrics python -m pip --version
```

源码安装：

```bash
conda run -n testing_metrics python -m pip install -e .
```

安装验证：

```bash
conda run -n testing_metrics python -c "import solox, sys; print(solox.__version__); print(solox.__file__); print(sys.version)"
conda run -n testing_metrics python -m pip show solox Flask Werkzeug Jinja2 Flask-SocketIO tidevice
conda run -n testing_metrics python -m pip list --format=columns
```

UI 启动：

```bash
conda run -n testing_metrics python -m solox --host=127.0.0.1 --port=50003
```

UI HTTP 验证：

```bash
conda run -n testing_metrics python -c "import requests; r=requests.get('http://127.0.0.1:50003/?platform=Android&lan=en', timeout=5); print(r.status_code); print(r.url); print(r.text[:160].replace('\n',' '))"
```

服务 API 验证：

```bash
conda run -n testing_metrics python -c "import requests; r=requests.get('http://127.0.0.1:50003/apm/initialize', timeout=10); print(r.status_code); print(r.text)"
conda run -n testing_metrics python -c "import requests; r=requests.get('http://127.0.0.1:50003/device/info?platform=Android', timeout=10); print(r.status_code); print(r.text[:500])"
conda run -n testing_metrics python -c "import requests; r=requests.get('http://127.0.0.1:50003/device/info?platform=iOS', timeout=10); print(r.status_code); print(r.text[:500])"
```

Python API 验证：

```bash
conda run -n testing_metrics python examples/solox_api_minimal_demo.py
conda run -n testing_metrics python examples/solox_validate_settings_metrics.py
```

服务采集 API 验证：

```bash
conda run -n testing_metrics python -c "import requests; params={'platform':'Android','deviceid':'I76XGQ5D7T5LBQVC','pkgname':'com.android.systemui','target':'cpu'}; r=requests.get('http://127.0.0.1:50003/apm/collect', params=params, timeout=15); print(r.status_code); print(r.text)"
```

本次仍未完成的验证：

- iOS 真机采集：当前未连接 iOS 设备。
- Android `com.android.settings` 已逐项验证 CPU、Memory、MemoryDetail、Network、FPS、Battery、Disk、Thermal、GPU。
- Network 对 Settings 返回 `0` 或很小的流量值，因为采集窗口内 Settings 基本不产生 Wi-Fi 流量；这不是网络采集链路报错。
- GPU 在本机 `PKB110` 上无法采集，原因是设备为 MTK/Mali，缺少 SoloX 当前代码需要的 KGSL 节点。
- Thermal 在本机 `PKB110` 上无法采集，原因是 thermal sysfs 节点普通 adb shell 无读取权限。
- 录屏：未验证 scrcpy。
- 生产部署：当前只验证 Flask 开发服务器，不建议直接作为生产 WSGI 服务使用。
