export async function onRequest(context) {
  const cookie = context.request.headers.get("Cookie") || "";
  const match = cookie.match(/admin_session=([^;]+)/);
  if (!match) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const session = await context.env.COUNTER.get(`session:${match[1]}`);
  if (!session) {
    return Response.json({ error: "Session expired" }, { status: 401 });
  }

  return await context.next();
}
