# Glove80 Layout

This configuration starts from MoErgo's factory Glove80 ZMK layout and makes
three deliberate changes:

- The unused left `Layer` thumb momentarily activates `Symbols`.
- `Magic+P` enters a direct-key `Gaming` layer.
- In Gaming, the left `Layer` thumb is Space and tapping `Magic` returns to Base.

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

The generated `glove80.uf2` is intentionally ignored by Git.

Without Docker, push the configuration and run the repository's **Build
Glove80 firmware** GitHub Actions workflow. Its `glove80-firmware` artifact
contains the combined UF2 for both halves.

## Flash Safely

Have a spare keyboard available. Build and retain both the factory firmware
and this custom firmware before flashing.

1. Connect the right half over USB-C and enter its bootloader.
2. Copy `glove80.uf2` to `GLV80RHBOOT`.
3. Connect the left half and enter its bootloader.
4. Copy the same `glove80.uf2` to `GLV80LHBOOT`.
5. After a firmware-version change, follow MoErgo's reset and re-pair guidance.

MoErgo documentation:

- https://docs.moergo.com/glove80-user-guide/customizing-key-layout/
- https://docs.moergo.com/layout-editor-guide/building-firmware/
- https://github.com/moergo-sc/glove80-zmk-config
