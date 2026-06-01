export async function onRequestGet(context) {
  const count = (await context.env.COUNTER.get("visits")) || "0";
  return Response.json({ count: parseInt(count) });
}

export async function onRequestPost(context) {
  const current = parseInt((await context.env.COUNTER.get("visits")) || "0");
  const next = current + 1;
  await context.env.COUNTER.put("visits", next.toString());
  return Response.json({ count: next });
}
