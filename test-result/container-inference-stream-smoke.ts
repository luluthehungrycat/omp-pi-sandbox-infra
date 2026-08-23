const response = await fetch("http://127.0.0.1:8090/v1/chat/completions", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({
    model: "LiquidAI_LFM2.5-2.6B-Q6_K_L",
    messages: [{ role: "user", content: "Reply with exactly STREAM_OK" }],
    max_tokens: 24,
    stream: true,
  }),
});
const text = await response.text();
console.log(JSON.stringify({ status: response.status, hasDone: text.includes("[DONE]"), dataLines: text.split("\n").filter((line) => line.startsWith("data:")).length, preview: text.slice(0, 600) }));
