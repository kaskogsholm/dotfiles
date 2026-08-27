from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pyudev
import trio

BOOT_LABELS = {
    "right": "GLV80RHBOOT",
    "left": "GLV80LHBOOT",
}


class FlashError(Exception):
    """An expected error that should be shown without a traceback."""


class DeviceBackend(Protocol):
    def find_device(self, label: str) -> str | None: ...

    async def wait_for_device(self, label: str) -> str: ...

    async def find_mountpoint(self, device: str) -> Path | None: ...

    async def mount(self, device: str) -> None: ...


class UdevBackend:
    """Observe block devices through udev's netlink event descriptor."""

    def __init__(self) -> None:
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem="block")
        self.monitor.start()

    @staticmethod
    def _label(device: pyudev.Device) -> str | None:
        return device.properties.get("ID_FS_LABEL")

    def find_device(self, label: str) -> str | None:
        for device in self.context.list_devices(subsystem="block"):
            if self._label(device) == label and device.device_node:
                return device.device_node
        return None

    async def wait_for_device(self, label: str) -> str:
        while True:
            await trio.lowlevel.wait_readable(self.monitor.fileno())
            while device := self.monitor.poll(timeout=0):
                if self._label(device) == label and device.device_node:
                    return device.device_node

    async def find_mountpoint(self, device: str) -> Path | None:
        process = await trio.run_process(
            ["lsblk", "--json", "--paths", "--output", "NAME,MOUNTPOINTS", device],
            capture_stdout=True,
            capture_stderr=True,
            check=False,
        )
        if process.returncode != 0:
            return None

        def mounted_path(nodes: list[dict[str, object]]) -> Path | None:
            for node in nodes:
                if node.get("name") == device:
                    for mountpoint in node.get("mountpoints", []) or []:
                        if mountpoint:
                            return Path(str(mountpoint))
                children = node.get("children", [])
                if isinstance(children, list) and (result := mounted_path(children)):
                    return result
            return None

        data = json.loads(process.stdout)
        return mounted_path(data.get("blockdevices", []))

    async def mount(self, device: str) -> None:
        process = await trio.run_process(
            ["udisksctl", "mount", "--block-device", device],
            capture_stdout=True,
            capture_stderr=True,
            check=False,
        )
        # A desktop automounter can win the race after our first query.
        if process.returncode != 0 and await self.find_mountpoint(device) is None:
            detail = process.stderr.decode(errors="replace").strip()
            raise FlashError(f"Could not mount {device}: {detail}")


@dataclass(frozen=True)
class Options:
    side: str
    firmware: Path
    timeout: float


def default_firmware() -> Path:
    return Path(__file__).resolve().parents[2] / "glove80.uf2"


def parse_args(argv: list[str] | None = None) -> Options:
    parser = argparse.ArgumentParser(
        description=(
            "Wait for a Glove80 bootloader event and copy firmware without "
            "requiring keyboard input."
        )
    )
    parser.add_argument("side", choices=BOOT_LABELS)
    parser.add_argument(
        "--firmware",
        type=Path,
        default=default_firmware(),
        help="UF2 to copy (default: the built firmware beside this project)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300,
        help="seconds to wait for the bootloader (default: 300)",
    )
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return Options(args.side, args.firmware.expanduser().resolve(), args.timeout)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


async def flash(options: Options, backend: DeviceBackend) -> None:
    firmware = options.firmware
    if not firmware.is_file():
        raise FlashError(f"Firmware is not readable: {firmware}")
    if firmware.suffix.lower() != ".uf2":
        raise FlashError(f"Firmware must have a .uf2 extension: {firmware}")
    if shutil.which("lsblk") is None or shutil.which("udisksctl") is None:
        raise FlashError("Required commands are unavailable: lsblk and udisksctl")

    label = BOOT_LABELS[options.side]
    checksum = await trio.to_thread.run_sync(sha256, firmware)
    print(f"Firmware: {firmware}")
    print(f"SHA-256: {checksum}")
    print(f"Waiting up to {options.timeout:g} seconds for {label}...")

    device = backend.find_device(label)
    if device is None:
        with trio.move_on_after(options.timeout) as timeout_scope:
            device = await backend.wait_for_device(label)
        if timeout_scope.cancelled_caught:
            raise FlashError(f"Timed out waiting for {label}. No files were copied.")

    print(f"Found {label} on {device}.")
    mountpoint = await backend.find_mountpoint(device)
    if mountpoint is None:
        print(f"Mounting {device}...")
        await backend.mount(device)
        mountpoint = await backend.find_mountpoint(device)
    if mountpoint is None or not mountpoint.is_dir():
        raise FlashError(f"Could not determine the mount point for {label}.")

    destination = mountpoint / "glove80.uf2"
    print(f"Copying firmware to {destination}...")
    try:
        await trio.to_thread.run_sync(shutil.copyfile, firmware, destination)
        await trio.to_thread.run_sync(os.sync)
    except OSError as error:
        if not Path(device).exists():
            print(
                "The boot drive disappeared during the copy. MoErgo documents "
                "this as a likely successful flash, but verify the half after reboot.",
                file=sys.stderr,
            )
            return
        raise FlashError(f"Firmware copy failed: {error}") from error

    print(
        f"Copy completed. The {options.side} half should reboot and the boot "
        "drive should disappear."
    )


async def async_main(options: Options) -> None:
    await flash(options, UdevBackend())


def entrypoint() -> None:
    try:
        trio.run(async_main, parse_args())
    except FlashError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from None
