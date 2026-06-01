export async function onRequestGet(context) {
  const { results } = await context.env.DB.prepare(
    "SELECT id, name, message, created_at FROM guestbook ORDER BY created_at DESC LIMIT 50"
  ).all();
  return Response.json(results);
}

export async function onRequestPost(context) {
  const { name, message } = await context.request.json();
  if (!name?.trim() || !message?.trim()) {
    return Response.json({ error: "이름과 메시지를 입력해주세요." }, { status: 400 });
  }
  if (name.length > 50 || message.length > 500) {
    return Response.json({ error: "이름은 50자, 메시지는 500자 이내로 입력해주세요." }, { status: 400 });
  }
  await context.env.DB.prepare(
    "INSERT INTO guestbook (name, message, created_at) VALUES (?, ?, datetime('now'))"
  ).bind(name.trim(), message.trim()).run();
  return Response.json({ success: true });
}
