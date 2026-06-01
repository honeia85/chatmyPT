export async function onRequestGet(context) {
  const count = (await context.env.COUNTER.get("visits")) || "0";
  return Response.json({ count: parseInt(count) });
}

export async function onRequestPost(context) {
  const today = new Date().toISOString().split('T')[0];
  const current = parseInt((await context.env.COUNTER.get("visits")) || "0");
  const dailyCurrent = parseInt((await context.env.COUNTER.get(`visits:${today}`)) || "0");
  const next = current + 1;
  await context.env.COUNTER.put("visits", next.toString());
  await context.env.COUNTER.put(`visits:${today}`, (dailyCurrent + 1).toString(), { expirationTtl: 86400 * 90 });
  return Response.json({ count: next });
}
