"""Check native test dependencies against the macOS app's universal2 baseline."""

import argparse
from pathlib import Path
import re
import shlex
import subprocess


MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe",  # 32-bit Mach-O
    b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe",  # 64-bit Mach-O
    b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca",  # Fat Mach-O
    b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca",  # 64-bit fat Mach-O
}


def parse_version(version):
    """Normalize macOS versions without treating 10.15 as a decimal number."""
    if not re.fullmatch(r"\d+(?:\.\d+){0,2}", version):
        raise ValueError(f"Invalid macOS version: {version}")
    numbers = tuple(int(part) for part in version.split("."))
    return numbers + (0,) * (3 - len(numbers))


def format_version(version):
    return ".".join(str(part) for part in version)


def parse_macos_minimum(output):
    """Read the minimum, not the SDK, from modern or legacy otool commands."""
    minimums = []
    for block in re.split(r"(?m)^\s*Load command \d+\s*$", output):
        command = re.search(r"(?m)^\s*cmd\s+(LC_\w+)\s*$", block)
        if command is None:
            continue
        if command[1] == "LC_BUILD_VERSION":
            platform = re.search(r"(?m)^\s*platform\s+(\S+)\s*$", block)
            if platform is None or platform[1].lower() not in {"1", "macos"}:
                continue
            field = "minos"
        elif command[1] == "LC_VERSION_MIN_MACOSX":
            field = "version"
        else:
            continue
        minimum = re.search(rf"(?m)^\s*{field}\s+(\S+)\s*$", block)
        if minimum is None:
            raise ValueError(f"Missing {field} in {command[1]}")
        minimums.append(parse_version(minimum[1]))
    if len(minimums) != 1:
        raise ValueError("Expected exactly one macOS minimum-version command")
    return minimums[0]


def run_xcrun(*arguments, show_output=True):
    """Log commands and build-version output without dumping all load commands."""
    command = ["xcrun", *(str(argument) for argument in arguments)]
    print("+", shlex.join(command), flush=True)
    output = subprocess.check_output(command, text=True)
    if output and show_output:
        print(output, end="" if output.endswith("\n") else "\n", flush=True)
    return output


def is_macho(path):
    """Recognize extensions, dylibs, and extensionless bundled executables."""
    with path.open("rb") as stream:
        return stream.read(4) in MACHO_MAGICS


def inspect_macho_binary(binary, baseline="11.0"):
    """Require both slices to support the copied app's minimum macOS version."""
    binary = binary.resolve()
    if not binary.is_file():
        raise ValueError(f"Native binary not found: {binary}")
    requested = parse_version(baseline)
    run_xcrun("lipo", "-verify_arch", "x86_64", "arm64", binary)
    minimums = {}
    for arch in ("x86_64", "arm64"):
        run_xcrun("vtool", "-arch", arch, "-show-build", binary)
        output = run_xcrun(
            "otool", "-arch", arch, "-l", binary, show_output=False)
        minimum = parse_macos_minimum(output)
        expected = max(requested, (11, 0, 0)) if arch == "arm64" else requested
        if minimum > expected:
            raise ValueError(
                f"{binary} ({arch}) has minimum {format_version(minimum)}; "
                f"expected <= {format_version(expected)}")
        minimums[arch] = format_version(minimum)
        print(f"{binary} ({arch}): minimum macOS {format_version(minimum)}",
              flush=True)
    return {
        "binary": str(binary), "minimums": minimums,
        "baseline": baseline,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--baseline", default="11.0")
    args = parser.parse_args()
    try:
        inspect_macho_binary(args.binary, args.baseline)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Native binary check failed: {error}\n")


if __name__ == "__main__":
    main()
