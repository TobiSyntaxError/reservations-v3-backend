# reservations-v3-backend – Local Dev Setup (Podman + kind + Biletado)

Diese README beschreibt, wie du **von Null** (clean reset) bis zur **laufenden Biletado-Weboberfläche** kommst und dabei den
`reservations`-Service im Cluster durch **dein Django-Backend** ersetzt – genau wie beim Quickstart.

> Umgebung: Windows PowerShell, kind mit Podman Provider

---

## Voraussetzungen (muss installiert sein)

- **Podman** (inkl. Podman Machine)  
  Check:
  ```powershell
  podman version
  podman info
  ```
- **kind**  
  Check:
  ```powershell
  kind version
  ```
- **kubectl**  
  Check:
  ```powershell
  kubectl version --client
  ```

---

## Wichtige Konventionen (damit es nicht wieder hakt)

### Image-Tag
Wir bauen und verwenden absichtlich das Image:

`localhost/reservations-django:local-dev`

Warum: Bei Podman/kind taucht das Image im Node zuverlässig unter `localhost/...` auf. Mit `imagePullPolicy: Never` muss der Name exakt passen.

### deploy/kind/kustomization.yaml
Stelle sicher, dass dein Patch bei `reservations` genau dieses Image nutzt:

```yaml
value: localhost/reservations-django:local-dev
```

---

## 0) In dieses Repo wechseln

```powershell
cd C:\tobi\studium\web2\backend\reservations-v3-backend
```

**Was passiert:** Du arbeitest im Projektordner, damit relative Pfade wie `deploy/kind` funktionieren.

---

## 1) Clean Reset: kind-Cluster löschen und neu erstellen

```powershell
kind delete cluster --name biletado
```
**Was passiert:** Löscht den kompletten Cluster (alles weg).

```powershell
$env:KIND_EXPERIMENTAL_PROVIDER="podman"
```
**Was passiert:** Kind nutzt Podman statt Docker.

```powershell
kind create cluster --name biletado
```
**Was passiert:** Erstellt einen neuen lokalen Kubernetes-Cluster (als Podman-Container “Node”).

```powershell
kubectl cluster-info
```
**Was passiert:** Prüft, ob der Cluster erreichbar ist.

---

## 2) Biletado Stack installieren (wie Quickstart)

```powershell
kubectl create namespace biletado
```
**Was passiert:** Erstellt Namespace `biletado` (isolierter Bereich in Kubernetes).

```powershell
kubectl config set-context --current --namespace biletado
```
**Was passiert:** Setzt deinen default Namespace auf `biletado`.

```powershell
kubectl apply -k "https://gitlab.com/biletado/kustomize.git//overlays/kind?ref=main" --prune -l app.kubernetes.io/part-of=biletado -n biletado
```
**Was passiert:** Installiert die komplette Biletado-Dev-Umgebung (Services/Deployments/Ingresses wie frontend, rapidoc, swagger-ui, postgres, keycloak, reservations, …).  
`--prune` räumt alte Ressourcen auf, die nicht mehr zur aktuellen Konfiguration gehören.

```powershell
kubectl rollout status deployment -n biletado -l app.kubernetes.io/part-of=biletado --timeout=600s
```
**Was passiert:** Wartet, bis alle Deployments erfolgreich ausgerollt sind.

```powershell
kubectl wait pods -n biletado -l app.kubernetes.io/part-of=biletado --for condition=Ready --timeout=240s
```
**Was passiert:** Wartet, bis alle Pods “Ready” sind.

Optionaler Status:
```powershell
kubectl get pods -n biletado
kubectl get svc -n biletado
```

---

## 3) Dein Django Backend als Image bauen

```powershell
podman build -t localhost/reservations-django:local-dev .
```
**Was passiert:** Baut ein Container-Image aus deinem `Containerfile`.

> Hinweis: Bei `src/` Layout muss im Container `PYTHONPATH=/app/src` gesetzt sein (damit `mini_service` importiert werden kann).

---

## 4) Image in kind laden (damit Kubernetes es starten kann)

```powershell
podman save localhost/reservations-django:local-dev --format oci-archive -o reservations-django.tar
```
**Was passiert:** Exportiert das Image als `.tar` (OCI-Archive).

```powershell
kind load image-archive reservations-django.tar -n biletado
```
**Was passiert:** Lädt das Image in den kind-Node. Wichtig für `imagePullPolicy: Never`.

Optionaler Check im Node:
```powershell
podman exec -it biletado-control-plane crictl images | findstr reservations-django
```

---

## 5) `reservations` im Cluster auf dein Image umbiegen (Kustomize Patch)

```powershell
kubectl apply -k deploy/kind --prune -l app.kubernetes.io/part-of=biletado -n biletado
```
**Was passiert:** Wendet dein lokales Kustomize an:
- nutzt Biletado Overlay als Basis
- patcht `deployment/reservations` auf dein Image (und ggf. Port/PullPolicy)

```powershell
kubectl rollout status deployment/reservations -n biletado --timeout=240s
```
**Was passiert:** Wartet, bis dein neues `reservations` Deployment fertig ist.

Optionaler Check:
```powershell
kubectl get deploy reservations -n biletado -o jsonpath="{.spec.template.spec.containers[0].image}{' | '}{.spec.template.spec.containers[0].imagePullPolicy}{'\n'}"
```

---

## 6) Testen (wie Quickstart, per Service port-forward)

```powershell
kubectl port-forward -n biletado svc/reservations 9093:80
```
**Was passiert:** Leitet lokalen Port 9093 auf den Kubernetes Service `reservations` (Port 80) weiter.

In einem zweiten Fenster testen:
```powershell
curl.exe http://localhost:9093/api/v3/reservations/status
curl.exe http://localhost:9093/api/v3/reservations/health
```

---

## 7) Weboberfläche wie Quickstart: alles unter `localhost:9090` (Ingress)

### 7.1 Ingress Controller installieren
```powershell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```
**Was passiert:** Installiert ingress-nginx im Cluster.

```powershell
kubectl wait --namespace ingress-nginx --for=condition=Ready pod --selector=app.kubernetes.io/component=controller --timeout=180s
```
**Was passiert:** Wartet, bis der Ingress Controller bereit ist.

### 7.2 Ingress Controller port-forwarden
```powershell
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 9090:80
```
**Was passiert:** Du erreichst nun alle Ingress-Routen über `http://localhost:9090`.

Im Browser:
- `http://localhost:9090/` (Frontend)
- `http://localhost:9090/rapidoc/` (RapiDoc)
- `http://localhost:9090/swagger-ui/` (Swagger UI)

---

## Update-Loop (nach Codeänderungen)

```powershell
podman build -t localhost/reservations-django:local-dev .
podman save localhost/reservations-django:local-dev --format oci-archive -o reservations-django.tar
kind load image-archive reservations-django.tar -n biletado
kubectl rollout restart deployment/reservations -n biletado
kubectl rollout status deployment/reservations -n biletado --timeout=240s
```
**Was passiert:** neu bauen → in kind laden → Deployment neu starten → warten bis ready.

---

## Debug (wenn etwas hängt)

Status:
```powershell
kubectl get pods -n biletado
```

Events + Gründe:
```powershell
kubectl describe pod -n biletado -l app.kubernetes.io/name=reservations
```

Logs:
```powershell
kubectl logs -n biletado deploy/reservations --tail=200
```

Typische Fehler:
- Image-Name stimmt nicht (muss exakt `localhost/reservations-django:local-dev` sein bei PullPolicy Never)
- Django importiert nicht wegen `src/` → `PYTHONPATH=/app/src` im Containerfile setzen
