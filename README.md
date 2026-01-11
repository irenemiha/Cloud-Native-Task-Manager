## Project: Cloud-Native Task Manager (Microservices)
### Obiectiv General
Acest proiect implementează o aplicație de gestionare a sarcinilor (Task Manager) folosind o arhitectură de tip microservicii, containerizată cu Docker și orchestrată în Kubernetes. Proiectul demonstrează utilizarea conceptelor de Cloud Computing învățate în laboratoarele 1-5.

### Arhitectura Sistemului
Aplicația este compusă din 5 microservicii independente:

1. **Auth Service (Python/Flask)**: Gestionează înregisrtarea, autentificarea utilizatorilor și validarea token-urilor.

2. **Task Service (Business Logic - Python/Flask)**: Serviciul principal pentru operațiuni CRUD asupra sarcinilor. Poate fi accesat doar de un token valid (user autentificat) și asigură izolarea datelor între utilizatori.

3. **Database Service (MySQL)**: Stocare persistentă a datelor: utilizatori, token-uri, task-uri (folosește PersistentVolumeClaim).

4. **Adminer**: Interfață grafică pentru administrarea bazei de date MySQL.

5. **Portainer**: Instrument de gestiune vizuală a resurselor din clusterul Kubernetes.

6. **Frontend Service** (HTML/JS): Interfață web tip "Weekly Planner" pentru gestionarea sarcinilor, cu funcționalități de Register, Login, Logout și CRUD și drag-and-drop pentru task-uri. 

### Tehnologii Utilizate
- **Containerizare**: Docker
- **Orchestrare**: Kubernetes (Cluster Kind)
- **Package Management**: Helm v3
- **Monitorizare**: Prometheus & Grafana
- **Limbaj**: Python (Flask)

### Ghid de Instalare
**1. Pregătirea clusterului**
```bash
# Permisiuni Docker (dacă este necesar)
sudo usermod -aG docker $USER
newgrp docker

# Creare cluster
kind create cluster --name task-manager-cluster
```

**2. Construirea și încărcarea imaginilor**
```bash
# Build Auth Service
cd auth-service
docker build -t auth-service:v1 .

# Build Task Service
cd ../task-service
docker build -t task-service:v1 .

# Build Frontend Service
cd ../frontend
docker build -t frontend-service:v1 .

# Încărcare imagini în Kind
kind load docker-image auth-service:v1 --name task-manager-cluster
kind load docker-image task-service:v1 --name task-manager-cluster
kind load docker-image frontend-service:v1 --name task-manager-cluster
```

**3. Instalarea aplicației cu Helm**
```bash
cd ../helm-chart
helm install task-manager-app ./task-manager

# Verificare status
kubectl get pods
```

**4. Setup Baza de Date**
1. Deschideți Adminer: `kubectl port-forward svc/adminer-service 8080:8080`
2. Accesați `http://localhost:8080` (Server: `mysql-service`, User: `root`, Pass: `password`).
3. Rulați SQL:
```sql
CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    deadline DATE,
    urgency ENUM('Low', 'Medium', 'High') DEFAULT 'Low',
    status VARCHAR(10) DEFAULT 'NEW'
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE tokens (
    token VARCHAR(64) PRIMARY KEY,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

ALTER TABLE tasks ADD COLUMN user_id INT;
```

**5. Monitorizare (Prometheus & Grafana)**
```bash
# Instalare Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# Instalare Prometheus/Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack
```

### Verificare Funcționalități
**Testare Autentificare & Business Logic:**
1. Pornire Tuneluri:
- `kubectl port-forward svc/auth-service 5001:5001`
- `kubectl port-forward svc/task-service 5002:5002`
- `kubectl port-forward svc/frontend-service 8081:80`

2. Obținere Token:
```bash
curl -X POST http://localhost:5001/register -H "Content-Type: application/json" -d '{"username": "admin", "password": "password"}'
curl -X POST http://localhost:5001/login -H "Content-Type: application/json" -d '{"username": "admin", "password": "password"}'
```
Înregistrarea se poate face cu orice user și parolă (atâta timp cat username-ul nu a fost deja folosit). După logare, se afișează un token. Acesta trebuie copiat pentru a fi folosit in urmatorul pas.

3. Accesare Task-uri:
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:5002/tasks
```

4. Accesare Frontend:
Deschideți browserul și accesați: `http://localhost:8081`
(Asigurați-vă că tunelul către `frontend-service` din pasul 1 este activ).

5. Monitorizare:

Accesare Grafana:
- `kubectl get secret monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo`
- `kubectl port-forward svc/monitoring-grafana 3000:80`
Se accesează `http://localhost:3000`. La login, se folosesc user: `admin` și parola obținută.

Accesare Prometheus:
- `kubectl port-forward svc/monitoring-prometheus 9090:90`
Se accesează `http://localhost:9090`.

Accesare Portainer:
- `kubectl port-forward svc/portainer-service 9000:9000`
Se accesează `http://localhost:9000`.