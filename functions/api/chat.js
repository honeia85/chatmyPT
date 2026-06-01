export async function onRequestPost(context) {
  const { message, history } = await context.request.json();
  if (!message?.trim()) {
    return Response.json({ error: "메시지를 입력해주세요." }, { status: 400 });
  }

  const messages = [
    { role: "system", content: "You are a friendly, helpful AI assistant. Respond in Korean. Keep responses concise (under 200 words)." },
  ];

  if (history?.length) {
    for (const h of history.slice(-6)) {
      messages.push({ role: "user", content: h.user });
      messages.push({ role: "assistant", content: h.ai });
    }
  }

  messages.push({ role: "user", content: message.trim() });

  const result = await context.env.AI.run("@cf/meta/llama-3.1-8b-instruct", { messages });

  return Response.json({ response: result.response });
}
