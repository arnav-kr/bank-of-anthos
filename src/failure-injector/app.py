import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, render_template, request
from kubernetes import client, config
from kubernetes.client import ApiException


ANNOTATION_KEY = "failure-injector.local/original-selector"
LEGACY_ANNOTATION_KEY = "failure-injector.bankofanthos.dev/original-selector"


@dataclass
class InjectorState:
    scaled_deployments: dict[str, int] = field(default_factory=dict)
    env_overrides: dict[str, dict[str, str]] = field(default_factory=dict)


class FaultInjector:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.state = InjectorState()
        self._load_cluster_config()
        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()

    def _load_cluster_config(self) -> None:
        try:
            config.load_incluster_config()
            self.logger.info("Using in-cluster Kubernetes config")
        except config.ConfigException:
            config.load_kube_config()
            self.logger.info("Using local kubeconfig")

    @staticmethod
    def _key(namespace: str, name: str) -> str:
        return f"{namespace}/{name}"

    def _deployment(self, namespace: str, deployment: str) -> client.V1Deployment:
        return self.apps.read_namespaced_deployment(name=deployment, namespace=namespace)

    def _service(self, namespace: str, service: str) -> client.V1Service:
        return self.core.read_namespaced_service(name=service, namespace=namespace)

    def _selector_to_query(self, selector: dict[str, str] | None) -> str:
        if not selector:
            return ""
        return ",".join([f"{k}={v}" for k, v in selector.items()])

    def _pods_for_deployment(self, namespace: str, deployment: str) -> list[client.V1Pod]:
        dep = self._deployment(namespace, deployment)
        selector = dep.spec.selector.match_labels or {}
        query = self._selector_to_query(selector)
        pods = self.core.list_namespaced_pod(namespace=namespace, label_selector=query).items
        running = [p for p in pods if p.status.phase == "Running"]
        return sorted(running, key=lambda p: p.metadata.creation_timestamp)

    def _scale_deployment(self, namespace: str, deployment: str, replicas: int) -> dict[str, Any]:
        dep = self._deployment(namespace, deployment)
        original = dep.spec.replicas
        key = self._key(namespace, deployment)
        if key not in self.state.scaled_deployments:
            self.state.scaled_deployments[key] = original

        body = {"spec": {"replicas": replicas}}
        self.apps.patch_namespaced_deployment(name=deployment, namespace=namespace, body=body)
        self.logger.info("Scaled %s to %s replicas", key, replicas)
        return {
            "deployment": deployment,
            "namespace": namespace,
            "originalReplicas": original,
            "newReplicas": replicas,
        }

    def _set_env_var(self, namespace: str, deployment: str, env_name: str, env_value: str) -> dict[str, Any]:
        dep = self._deployment(namespace, deployment)
        container = dep.spec.template.spec.containers[0]
        env = container.env or []

        key = self._key(namespace, deployment)
        if key not in self.state.env_overrides:
            self.state.env_overrides[key] = {}

        existing = None
        for item in env:
            if item.name == env_name:
                existing = item
                break

        if env_name not in self.state.env_overrides[key]:
            self.state.env_overrides[key][env_name] = existing.value if existing else ""

        if existing:
            existing.value = env_value
        else:
            env.append(client.V1EnvVar(name=env_name, value=env_value))

        patch = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": container.name,
                                "env": [{"name": e.name, "value": e.value} for e in env],
                            }
                        ]
                    }
                }
            }
        }

        self.apps.patch_namespaced_deployment(name=deployment, namespace=namespace, body=patch)
        self.logger.info("Set env %s=%s on %s", env_name, env_value, key)
        return {
            "deployment": deployment,
            "namespace": namespace,
            "env": env_name,
            "value": env_value,
        }

    def crash_pod(self, namespace: str, deployment: str) -> dict[str, Any]:
        pods = self._pods_for_deployment(namespace, deployment)
        if not pods:
            raise ValueError(f"No running pods found for deployment '{deployment}'")

        target = pods[0]
        self.core.delete_namespaced_pod(name=target.metadata.name, namespace=namespace)
        self.logger.info("Deleted pod %s in %s", target.metadata.name, namespace)
        return {
            "fault": "pod-crash",
            "namespace": namespace,
            "deployment": deployment,
            "deletedPod": target.metadata.name,
            "expected": "Kubernetes will recreate a fresh pod",
        }

    def resource_pressure(self, namespace: str, deployment: str, replicas: int) -> dict[str, Any]:
        return {
            "fault": "resource-pressure",
            **self._scale_deployment(namespace, deployment, replicas),
            "expected": "Replica count changed to increase pressure",
        }

    def network_partition(self, namespace: str, service: str, deployment: str, action: str) -> dict[str, Any]:
        svc = self._service(namespace, service)
        selector = svc.spec.selector or {}

        if action == "heal":
            annotations = svc.metadata.annotations or {}
            original = annotations.get(ANNOTATION_KEY) or annotations.get(LEGACY_ANNOTATION_KEY)
            if not original:
                raise ValueError("No network partition state found on this service")

            original_selector = json.loads(original)
            annotations.pop(ANNOTATION_KEY, None)
            annotations.pop(LEGACY_ANNOTATION_KEY, None)
            body = {
                "spec": {"selector": original_selector},
                "metadata": {"annotations": annotations},
            }
            self.core.patch_namespaced_service(name=service, namespace=namespace, body=body)
            return {
                "fault": "network-partition",
                "action": "heal",
                "namespace": namespace,
                "service": service,
                "restoredSelector": original_selector,
            }

        pods = self._pods_for_deployment(namespace, deployment)
        if not pods:
            raise ValueError(f"No running pods found for deployment '{deployment}'")

        newest = pods[-1]
        pod_hash = newest.metadata.labels.get("pod-template-hash")
        if not pod_hash:
            raise ValueError("Target pod does not have pod-template-hash label")

        annotations = svc.metadata.annotations or {}
        if ANNOTATION_KEY not in annotations:
            annotations[ANNOTATION_KEY] = json.dumps(selector)

        reroute_selector = dict(selector)
        reroute_selector["pod-template-hash"] = pod_hash
        body = {
            "spec": {"selector": reroute_selector},
            "metadata": {"annotations": annotations},
        }
        self.core.patch_namespaced_service(name=service, namespace=namespace, body=body)

        return {
            "fault": "network-partition",
            "action": "apply",
            "namespace": namespace,
            "service": service,
            "deployment": deployment,
            "reroutedPod": newest.metadata.name,
            "selector": reroute_selector,
            "expected": "Service traffic is pinned to a specific replica revision",
        }

    def latency_injection(
        self,
        namespace: str,
        deployment: str,
        service: str | None,
        mode: str,
        delay_ms: int,
    ) -> dict[str, Any]:
        if mode == "cold-start":
            payload = self.crash_pod(namespace, deployment)
            payload["fault"] = "latency-injection"
            payload["mode"] = "cold-start"
            payload["expected"] = "Cold restart introduces temporary request latency"
            return payload

        if mode == "reroute-fresh-replica":
            dep = self._deployment(namespace, deployment)
            current = dep.spec.replicas or 1
            self._scale_deployment(namespace, deployment, current + 1)
            if not service:
                raise ValueError("service is required for reroute-fresh-replica mode")
            routed = self.network_partition(namespace, service, deployment, "apply")
            routed["fault"] = "latency-injection"
            routed["mode"] = "reroute-fresh-replica"
            routed["requestedDelayMs"] = delay_ms
            routed["note"] = "Delay value is advisory for dashboard tracking"
            return routed

        if mode == "remove":
            if service:
                healed = self.network_partition(namespace, service, deployment, "heal")
            else:
                healed = {
                    "fault": "latency-injection",
                    "mode": "remove",
                    "note": "No service provided, only deployment scale will be restored if tracked",
                }

            key = self._key(namespace, deployment)
            if key in self.state.scaled_deployments:
                original = self.state.scaled_deployments.pop(key)
                self._scale_deployment(namespace, deployment, original)
                healed["restoredReplicas"] = original

            healed["fault"] = "latency-injection"
            healed["mode"] = "remove"
            return healed

        raise ValueError("Unsupported mode. Use cold-start, reroute-fresh-replica, or remove")

    def database_pressure(
        self,
        namespace: str,
        action: str,
        strategy: str,
        target_deployments: list[str],
        throttle_replicas: int,
        loadgenerator_users: int,
    ) -> dict[str, Any]:
        results = []

        if action == "heal":
            for key, original in list(self.state.scaled_deployments.items()):
                ns, dep = key.split("/", 1)
                if ns != namespace:
                    continue
                self._scale_deployment(ns, dep, original)
                self.state.scaled_deployments.pop(key, None)
                results.append({"deployment": dep, "restoredReplicas": original})

            for key, vars_dict in list(self.state.env_overrides.items()):
                ns, dep = key.split("/", 1)
                if ns != namespace:
                    continue
                for env_name, original in vars_dict.items():
                    self._set_env_var(ns, dep, env_name, original)
                    results.append(
                        {
                            "deployment": dep,
                            "env": env_name,
                            "restoredValue": original,
                        }
                    )
                self.state.env_overrides.pop(key, None)

            return {
                "fault": "database-pressure",
                "action": "heal",
                "namespace": namespace,
                "changes": results,
            }

        if strategy == "limit-services":
            for dep in target_deployments:
                results.append(self._scale_deployment(namespace, dep, throttle_replicas))

        elif strategy == "deprioritize-non-critical":
            for dep in target_deployments:
                results.append(self._scale_deployment(namespace, dep, 0))

        elif strategy == "loadgenerator-pressure":
            results.append(self._set_env_var(namespace, "loadgenerator", "USERS", str(loadgenerator_users)))

        elif strategy == "redis-cache":
            results.append(
                {
                    "note": "No Redis component exists in default Bank of Anthos deployment. "
                    "Use 'loadgenerator-pressure' or 'limit-services' instead.",
                }
            )
        else:
            raise ValueError(
                "Unsupported strategy. Use limit-services, deprioritize-non-critical, "
                "loadgenerator-pressure, or redis-cache"
            )

        return {
            "fault": "database-pressure",
            "action": "apply",
            "namespace": namespace,
            "strategy": strategy,
            "changes": results,
        }

    def inventory(self, namespace: str) -> dict[str, Any]:
        deployments = self.apps.list_namespaced_deployment(namespace=namespace).items
        services = self.core.list_namespaced_service(namespace=namespace).items

        return {
            "namespace": namespace,
            "deployments": [
                {
                    "name": d.metadata.name,
                    "replicas": d.spec.replicas,
                    "availableReplicas": d.status.available_replicas or 0,
                }
                for d in deployments
            ],
            "services": [
                {
                    "name": s.metadata.name,
                    "type": s.spec.type,
                    "selector": s.spec.selector or {},
                }
                for s in services
            ],
            "state": {
                "scaledDeployments": self.state.scaled_deployments,
                "envOverrides": self.state.env_overrides,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


def create_app() -> Flask:
    app = Flask(__name__)
    app.logger.handlers = logging.getLogger("gunicorn.error").handlers
    app.logger.setLevel(logging.getLogger("gunicorn.error").level)

    injector = FaultInjector(app.logger)

    @app.route("/", methods=["GET"])
    def dashboard() -> str:
        return render_template("dashboard.html")

    @app.route("/ready", methods=["GET"])
    def ready() -> tuple[str, int]:
        return "ok", 200

    @app.route("/api/inventory", methods=["GET"])
    def inventory() -> tuple[Any, int]:
        namespace = request.args.get("namespace", "default")
        return jsonify(injector.inventory(namespace)), 200

    @app.route("/api/faults/pod-crash", methods=["POST"])
    def pod_crash() -> tuple[Any, int]:
        body = request.get_json(force=True)
        namespace = body.get("namespace", "default")
        deployment = body["deployment"]
        return jsonify(injector.crash_pod(namespace, deployment)), 200

    @app.route("/api/faults/resource-pressure", methods=["POST"])
    def resource_pressure() -> tuple[Any, int]:
        body = request.get_json(force=True)
        namespace = body.get("namespace", "default")
        deployment = body["deployment"]
        replicas = int(body.get("replicas", 3))
        return jsonify(injector.resource_pressure(namespace, deployment, replicas)), 200

    @app.route("/api/faults/network-partition", methods=["POST"])
    def network_partition() -> tuple[Any, int]:
        body = request.get_json(force=True)
        namespace = body.get("namespace", "default")
        service = body["service"]
        deployment = body["deployment"]
        action = body.get("action", "apply")
        return jsonify(injector.network_partition(namespace, service, deployment, action)), 200

    @app.route("/api/faults/latency", methods=["POST"])
    def latency() -> tuple[Any, int]:
        body = request.get_json(force=True)
        namespace = body.get("namespace", "default")
        deployment = body["deployment"]
        service = body.get("service")
        mode = body.get("mode", "cold-start")
        delay_ms = int(body.get("delayMs", 500))
        return jsonify(injector.latency_injection(namespace, deployment, service, mode, delay_ms)), 200

    @app.route("/api/faults/database-pressure", methods=["POST"])
    def database_pressure() -> tuple[Any, int]:
        body = request.get_json(force=True)
        namespace = body.get("namespace", "default")
        action = body.get("action", "apply")
        strategy = body.get("strategy", "limit-services")
        targets = body.get("targetDeployments", ["contacts", "userservice"]) or []
        throttle_replicas = int(body.get("throttleReplicas", 1))
        load_users = int(body.get("loadgeneratorUsers", 100))
        return (
            jsonify(
                injector.database_pressure(
                    namespace,
                    action,
                    strategy,
                    targets,
                    throttle_replicas,
                    load_users,
                )
            ),
            200,
        )

    @app.errorhandler(ApiException)
    @app.errorhandler(ValueError)
    @app.errorhandler(KeyError)
    def handle_bad_request(err: Exception) -> tuple[Any, int]:
        code = 400
        if isinstance(err, ApiException):
            code = err.status if err.status and err.status >= 400 else 500
        return jsonify({"error": str(err)}), code

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception) -> tuple[Any, int]:
        app.logger.exception("Unexpected error")
        return jsonify({"error": str(err)}), 500

    app.logger.info("Failure injector service started")
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
