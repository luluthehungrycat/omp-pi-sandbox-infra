const response = await fetch("http://127.0.0.1:8090/v1/chat/completions", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({
    model: "codex-oauth/gpt-5.5",
    messages: [
      { role: "system", content: "You are a test endpoint. Do not use tools. Reply with exactly CODEX_STREAM_OK." },
      { role: "user", content: "Return the required test marker." },
    ],
    max_tokens: 32,
    stream: true,
  }),
});
const text = await response.text();
console.log(JSON.stringify({ status: response.status, hasDone: text.includes("[DONE]"), dataLines: text.split("\n").filter((line) => line.startsWith("data:")).length, preview: text.slice(0, 500) }));
