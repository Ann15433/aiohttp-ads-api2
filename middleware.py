from aiohttp import web
from models import decode_jwt_token

async def auth_middleware(app, handler):
    async def middleware_handler(request):
        # ПРОПУСКАЕМ ПУБЛИЧНЫЕ МАРШРУТЫ В САМОМ НАЧАЛЕ
        if (
            request.path in ['/', '/register', '/login']
            or (request.path.startswith('/ads/') and request.method == 'GET')
        ):
            return await handler(request)

        # Теперь проверяем авторизацию для остальных маршрутов
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return web.json_response(
                {"error": "Authorization required"},
                status=401
            )

        token = auth_header[7:]  # убираем 'Bearer '

        try:
            payload = decode_jwt_token(token)
            if not payload:
                return web.json_response(
                    {"error": "Invalid or expired token"},
                    status=401
                )

            if 'user_id' not in payload:
                return web.json_response(
                    {"error": "Token is missing user_id"},
                    status=401
                )

            request['user_id'] = payload['user_id']

        except Exception as e:
            print(f"Error decoding JWT token: {e}")
            return web.json_response(
                {"error": "Invalid token format"},
                status=401
            )

        return await handler(request)
    return middleware_handler
