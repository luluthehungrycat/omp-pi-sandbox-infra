import net from "node:net";

const socketPath = process.env.OMP_INFERENCE_SOCKET ?? "/run/omp-inference.sock";
const listenPort = Number(process.env.OMP_INFERENCE_BRIDGE_PORT ?? "8090");

const server = net.createServer((client) => {
  const upstream = net.createConnection({ path: socketPath });
  client.pipe(upstream);
  upstream.pipe(client);
  const close = () => {
    client.destroy();
    upstream.destroy();
  };
  client.on("error", close);
  upstream.on("error", close);
  client.on("close", () => upstream.destroy());
  upstream.on("close", () => client.destroy());
});

server.listen(listenPort, "127.0.0.1", () => {
  console.error(`inference bridge listening on 127.0.0.1:${listenPort} -> ${socketPath}`);
});
