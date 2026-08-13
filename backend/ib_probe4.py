import httpx
from html.parser import HTMLParser

resp = httpx.get(
    "https://www.interviewbit.com/profile/royalpranjal",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=20,
    follow_redirects=True,
)

# Extract meta tags
class MetaExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metas = {}
        self.title = ""
    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            d = dict(attrs)
            name = d.get("name") or d.get("property") or d.get("itemprop")
            if name and d.get("content"):
                self.metas[name] = d["content"]
        if tag == "title":
            pass
    def handle_data(self, data):
        pass

extractor = MetaExtractor()
extractor.feed(resp.text)

print("Title:", resp.text[resp.text.find("<title>")+7:resp.text.find("</title>")] if "<title>" in resp.text else "N/A")
print("\nMeta tags:")
for k, v in extractor.metas.items():
    print(f"  {k}: {v}")

# Also look for JSON-LD
import re
import json
ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', resp.text, re.DOTALL)
for m in ld_matches:
    try:
        print("\nJSON-LD:", json.dumps(json.loads(m), indent=2)[:500])
    except Exception:
        pass
