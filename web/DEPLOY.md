# Hosting the website (Render, free plan)

The site needs only what is committed to the repository: `cards.csv` (the day's estimates),
`data/refresh_log.csv` (so the guard can verify the listing), and `data/recent_prices.csv` for the
public one-year history. It does **not** need `prices_all.csv`, which stays on your machine.

## One-time setup

1. Sign in at render.com with your GitHub account.
2. New, then **Blueprint**, then pick the repository `IT25101414/price-signal`. Render reads `render.yaml`.
3. Approve the free web service. The first build takes a few minutes and gives a public `https://...onrender.com` address.
4. Open `/healthz` on that address. It should answer `{"ok":true}`. Then open the address itself.
5. Put the address in the README (top, under the title) and in the report.

A free service sleeps after a period without visitors, and the first request afterwards can take about a minute.
Open the page once shortly before any demo or video.

## Every working day

```
bash run_daily.sh
```

It refreshes from the Central Bank site, rebuilds `cards.csv`, and commits and pushes `cards.csv` and the refresh log.
Render redeploys on each push and rebuilds the database. If the push does not happen, the site keeps the old cards and the
guard withholds every number once the report is more than 3 working days old.

## Check it from outside

```
curl -s https://YOUR-ADDRESS.onrender.com/api/status
```

`state` is `ok`, `stale` or `report_not_read`; `report_date` should be the latest report.

## Local test of the production command

```
python3 -m pip install -r web/requirements.lock
gunicorn --chdir web --bind 127.0.0.1:8000 --workers 1 server:app
```
