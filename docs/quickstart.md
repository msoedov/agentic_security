# Quickstart Guide

Welcome to the Quickstart Guide for Agentic Security. This guide will help you set up and start using the project quickly.

## Installation

To get started with Agentic Security, install the package using pip:

```shell
pip install agentic_security
```

## Initial Setup

After installation, you can start the application using the following command:

```shell
agentic_security
```

This will initialize the server and prepare it for use.

## Basic Usage

To run the main application, use:

```shell
python -m agentic_security
```

You can also view help options with:

```shell
agentic_security --help
```

## Running as a CI Check

Initialize the configuration for CI checks:

```shell
agentic_security init
```

This will generate a default configuration file named `agesec.toml`.

## Additional Commands

- List available modules:

  ```shell
  agentic_security ls
  ```

- Run a security scan:

  ```shell
  agentic_security ci
  ```

## Further Information

For more detailed information, refer to the [Documentation](index.md) or the [API Reference](api_reference.md).

This quickstart guide should help you get up and running with Agentic Security efficiently.
