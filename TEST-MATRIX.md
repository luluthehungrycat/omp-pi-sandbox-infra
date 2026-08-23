# OMP sandbox port verification matrix

## A. Package and loader compatibility

- `package.json` has an `omp.extensions` entry or a tested local `-e` path.
- All runtime imports resolve through `@oh-my-pi/*` or a verified OMP legacy shim.
- `bun install` completes without lifecycle or native-module errors.
- TypeScript check/build passes with OMP 18.0.0.
- OMP starts with the extension and reports zero extension-load errors.
- `/extensions` shows the extension as loaded.

## B. Extension registration

- Extension factory executes once.
- Built-in tool replacement or interception is registered.
- `tool_call` handlers receive the current OMP event shape.
- `user_bash` and `user_python` behavior is explicitly tested where relevant.
- Commands and flags register without collisions.
- TUI status/notification calls work in interactive mode.

## C. Sandbox enforcement

For each port, test both allowed and denied cases:

- write inside the disposable workspace;
- write outside the workspace;
- read a denied secret path;
- traverse `..` and symlinks outside the workspace;
- run a child shell;
- run Python, Node, Perl, and compiled helpers;
- use redirection, heredocs, pipelines, command substitution, and background jobs;
- attempt network access with curl, Python, Node, and DNS;
- inspect `/proc`, devices, and host processes;
- invoke Docker/Podman and confirm the intended deny/escalation behavior;
- distinguish socket pathname visibility from an actual Unix-socket `connect()` attempt; visibility alone is not API access;
- assert explicit `allowUnixSockets: []` and `allowAllUnixSockets: false` invariants;
- terminate and time out a long-running process;
- simulate missing bwrap/QEMU/sandbox-runtime prerequisites.

## D. OMP-specific surfaces

- model `bash` tool;
- `eval` or equivalent execution tools;
- user `!` and `!!` commands;
- read/write/edit/AST-edit tools;
- Python/JavaScript kernels;
- subagents and task isolation;
- MCP/custom tools;
- third-party extensions loaded beside the sandbox extension.

## E. Fail-closed requirements

- Missing sandbox dependency must produce an explicit error.
- Sandbox startup failure must not silently run the original host implementation.
- An explicit unsandboxed escape must be visibly labeled and approval-gated.
- Project configuration must not be able to disable hard-deny paths silently.
- Session shutdown must clean up child processes and VM/container state.

## F. UX verification

- Start-up success/failure is visible in the status bar.
- `/sandbox` or equivalent displays effective configuration.
- Denials explain the violated rule and suggested remedy.
- Approval prompts do not appear for ordinary allowed operations.
- TUI resize, cancellation, timeout, and Ctrl-C behavior remain usable.
- Run one interactive smoke test through a real PTY; use CUA-driver only for final visual/UI confirmation.
