"""Haalt BAG-, 3DBAG- en luchtfotodata op rond één adres (draait in GitHub Actions)."""
import json, re, sys, urllib.request, urllib.parse

UA = {"User-Agent": "Oranjelaan-digital-twin/1.0 (+https://github.com/cobra8nederland-bot/Oranjelaan)"}
OUT = "huis12/data/"
QUERY = "Oranjelaan 12 1901TX Castricum"
R = 70  # meter rondom

def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        b = r.read()
    return b if binary else json.loads(b)

def save(name, obj):
    with open(OUT + name, "w") as f: json.dump(obj, f)
    print("opgeslagen", name)

loc = get("https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?" + urllib.parse.urlencode(
    {"q": QUERY, "fq": "type:adres", "rows": 1, "fl": "*"}))
doc = loc["response"]["docs"][0]
print("adres:", doc.get("weergavenaam"))
save("adres.json", doc)
x, y = map(float, re.findall(r"[-\d.]+", doc["centroide_rd"]))
bbox = (x - R, y - R, x + R, y + R)
bb = ",".join(f"{v:.2f}" for v in bbox)

for name, url, binary in [
    ("bag_pand.json", "https://service.pdok.nl/lv/bag/wfs/v2_0?" + urllib.parse.urlencode({
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeName": "bag:pand",
        "outputFormat": "application/json", "srsName": "EPSG:28992", "bbox": bb + ",urn:ogc:def:crs:EPSG::28992"}), False),
    ("bag_vbo.json", "https://service.pdok.nl/lv/bag/wfs/v2_0?" + urllib.parse.urlencode({
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeName": "bag:verblijfsobject",
        "outputFormat": "application/json", "srsName": "EPSG:28992", "bbox": bb + ",urn:ogc:def:crs:EPSG::28992"}), False),
    ("3dbag.json", "https://api.3dbag.nl/collections/pand/items?" + urllib.parse.urlencode({"bbox": bb, "limit": 100}), False),
    ("luchtfoto.jpg", "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0?" + urllib.parse.urlencode({
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap", "LAYERS": "Actueel_orthoHR", "STYLES": "",
        "CRS": "EPSG:28992", "BBOX": bb, "WIDTH": 2048, "HEIGHT": 2048, "FORMAT": "image/jpeg"}), True),
]:
    try:
        data = get(url, binary)
        if binary:
            open(OUT + name, "wb").write(data); print("opgeslagen", name, len(data), "bytes")
        else:
            save(name, data)
    except Exception as e:
        print("MISLUKT", name, e, file=sys.stderr)

save("meta.json", {"query": QUERY, "center_rd": [x, y], "bbox_rd": bbox})
