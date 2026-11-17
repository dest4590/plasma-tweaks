<p align="center">
  <img src="logo.svg" width="96" alt="plasma-tweaks">
</p>

# plasma-tweaks

Two KDE Plasma customizations with one CLI. Python 3.10+, standard library only.

- `tray`: compact Windows-style system tray, small icons, names on hover, and an expand arrow on the left.
- `microphone`: microphone activity indicators and mute controls in Icons-only Task Manager.

![tray preview](features/tray/preview.png)

## Install

```sh
git clone https://github.com/dest4590/plasma-tweaks.git
cd plasma-tweaks
./plasma-tweaks install all --restart
```

Or install one feature:

```sh
./plasma-tweaks install tray --restart
./plasma-tweaks install microphone --restart
./plasma-tweaks status
```

Run as your desktop user, without sudo. `--restart` briefly restarts the panel through the `plasma-plasmashell.service` user service. Without it, files are installed but you must log out and back in. Keep the checkout: the CLI uses its bundled `features/` directory. You can symlink the executable into a directory in your PATH.

The installer supports Plasma **6.8.2 and 6.8.3** only. The tray snapshot was tested on Wayland/CachyOS upstream; the combined installer and microphone UI still need a desktop smoke test. These packages use private Plasma QML APIs, so other versions are blocked. Qt 6 `qtpaths6` (or `/usr/lib{,64}/qt6/bin/qtpaths`) and the system Plasma applet plugins must be installed. No binary plugins are downloaded: the CLI copies them from your machine.

## Remove or update

```sh
./plasma-tweaks uninstall tray --restart
./plasma-tweaks uninstall microphone --restart
./plasma-tweaks uninstall all --restart
```

Removing one feature keeps the other working. Uninstall restores the files saved before the first installation, including an existing local launcher. Reinstalling refreshes QML and plugins without replacing that original backup.

Uninstall **before upgrading Plasma**. Reinstall only after checking compatibility with the new version.

## What changes

The CLI overrides `org.kde.plasma.systemtray` and/or `org.kde.plasma.icontasks` in `$XDG_DATA_HOME/plasma/plasmoids` (default `~/.local/share`). It never edits your panel layout or system files. The microphone feature applies to Icons-only Task Manager, not the regular Task Manager.

Both features share one Qt plugin path, a systemd drop-in at `$XDG_CONFIG_HOME/systemd/user/plasma-plasmashell.service.d/zz-plasma-tweaks.conf`, and `~/.local/bin/plasmashell`. Keep `~/.local/bin` before `/usr/bin` in PATH for manual `plasmashell --replace` calls. Snapshots live in `$XDG_DATA_HOME/plasma-tweaks`. Do not delete them before uninstalling.

Caught installation errors restore the pre-command files. This is not protection against power loss or filesystem failure. Avoid changing HOME/XDG paths between installation and removal.

## Moving from the old repositories

Uninstall both old overrides using their original installers before running this CLI. The CLI refuses known legacy drop-ins instead of silently losing their backups. Do not run both sets of installers together.

The old microphone installer has a bug in `uninstall()`: it uses an undefined `qt_plugin_path` after removing its files. If it ends with that NameError, its file removal has already happened; log out and back in before proceeding. It did not keep backups of previous local task-manager files.

## Development

```sh
python3 -m unittest discover -s tests -v
```

Tests exercise file installation and restoration in temporary directories with mocked platform discovery. They do not launch Plasma or validate the QML UI.

## Sources and licensing

Bundled QML comes from [plasma-icon-tray](https://github.com/dest4590/plasma-icon-tray) and [plasma-microphone-icon](https://github.com/dest4590/plasma-microphone-icon), based on KDE Plasma. Copyright/SPDX headers are preserved. See [UPSTREAM.md](UPSTREAM.md) and `LICENSES/`. The CLI is GPL-2.0-or-later; bundled files retain their marked licenses.
