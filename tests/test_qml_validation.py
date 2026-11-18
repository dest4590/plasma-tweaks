from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import qml_validation


class QmlValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_valid_qml_passes_with_fake_qmlformat(self):
        pkg = self.root / "pkg"
        (pkg / "contents/ui").mkdir(parents=True)
        (pkg / "contents/ui/main.qml").write_text("import QtQuick\nItem { width: 10 }\n")

        fake_bin = self.root / "qmlformat"
        fake_bin.write_text("#!/bin/sh\nexit 0\n")
        fake_bin.chmod(0o755)

        with patch.object(qml_validation, "find_qmlformat", return_value=str(fake_bin)):
            warnings = qml_validation.validate_qml_directory(pkg, "tray")
        self.assertEqual(warnings, [])

    def test_invalid_qml_fails_with_fake_qmlformat(self):
        pkg = self.root / "pkg"
        (pkg / "contents/ui").mkdir(parents=True)
        (pkg / "contents/ui/main.qml").write_text("import QtQuick\nItem { width: }\n")

        fake_bin = self.root / "qmlformat"
        fake_bin.write_text(
            "#!/bin/sh\n"
            "for a in \"$@\"; do f=\"$a\"; done\n"
            "if grep -q 'width: }' \"$f\"; then\n"
            "  echo 'Error: Expected expression' >&2\n"
            "  exit 1\n"
            "fi\n"
            "exit 0\n"
        )
        fake_bin.chmod(0o755)

        with patch.object(qml_validation, "find_qmlformat", return_value=str(fake_bin)):
            with self.assertRaisesRegex(ValueError, "QML syntax check failed"):
                qml_validation.validate_qml_directory(pkg, "tray")

    def test_qmlformat_failure_without_diagnostics_becomes_warning(self):
        pkg = self.root / "pkg"
        (pkg / "contents/ui").mkdir(parents=True)
        (pkg / "contents/ui/main.qml").write_text("import QtQuick\nItem { width: 10 }\n")

        fake_bin = self.root / "qmlformat"
        fake_bin.write_text(
            "#!/bin/sh\n"
            "for a in \"$@\"; do f=\"$a\"; done\n"
            "if grep -q 'width: 10' \"$f\"; then\n"
            "  exit 1\n"
            "fi\n"
            "exit 0\n"
        )
        fake_bin.chmod(0o755)

        with patch.object(qml_validation, "find_qmlformat", return_value=str(fake_bin)):
            warnings = qml_validation.validate_qml_directory(pkg, "tray")
        self.assertTrue(any("returned 1 without diagnostics" in w for w in warnings))

    def test_old_qmlformat_parser_falls_back_to_delimiter_only(self):
        pkg = self.root / "pkg"
        (pkg / "contents/ui").mkdir(parents=True)
        (pkg / "contents/ui/main.qml").write_text("import QtQuick\nItem { width: 10 }\n")

        fake_bin = self.root / "qmlformat"
        fake_bin.write_text("#!/bin/sh\nexit 1\n")
        fake_bin.chmod(0o755)

        with patch.object(qml_validation, "find_qmlformat", return_value=str(fake_bin)):
            warnings = qml_validation.validate_qml_directory(pkg, "tray")
        self.assertTrue(any("parser is too old" in w for w in warnings))

    def test_qmlformat_unknown_ignore_settings_option_falls_back(self):
        pkg = self.root / "pkg"
        (pkg / "contents/ui").mkdir(parents=True)
        (pkg / "contents/ui/main.qml").write_text("import QtQuick\nItem { width: 10 }\n")

        fake_bin = self.root / "qmlformat"
        fake_bin.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = \"--ignore-settings\" ]; then\n"
            "  echo \"Unknown option 'ignore-settings'.\" >&2\n"
            "  exit 1\n"
            "fi\n"
            "exit 0\n"
        )
        fake_bin.chmod(0o755)

        with patch.object(qml_validation, "find_qmlformat", return_value=str(fake_bin)):
            warnings = qml_validation.validate_qml_directory(pkg, "tray")
        self.assertEqual(warnings, [])

    def test_fallback_checks_unbalanced_braces_when_qmlformat_missing(self):
        pkg = self.root / "pkg"
        (pkg / "contents/ui").mkdir(parents=True)
        (pkg / "contents/ui/Broken.qml").write_text("import QtQuick\nItem {\n")

        with patch.object(qml_validation, "find_qmlformat", return_value=None):
            with self.assertRaisesRegex(ValueError, "Unbalanced delimiters"):
                qml_validation.validate_qml_directory(pkg, "tray")

    def test_fallback_warns_when_qmlformat_missing_on_valid_files(self):
        pkg = self.root / "pkg"
        (pkg / "contents/ui").mkdir(parents=True)
        (pkg / "contents/ui/main.qml").write_text("import QtQuick\nItem { property string s: '{' }\n")

        with patch.object(qml_validation, "find_qmlformat", return_value=None):
            warnings = qml_validation.validate_qml_directory(pkg, "tray")
        self.assertTrue(any("qmlformat not found" in w for w in warnings))

    def test_bundled_feature_files_have_balanced_delimiters(self):
        repo_root = Path(__file__).resolve().parents[1]
        for rel in (
            "features/microphone/files/contents/ui/MicStream.qml",
        ):
            path = repo_root / rel
            qml_validation.check_balanced_delimiters(path.read_text(encoding="utf-8"), rel, "repo")


if __name__ == "__main__":
    unittest.main()
