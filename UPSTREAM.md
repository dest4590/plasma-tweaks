# Upstream sources and extraction

`plasma-tweaks` does not vendor KDE widget copies. At install/rebase time it extracts QML and configuration files directly from the system Plasma applet plugins:

- `tray` (`org.kde.plasma.systemtray`): extracted from `plasma/applets/org.kde.plasma.systemtray.so` (`:/qt/qml/plasma/applet/org/kde/plasma/systemtray/`) and `QPluginLoader::metaData()`.
- `microphone` & `app-volume` (`org.kde.plasma.icontasks`): QML/config extracted from `plasma/applets/org.kde.plasma.taskmanager.so` (`:/qt/qml/plasma/applet/org/kde/plasma/taskmanager/`), paired with `plasma/plasmoids/org.kde.plasma.icontasks/metadata.json`.

## Verified builds

- **KDE Plasma 6.8.3** (Qt 6.11.2, Fedora/CachyOS-style `/usr/lib64/qt6/plugins`):
  - Resource extraction verified from `/usr/lib64/qt6/plugins/plasma/applets/org.kde.plasma.systemtray.so` (18 files + plugin metadata) and `org.kde.plasma.taskmanager.so` (24 files + `/usr/share/plasma/plasmoids/org.kde.plasma.icontasks/metadata.json`).
  - All feature patches (`tray`, `microphone`, `app-volume`, and `microphone + app-volume`) verified to apply cleanly with exact single-match anchors.

## Upstream conflict notes

- Plasma 6.8.3 added `wheelEnabled === 3` (`AdjustVolume`) in `taskmanager` `MouseHandler.qml` / `ConfigBehavior.qml` / `main.xml`. `app-volume` extends the existing `WheelHandler` in `MouseHandler.qml` rather than adding a competing handler, preserving normal task-wheel behavior when no output streams are present or the modifier does not match, shifting multiple streams by equal percentage points, and keeping mute state unchanged.
