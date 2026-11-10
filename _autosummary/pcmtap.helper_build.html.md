# pcmtap.helper_build

Find or build the native helper (`pcmtap-helper`) that does the real-time capture.

The helper is a small Swift program shipped as source (`pcmtap/helper/`) and
compiled with `swiftc` on first use into [`helper_dir()`](#pcmtap.helper_build.helper_dir), under a name that
carries the source’s hash, so a new pcmtap version rebuilds it and an unchanged one
never does. macOS keys the *System Audio Recording* permission to the binary, so a
rebuild means granting it once more; keeping the build stable is the point.

Set `$PCMTAP_HELPER` to use a helper binary built elsewhere.

### Module Attributes

| [`MIN_MACOS`](#pcmtap.helper_build.MIN_MACOS)   | Process taps arrived in macOS 14.2.   |
|--------------------------------------------------------------|---------------------------------------|

### Functions

| [`build_helper`](#pcmtap.helper_build.build_helper)(target)       | Compile the helper into `target` with `swiftc` and sign it (ad hoc).             |
|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [`helper_dir`](#pcmtap.helper_build.helper_dir)()               | Where built helpers live: `$PCMTAP_DATA_DIR/bin` or `~/.local/share/pcmtap/bin`. |
| [`helper_path`](#pcmtap.helper_build.helper_path)(\*[, rebuild]) | The helper binary, building it first if this version has not been built yet.     |
| [`macos_version`](#pcmtap.helper_build.macos_version)()            | This Mac's version as a tuple, or `None` when not on macOS.                      |

### Exceptions

| [`HelperUnavailable`](#pcmtap.helper_build.HelperUnavailable)   | The native helper cannot be found or built on this machine.   |
|----------------------------------------------------------------------|---------------------------------------------------------------|

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
