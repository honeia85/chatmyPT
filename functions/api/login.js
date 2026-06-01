export async function onRequestPost(context) {
  const { password } = await context.request.json();
  const adminPw = context.env.ADMIN_PASSWORD;
  if (!adminPw || password !== adminPw) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const token = crypto.randomUUID();
  await context.env.COUNTER.put(`session:${token}`, "1", { expirationTtl: 86400 });

  return new Response(JSON.stringify({ success: true }), {
    headers: {
      "Content-Type": "application/json",
      "Set-Cookie": `admin_session=${token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=86400`,
    },
  });
}
