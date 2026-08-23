const response = await fetch("http://127.0.0.1:8090/v1/chat/completions", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({
    model: "codex-oauth/gpt-5.5",
    messages: [
      { role: "system", content: "You are a test endpoint. Do not use tools. Reply with exactly CODEX_CONTAINER_OK." },
      { role: "user", content: "Return the required test marker." },
    ],
    max_tokens: 32,
    stream: false,
  }),
});
console.log(response.status, (await response.text()).slice(0, 1000));
