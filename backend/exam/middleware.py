from django.http import HttpResponse


class DevCorsMiddleware:
    """
    Minimal CORS middleware for local React development.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin", "")
        allow_origin = ""
        if origin.startswith("http://localhost:") or origin.startswith(
            "http://127.0.0.1:"
        ):
            allow_origin = origin

        if request.method == "OPTIONS":
            response = HttpResponse(status=200)
        else:
            response = self.get_response(request)
        if allow_origin:
            response["Access-Control-Allow-Origin"] = allow_origin
            response["Vary"] = "Origin"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-User-Id"
        return response
