from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from urllib.error import URLError

import trio

from glove80_flash.cli import (
    RELEASE_API,
    FlashError,
    Options,
    fetch_latest_firmware,
    flash,
)


class FakeBackend:
    def __init__(
        self,
        devices: dict[str, str],
        mountpoints: dict[str, Path | None],
        arrivals: list[tuple[str, str]] | None = None,
        mount_targets: dict[str, Path] | None = None,
    ) -> None:
        self.devices = devices
        self.mountpoints = mountpoints
        self.arrivals = arrivals or []
        self.mount_targets = mount_targets or {}
        self.mounted: list[str] = []

    def find_device(self, label: str) -> str | None:
        return self.devices.pop(label, None)

    async def wait_for_device(self, labels: set[str]) -> tuple[str, str]:
        for index, (label, device) in enumerate(self.arrivals):
            if label in labels:
                self.arrivals.pop(index)
                return label, device
        await trio.sleep_forever()

    async def find_mountpoint(self, device: str) -> Path | None:
        return self.mountpoints[device]

    async def mount(self, device: str) -> None:
        self.mounted.append(device)
        self.mountpoints[device] = self.mount_targets[device]


class FlashTests(unittest.TestCase):
    def test_copy_to_mounted_bootloader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "input.uf2"
            firmware.write_bytes(b"test firmware")
            mountpoint = root / "mount"
            mountpoint.mkdir()
            backend = FakeBackend(
                {"GLV80RHBOOT": "/dev/right"}, {"/dev/right": mountpoint}
            )

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
            backend = FakeBackend(
                {"GLV80LHBOOT": "/dev/left"},
                {"/dev/left": None},
                mount_targets={"/dev/left": mountpoint},
            )

            trio.run(flash, Options("left", firmware, 1), backend)

            self.assertEqual(backend.mounted, ["/dev/left"])
            self.assertEqual(
                (mountpoint / "glove80.uf2").read_bytes(), b"test firmware"
            )

    def test_timeout_has_no_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "input.uf2"
            firmware.write_bytes(b"test firmware")
            backend = FakeBackend({}, {})

            with self.assertRaisesRegex(FlashError, "Timed out"):
                trio.run(flash, Options("left", firmware, 0.01), backend)

    def test_waits_for_both_halves_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "input.uf2"
            firmware.write_bytes(b"test firmware")
            right_mount = root / "right"
            left_mount = root / "left"
            right_mount.mkdir()
            left_mount.mkdir()
            backend = FakeBackend(
                {"GLV80RHBOOT": "/dev/right"},
                {"/dev/right": right_mount, "/dev/left": left_mount},
                arrivals=[("GLV80LHBOOT", "/dev/left")],
            )

            trio.run(flash, Options(None, firmware, 1), backend)

            self.assertEqual(
                (right_mount / "glove80.uf2").read_bytes(), b"test firmware"
            )
            self.assertEqual(
                (left_mount / "glove80.uf2").read_bytes(), b"test firmware"
            )


class FirmwareDownloadTests(unittest.TestCase):
    def test_downloads_verifies_and_reuses_cached_firmware(self) -> None:
        firmware = b"released firmware"
        checksum = hashlib.sha256(firmware).hexdigest()
        release = json_bytes(
            {
                "assets": [
                    {
                        "name": "glove80.uf2",
                        "browser_download_url": "https://example.test/glove80.uf2",
                    },
                    {
                        "name": "glove80.uf2.sha256",
                        "browser_download_url": "https://example.test/checksum",
                    },
                ]
            }
        )
        responses = {
            RELEASE_API: release,
            "https://example.test/glove80.uf2": firmware,
            "https://example.test/checksum": f"{checksum}  glove80.uf2\n".encode(),
        }

        def opener(request, timeout):
            return BytesIO(responses[request.full_url])

        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            downloaded = fetch_latest_firmware(cache, opener)
            self.assertEqual(downloaded.read_bytes(), firmware)

            def offline(request, timeout):
                raise URLError("offline")

            self.assertEqual(fetch_latest_firmware(cache, offline), downloaded)


def json_bytes(value: object) -> bytes:
    return json.dumps(value).encode()


if __name__ == "__main__":
    unittest.main()
