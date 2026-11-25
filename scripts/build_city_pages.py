#!/usr/bin/env python3
"""Build one web page per Wizzy city, plus the cities index data.

Only cities that are in the App Store build go on the site, so pass the git
ref of the build that is live (or in review) in the app repo:

    python3 scripts/build_city_pages.py --app ../Wizzy --ref 7d9e4ee

The city list comes from that ref. The text comes from the app repo's working
copy, so fact fixes made after the build still reach the site. Landmarks added
after the build are left out.

Writes:
    cities/<id>.html      one page per city (regenerated each run)
    _data/wizzy.json      city list and totals, used by index.md and cities.md
"""

import argparse
import html
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
RES = "Wizzy/Data/Resources"

CATEGORY_LABELS = {
    "architecture": "Buildings",
    "bridge": "Bridges",
    "church": "Churches",
    "commerce": "Shops and arcades",
    "culture": "Culture",
    "entertainment": "Theatres and venues",
    "fortress": "Forts and walls",
    "government": "Civic buildings",
    "hotel": "Hotels",
    "landmark": "Landmarks",
    "market": "Markets",
    "museum": "Museums",
    "neighbourhood": "Neighbourhoods",
    "palace": "Palaces",
    "park": "Parks and gardens",
    "square": "Squares",
    "transport": "Stations",
    "viewpoint": "Viewpoints",
    "waterfront": "Waterfront",
}

CATEGORY_SINGULAR = {
    "architecture": "Building", "bridge": "Bridge", "church": "Church",
    "commerce": "Shopping", "culture": "Culture", "entertainment": "Venue",
    "fortress": "Fortress", "government": "Civic building", "hotel": "Hotel",
    "landmark": "Landmark", "market": "Market", "museum": "Museum",
    "neighbourhood": "Neighbourhood", "palace": "Palace", "park": "Park",
    "square": "Square", "transport": "Station", "viewpoint": "Viewpoint",
    "waterfront": "Waterfront",
}

e = html.escape


def git(app, *args):
    return subprocess.run(["git", "-C", str(app), *args], check=True,
                          capture_output=True, text=True).stdout


def shipped(app, ref):
    """Landmark file names and landmark ids in the given build."""
    cities, landmarks = [], set()
    for name in git(app, "ls-tree", "--name-only", ref, RES + "/").split():
        if not name.endswith("_landmarks.json"):
            continue
        data = json.loads(git(app, "show", f"{ref}:{name}"))
        cities.append(name.rsplit("/", 1)[-1])
        landmarks.update(l["id"] for l in data["landmarks"])
    return cities, landmarks


def ct(city_id):
    # App Store campaign tokens are at most 40 characters.
    return ("web-" + city_id)[:40]


CREAM = (0.965, 0.933, 0.894)   # #F6EEE4, text on city covers
DEFAULT_COLOURS = ((0.09, 0.36, 0.38), (0.96, 0.77, 0.09))  # WizzyTheme.ocean and gold


def city_colours(app):
    """Each city's cover colour and accent, read from the app's CityIdentity.swift."""
    src = (app / "Wizzy/DesignSystem/CityIdentity.swift").read_text()
    body = src.split("static func forCity", 1)[1].split("        default:", 1)[0]
    rgb = r"Color\(red: ([\d.]+), green: ([\d.]+), blue: ([\d.]+)\)"
    out = {}
    for block in re.split(r"\n        case ", body)[1:]:
        ids = re.findall(r'"([^"]+)"', block.split(":", 1)[0])
        start = re.search(r"start: " + rgb, block)
        accent = re.search(r"accent: " + rgb, block)
        if not (ids and start and accent):
            continue
        colours = (tuple(map(float, start.groups())), tuple(map(float, accent.groups())))
        for cid in ids:
            out[cid] = colours
    return out


def lum(c):
    lin = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def hexc(c):
    return "#" + "".join(f"{round(max(0, min(1, x)) * 255):02X}" for x in c)


def cover_vars(city_id, colours):
    start, accent = colours.get(city_id, DEFAULT_COLOURS)
    # Darken until cream body text passes 4.5:1, then pick an accent that passes too.
    while contrast(start, CREAM) < 4.5:
        start = tuple(x * 0.9 for x in start)
    dark = tuple(x * 0.75 for x in start)
    if contrast(accent, start) < 4.5:
        accent = (0.96, 0.84, 0.58)
        if contrast(accent, start) < 4.5:
            accent = CREAM
    return f"--city: {hexc(start)}; --city-dark: {hexc(dark)}; --city-accent: {hexc(accent)};"


def ping_card(l):
    return f"""<div class="ping" aria-label="Example Wizzy notification">
      <img src="{{{{ '/assets/icon.png' | relative_url }}}}" alt="">
      <div>
        <div class="ping-top"><span>Wizzy</span><span>now</span></div>
        <strong>{e(l['name'])}</strong>
        <p>{e(l['snippet'])}</p>
      </div>
    </div>"""


def meta_label(l):
    meta = CATEGORY_SINGULAR.get(l["category"], l["category"].title())
    built = l.get("builtYear")
    if built:
        year = f"{-built} BCE" if built < 0 else f"{built} CE" if built < 1000 else str(built)
        meta += f" · {year}"
    return meta


def must_see(i, l):
    look = next((x["text"] for x in l.get("extras", []) if x["kind"] == "look"), None)
    out = f"""    <li class="place">
      <span class="num">{i:02d}</span>
      <div>
        <span class="meta">{e(meta_label(l))}</span>
        <h3>{e(l['name'])}</h3>
        <p class="story">{e(l['story'])}</p>"""
    if look:
        out += f"""
        <div class="look"><span class="label">Look for</span><p>{e(look)}</p></div>"""
    return out + "\n      </div>\n    </li>"


def json_ld(city, places, url):
    items = [{
        "@type": "ListItem", "position": i + 1,
        "item": {"@type": "TouristAttraction", "name": l["name"],
                 "description": l["snippet"],
                 "geo": {"@type": "GeoCoordinates",
                         "latitude": l["latitude"], "longitude": l["longitude"]}},
    } for i, l in enumerate(places)]
    data = {"@context": "https://schema.org", "@type": "ItemList",
            "name": f"Landmarks in {city['name']}", "url": url,
            "itemListElement": items}
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def groups(landmarks):
    """The places that aren't must-sees, by category; one-offs go together under "And"."""
    by_cat = defaultdict(list)
    for l in landmarks:
        if l["importance"] < 3:
            by_cat[l["category"]].append(l["name"])
    named = sorted((c for c in by_cat if len(by_cat[c]) > 1),
                   key=lambda c: (-len(by_cat[c]), CATEGORY_LABELS.get(c, c)))
    out = [(CATEGORY_LABELS.get(c, c.title()), sorted(by_cat[c])) for c in named]
    rest = sorted(n for c in by_cat if len(by_cat[c]) == 1 for n in by_cat[c])
    if rest:
        out.append(("And" if out else "Places", rest))
    return out


def page(city, landmarks, neighbours, site_url, colours):
    n = len(landmarks)
    name = e(city["name"])
    top = sorted([l for l in landmarks if l["importance"] == 3], key=lambda l: l["name"])
    first = min(top or landmarks, key=lambda l: len(l["snippet"]))
    more = n - len(top)
    url = f"{site_url}/cities/{city['id']}/"
    desc = (f"{n} places in {city['name']}, {city['country']}, each with a short story. "
            f"Start a walk and Wizzy taps you on the shoulder when you pass one.")
    tops = f" · {len(top)} must-sees" if top else ""

    out = [f"""---
layout: default
cover: true
title: "Walking {city['name']}: the stories behind {n} places"
description: "{desc}"
permalink: /cities/{city['id']}/
---
<!-- Generated by scripts/build_city_pages.py. Edit the script, not this file. -->
<script type="application/ld+json">{json_ld(city, top, url)}</script>
<div class="cover" style="{cover_vars(city['id'], colours)}">
  <div class="wrap">{{% include site-header.html %}}</div>
  <section class="wrap cover-body">
    <div class="cover-text">
      <p class="eyebrow"><a href="{{{{ '/cities/' | relative_url }}}}">{e(city['country'])}</a> · {n} places{tops}</p>
      <h1>{name}<br>on foot</h1>
      <p class="lede">From the big sights to the corners most people walk straight past. Start a walk, put your phone away, and Wizzy taps you when there’s something worth looking up at.</p>
      <div class="cta-row">{{% include appstore-badge.html ct="{ct(city['id'])}" tone="white" %}}</div>
    </div>
    {ping_card(first)}
  </section>
</div>
<main>
"""]
    if top:
        out.append(f"""<section class="wrap section-intro">
  <h2 class="h2">The must-sees</h2>
  <p class="sub">{len(top)} places Wizzy will tap you for first, each with a story and something to look for.</p>
</section>
<div class="wrap">
  <ol class="places">
""" + "\n".join(must_see(i + 1, l) for i, l in enumerate(top)) + "\n  </ol>\n</div>\n")
    g = groups(landmarks)
    if g:
        out.append(f"""<section class="more-band">
  <div class="wrap more">
    <div class="section-head" style="flex-direction: column; align-items: flex-start; gap: 8px;">
      <h2 class="h2">And {more} more in the app</h2>
      <p class="sub">Each with its own short story, waiting for you to walk past.</p>
    </div>
    <dl class="groups">
""" + "\n".join(f'      <div><dt class="label">{e(label)}</dt><dd>{e(", ".join(names))}</dd></div>'
                for label, names in g) + "\n    </dl>\n  </div>\n</section>\n")
    out.append(f"""<section class="wrap closing">
  <div>
    <h2 class="h2">Take {name} with you.</h2>
    <p class="sub">Every place you see gets stamped in your {name} passport. Your location stays on your phone. No ads, no tracking.</p>
  </div>
  {{% include appstore-badge.html ct="{ct(city['id'])}" %}}
</section>
""")
    if neighbours:
        chips = "\n".join(f'      <a class="chip" href="{{{{ \'/cities/{c["id"]}/\' | relative_url }}}}">{e(c["name"])}</a>'
                          for c in neighbours)
        out.append(f"""<div class="wrap"><section class="related">
    <span class="label">Also in {e(city['country'])}</span>
    <div class="chips">
{chips}
    </div>
</section></div>
""")
    out.append("</main>\n")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app", default=str(SITE.parent / "Wizzy"), help="path to the Wizzy app repo")
    ap.add_argument("--ref", required=True, help="git ref of the App Store build")
    ap.add_argument("--url", default="https://mrivolo46.github.io/wizzy-site")
    args = ap.parse_args()
    app = Path(args.app)

    files, landmark_ids = shipped(app, args.ref)
    colours = city_colours(app)
    cities = []
    for name in files:
        path = app / RES / name
        data = json.loads(path.read_text())
        lms = [l for l in data["landmarks"] if l["id"] in landmark_ids]
        cities.append((data["city"], lms))

    by_country = defaultdict(list)
    for c, _ in cities:
        by_country[c["country"]].append(c)

    out_dir = SITE / "cities"
    out_dir.mkdir(exist_ok=True)
    for old in out_dir.glob("*.html"):
        old.unlink()
    for c, lms in cities:
        neighbours = sorted((x for x in by_country[c["country"]] if x["id"] != c["id"]),
                            key=lambda x: x["name"])
        (out_dir / f"{c['id']}.html").write_text(page(c, lms, neighbours, args.url, colours))

    summary = {
        "ref": args.ref,
        "city_count": len(cities),
        "landmark_count": sum(len(l) for _, l in cities),
        "landmark_count_text": f"{sum(len(l) for _, l in cities):,}",
        "countries": [
            {"name": country,
             "cities": [{"id": c["id"], "name": c["name"]}
                        for c in sorted(cs, key=lambda c: c["name"])]}
            for country, cs in sorted(by_country.items())
        ],
        "cities": [{"id": c["id"], "name": c["name"], "country": c["country"], "count": len(l)}
                   for c, l in sorted(cities, key=lambda x: x[0]["name"])],
    }
    (SITE / "_data").mkdir(exist_ok=True)
    (SITE / "_data" / "wizzy.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(cities)} cities, {summary['landmark_count']} landmarks, from {args.ref}")


if __name__ == "__main__":
    main()
