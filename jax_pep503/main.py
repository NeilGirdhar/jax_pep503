from datetime import datetime, timedelta
import re
from typing import Final

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import httpx
import yarl


VERSION: Final = "1.0"
JAX_URL: Final = yarl.URL("https://storage.googleapis.com/jax-releases/")
PATTERN_XML_KEY = re.compile(r'<Key>(.*?)</Key>')
RESCRAPE_INTERVAL = timedelta(days=1)

app: Final = FastAPI()
templates: Final = Jinja2Templates(directory="templates")


_last_scrape = datetime.min
_jaxlib_links = None


async def get_jaxlib_links() -> dict[str, str]:
    global _last_scrape, _jaxlib_links

    if not _jaxlib_links or datetime.now() - _last_scrape > RESCRAPE_INTERVAL:
        _jaxlib_links = await _get_jaxlib_links()
        _last_scrape = datetime.now()

    return _jaxlib_links


async def _get_jaxlib_links() -> dict[str, str]:
    # TODO cache
    links = {}

    async with httpx.AsyncClient() as client:
        r: httpx.Response = await client.get(str(JAX_URL))
        r.raise_for_status()

        xml = r.text
        for match in re.findall(PATTERN_XML_KEY, xml):
            if not match.endswith('.whl'):
                continue

            links[match] = str(JAX_URL / match)

    return links


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "version": VERSION,
    })


@app.get("/jaxlib/", response_class=HTMLResponse)
async def package_jaxlib(request: Request):
    links = await get_jaxlib_links()

    return templates.TemplateResponse("package.html", {
        "request": request,
        "version": VERSION,
        "name": "jaxlib",
        "links": links,
    })