# PyCan
Python library that simulates the behaviour of different ecus connected to a CAN BUS.

## Usage

```bash
python main.py [--time <t>] [--debug] [--no-sleep]
```

## Options

| Argument | Type | Default | Description |
|---|---|---|---|
| `--time <t>` | float | `1.0` | Sets the sleep duration (in seconds) used by the `Canbus` instance |
| `--debug` | flag | `False` | Enables debug mode by setting `DEBUG = True` |
| `--no-sleep` | flag | `False` | Disables sleeping by setting the sleep time to `0`, overriding `--time` |

## Examples

Run with a custom sleep time of 2.5 seconds:
```bash
python main.py --time 2.5
```

Run with debug mode enabled:
```bash
python main.py --debug
```

## Notes

- `--no-sleep` takes priority over `--time`. If both are provided, the sleep time will be set to `0`.
- If neither `--time` nor `--no-sleep` is specified, the sleep time defaults to `1.0` second.
- `--debug` is a boolean flag; it is `False` unless explicitly passed.

