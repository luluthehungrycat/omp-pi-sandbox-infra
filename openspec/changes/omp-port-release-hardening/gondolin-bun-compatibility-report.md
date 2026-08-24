# Gondolin / Bun Native Compatibility Report Draft

## Summary

The OMP port of `pi-gondolin` cannot load under Bun 1.4.0 because `@earendil-works/gondolin` loads the native `ssh2` crypto addon, which calls the unsupported POSIX libuv function `uv_version_string`.

## Reproduction

Environment:

```text
Linux x64
Bun 1.4.0
Gondolin 0.12.0
ssh2 1.17.0
```

Command shape:

```bash
bun add @earendil-works/gondolin@0.12.0
bun -e 'import { VM } from "@earendil-works/gondolin"; console.log(typeof VM)'
```

Observed result:

```text
panic(main thread): unsupported uv function: uv_version_string
Crashed while loading native module: .../node_modules/ssh2/lib/protocol/crypto/build/Release/sshcrypto.node
```

## Scope

The failure occurs during native module loading, before extension registration or VM startup. Gondolin 0.4.0 and the latest tested 0.12.0 both retain `ssh2 ^1.17.0`.

## Safety constraint

Do not bypass the VM, disable Gondolin network policy, or fall back to unsandboxed host tool execution. Re-test only after a Bun, Gondolin, or ssh2 release provides a supported native compatibility path.

## Related upstream reference

- Bun issue: https://github.com/oven-sh/bun/issues/18546
