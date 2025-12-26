# Minimal Django (reservations) – Lernprojekt

Dieses Mini-Projekt ist bewusst **sehr klein**, damit du erstmal verstehst, wie alles zusammenhängt.

## Was kann es?
- `GET /api/v3/reservations/status`
- `GET /api/v3/reservations/health`

## 1) Lokal starten (Windows PowerShell)
```powershell
cd minimal-django-reservations
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py manage.py runserver 0.0.0.0:9000
```

Test:
```powershell
curl.exe http://127.0.0.1:9000/api/v3/reservations/status
curl.exe http://127.0.0.1:9000/api/v3/reservations/health
```

## 2) Als Container bauen (Podman)
```powershell
podman build -t reservations-django:local-dev .
```

## 3) In kind laden + in biletado ersetzen (optional)
> Nur nötig, wenn du den `reservations`-Service in der biletado-Umgebung ersetzen willst.

```powershell
podman save reservations-django:local-dev --format oci-archive -o reservations-django.tar
kind load image-archive reservations-django.tar -n biletado

kubectl apply -k deploy/kind --prune -l app.kubernetes.io/part-of=biletado -n biletado
kubectl rollout status deployment/reservations -n biletado --timeout=180s
```

Dann testen:
- wenn du biletado über Ingress auf `localhost:9090` offen hast:
  - `http://localhost:9090/api/v3/reservations/status`
- oder per port-forward:
```powershell
kubectl port-forward -n biletado svc/reservations 9093:80
curl.exe http://localhost:9093/api/v3/reservations/status
```
