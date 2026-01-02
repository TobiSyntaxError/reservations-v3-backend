import jwt
import os
from functools import wraps 
from django.http import JsonResponse

def jwt_auth_required(func):
    @wraps(func) # Das hast du importiert, also nutzen wir es auch (gute Praxis)
    def wrapper(request, *args, **kwargs):
        # 1. Token aus dem Header abrufen.
        header = request.headers.get('Authorization', '')
        
        if not header.startswith('Bearer '):
            # HIER WAR DER FEHLER: { } hinzugefügt
            return JsonResponse({"error": "Fehlender oder falscher Token"}, status=401)
                
        token = header.split(' ')[1]

        # 2. Key holen & Docker-Problem (\n) fixen
        # Achte darauf, dass der Name exakt so ist wie in deiner docker-compose/k8s config
        pk = os.environ.get("JWT_PUBLIC_KEY", "").replace('\\n', '\n')
        
        if not pk:
             return JsonResponse({"error": "Server Konfigurationsfehler (Key fehlt)"}, status=500)

        try:
            jwt.decode(token, pk, algorithms=["RS256"], options={"verify_aud": False})
        except Exception:
            # Token ungültig
            return JsonResponse({"error": "Zugriff verweigert (Token ungültig)"}, status=401)

        # 3. Alles gut -> Weiter zur View
        return func(request, *args, **kwargs)
        
    return wrapper