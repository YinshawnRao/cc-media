#!/usr/bin/env python3
"""Safe, stdlib-only Metal availability probe for the Qwen/MLX TTS path."""

from __future__ import annotations

import ctypes
import sys
from collections.abc import Callable


METAL_FRAMEWORK = "/System/Library/Frameworks/Metal.framework/Metal"
PASS_MESSAGE = "QWEN METAL PREFLIGHT: PASS"
FAIL_MESSAGE = (
    "QWEN METAL PREFLIGHT: FAIL — no default Metal device is available in this "
    "execution context; rerun the narration command with the required execution permission"
)
EXIT_UNAVAILABLE = 78


class MetalUnavailable(RuntimeError):
    """Raised before MLX import when the current process cannot use Metal."""


def default_metal_device_available(
    *,
    platform_name: str | None = None,
    library_loader: Callable[[str], object] | None = None,
) -> bool:
    """Return whether Metal exposes a default device without importing MLX."""

    if (platform_name or sys.platform) != "darwin":
        return False
    loader = library_loader or ctypes.CDLL
    try:
        metal = loader(METAL_FRAMEWORK)
        create_default_device = metal.MTLCreateSystemDefaultDevice
        create_default_device.argtypes = []
        create_default_device.restype = ctypes.c_void_p
        return bool(create_default_device())
    except Exception:
        # This probe is a process-boundary guard. Its public failure is deliberately
        # categorical so dyld/Objective-C details and local paths never leak.
        return False


def require_default_metal_device(
    *, checker: Callable[[], bool] | None = None
) -> None:
    available = checker or default_metal_device_available
    if not available():
        raise MetalUnavailable(FAIL_MESSAGE)


def main() -> int:
    if default_metal_device_available():
        print(PASS_MESSAGE)
        return 0
    print(FAIL_MESSAGE, file=sys.stderr)
    return EXIT_UNAVAILABLE


if __name__ == "__main__":
    raise SystemExit(main())
