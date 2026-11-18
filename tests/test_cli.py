import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
from importlib.machinery import SourceFileLoader

loader = SourceFileLoader("cli", str(ROOT / "plasma-tweaks"))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
cli = importlib.util.module_from_spec(spec)
loader.exec_module(cli)


def make_fake_raw_systemtray(out_dir: Path, extra_line: str = "") -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "CompactApplet.qml").write_text(
        "import QtQuick\nimport org.kde.plasma.plasmoid\nItem {\n"
        "    location: if ((plasmoidItem?.parent as AbstractItem)?.inHiddenLayout && Plasmoid.location !== PlasmaCore.Types.LeftEdge) {\n"
        "    property PlasmoidItem plasmoidItem\n}\n"
    )
    (out_dir / "AbstractItem.qml").write_text(
        "import QtQuick\nItem {\n"
        "            readonly property int size: abstractItem.inVisibleLayout ? root.itemSize : Kirigami.Units.iconSizes.medium\n"
        "            visible: abstractItem.inHiddenLayout\n}\n"
    )
    (out_dir / "ExpandedRepresentation.qml").write_text(
        "import QtQuick\nItem {\n"
        "    Layout.minimumWidth: Kirigami.Units.gridUnit * 24\n"
        "    Layout.minimumHeight: Kirigami.Units.gridUnit * 24\n"
        "        height: trayHeading.height + bottomPadding + container.headingHeight\n"
        "        spacing: plasmoidHeading.bottomPadding\n"
        "        RowLayout {\n            id: trayHeading\n"
        "                level: 1\n                text: systemTrayState.activeApplet\n"
        "            Layout.fillHeight: true\n            Layout.topMargin: Kirigami.Units.smallSpacing\n            visible: !systemTrayState.activeApplet\n}\n"
    )
    (out_dir / "HiddenItemsView.qml").write_text(
        "import QtQuick\nItem {\n"
        "    background: null\n"
        "        readonly property int columns: 2\n"
        "        readonly property int delegateHeight: (metrics.height * delegateMaxTextLines) + (delegateMargins * 2)\n"
        "        cellWidth: Math.floor(hiddenTasksView.availableWidth / columns)\n"
        "        currentIndex: -1\n"
        "        readonly property int itemCount: model.count\n}\n"
    )
    (out_dir / "main.qml").write_text(
        f"import QtQuick\n{extra_line}Item {{\n"
        "                Layout.row: root.vertical && root.reverseLayout ? 1 : 0 // Explicitly define grid coordinates\n"
        "                Layout.column: 0                                        // to prevent overlapping\n"
        "                Layout.row: root.vertical && !root.reverseLayout ? 1 : 0 // Explicitly define grid coordinates\n"
        "                Layout.column: root.vertical ? 0 : 1                     // to prevent overlapping\n}\n"
    )
    (out_dir / "Unmodified.qml").write_text(f"// upstream\n{extra_line}Item {{}}\n")
    (out_dir / "main.xml").write_text("<kcfg><group name=\"General\"/></kcfg>\n")
    (out_dir / "config.qml").write_text("import QtQuick\nItem {}\n")
    (out_dir / "_plugin_metadata.json").write_text(
        json.dumps({"KPlugin": {"Name": "System Tray"}}) + "\n"
    )


def make_fake_raw_taskmanager(out_dir: Path, extra_line: str = "") -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "main.qml").write_text(f"import QtQuick\n{extra_line}Item {{}}\n")
    (out_dir / "Unmodified.qml").write_text(f"// upstream\n{extra_line}Item {{}}\n")
    (out_dir / "config.qml").write_text("import QtQuick\nItem {}\n")
    (out_dir / "main.xml").write_text(
        '<kcfg><group name="General">\n'
        '    <entry name="wheelSkipMinimized" type="Bool">\n'
        "      <label>Whether to skip minimized tasks when switching between them using the mouse wheel.</label>\n"
        "      <default>true</default>\n"
        "    </entry>\n"
        "</group></kcfg>\n"
    )
    (out_dir / "ContextMenu.qml").write_text(
        "import QtQuick\nItem {\n"
        "            if (!(menu.visualParent as Task).hasAudioStream) {\n"
        '            muteItem.icon = "audio-volume-muted" + (Application.layoutDirection === Qt.RightToLeft ? "-rtl" : "");\n'
        "            menu.addMenuItem(muteItem, startNewInstanceItem);\n\n"
        "            menu.addMenuItem(newSeparator(menu), startNewInstanceItem);\n        }\n}\n"
    )
    (out_dir / "PulseAudio.qml").write_text(
        "import QtQuick\nQtObject {\n"
        "    signal streamsChanged()\n"
        "            streamsChanged();\n"
        "    function findStreams(key: string, value: var): /*[QtObject]*/ var {\n"
        "        return findStreamsFn(stream => stream[key] === value);\n    }\n\n"
        "    function findStreamsFn(fn: var): var {\n"
        "        const streams = [];\n"
        "        for (let i = 0, count = instantiator.count; i < count; ++i) {\n"
        "            const stream = instantiator.objectAt(i);\n"
        "            if (fn(stream)) {\n"
        "                streams.push(stream);\n"
        "            }\n        }\n        return streams;\n    }\n\n"
        "    function streamsForAppId(appId: string): /*[QtObject]*/ var {\n"
        '        return findStreams("portalAppId", appId);\n    }\n\n'
        "    function streamsForAppName(appName: string): /*[QtObject]*/ var {\n"
        '        return findStreams("appName", appName);\n    }\n\n'
        "    function streamsForPid(pid: int): /*[QtObject]*/ var {\n"
        "        // skip stream that has portalAppId\n"
        "        // app using portal may have a sandbox pid\n"
        "        const streams = findStreamsFn(stream => stream.pid === pid && !stream.portalAppId);\n\n"
        "        if (streams.length === 0) {\n"
        "            for (let i = 0, length = instantiator.count; i < length; ++i) {\n"
        "                const stream = instantiator.objectAt(i) as StreamDelegate;\n"
        "        return streams;\n    }\n\n"
        "    // QtObject has no default property, hence adding the Instantiator to one explicitly.\n"
        "    readonly property Instantiator instantiator: Instantiator {\n"
        "        model: PlasmaPa.PulseObjectFilterModel {\n"
        '            filters: [ { role: "VirtualStream", value: false } ]\n'
        "            sourceModel: PlasmaPa.SinkInputModel {}\n"
        "        }\n\n"
        "        component StreamDelegate: QtObject {\n"
        "            id: delegate\n"
        "            required property var model\n"
        '            readonly property int pid: model.Client?.properties["application.process.id"] ?? 0\n'
        "            // Determined on demand.\n"
        "            property int parentPid: -1\n"
        '            readonly property string appName: model.Client?.properties["application.name"] ?? ""\n'
        '            readonly property string portalAppId: model.Client?.properties["pipewire.access.portal.app_id"] ?? ""\n'
        "            readonly property bool muted: model.Muted\n"
        "            // whether there is nothing actually going on on that stream\n"
        "            readonly property bool corked: model.Corked\n"
        "            readonly property int volume: model.Volume\n\n"
        "            function mute(): void {\n                model.Muted = true;\n            }\n"
        "            function unmute(): void {\n                model.Muted = false;\n            }\n        }\n\n"
        "        delegate: StreamDelegate { }\n\n"
        "        onObjectAdded: (index, object) => pulseAudio.streamsChanged()\n"
        "        onObjectRemoved: (index, object) => pulseAudio.streamsChanged()\n"
        "    }\n}\n"
    )
    (out_dir / "Task.qml").write_text(
        "import QtQuick\nItem {\n"
        "    property Item audioStreamIcon: null\n"
        "    property var audioStreams: []\n"
        "    readonly property bool hasAudioStream: audioStreams.length > 0\n"
        "    readonly property bool playingAudio: hasAudioStream && audioStreams.some(item => !item.corked)\n"
        "    readonly property bool muted: hasAudioStream && audioStreams.every(item => item.muted)\n"
        "    onPidChanged: updateAudioStreams({delay: false})\n"
        "    onAppNameChanged: updateAudioStreams({delay: false})\n\n"
        "    onIsWindowChanged: {\n        if (model.IsWindow) {\n            taskInitComponent.createObject(task);\n            updateAudioStreams({delay: false});\n        }\n    }\n"
        "    onAudioIndicatorsEnabledChanged: task.hasAudioStreamChanged()\n"
        "    function updateAudioStreams(args: var): void {\n"
        "        if (args) {\n"
        "            // When the task just appeared (e.g. virtual desktop switch), show the audio indicator\n"
        "            // right away. Only when audio streams change during the lifetime of this task, delay\n"
        "            // showing that to avoid distraction.\n"
        "            delayAudioStreamIndicator = !!args.delay;\n        }\n\n"
        "        var pa = pulseAudio.item;\n"
        "        if (!pa || !task.isWindow) {\n            task.audioStreams = [];\n            return;\n        }\n\n"
        "        var streams = [];\n\n"
        "        // Check appid first for app using portal\n"
        "        // https://docs.pipewire.org/page_portal.html\n"
        "        if (task.appId) {\n            streams = pa.streamsForAppId(task.appId);\n        }\n\n"
        "        if (!streams.length) {\n            streams = pa.streamsForPid(model.AppPid);\n            if (streams.length) {\n                pa.registerPidMatch(model.AppName);\n            } else {\n"
        "                // We only want to fall back to appName matching if we never managed to map\n"
        "                // a PID to an audio stream window. Otherwise if you have two instances of\n"
        "                // an application, one playing and the other not, it will look up appName\n"
        "                // for the non-playing instance and erroneously show an indicator on both.\n"
        "                if (!pa.hasPidMatch(model.AppName)) {\n                    streams = pa.streamsForAppName(model.AppName);\n                }\n            }\n        }\n\n        task.audioStreams = streams;\n    }\n"
        "    function toggleMuted(): void {\n        if (muted) {\n            task.audioStreams.forEach(item => item.unmute());\n        } else {\n            task.audioStreams.forEach(item => item.mute());\n        }\n    }\n"
        "        function onStreamsChanged(): void {\n            task.updateAudioStreams({delay: true})\n        }\n"
        "            component.createObject(task);\n            component.destroy();\n            updateAudioStreams({delay: false});\n        }\n\n        if (!inPopup && !model.IsWindow) {\n}\n"
    )
    (out_dir / "ConfigBehavior.qml").write_text(
        "import QtQuick\nItem {\n"
        "    property alias cfg_wheelSkipMinimized: wheelSkipMinimized.checked\n"
        "        QQC2.CheckBox {\n            id: wheelSkipMinimized\n"
        "            leftPadding: mirrored ? 0 : (wheelEnabled.indicator.width + wheelEnabled.spacing)\n"
        "            rightPadding: mirrored ? (wheelEnabled.indicator.width + wheelEnabled.spacing) : 0\n"
        '            text: i18nc("@option:check mouse wheel task cycling", "Skip minimized tasks")\n'
        "            enabled: wheelEnabled.currentIndex !== 0 // None\n        }\n}\n"
    )
    (out_dir / "MouseHandler.qml").write_text(
        "import QtQuick\nimport plasma.applet.org.kde.plasma.taskmanager as TaskManagerApplet\nDropArea {\n"
        "    WheelHandler {\n        id: wheelHandler\n\n"
        "        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad\n\n"
        "        property bool handleWheelEvents: true\n\n"
        "        enabled: handleWheelEvents && Plasmoid.configuration.wheelEnabled !== 0\n\n"
        "        onWheel: event => {\n"
        '            // magic number 15 for common "one scroll"\n'
        "            // See https://doc.qt.io/qt-6/qml-qtquick-wheelhandler.html#rotation-prop\n"
        "            let increment = 0;\n"
        "            while (rotation >= 15) {\n                rotation -= 15;\n                increment++;\n            }\n"
        "            while (rotation <= -15) {\n                rotation += 15;\n                increment--;\n            }\n"
        "            const anchor = dropArea.target.childAt(event.x, event.y);\n"
        "            if (Plasmoid.configuration.wheelEnabled === 3) {\n"
        "                const loudest = anchor?.audioStreams?.reduce((loudest, stream) => Math.max(loudest, stream.volume), 0)\n"
        "                const step = (pulseAudio.item.normalVolume - pulseAudio.item.minimalVolume) * pulseAudio.item.globalConfig.volumeStep / 100;\n"
        "                anchor?.audioStreams?.forEach((stream) => {\n"
        "                    let delta = step * increment;\n"
        "                    if (loudest > 0) {\n                        delta *= stream.volume / loudest;\n                    }\n"
        "                    const volume = stream.volume + delta;\n"
        "                    console.log(volume, Math.max(pulseAudio.item.minimalVolume, Math.min(volume, pulseAudio.item.normalVolume)));\n"
        "                    stream.model.Volume = Math.max(pulseAudio.item.minimalVolume, Math.min(volume, pulseAudio.item.normalVolume));\n"
        "                    stream.model.Muted = volume === 0\n"
        "                })\n            return;\n            }\n"
        "            while (increment !== 0) {\n"
        "                TaskManagerApplet.TaskTools.activateNextPrevTask(anchor, increment < 0, Plasmoid.configuration.wheelSkipMinimized, Plasmoid.configuration.wheelEnabled, tasks);\n"
        "                increment += (increment < 0) ? 1 : -1;\n            }\n        }\n    }\n}\n"
    )
    (out_dir / "ToolTipInstance.qml").write_text(
        "import QtQuick\nItem {\n"
        '                text: i18nc("volume percentage", "%1%", slider.displayValue)\n}\n'
    )


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.plugins = self.home / "system-plugins"
        applets = self.plugins / "plasma/applets"
        applets.mkdir(parents=True)
        for name in ("systemtray", "taskmanager"):
            (applets / f"org.kde.plasma.{name}.so").write_bytes(f"system plugin {name}".encode())
        self.icontasks_meta = self.home / "usr/share/plasma/plasmoids/org.kde.plasma.icontasks/metadata.json"
        self.icontasks_meta.parent.mkdir(parents=True)
        self.icontasks_meta.write_text(
            json.dumps(
                {
                    "KPlugin": {"Id": "org.kde.plasma.icontasks"},
                    "X-Plasma-RootPath": "org.kde.plasma.taskmanager",
                }
            )
            + "\n"
        )
        self.shell = self.home / "usr/bin/plasmashell"
        self.shell.parent.mkdir(parents=True)
        self.shell.write_text("#!/bin/sh\n")
        self.manager = cli.Manager(ROOT, self.home, self.home / "data", self.home / "config")
        self.upstream_extra = ""
        self.break_tray = False

        def fake_discover(_launcher, _data=None):
            return {
                "shell": self.shell,
                "version": "6.8.3",
                "qtpaths": "qtpaths6",
                "plugins": self.plugins,
                "icontasks_metadata": self.icontasks_meta,
            }

        def fake_extract(_root, plugin_path, _prefix, out_dir):
            if "systemtray" in plugin_path.name:
                if self.break_tray:
                    out_dir.mkdir(parents=True, exist_ok=True)
                    (out_dir / "main.qml").write_text("import QtQuick\nItem {}\n")
                    (out_dir / "_plugin_metadata.json").write_text(json.dumps({"KPlugin": {"Name": "Tray"}}))
                else:
                    make_fake_raw_systemtray(out_dir, self.upstream_extra)
            else:
                make_fake_raw_taskmanager(out_dir, self.upstream_extra)

        self.p_discover = patch.object(cli, "discover", side_effect=fake_discover)
        self.p_extract = patch.object(cli, "extract_resources", side_effect=fake_extract)
        self.p_discover.start()
        self.p_extract.start()
        self.addCleanup(self.p_discover.stop)
        self.addCleanup(self.p_extract.stop)

    def test_install_and_restore_tray(self):
        target = self.manager.package_targets("tray")[0]
        target.mkdir(parents=True)
        (target / "original").write_text("keep me")
        _, warnings = self.manager.change("install", ["tray"])
        self.assertEqual(warnings, [])
        self.assertTrue((target / "metadata.json").is_file())
        _, warnings = self.manager.change("uninstall", ["tray"])
        self.assertEqual((target / "original").read_text(), "keep me")
        self.assertTrue(any("pre-existing user override" in w for w in warnings))
        self.assertFalse(self.manager.manifest.exists())

    def test_independent_features_keep_shared_plugin_path(self):
        self.manager.change("install", ["tray", "microphone"])
        self.manager.change("uninstall", ["tray"])
        content = self.manager.shared[0].read_text()
        self.assertIn(str(self.manager.plugin_root / "icontasks"), content)
        self.assertNotIn(str(self.manager.plugin_root / "tray"), content)
        self.assertTrue((self.manager.package_targets("icontasks")[0] / "metadata.json").is_file())
        self.manager.change("uninstall", ["microphone"])
        self.assertFalse(self.manager.shared[0].exists())

    def test_microphone_and_app_volume_compose_and_rebuild_on_partial_uninstall(self):
        self.manager.change("install", ["microphone", "app-volume"])
        ic_dir = self.manager.package_targets("icontasks")[0]
        self.assertTrue((ic_dir / "contents/ui/MicStream.qml").is_file())
        self.assertTrue((ic_dir / "contents/ui/AppVolume.js").is_file())
        self.assertIn("appVolumeEnabled", (ic_dir / "contents/config/main.xml").read_text())
        self.assertIn("hasMicStream", (ic_dir / "contents/ui/Task.qml").read_text())

        self.manager.change("uninstall", ["microphone"])
        self.assertFalse((ic_dir / "contents/ui/MicStream.qml").exists())
        self.assertTrue((ic_dir / "contents/ui/AppVolume.js").is_file())
        self.assertNotIn("hasMicStream", (ic_dir / "contents/ui/Task.qml").read_text())
        state = self.manager.load()
        self.assertEqual(state["desired"], ["app-volume"])
        self.assertEqual(state["active"], ["app-volume"])

        self.manager.change("uninstall", ["app-volume"])
        self.assertFalse(ic_dir.exists())

    def test_reinstall_keeps_original_backup(self):
        target = self.manager.package_targets("icontasks")[0]
        target.mkdir(parents=True)
        (target / "original").write_text("before")
        self.manager.change("install", ["microphone"])
        self.manager.change("install", ["app-volume"])
        self.manager.change("uninstall", ["microphone", "app-volume"])
        self.assertEqual((target / "original").read_text(), "before")

    def test_rebase_is_idempotent_and_preserves_upstream_changes(self):
        self.manager.change("install", ["tray", "microphone", "app-volume"])
        h1 = self.manager.load()["packages"]["icontasks"]["output_hash"]
        self.manager.rebase()
        h2 = self.manager.load()["packages"]["icontasks"]["output_hash"]
        self.assertEqual(h1, h2)

        self.upstream_extra = "// upstream-fix-123\n"
        self.manager.rebase()
        unmod = (self.manager.package_targets("icontasks")[0] / "contents/ui/Unmodified.qml").read_text()
        self.assertIn("upstream-fix-123", unmod)

    def test_patch_failure_does_not_publish_broken_override(self):
        self.manager.change("install", ["tray"])
        before_main = (self.manager.package_targets("tray")[0] / "contents/ui/main.qml").read_text()
        self.break_tray = True
        with self.assertRaisesRegex(ValueError, "Missing source file|Target file missing"):
            self.manager.rebase()
        self.assertEqual((self.manager.package_targets("tray")[0] / "contents/ui/main.qml").read_text(), before_main)

    def test_preflight_rebuilds_or_disables_incompatible_package_without_blocking(self):
        self.manager.change("install", ["tray", "app-volume"])
        (self.plugins / "plasma/applets/org.kde.plasma.systemtray.so").write_bytes(b"new incompatible tray")
        self.break_tray = True
        res = self.manager.preflight()
        self.assertEqual(res["action"], "rebuilt")
        self.assertIn("tray", res["disabled"])
        state = self.manager.load()
        self.assertEqual(state["desired"], ["tray", "app-volume"])
        self.assertEqual(state["active"], ["app-volume"])
        self.assertFalse(self.manager.package_targets("tray")[0].exists())
        self.assertTrue(self.manager.package_targets("icontasks")[0].exists())

    def test_shared_symlink_restored_exactly(self):
        launcher = self.manager.shared[1]
        launcher.parent.mkdir(parents=True)
        launcher.symlink_to("/missing/original")
        self.manager.change("install", ["tray"])
        self.manager.change("uninstall", ["tray"])
        self.assertTrue(launcher.is_symlink())
        self.assertEqual(str(launcher.readlink()), "/missing/original")

    def test_missing_plugin_changes_nothing(self):
        (self.plugins / "plasma/applets/org.kde.plasma.taskmanager.so").unlink()
        with self.assertRaisesRegex(ValueError, "System plugin not found"):
            self.manager.change("install", ["tray", "microphone"])
        self.assertFalse(self.manager.package_targets("tray")[0].exists())
        self.assertFalse(self.manager.manifest.exists())

    def test_copy_failure_restores_previous_installation(self):
        self.manager.change("install", ["tray"])
        original = self.manager.manifest.read_bytes()
        real_copy = cli.copy

        def fail(source, target):
            if target == self.manager.package_targets("icontasks")[0]:
                raise OSError("disk full")
            real_copy(source, target)

        with patch.object(cli, "copy", side_effect=fail):
            with self.assertRaisesRegex(OSError, "disk full"):
                self.manager.change("install", ["microphone"])
        self.assertEqual(self.manager.manifest.read_bytes(), original)
        self.assertFalse(self.manager.package_targets("icontasks")[0].exists())
        self.assertTrue((self.manager.package_targets("tray")[0] / "metadata.json").exists())

    def test_legacy_install_refused(self):
        legacy = self.manager.config / "systemd/user/plasma-plasmashell.service.d/microphone-icon.conf"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("legacy")
        with self.assertRaisesRegex(ValueError, "Legacy installation"):
            self.manager.change("install", ["tray"])
        self.assertEqual(legacy.read_text(), "legacy")

    def test_missing_backup_does_not_remove_install(self):
        self.manager.change("install", ["tray"])
        cli.remove(self.manager.state / "backup/tray")
        with self.assertRaisesRegex(ValueError, "Missing rollback"):
            self.manager.change("uninstall", ["tray"])
        self.assertTrue((self.manager.package_targets("tray")[0] / "metadata.json").exists())

    def test_corrupted_manifest_rejected(self):
        self.manager.state.mkdir(parents=True)
        self.manager.manifest.write_text("{not json")
        with self.assertRaisesRegex(ValueError, "Corrupted installation manifest"):
            self.manager.load()

    def test_v1_migration_preserves_original_backups(self):
        self.manager.state.mkdir(parents=True)
        (self.manager.state / "backup/tray/0").mkdir(parents=True)
        (self.manager.state / "backup/tray/0/user.txt").write_text("user tray")
        (self.manager.state / "backup/microphone/0").mkdir(parents=True)
        (self.manager.state / "backup/microphone/0/user_ic.txt").write_text("user ic")
        (self.manager.state / "backup/shared").mkdir(parents=True)
        (self.manager.state / "backup/shared/1").symlink_to("/orig/plasmashell")

        old_targets = [
            str(self.manager.data / "plasma/plasmoids/org.kde.plasma.systemtray"),
            str(self.manager.plugin_root / "tray"),
            str(self.manager.data / "plasma/plasmoids/org.kde.plasma.icontasks"),
            str(self.manager.plugin_root / "microphone"),
            *map(str, self.manager.shared),
        ]
        self.manager.manifest.write_text(
            json.dumps({"targets": old_targets, "installed": ["tray", "microphone"]})
        )

        self.manager.rebase()
        self.assertEqual(self.manager.load()["schema_version"], 2)
        self.manager.change("uninstall", ["tray", "microphone"])
        self.assertEqual(
            (self.manager.package_targets("tray")[0] / "user.txt").read_text(),
            "user tray",
        )
        self.assertEqual(
            (self.manager.package_targets("icontasks")[0] / "user_ic.txt").read_text(),
            "user ic",
        )
        self.assertEqual(str(self.manager.shared[1].readlink()), "/orig/plasmashell")

    def test_changed_xdg_paths_rejected(self):
        self.manager.change("install", ["tray"])
        other = cli.Manager(ROOT, self.home, self.home / "data", self.home / "other-config")
        with self.assertRaisesRegex(ValueError, "Paths differ"):
            other.change("uninstall", ["tray"])

    def test_dropin_symlink_referent_not_modified(self):
        dropin = self.manager.shared[0]
        dropin.parent.mkdir(parents=True)
        referent = self.home / "external.conf"
        referent.write_text("original environment")
        dropin.symlink_to(referent)
        self.manager.change("install", ["tray"])
        self.assertEqual(referent.read_text(), "original environment")
        self.manager.change("uninstall", ["tray"])
        self.assertTrue(dropin.is_symlink())

    def test_invalid_xdg_path_rejected(self):
        with self.assertRaises(ValueError):
            cli.Manager(ROOT, self.home, Path("relative"), self.home / "config")

    def test_doctor_is_read_only(self):
        report = self.manager.doctor()
        self.assertTrue(report["ok"])
        self.assertFalse(self.manager.state.exists())


if __name__ == "__main__":
    unittest.main()
