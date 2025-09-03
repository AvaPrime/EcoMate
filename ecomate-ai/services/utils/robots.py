import urllib.robotparser as urp
from urllib.parse import urlparse
from functools import lru_cache

AGENT = "EcoMateBot/1.0"

@lru_cache(maxsize=512)
def _rp_for(root: str) -> urp.RobotFileParser:
    rp = urp.RobotFileParser()
    rp.set_url(root + "/robots.txt")
    try:
        rp.read()
    except Exception:
        # Be conservative if robots.txt unreachable
        rp = urp.RobotFileParser()
        rp.parse([f"User-agent: *", "Allow: /"])
    return rp

def allowed(url: str, agent: str = AGENT) -> bool:
    p = urlparse(url)
    root = f"{p.scheme}://{p.netloc}"
    return _rp_for(root).can_fetch(agent, url)