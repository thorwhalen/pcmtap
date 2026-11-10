# pcmtap.requirements

`check_requirements`: what this machine still needs for pcmtap, and how to get it.

### Functions

| [`check_requirements`](#pcmtap.requirements.check_requirements)(\*[, request])   | Problems (each with its remedy) that stop pcmtap from recording; empty means ready.   |
|--------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|

### pcmtap.requirements.check_requirements(, request=False)

Problems (each with its remedy) that stop pcmtap from recording; empty means ready.

With `request=True`, a missing permission is asked for (a dialog on the Mac).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
