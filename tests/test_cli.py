import importlib.util
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


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.plugins = self.home / "system-plugins"
        applets = self.plugins / "plasma/applets"
        applets.mkdir(parents=True)
        for name in ("systemtray", "taskmanager"):
            (applets / f"org.kde.plasma.{name}.so").write_bytes(b"system plugin")
        self.shell = self.home / "usr/bin/plasmashell"
        self.shell.parent.mkdir(parents=True)
        self.shell.write_text("#!/bin/sh\n")
        self.manager = cli.Manager(ROOT, self.home, self.home / "data", self.home / "config")
        self.discovery = patch.object(cli, "discover", return_value=(self.shell, self.plugins, "6.8.3"))
        self.discovery.start()
        self.addCleanup(self.discovery.stop)

    def test_install_and_restore_tray(self):
        target = self.manager.feature_targets("tray")[0]
        target.mkdir(parents=True)
        (target / "original").write_text("keep me")
        self.manager.change("install", ["tray"])
        self.assertTrue((target / "metadata.json").is_file())
        self.manager.change("uninstall", ["tray"])
        self.assertEqual((target / "original").read_text(), "keep me")
        self.assertFalse(self.manager.manifest.exists())


    def test_independent_features_keep_shared_plugin_path(self):
        self.manager.change("install", ["tray", "microphone"])
        self.manager.change("uninstall", ["tray"])
        content = self.manager.shared[0].read_text()
        self.assertIn(str(self.manager.plugin_root / "microphone"), content)
        self.assertNotIn(str(self.manager.plugin_root / "tray"), content)
        self.assertTrue((self.manager.feature_targets("microphone")[0] / "metadata.json").is_file())
        self.manager.change("uninstall", ["microphone"])
        self.assertFalse(self.manager.shared[0].exists())

    def test_reinstall_keeps_original_backup(self):
        target = self.manager.feature_targets("microphone")[0]
        target.mkdir(parents=True)
        (target / "original").write_text("before")
        self.manager.change("install", ["microphone"])
        self.manager.change("install", ["microphone"])
        self.manager.change("uninstall", ["microphone"])
        self.assertEqual((target / "original").read_text(), "before")

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
        self.assertFalse(self.manager.feature_targets("tray")[0].exists())
        self.assertFalse(self.manager.manifest.exists())

    def test_copy_failure_restores_previous_installation(self):
        self.manager.change("install", ["tray"])
        original = self.manager.manifest.read_bytes()
        real_copy = cli.copy
        def fail(source, target):
            if source == ROOT / "features/microphone/plasmoid":
                raise OSError("disk full")
            real_copy(source, target)
        with patch.object(cli, "copy", side_effect=fail):
            with self.assertRaisesRegex(OSError, "disk full"):
                self.manager.change("install", ["microphone"])
        self.assertEqual(self.manager.manifest.read_bytes(), original)
        self.assertFalse(self.manager.feature_targets("microphone")[0].exists())
        self.assertTrue((self.manager.feature_targets("tray")[0] / "metadata.json").exists())

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
        self.assertTrue((self.manager.feature_targets("tray")[0] / "metadata.json").exists())

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


if __name__ == "__main__":
    unittest.main()
