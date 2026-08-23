import { mkdir, writeFile, readFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import { buildBwrapArgs } from "/home/hermes/omp-sandbox-dev/plugins/pi-bash-wrap/dist/bwrap.js";

const root = "/home/hermes/omp-sandbox-dev";
const cwd = `${root}/test-project`;
const resultDir = `${root}/test-result/bwrap-run`;
await mkdir(resultDir, { recursive: true });
await writeFile(`${root}/test-home/secret-sentinel.txt`, "HOST_SECRET_SENTINEL\n");
await writeFile(`${cwd}/symlink-to-host-secret`, `${root}/test-home/secret-sentinel.txt`);

const config = {
  enabled: true,
  internet: "block" as const,
  extraReadPaths: [] as string[],
  extraWritePaths: [] as string[],
  promptOnFailure: false,
  writeTools: {},
};

type Probe = { name: string; command: string; expect: "pass" | "deny" };
const probes: Probe[] = [
  { name: "write-project", command: `printf PROJECT_OK > ${cwd}/inside.txt`, expect: "pass" },
  { name: "write-outside-cwd", command: `printf ESCAPE > ${root}/test-result/outside.txt`, expect: "deny" },
  { name: "read-host-secret", command: `test "$(cat ${root}/test-home/secret-sentinel.txt)" = HOST_SECRET_SENTINEL`, expect: "deny" },
  { name: "symlink-read-escape", command: `test "$(cat ${cwd}/symlink-to-host-secret)" = HOST_SECRET_SENTINEL`, expect: "deny" },
  { name: "docker-socket-visible", command: `test -S /var/run/docker.sock`, expect: "deny" },
  { name: "docker-socket-connect", command: `python3 -c 'import socket; s=socket.socket(socket.AF_UNIX); s.settimeout(1); s.connect("/var/run/docker.sock")'`, expect: "deny" },  { name: "ssh-agent-path-visible", command: `test -n "$SSH_AUTH_SOCK" && test -S "$SSH_AUTH_SOCK"`, expect: "deny" },
  { name: "host-pid-visible", command: `test -e /proc/$HOST_PID`, expect: "deny" },
  { name: "kvm-visible", command: `test -e /dev/kvm`, expect: "deny" },
  { name: "network-blocked", command: `curl --connect-timeout 2 --silent --show-error https://example.com >/dev/null`, expect: "deny" },
  { name: "nested-eval-stays-contained", command: `eval 'printf NESTED_OK > ${cwd}/nested.txt'`, expect: "pass" },
];

function run(command: string): Promise<{ code: number | null; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    const args = buildBwrapArgs(config, cwd, command);
    const child = spawn("/usr/bin/bwrap", args, {
      cwd,
      env: { ...process.env, HOST_PID: String(process.pid), SSH_AUTH_SOCK: process.env.SSH_AUTH_SOCK ?? "" },
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (b) => (stdout += b));
    child.stderr.on("data", (b) => (stderr += b));
    child.on("close", (code) => resolve({ code, stdout, stderr }));
    child.on("error", (error) => resolve({ code: null, stdout, stderr: String(error) }));
  });
}

const results = [];
for (const probe of probes) {
  const observed = await run(probe.command);
  const passed = probe.expect === "pass" ? observed.code === 0 : observed.code !== 0;
  results.push({ name: probe.name, expected: probe.expect, passed, code: observed.code, stderr: observed.stderr.trim().slice(0, 300) });
}
console.log(JSON.stringify({ config, probes: results }, null, 2));
