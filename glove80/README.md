# Glove80 Layout

This configuration starts from MoErgo's factory Glove80 ZMK layout and makes
three deliberate changes:

- The unused left `Layer` thumb momentarily activates `Symbols`.
- `Magic+P` enters a direct-key `Gaming` layer.
- In Gaming, the left `Layer` thumb is Space and tapping `Magic` returns to Base.
- Base uses very dim solid cobalt lighting; Symbols doubles its brightness.
- Gaming uses the slowest breathing effect in burnt orange.

ZMK persists RGB state across firmware updates. If Base remains dark after the
first flash, hold and release `Symbols` once to initialize the cobalt profile.

Base and the remaining thumb bindings retain their factory behavior. Every
thumb key on Symbols is transparent.

## Symbols

Hold the left `Layer` thumb:

```text
     W:"  E:*  R:&  T:|       Y:^  U:{  I:}  O:'
A:!  S:-  D:+  F:=  G:\       H:#  J:(  K:)  L:_
          C:[  V:]                  ,:<  .:>
```

The source of truth is `config/glove80.keymap`. The training graphic is
available as `cheatsheet.svg` and `cheatsheet.png`.

## Build

MoErgo recommends its Layout Editor for most users. This repository instead
uses MoErgo's official source-controlled ZMK build approach so the complete
configuration can live with the rest of the dotfiles.

With Docker installed:

```sh
./build.sh
```

Successful builds from `main` are published as immutable GitHub releases with
a SHA-256 checksum. `glove80-flash` automatically downloads, verifies, and
caches the latest release; no manual Actions artifact handling is required.

Dotbot installs the flashing utility as an editable `pipx` package, so the
`glove80-flash` command always runs the version in this directory.

Without Docker, push the configuration and run the repository's **Build
Glove80 firmware** GitHub Actions workflow. Its `glove80-firmware` artifact
contains the combined UF2 for both halves.

## Flash Safely

Build and retain both the factory firmware and this custom firmware before
flashing. The `glove80-flash` watcher lets you start each copy before putting a
half into bootloader mode, so no keyboard input is needed during the flash.

Start the watcher for both halves:

```sh
glove80-flash
```

Enter the right bootloader first. After it finishes, switch the right half off
and enter the left bootloader. To flash only one half, pass it explicitly:

```sh
glove80-flash right
glove80-flash left
```

For each command, the watcher prints the firmware checksum and waits five
minutes for the exact bootloader label. While it is waiting:

- Right: hold physical `I + PgDn` and switch the right half on.
- Left: hold physical `Magic + E` and switch the left half on.

The Trio-based watcher checks the latest release, listens to udev's netlink file
descriptor, mounts each drive if required, copies the firmware, syncs the file
system, and exits. It does not poll, and it never uses `sudo` or `dd`. If GitHub
is unavailable, it uses the last verified cached firmware.

To restore a factory image, use the same process with an explicit file:

```sh
glove80-flash --firmware ~/Downloads/factory-default.uf2
```

Manual equivalent:

1. Connect the right half over USB-C and enter its bootloader.
2. Copy `glove80.uf2` to `GLV80RHBOOT`.
3. Connect the left half and enter its bootloader.
4. Copy the same `glove80.uf2` to `GLV80LHBOOT`.
5. After a firmware-version change, follow MoErgo's reset and re-pair guidance.

MoErgo documentation:

- https://docs.moergo.com/glove80-user-guide/customizing-key-layout/
- https://docs.moergo.com/layout-editor-guide/building-firmware/
- https://github.com/moergo-sc/glove80-zmk-config
