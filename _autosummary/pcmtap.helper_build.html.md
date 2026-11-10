# pcmtap.helper_build

Find or build the native helper (`pcmtap-helper`) that does the real-time capture.

The helper is a small Swift program shipped as source (`pcmtap/helper/`) and
compiled with `swiftc` on first use into [`helper_dir()`](#pcmtap.helper_build.helper_dir), always at the same
path ([`HELPER_NAME`](#pcmtap.helper_build.HELPER_NAME)), with the source’s hash in a sidecar file. A pcmtap
version whose helper source changed rebuilds it in place; any other version reuses
it. macOS keys the *System Audio Recording* permission to the binary’s path (and,
for an ad hoc signature, its contents), so the stable path is what lets an upgrade
that does not touch the helper keep the permission.

Set `$PCMTAP_HELPER` to use a helper binary built elsewhere.

### Module Attributes

| [`HELPER_NAME`](#pcmtap.helper_build.HELPER_NAME)   | stable, because macOS keys the permission to its path.   |
|----------------------------------------------------------------|----------------------------------------------------------|
| [`MIN_MACOS`](#pcmtap.helper_build.MIN_MACOS)     | Process taps arrived in macOS 14.2.                      |

### Functions

| [`build_helper`](#pcmtap.helper_build.build_helper)(target)       | Compile the helper into `target` with `swiftc` and sign it (ad hoc).             |
|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [`helper_dir`](#pcmtap.helper_build.helper_dir)()               | Where built helpers live: `$PCMTAP_DATA_DIR/bin` or `~/.local/share/pcmtap/bin`. |
| [`helper_path`](#pcmtap.helper_build.helper_path)(\*[, rebuild]) | The helper binary, building it first if this version has not been built yet.     |
| [`macos_version`](#pcmtap.helper_build.macos_version)()            | This Mac's version as a tuple, or `None` when not on macOS.                      |

### Exceptions

| [`HelperUnavailable`](#pcmtap.helper_build.HelperUnavailable)   | The native helper cannot be found or built on this machine.   |
|----------------------------------------------------------------------|---------------------------------------------------------------|

### pcmtap.helper_build.HELPER_NAME *= 'pcmtap-helper'*

stable, because macOS keys the permission to its path.

* **Type:**
  The helper’s file name

### *exception* pcmtap.helper_build.HelperUnavailable

Bases: [`RuntimeError`](https://docs.python.org/3/builtins/exceptions.html#RuntimeError)

The native helper cannot be found or built on this machine.

### pcmtap.helper_build.MIN_MACOS *= (14, 2)*

Process taps arrived in macOS 14.2.

### pcmtap.helper_build.build_helper(target)

Compile the helper into `target` with `swiftc` and sign it (ad hoc).

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### pcmtap.helper_build.helper_dir()

Where built helpers live: `$PCMTAP_DATA_DIR/bin` or `~/.local/share/pcmtap/bin`.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### pcmtap.helper_build.helper_path(, rebuild=False)

The helper binary, building it first if this version has not been built yet.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### pcmtap.helper_build.macos_version()

This Mac’s version as a tuple, or `None` when not on macOS.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)
