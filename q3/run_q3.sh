
minikube delete --all --purge
minikube start --nodes 2 --cpus 2 --memory 2048 


kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.allocatable.cpu}{"\n"}{end}'
python generate_shards.py
 
docker build --no-cache -t shard-validator:v1 .
minikube image load shard-validator:v1
 

minikube image ls --format table | grep shard-validator
 

docker run --rm -e JOB_COMPLETION_INDEX=0 shard-validator:v1
 

kubectl describe nodes | grep -A 4 "Allocated resources"

kubectl delete job shard-validation --ignore-not-found
kubectl apply -f validation-job.yaml
 
sleep 5

kubectl get pods -l job-name=shard-validation -o wide
 
kubectl wait --for=condition=complete --timeout=300s job/shard-validation

kubectl get pods -l job-name=shard-validation -o wide

python collect_results.py
 
