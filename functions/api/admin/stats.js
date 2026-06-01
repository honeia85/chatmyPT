export async function onRequestGet(context) {
  const totalVisits = parseInt((await context.env.COUNTER.get("visits")) || "0");

  const daily = [];
  const today = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().split('T')[0];
    const count = parseInt((await context.env.COUNTER.get(`visits:${key}`)) || "0");
    daily.push({ date: key, count });
  }

  const { results: gbEntries } = await context.env.DB.prepare(
    "SELECT COUNT(*) as total FROM guestbook"
  ).all();
  const totalGuestbook = gbEntries[0]?.total || 0;

  const todayStr = today.toISOString().split('T')[0];
  const { results: todayGb } = await context.env.DB.prepare(
    "SELECT COUNT(*) as total FROM guestbook WHERE created_at >= ?"
  ).bind(todayStr).all();
  const todayGuestbook = todayGb[0]?.total || 0;

  return Response.json({
    totalVisits,
    todayVisits: daily[daily.length - 1]?.count || 0,
    totalGuestbook,
    todayGuestbook,
    dailyVisits: daily,
  });
}
