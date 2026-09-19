#!/usr/bin/env bash
# Q4: deploy, self-healing, rolling update.

eval $(minikube docker-env)
[ -f model.joblib ] || (python generate_dataset.py && python train_model.py)
docker build -t spam-api:v1 .

echo ""
echo "=== deploy ==="
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl rollout status deployment/spam-api
kubectl get pods -l app=spam-api

echo ""
echo "=== self-healing ==="
kubectl get pods -l app=spam-api
VICTIM=$(kubectl get pods -l app=spam-api -o jsonpath='{.items[0].metadata.name}')
echo "deleting $VICTIM"
kubectl delete pod "$VICTIM"
sleep 10
kubectl get pods -l app=spam-api

echo ""
echo "=== rolling update ==="
docker build -t spam-api:v2 --build-arg APP_VERSION=v2 .
kubectl set image deployment/spam-api api=spam-api:v2
kubectl rollout status deployment/spam-api
kubectl rollout history deployment/spam-api
kubectl get pods -l app=spam-api
curl $(minikube service spam-api-svc --url)/healthz


