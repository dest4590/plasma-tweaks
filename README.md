<p align="center">
  <img src="logo.svg" width="96" alt="plasma-tweaks">
</p>

# plasma-tweaks

Three KDE Plasma customizations with one CLI. Python 3.10+, standard library only.

Instead of bundling static copies of KDE widgets, `plasma-tweaks` extracts the QML/config resources from your installed Plasma plugins at install/rebase time, applies targeted patches, validates the staged package, and publishes local overrides.

- `tray`: compact Windows-style system tray, small icons, names on hover, and an expand arrow on the left.
- `microphone`: microphone activity indicators and mute controls in Icons-only Task Manager.
- `app-volume`: mouse wheel / touchpad volume control (5 percentage point steps, 0–100%, preserves mute state) over running tasks with output audio streams in Icons-only Task Manager, with optional `Alt` modifier and range display in tooltips.

![tray preview](features/tray/preview.png)

![microphone preview](features/microphone/preview.png)
![microphone preview](features/microphone/preview2.png)

## Requirements

- KDE Plasma 6 with `plasmashell` and `qtpaths6` (or `/usr/lib{,64}/qt6/bin/qtpaths`).
- One Qt 6 resource extractor backend (runs in a separate process loading only the trusted system `.so` plugin):
  - `PySide6` or `PyQt6` Python bindings (`python3-pyside6` / `python3-pyqt6`), **or**
  - The optional C++ helper in [helper/](helper/):
    ```sh
    cmake -S helper -B helper/build
    cmake --build helper/build
    ```
    Requires `Qt6Core` development headers and a C++17 compiler.

## Install

`all` installs all three features (`tray`, `microphone`, `app-volume`):

```sh
git clone https://github.com/dest4590/plasma-tweaks.git
cd plasma-tweaks
./plasma-tweaks install all --restart
```

Or install individual features:

```sh
./plasma-tweaks install tray --restart
./plasma-tweaks install microphone app-volume --restart
./plasma-tweaks status
./plasma-tweaks doctor
```

Run as your desktop user, without `sudo`. `--restart` restarts `plasma-plasmashell.service` (briefly hides the panel). Without it, files are staged and published, and take effect on next login.

`microphone` and `app-volume` both customize `org.kde.plasma.icontasks` and are composed into a single local override. Uninstalling one rebuilds `org.kde.plasma.icontasks` with only the remaining feature.

## Update, Rebase, and Remove

```sh
./plasma-tweaks rebase --restart
./plasma-tweaks uninstall microphone --restart
./plasma-tweaks uninstall all --restart
```

- `rebase` rebuilds your `desired` features from the current system Plasma plugins (never enables new features).
- `doctor` is read-only: it reports detected Plasma/Qt6 paths, extractor backend, source artifact SHA-256 status, `desired`/`active`/`disabled` state, other systemd drop-ins, and pre-start hook coverage.
- `uninstall` restores the pre-installation backup (including any pre-existing user override or launcher symlink). If a pre-existing user override is restored, `plasma-tweaks` warns you to check its compatibility with your current Plasma version.

## How loading and update protection work

System Plasma applets (`org.kde.plasma.systemtray.so` and `org.kde.plasma.taskmanager.so`) embed upstream QML in Qt resources (`:/qt/qml/plasma/applet/...`). To load the patched local QML from `$XDG_DATA_HOME/plasma/plasmoids/` instead of the embedded resources while still using the system C++ applet code, `plasma-tweaks` sets `X-Plasma-RootPath` to `org.local.icontray` / `org.local.taskmanager` and copies the system `.so` into `$XDG_DATA_HOME/plasma-tweaks-plugins/<pkg>/plasma/applets/org.local.<name>.so` exposed via `QT_PLUGIN_PATH`.

Both `$XDG_CONFIG_HOME/systemd/user/plasma-plasmashell.service.d/zz-plasma-tweaks.conf` and `~/.local/bin/plasmashell` invoke `plasma-tweaks preflight` before `plasmashell` starts:

- If source plugin/metadata SHA-256 hashes are unchanged, `preflight` exits immediately.
- If KDE was updated, `preflight` attempts to rebuild `desired` features from the new resources.
- If a package is incompatible with the new KDE resources, `preflight` disables only the affected override so the stock system widget is used and `plasmashell` still starts normally.

If your session does not use `plasma-plasmashell.service` and `~/.local/bin` is not ahead of `/usr/bin` in `PATH`, uninstall before upgrading Plasma and check `./plasma-tweaks doctor`.

## App-volume notes

Plasma 6.8.3 introduced an upstream `AdjustVolume` option in `wheelEnabled`, which replaces task switching globally, scales deltas by `stream.volume / loudest` (leaving 0% streams at 0%), and auto-mutes at 0%. `app-volume` extends `MouseHandler.qml` and `ToolTipInstance.qml` instead of adding a second `WheelHandler`: when `appVolumeEnabled` is enabled (default) and the configured modifier (`None` by default, or `Alt`) matches over a task with output streams, scrolling adjusts each stream by 5 percentage points without changing mute state or switching tasks; otherwise normal `wheelEnabled` behavior applies.

## Development

```sh
python3 -m unittest discover -s tests -v
```

## Licensing

Original KDE copyright and SPDX notices are preserved. See [UPSTREAM.md](UPSTREAM.md) and `LICENSES/`. The CLI, helper, and patch/JS additions are GPL-2.0-or-later.
