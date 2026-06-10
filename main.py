import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from aiohttp import web
from models import AdCreate, Ad, ads_db


async def create_ad(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    try:
        ad_create = AdCreate(**data)
    except Exception as e:
        return web.json_response({"error": "Validation error", "details": str(e)}, status=400)

    ad_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    ad = Ad(
        id=ad_id,
        title=ad_create.title,
        description=ad_create.description,
        owner=ad_create.owner,
        created_at=now,
    )
    ads_db[ad_id] = ad

    response_data = ad.model_dump()
    response_data["created_at"] = response_data["created_at"].isoformat()

    return web.json_response(response_data, status=201)


async def get_ad(request: web.Request) -> web.Response:
    ad_id = request.match_info.get("id")
    ad = ads_db.get(ad_id)
    if not ad:
        return web.json_response({"error": "Ad not found"}, status=404)

    response_data = ad.model_dump()
    response_data["created_at"] = response_data["created_at"].isoformat()
    return web.json_response(response_data)


async def delete_ad(request: web.Request) -> web.Response:
    ad_id = request.match_info.get("id")
    if ad_id not in ads_db:
        return web.json_response({"error": "Ad not found"}, status=404)
    del ads_db[ad_id]
    return web.json_response({"status": "deleted"}, status=200)


async def patch_ad(request: web.Request) -> web.Response:
    ad_id = request.match_info.get("id")
    ad = ads_db.get(ad_id)
    if not ad:
        return web.json_response({"error": "Ad not found"}, status=404)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    if "title" in data:
        if not (1 <= len(data["title"]) <= 200):
            return web.json_response({"error": "Title length must be 1–200"}, status=400)
        ad.title = data["title"]
    if "description" in data:
        if len(data["description"]) < 1:
            return web.json_response({"error": "Description cannot be empty"}, status=400)
        ad.description = data["description"]
    if "owner" in data:
        if len(data["owner"]) < 1:
            return web.json_response({"error": "Owner cannot be empty"}, status=400)
        ad.owner = data["owner"]

    ads_db[ad_id] = ad

    response_data = ad.model_dump()
    response_data["created_at"] = response_data["created_at"].isoformat()
    return web.json_response(response_data, status=200)


def setup_routes(app: web.Application) -> None:
    app.router.add_post("/ads", create_ad)
    app.router.add_get("/ads/{id}", get_ad)
    app.router.add_delete("/ads/{id}", delete_ad)
    app.router.add_patch("/ads/{id}", patch_ad)


def main() -> None:
    app = web.Application()
    setup_routes(app)
    web.run_app(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
