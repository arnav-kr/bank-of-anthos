# The Bank of Catz - Demo Banking Platform

A modern, microservices-based banking platform with fault injection testing capabilities. Built with Python/Flask backends, Kubernetes, and a modern shadcn/ui-inspired frontend.

**Branding**: *The Bank of Catz* - A fintech demo showcasing modern cloud-native principles.

---

## 📋 Prerequisites

Before running the application, ensure you have the following installed:

- **Minikube** (v1.28+): Local Kubernetes cluster
- **kubectl** (v1.24+): Kubernetes CLI
- **Docker**: Container runtime (included with Docker Desktop)
- **Python** (3.9+): For local development (optional)
- **Maven** (3.6+): For Java microservices builds

**Installation Links**:
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Maven](https://maven.apache.org/download.cgi)

---

## 🚀 Quick Start (First Time Setup)

### Step 1: Start Minikube

```bash
# Start Minikube cluster (allocate resources)
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

### Step 2: Clone & Navigate to Repository

```bash
# Clone the repository (assuming already done)
cd bank-of-anthos

# Verify structure
ls -la src/  # frontend, ledger, accounts, etc.
```

### Step 3: Build Docker Images

The application uses pre-built images, but if you want to rebuild:

```bash
# Build all microservice images in Minikube
for dir in src/*/; do
  SERVICE_NAME=$(basename "$dir")
  minikube image build -t "bank-of-anthos/$SERVICE_NAME:latest" "$dir"
  echo "✓ Built $SERVICE_NAME"
done

# Or build specific services:
minikube image build -t frontend:latest ./src/frontend
minikube image build -t ledger:latest ./src/ledger
minikube image build -t accounts:latest ./src/accounts
```

### Step 4: Deploy to Kubernetes

```bash
# Apply all manifests to your cluster
kubectl apply -f kubernetes-manifests/

# Verify deployments are running
kubectl get deployments
kubectl get pods
kubectl get svc

# Wait for pods to be Ready (may take 1-2 minutes)
kubectl wait --for=condition=ready pod -l app --all --timeout=120s
```

### Step 5: Port-Forward Services

Open separate terminal tabs for each service:

```bash
# Terminal 1: Frontend (Banking UI)
kubectl port-forward svc/frontend 8080:80

# Terminal 2: Failure Injector (Testing Dashboard)
kubectl port-forward svc/failure-injector 8090:8080

# Terminal 3: (Optional) Database port for direct access
kubectl port-forward svc/postgres 5432:5432
```

### Step 6: Access the Application

Once port-forwards are active:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:8080 | Banking UI - Login, view balance, transfer funds |
| **Failure Injector** | http://localhost:8090 | Chaos testing dashboard - Inject failures, observe resilience |

---

## 🎯 Common Workflows

### Workflow 1: Login & Explore Banking UI

1. Navigate to http://localhost:8080/login
2. **Default credentials**:
   - Username: `testuser`
   - Password: `password`
3. Click **Sign in**
4. On dashboard:
   - View **Current Balance**
   - Click **Deposit Funds** to transfer from external account
   - Click **Send Payment** to transfer to another account
   - Review **Transaction History** below

### Workflow 2: Test Failure Scenarios

1. Navigate to http://localhost:8090
2. Enter namespace: `default`
3. Click **Refresh** to load cluster inventory
4. Try scenarios:

   **Pod Crash Test**:
   - Deployment: `frontend`
   - Click **Pod Crash** → observe pod restarts

   **Resource Pressure**:
   - Deployment: `ledger-writer`
   - Replicas: `3`
   - Click **Apply** → watch scaling

   **Database Pressure**:
   - Strategy: `limit-services`
   - Targets: `contacts,userservice`
   - Click **Apply** → monitor impact

5. Click **Heal Changes** to rollback all failures

### Workflow 3: Monitor Logs

```bash
# Watch frontend logs
kubectl logs -f deploy/frontend

# Watch ledger writer logs
kubectl logs -f deploy/ledger-writer

# Follow all pod events
kubectl get events --all-namespaces --watch
```

### Workflow 4: Inspect Database

```bash
# Port-forward PostgreSQL
kubectl port-forward svc/postgres 5432:5432 &

# Connect with psql (install if needed: brew install postgresql)
psql -h localhost -U postgres -d postgres
# Password: (usually blank or "password")

# Common queries:
SELECT * FROM accounts;
SELECT * FROM balances;
SELECT * FROM transactions LIMIT 10;
```

---

## 📁 Project Structure

```
bank-of-anthos/
├── src/
│   ├── frontend/              # Flask UI (Python)
│   │   ├── app.py
│   │   ├── templates/         # HTML templates
│   │   ├── static/
│   │   └── Dockerfile
│   ├── ledger/                # Ledger microservice (Java)
│   ├── accounts/              # Accounts service (Java)
│   ├── ledger-monolith/       # Legacy monolith option
│   ├── userservice/           # User authentication
│   ├── loadgenerator/         # Synthetic traffic generator
│   └── failure-injector/      # Chaos testing dashboard
│
├── kubernetes-manifests/      # K8s deployment files
│   ├── frontend.yaml
│   ├── ledger-writer.yaml
│   ├── accounts-db.yaml
│   ├── balance-reader.yaml
│   └── ... (other services)
│
├── docs/                      # Documentation
├── iac/                       # Infrastructure-as-Code (Terraform)
├── pom.xml                    # Maven parent POM
├── Makefile                   # Convenience commands
└── README.md                  # This file
```

---

## 🛠️ Development

### Local Frontend Development

```bash
# Install Python dependencies
cd src/frontend
pip install -r requirements.txt

# Run Flask app locally (without Kubernetes)
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py

# Access at http://localhost:5000
```

### Running Tests

```bash
# Run end-to-end tests (requires cluster running)
make test-e2e

# Run unit tests (Java services)
cd src/ledger
mvn test

cd ../accounts
mvn test
```

### Building Images Locally

```bash
# Build specific service
docker build -t frontend:dev ./src/frontend
docker build -t ledger:dev ./src/ledger

# Load into Minikube
minikube image load frontend:dev
minikube image load ledger:dev
```

---

## 🔄 Complete Shutdown & Cleanup

```bash
# Delete all Kubernetes resources
kubectl delete -f kubernetes-manifests/

# Stop Minikube
minikube stop

# Full cluster reset (⚠️ deletes everything)
minikube delete

# Restart fresh
minikube start --cpus=4 --memory=8192
```

---

## 🎨 UI Design

The application features a modern, shadcn/ui-inspired design:

- **Clean typography** with Space Grotesk headers and Inter body text
- **Comprehensive color system**: Slate grays + brand blue accent
- **Smart form inputs**: Focus rings, placeholder hints, validation feedback
- **Responsive cards**: Hover effects, smooth transitions
- **Transaction list**: Color-coded credits (green) and debits (red) with icons
- **Modal dialogs**: Clean forms for deposits/payments with proper spacing
- **Success notifications**: Brief, non-intrusive feedback popups
- **Mobile-first responsive** design that works on all screen sizes

---

## 🔧 Configuration

### Environment Variables (Pod-level)

Set in `kubernetes-manifests/config.yaml`:

```yaml
BANK_NAME: "The Bank of Catz"
LOG_LEVEL: "INFO"
DATABASE_URL: "postgresql://postgres:...@postgres/..."
```

### Namespaces

By default, everything deploys to `default` namespace. For multi-environment setups:

```bash
# Deploy to staging
kubectl apply -f kubernetes-manifests/ -n staging

# Deploy to production
kubectl apply -f kubernetes-manifests/ -n production
```

---

## 📊 Architecture

```
┌─────────────────┐
│   Frontend      │ (8080)
│   Flask + UI    │
└────────┬────────┘
         │
    ┌────┴────┬────────┬──────────┐
    │          │        │          │
┌───▼──┐  ┌───▼──┐  ┌──▼──┐  ┌───▼──────┐
│Users │  │Ledger│  │Bal. │  │Contacts  │
│Svc   │  │Writer│  │Read │  │Service   │
└──────┘  └──────┘  └─────┘  └──────────┘
    │
    └─────────────────┐
                      │
              ┌───────▼────────┐
              │  PostgreSQL    │
              │  Database      │
              └────────────────┘
```

---

## 🐛 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name>
kubectl logs <pod-name>

# Common issues:
# - Image not found: Build with minikube image build
# - Database connection: Wait for postgres pod to be ready
# - Memory limits: Increase minikube --memory flag
```

### Port-Forward Not Working

```bash
# Kill hung processes
lsof -ti:8080 | xargs kill -9
lsof -ti:8090 | xargs kill -9

# Restart port-forwards
kubectl port-forward svc/frontend 8080:80 &
kubectl port-forward svc/failure-injector 8090:8080 &
```

### Database Connection Issues

```bash
# Verify postgres is running
kubectl get pod -l app=postgres

# Check database logs
kubectl logs deploy/postgres

# Reset database (⚠️ deletes data)
kubectl delete pvc postgres-storage
kubectl delete pod -l app=postgres
```

### Frontend Shows Stale Data

```bash
# Force image rebuild
minikube image rm frontend:latest
minikube image build -t frontend:latest ./src/frontend

# Restart deployment
kubectl rollout restart deployment/frontend
```

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Minikube Handbook](https://minikube.sigs.k8s.io/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [shadcn/ui Design System](https://ui.shadcn.com/)

---

## 📝 License

Licensed under Apache 2.0. See LICENSE file for details.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

**Last Updated**: March 28, 2026  
**Version**: 1.0.0 (Modern UI)  
**Status**: Production Ready
