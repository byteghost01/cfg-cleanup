"""CF Gallery clean-up — lets the CF Gallery app delete images it has already downloaded, so its
generations don't stay on this server (CF Gallery decision D-028).

Install: copy this `cfg_cleanup` folder into `ComfyUI/custom_nodes/` and restart ComfyUI.
Adds no nodes, only two routes:

  GET  /cfg/cleanup   → {"version": 1}   (the app checks that the plugin is installed)
  POST /cfg/cleanup   {"files": [{"filename", "subfolder", "type"}, …]}
                      → {"deleted": [...], "missing": [...], "refused": [...]}

What may be deleted is in `rules.py`: in `output/` only files named `cfg_…` (the app's own), in
`temp/` any image. Everything else is refused.
"""
import logging
import os

from aiohttp import web

import folder_paths
from server import PromptServer

from .rules import target

VERSION = 1
NODE_CLASS_MAPPINGS = {}           # no nodes; ComfyUI still loads the package (and its routes)
NODE_DISPLAY_NAME_MAPPINGS = {}

log = logging.getLogger("cfg_cleanup")
routes = PromptServer.instance.routes


@routes.get("/cfg/cleanup")
async def info(request):
    return web.json_response({"version": VERSION})


@routes.post("/cfg/cleanup")
async def delete_files(request):
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "expected JSON"}, status=400)
    files = body.get("files") if isinstance(body, dict) else None
    if not isinstance(files, list):
        return web.json_response({"error": "expected {\"files\": [...]}"}, status=400)
    dirs = {"output": folder_paths.get_output_directory(), "temp": folder_paths.get_temp_directory()}
    out = {"deleted": [], "missing": [], "refused": []}
    for item in files:
        name = item.get("filename") if isinstance(item, dict) else None
        path = target(item, dirs)
        if path is None:
            out["refused"].append(name)
            continue
        try:
            os.remove(path)
            out["deleted"].append(name)
        except FileNotFoundError:
            out["missing"].append(name)
        except OSError as e:
            log.warning("cfg_cleanup: couldn't delete %s: %s", path, e)
            out["refused"].append(name)
    return web.json_response(out)


log.info("cfg_cleanup %s: CF Gallery clean-up route ready at /cfg/cleanup", VERSION)
