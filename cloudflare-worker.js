/**
 * Live-quote CORS proxy for the GitHub Pages dashboard.
 *
 * Yahoo Finance's chart API doesn't send Access-Control-Allow-Origin, so a
 * browser running on github.io can't call it directly. This Worker just
 * forwards the request server-side (no CORS restriction there) and adds the
 * header back on the response.
 *
 * Deploy: Cloudflare dashboard -> Workers & Pages -> Create -> paste this ->
 * Deploy. Copy the resulting *.workers.dev URL and give it to the dashboard
 * generator (LIVE_QUOTE_PROXY_URL in src/site_generator.py).
 *
 * Usage: GET https://<your-worker>.workers.dev/?symbol=RELIANCE.NS
 */
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const symbol = url.searchParams.get("symbol");

    if (!symbol) {
      return json({ error: "missing ?symbol= param" }, 400);
    }

    const yahooUrl = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`;

    try {
      const resp = await fetch(yahooUrl, {
        headers: { "User-Agent": "Mozilla/5.0 (compatible; PriceProxy/1.0)" },
      });
      const data = await resp.json();
      return json(data, resp.status);
    } catch (e) {
      return json({ error: String(e) }, 502);
    }
  },
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "public, max-age=15", // don't hammer Yahoo on every rapid refresh
    },
  });
}
