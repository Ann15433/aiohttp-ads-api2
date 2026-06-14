from aiohttp import web
import uuid
from datetime import datetime, timezone
from models import AdCreate, Ad, ads_db, UserCreate, User, users_db, hash_password, create_jwt_token, verify_password
from middleware import auth_middleware

app = web.Application(middlewares=[auth_middleware])

# Обработчики
async def register(request: web.Request) -> web.Response:
    print("Received POST request to /register")
    try:
        data = await request.json()
        user_create = UserCreate(**data)
    except Exception as e:
        return web.json_response(
            {"error": "Validation error", "details": str(e)},
            status=400
        )

    if any(u['email'] == user_create.email for u in users_db.values()):
        return web.json_response({"error": "User already exists"}, status=400)

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=user_create.email,
        password_hash=hash_password(user_create.password)
    )
    users_db[user_id] = user.model_dump()
    return web.json_response({
        "message": "User registered successfully",
        "user_id": user_id
    }, status=201)

async def login(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        email = data.get('email')
        password = data.get('password')
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    user = None
    for u in users_db.values():
        if u['email'] == email:
            user = u
            break

    if not user or not verify_password(password, user['password_hash']):
        return web.json_response({"error": "Invalid credentials"}, status=401)

    token = create_jwt_token(user['id'])
    return web.json_response({"token": token}, status=200)

async def create_ad(request: web.Request) -> web.Response:
    if 'user_id' not in request:
        return web.json_response({"error": "Authentication required"}, status=401)
    user_id = request['user_id']

    try:
        data = await request.json()
        ad_create = AdCreate(**data)
    except Exception as e:
        return web.json_response(
            {"error": "Validation error", "details": str(e)},
            status=400
        )
    ad_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    ad = Ad(
        id=ad_id,
        title=ad_create.title,
        description=ad_create.description,
        owner_id=user_id,
        created_at=now,
    )
    ads_db[ad_id] = ad
    response_data = ad.model_dump()
    response_data["created_at"] = response_data["created_at"].isoformat()
    return web.json_response(response_data, status=201)

async def get_ad(request: web.Request) -> web.Response:
    ad_id = request.match_info['ad_id']
    ad = ads_db.get(ad_id)
    if not ad:
        return web.json_response({"error": "Ad not found"}, status=404)
    response_data = ad.model_dump()
    response_data["created_at"] = response_data["created_at"].isoformat()
    return web.json_response(response_data)

async def patch_ad(request: web.Request) -> web.Response:
    if 'user_id' not in request:
        return web.json_response({"error": "Authentication required"}, status=401)
    user_id = request['user_id']
    ad_id = request.match_info['ad_id']
    ad = ads_db.get(ad_id)
    if not ad:
        return web.json_response({"error": "Ad not found"}, status=404)
    if ad.owner_id != user_id:
        return web.json_response({"error": "Forbidden: you are not the owner"}, status=403)
    try:
        data = await request.json()
        if 'title' in data:
            ad.title = data['title']
        if 'description' in data:
            ad.description = data['description']
    except Exception as e:
        return web.json_response(
            {"error": "Validation error", "details": str(e)},
            status=400
        )
    ads_db[ad_id] = ad
    response_data = ad.model_dump()
    response_data["created_at"] = response_data["created_at"].isoformat()
    return web.json_response(response_data)

async def delete_ad(request: web.Request) -> web.Response:
    if 'user_id' not in request:
        return web.json_response({"error": "Authentication required"}, status=401)
    user_id = request['user_id']
    ad_id = request.match_info['ad_id']
    ad = ads_db.get(ad_id)
    if not ad:
        return web.json_response({"error": "Ad not found"}, status=404)
    if ad.owner_id != user_id:
        return web.json_response({"error": "Forbidden: you are not the owner"}, status=403)
    del ads_db[ad_id]
    return web.json_response({"status": "deleted"}, status=200)


# Регистрация маршрутов
app.router.add_post('/register', register)
app.router.add_post('/login', login)
app.router.add_post('/ads', create_ad)
app.router.add_get('/ads/{ad_id}', get_ad)
app.router.add_patch('/ads/{ad_id}', patch_ad)
app.router.add_delete('/ads/{ad_id}', delete_ad)

async def hello(request):
    return web.json_response({"message": "Server is running!"})

app.router.add_get('/', hello)

if __name__ == '__main__':
    print("Registered routes:")
    for route in app.router.routes():
        print(f"  {route.method} {route.resource.canonical} -> {route.handler.__name__}")

    web.run_app(app, host='127.0.0.1', port=8000)
