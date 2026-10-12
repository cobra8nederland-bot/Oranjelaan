"""Zoekt open straatfoto's (Panoramax, Mapillary-vrij) rond Oranjelaan 12."""
import json, re, sys, urllib.request, urllib.parse, os

UA = {"User-Agent": "Oranjelaan-digital-twin/1.0 (+https://github.com/cobra8nederland-bot/Oranjelaan)"}
OUT = "huis12/fotos/"
os.makedirs(OUT, exist_ok=True)
a = json.load(open("huis12/data/adres.json"))
lon, lat = map(float, re.findall(r"[-\d.]+", a["centroide_ll"]))
d = 0.0006  # ~ 60 m
found = []
for base in ["https://api.panoramax.xyz/api", "https://panoramax.ign.fr/api", "https://panoramax.openstreetmap.fr/api"]:
    url = base + "/search?" + urllib.parse.urlencode({"bbox": f"{lon-d},{lat-d/1.6},{lon+d},{lat+d/1.6}", "limit": 40})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            res = json.load(r)
        feats = res.get("features", [])
        print(base, len(feats), "foto's")
        for f in feats:
            found.append({"id": f["id"], "geom": f["geometry"], "datetime": f.get("properties", {}).get("datetime"),
                          "heading": f.get("properties", {}).get("view:azimuth"), "assets": {k: v.get("href") for k, v in f.get("assets", {}).items()},
                          "license": f.get("properties", {}).get("license"), "provider": [p.get("name") for p in f.get("providers", [])], "api": base})
        if feats: break
    except Exception as e:
        print("MISLUKT", base, e, file=sys.stderr)
json.dump(found, open(OUT + "panoramax.json", "w"), indent=1)
# download de 12 dichtstbijzijnde (sd-formaat)
def dist(f):
    x, y = f["geom"]["coordinates"]; return ((x - lon) * 0.6) ** 2 + (y - lat) ** 2
for i, f in enumerate(sorted(found, key=dist)[:12]):
    href = f["assets"].get("sd") or f["assets"].get("hd") or f["assets"].get("thumb")
    if not href: continue
    try:
        with urllib.request.urlopen(urllib.request.Request(href, headers=UA), timeout=120) as r:
            open(OUT + f"{i:02d}_{f['id'][:8]}.jpg", "wb").write(r.read())
        print("foto", i, f["datetime"], f["heading"])
    except Exception as e:
        print("MISLUKT foto", href, e, file=sys.stderr)
