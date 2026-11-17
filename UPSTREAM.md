# Source snapshots

- Tray: https://github.com/dest4590/plasma-icon-tray at `83f20be949cd3b443eb55291fa7f2d5205893701`.
- Microphone: https://github.com/dest4590/plasma-microphone-icon at `25a6a45ef9d4534dd807bd6eecf3a492c4b85a72`.

Both plasmoid directories are copied unchanged. Original KDE copyright and SPDX notices are preserved.

The tray source was extracted from Plasma Workspace 6.8.2 Qt resources and updated for the BackgroundAppItem.qml change in 6.8.3. Upstream: https://invent.kde.org/plasma/plasma-workspace, applets/systemtray.

The microphone source customizes Icons-only Task Manager from https://invent.kde.org/plasma/plasma-desktop, applets/taskmanager. Its source repository does not identify the exact KDE snapshot version. The installer's version gate does not establish UI compatibility; verify on a desktop before relying on it.

Before adding a Plasma version, compare all vendored files with its embedded resources and check the plugin/QML interface. Verify tray popup lifecycle and task-manager microphone activity/mute behavior on a desktop. Do not widen the version gate based only on the Python tests.
