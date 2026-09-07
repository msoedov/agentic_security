# Command-line interface

The `agentic_security` command provides four commands: start the web server,
create a configuration file, list the available checks, and run a configured
scan.

```bash
agentic_security --help
```

## Start the server

Run the web application on the local machine:

```bash
agentic_security server --host=127.0.0.1 --port=8718
```

`s` is a short alias for `server`. Running `agentic_security` without a
subcommand shows the available command help.

## Create a scan configuration

Create `agentic_security.toml` in the current directory:

```bash
agentic_security init
```

Set a different target host or port in the generated HTTP specification:

```bash
agentic_security init --host=127.0.0.1 --port=8718
```

`i` is a short alias for `init`. The command overwrites an existing
`agentic_security.toml`, so save any custom changes first.

## List available checks

Inspect the built-in dataset registry before selecting modules for a scan:

```bash
agentic_security ls
```

## Run a configured scan

After reviewing `agentic_security.toml` and replacing the example `llmSpec`
with the target endpoint, run:

```bash
agentic_security ci
```

The command uses `agentic_security.toml` from the current directory. It exits
without scanning if the file is missing. To include your own prompts, follow
the [local datasets guide](datasets.md).

## Python module form

If the console script is not on your `PATH`, invoke the same CLI through
Python:

```bash
python -m agentic_security ls
```
