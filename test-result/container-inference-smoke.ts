const body = {
  model: "LiquidAI_LFM2.5-2.6B-Q6_K_L",
  messages: [{ role: "user", content: "Reply with exactly BROKER_CONTAINER_OK" }],
  max_tokens: 32,
  stream: false,
};
const response = await fetch("http://127.0.0.1:8090/v1/chat/completions", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify(body),
});
console.log(response.status, (await response.text()).slice(0, 1000));
