# [next] - 2026-05-13

## User-Facing Changelog

## Version next (Initial Release)

- **Initial release of clgen** – a new tool that helps you generate commit messages from your code changes.  
- **API key auto-detection and verification** – clgen can now automatically detect which model to use based on your API key, and it verifies that the key is valid before generating messages.  
- **Chinese README** – added full Chinese-language documentation for Chinese-speaking users.
---

## Developer Changelog

# Changelog (next)

## Features

- **API key auto-detection**  
  Added automatic detection of the API key's corresponding model. The system now inspects the key’s prefix or metadata to select the correct endpoint.  
  New function: `detect_api_key_model(api_key: str) -> str` – returns the model identifier (e.g., `"gpt-4"`, `"claude-3"`).  
  Example usage:
  ```python
  model = detect_api_key_model("sk-abc123...")
  ```

- **API key verification**  
  Added a verification mechanism that checks the validity of an API key before making requests.  
  New method: `verify_api_key(key: str) -> bool` – returns `True` if the key is valid, `False` otherwise.  
  Example:
  ```python
  if not verify_api_key(user_key):
      raise ValueError("Invalid API key")
  ```

- **Chinese README**  
  Added a fully translated Chinese version of the project’s README (`README.zh-CN.md`) with identical structure and technical details, enabling Chinese-speaking developers to quickly onboard.

- **Initial release of clgen v0.1.0**  
  The first public release of `clgen`, a command-line code generation tool. Includes:
  - Basic template rendering engine
  - Support for multiple output formats (JSON, YAML, plain text)
  - Configuration via YAML/TOML files
  - `gen` command for generating code from templates

  No breaking changes are introduced in this version – all additions are backward-compatible.
---

## Release Summary

We're excited to announce the next release! It introduces API key auto-detection and verification for seamless setup, plus a Chinese README for broader accessibility. This also marks the initial release of clgen v0.1.0, our new code generation tool.