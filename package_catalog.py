# SPDX-License-Identifier: GPL-2.0-or-later
"""System applets and their ordered feature overlays."""

FEATURE_ORDER = ("tray", "tray-hover", "microphone", "launcher")
PACKAGES = {
    "tray": {
        "applet": "org.kde.plasma.systemtray",
        "plugin": "org.local.icontray",
        "system_plugin": "org.kde.plasma.systemtray.so",
        "resource_prefix": ":/qt/qml/plasma/applet/org/kde/plasma/systemtray/",
        "patches": {"tray": "tray", "tray-hover": "tray-hover"},
    },
    "icontasks": {
        "applet": "org.kde.plasma.icontasks",
        "plugin": "org.local.taskmanager",
        "system_plugin": "org.kde.plasma.taskmanager.so",
        "resource_prefix": ":/qt/qml/plasma/applet/org/kde/plasma/taskmanager/",
        "patches": {"microphone": "microphone", "launcher": "launcher/icontasks"},
        "metadata_key": "icontasks_metadata",
    },
    "launcher": {
        "applet": "org.kde.plasma.kickoff",
        "plugin": "org.local.kickoff",
        "system_plugin": "org.kde.plasma.kickoff.so",
        "resource_prefix": ":/qt/qml/plasma/applet/org/kde/plasma/kickoff/",
        "patches": {"launcher": "launcher"},
    },
}


def packages_for(features: list[str]) -> set[str]:
    return {
        pkg
        for pkg, info in PACKAGES.items()
        if any(f in features for f in info["patches"])
    }
