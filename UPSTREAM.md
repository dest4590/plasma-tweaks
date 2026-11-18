# Upstream sources and extraction

`plasma-tweaks` does not vendor KDE widget copies. At install/rebase time it extracts QML and configuration files directly from the system Plasma applet plugins:

- `tray` (`org.kde.plasma.systemtray`): extracted from `plasma/applets/org.kde.plasma.systemtray.so` (`:/qt/qml/plasma/applet/org/kde/plasma/systemtray/`) and `QPluginLoader::metaData()`.
- `microphone` (`org.kde.plasma.icontasks`): QML/config extracted from `plasma/applets/org.kde.plasma.taskmanager.so` (`:/qt/qml/plasma/applet/org/kde/plasma/taskmanager/`), paired with `plasma/plasmoids/org.kde.plasma.icontasks/metadata.json`.

## Verified builds

- **KDE Plasma 6.8.3** (Qt 6.11.2, Fedora/CachyOS-style `/usr/lib64/qt6/plugins`):
  - Resource extraction verified from `/usr/lib64/qt6/plugins/plasma/applets/org.kde.plasma.systemtray.so` (18 files + plugin metadata) and `org.kde.plasma.taskmanager.so` (24 files + `/usr/share/plasma/plasmoids/org.kde.plasma.icontasks/metadata.json`).
  - All feature patches (`tray` and `microphone`) verified to apply cleanly with exact single-match anchors.
