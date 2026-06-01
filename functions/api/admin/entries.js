export async function onRequestGet(context) {
  const { results } = await context.env.DB.prepare(
    "SELECT id, name, message, created_at FROM guestbook ORDER BY created_at DESC LIMIT 100"
  ).all();
  return Response.json(results);
}

export async function onRequestDelete(context) {
  const url = new URL(context.request.url);
  const id = url.searchParams.get("id");
  if (!id) {
    return Response.json({ error: "id required" }, { status: 400 });
  }
  await context.env.DB.prepare("DELETE FROM guestbook WHERE id = ?").bind(parseInt(id)).run();
  return Response.json({ success: true });
}
