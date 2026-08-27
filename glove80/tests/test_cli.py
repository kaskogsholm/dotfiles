from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import trio

from glove80_flash.cli import FlashError, Options, flash


class FakeBackend:
    def __init__(
        self,
        mountpoint: Path | None,
        *,
        connected: bool = True,
        mount_target: Path | None = None,
    ) -> None:
        self.mountpoint = mountpoint
        self.connected = connected
        self.mount_target = mount_target
        self.mounted = False

    def find_device(self, label: str) -> str | None:
        return "/dev/mock" if self.connected else None

    async def wait_for_device(self, label: str) -> str:
        await trio.sleep_forever()

    async def find_mountpoint(self, device: str) -> Path | None:
        return self.mountpoint

    async def mount(self, device: str) -> None:
        self.mounted = True
        self.mountpoint = self.mount_target


class FlashTests(unittest.TestCase):
    def test_copy_to_mounted_bootloader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "input.uf2"
            firmware.write_bytes(b"test firmware")
            mountpoint = root / "mount"
            mountpoint.mkdir()
            backend = FakeBackend(mountpoint)

            trio.run(flash, Options("right", firmware, 1), backend)

            self.assertEqual(
                (mountpoint / "glove80.uf2").read_bytes(), b"test firmware"
            )
            self.assertFalse(backend.mounted)

    def test_mounts_bootloader_before_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "input.uf2"
            firmware.write_bytes(b"test firmware")
            mountpoint = root / "mount"
            mountpoint.mkdir()
            backend = FakeBackend(None, mount_target=mountpoint)

            trio.run(flash, Options("left", firmware, 1), backend)

            self.assertTrue(backend.mounted)
            self.assertEqual(
                (mountpoint / "glove80.uf2").read_bytes(), b"test firmware"
            )

    def test_timeout_has_no_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "input.uf2"
            firmware.write_bytes(b"test firmware")
            backend = FakeBackend(root, connected=False)

            with self.assertRaisesRegex(FlashError, "Timed out"):
                trio.run(flash, Options("left", firmware, 0.01), backend)


if __name__ == "__main__":
    unittest.main()
