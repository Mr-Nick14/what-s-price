#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

cluster_name=ml-pro
if ! kind get clusters | grep -Fxq "$cluster_name"; then
  kind create cluster --name "$cluster_name"
fi

kind load docker-image what-s-price:1.0 --name "$cluster_name"
kubectl config use-context "kind-$cluster_name"
kubectl apply -f k8s/configmap.yaml -f k8s/secret.example.yaml -f k8s/postgres.yaml
kubectl rollout status deployment/postgres --timeout=180s
restart_api=false
if kubectl get deployment/what-s-price >/dev/null 2>&1; then
  restart_api=true
fi
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
if [ "$restart_api" = true ]; then
  kubectl rollout restart deployment/what-s-price
fi
kubectl rollout status deployment/what-s-price --timeout=180s
for _ in $(seq 1 30); do
  api_pods=$(kubectl get pods -l app=what-s-price --no-headers | wc -l | tr -d '[:space:]')
  if [ "$api_pods" = 2 ]; then
    break
  fi
  sleep 1
done
if [ "$api_pods" != 2 ]; then
  echo "expected 2 API pods, found $api_pods" >&2
  exit 1
fi
kubectl get pods

kubectl port-forward service/what-s-price 18080:80 >/dev/null 2>&1 &
forward_pid=$!
trap 'kill "$forward_pid" 2>/dev/null || true' EXIT

for _ in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:18080/ready >/dev/null; then
    curl --fail --silent --show-error -X POST http://127.0.0.1:18080/v1/predict \
      -H 'Content-Type: application/json' --data-binary @good.json
    printf '\n'
    exit 0
  fi
  sleep 1
done

echo 'port-forward did not become ready within 30 seconds' >&2
exit 1
