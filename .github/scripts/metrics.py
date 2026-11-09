"""Gera .github/metrics.svg com métricas do GitHub (PRs, issues, stars, linguagens)."""
import json, os, sys, urllib.request
from datetime import date
from html import escape

USER = "lucas3g"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = os.path.join(os.path.dirname(__file__), "..", "metrics.svg")

QUERY = """
query($login:String!){ user(login:$login){
  pullRequests{totalCount}
  merged: pullRequests(states:MERGED){totalCount}
  open: pullRequests(states:OPEN){totalCount}
  issues{totalCount}
  followers{totalCount}
  contributionsCollection{ contributionCalendar{totalContributions} totalPullRequestReviewContributions }
  repositories(ownerAffiliations:OWNER, isFork:false, first:100){
    totalCount
    nodes{ stargazerCount languages(first:5, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name color } } } }
  }
}}"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
data = json.load(urllib.request.urlopen(req))
if "errors" in data:
    sys.exit(json.dumps(data["errors"]))
u = data["data"]["user"]

stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
langs = {}
for r in u["repositories"]["nodes"]:
    for e in r["languages"]["edges"]:
        n = e["node"]
        langs.setdefault(n["name"], [0, n["color"] or "#8b949e"])[0] += e["size"]
top = sorted(langs.items(), key=lambda x: -x[1][0])[:6]
total = sum(v[0] for _, v in top) or 1

cc = u["contributionsCollection"]
stats = [
    ("Pull requests", u["pullRequests"]["totalCount"], "#3fb950"),
    ("PRs mergeados", u["merged"]["totalCount"], "#a371f7"),
    ("PRs abertos", u["open"]["totalCount"], "#58a6ff"),
    ("Issues", u["issues"]["totalCount"], "#d29922"),
    ("Reviews (12 meses)", cc["totalPullRequestReviewContributions"], "#39c5cf"),
    ("Contribuições (12 meses)", cc["contributionCalendar"]["totalContributions"], "#f778ba"),
    ("Repositórios", u["repositories"]["totalCount"], "#79c0ff"),
    ("Stars recebidas", stars, "#e3b341"),
]

W, PAD = 800, 24
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="330" viewBox="0 0 {W} 330" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
    f'<rect width="{W}" height="330" rx="12" fill="#0d1117" stroke="#30363d"/>',
    f'<text x="{PAD}" y="38" fill="#e6edf3" font-size="18" font-weight="600">Métricas de @{USER}</text>',
]
cw = (W - 2 * PAD - 3 * 12) / 4
for i, (label, value, color) in enumerate(stats):
    x = PAD + (i % 4) * (cw + 12)
    y = 58 + (i // 4) * 92
    parts += [
        f'<rect x="{x}" y="{y}" width="{cw}" height="80" rx="8" fill="#161b22" stroke="#30363d"/>',
        f'<rect x="{x}" y="{y}" width="4" height="80" rx="2" fill="{color}"/>',
        f'<text x="{x+18}" y="{y+40}" fill="{color}" font-size="28" font-weight="700">{value:,}</text>'.replace(",", "."),
        f'<text x="{x+18}" y="{y+62}" fill="#8b949e" font-size="12">{escape(label)}</text>',
    ]
ly = 262
parts.append(f'<text x="{PAD}" y="{ly}" fill="#e6edf3" font-size="13" font-weight="600">Linguagens mais usadas</text>')
x = PAD
bar_w = W - 2 * PAD
parts.append(f'<clipPath id="c"><rect x="{PAD}" y="{ly+10}" width="{bar_w}" height="8" rx="4"/></clipPath><g clip-path="url(#c)">')
for name, (size, color) in top:
    w = bar_w * size / total
    parts.append(f'<rect x="{x:.1f}" y="{ly+10}" width="{w:.1f}" height="8" fill="{color}"/>')
    x += w
parts.append("</g>")
x = PAD
for name, (size, color) in top:
    pct = 100 * size / total
    parts.append(f'<circle cx="{x+5}" cy="{ly+36}" r="5" fill="{color}"/><text x="{x+15}" y="{ly+40}" fill="#8b949e" font-size="12">{escape(name)} {pct:.0f}%</text>')
    x += 28 + 7 * len(name) + 30
parts.append(f'<text x="{W-PAD}" y="38" text-anchor="end" fill="#6e7681" font-size="11">atualizado em {date.today():%d/%m/%Y}</text></svg>')

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print("ok", OUT)
