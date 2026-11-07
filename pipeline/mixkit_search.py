"""List Mixkit free stock video results (id + title) for search terms.

Usage: python3 mixkit_search.py "term one" "term two" ...
"""
import re, sys, urllib.request

for term in sys.argv[1:]:
    url = "https://mixkit.co/free-stock-video/" + term.strip().replace(" ", "-") + "/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf8", "replace")
    except Exception as e:
        print(f"## {term}: ERROR {e}")
        continue
    items = re.findall(r'videos/(\d+)/\1-thumb-360-0\.jpg" class="item-grid-video-player__thumb" alt="([^"]*)"', html)
    print(f"## {term} ({len(items)})")
    for vid, title in items[:14]:
        print(f"  {vid}: {title}")
