
minikube delete --all --purge
minikube start --nodes 2 --cpus 2 --memory 2048 

echo ""
echo "=== allocatable CPU per node ==="
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.allocatable.cpu}{"\n"}{end}'
python generate_shards.py
 
docker build --no-cache -t shard-validator:v1 .
minikube image load shard-validator:v1
 
echo ""
echo "=== image present on both nodes ==="
minikube image ls --format table | grep shard-validator
 
echo ""
echo "=== image runs before Kubernetes gets it ==="
docker run --rm -e JOB_COMPLETION_INDEX=0 shard-validator:v1
 
echo ""
echo "=== CPU already requested on each node ==="
kubectl describe nodes | grep -A 4 "Allocated resources"
 
echo ""
echo "=== run the job ==="
kubectl delete job shard-validation --ignore-not-found
kubectl apply -f validation-job.yaml
 
sleep 5
echo ""
echo "=== pods while running ==="
kubectl get pods -l job-name=shard-validation -o wide
 
kubectl wait --for=condition=complete --timeout=300s job/shard-validation
 
echo ""
echo "=== all pods ==="
kubectl get pods -l job-name=shard-validation -o wide
 
echo ""
echo "=== results ==="
python collect_results.py
 
