# Failure Injector Service

Flask-based control plane for fault injection against Bank of Anthos deployments.

## Included fault controls

- Pod Crash: delete one running pod from a deployment.
- Resource Pressure: scale replicas for a deployment.
- Network Partition: patch a service selector to pin traffic to one pod-template revision and heal back.
- Latency Injection: cold-start a pod or reroute to a fresh replica.
- Database Pressure: throttle selected services, deprioritize non-critical services, or increase synthetic load via `loadgenerator`.

## Run locally (outside cluster)

```bash
pip install -r requirements.txt
python app.py
```

It attempts in-cluster config first and falls back to local kubeconfig.

## Build and deploy

Use the manifest file added at:

- `kubernetes-manifests/failure-injector.yaml`

Then port-forward:

```bash
kubectl port-forward svc/failure-injector 8090:8080
```

Open:

- `http://localhost:8090`
