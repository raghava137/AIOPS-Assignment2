#!/usr/bin/env bash
# Builds the validator image into minikube, runs the Indexed Job, captures the
# concurrency evidence, and collects results through the Kubernetes API.
set -e

echo "################ cluster ################"
kubectl get nodes -o wide
echo ""
echo "Allocatable CPU per node:"
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.allocatable.cpu}{"\n"}{end}'

echo ""
echo "################ shards + image ################"
python generate_shards.py
eval $(minikube docker-env)          # build straight into minikube's daemon
docker build -t shard-validator:v1 .

echo ""
echo "################ apply the Job ################"
kubectl delete job shard-validation --ignore-not-found
kubectl apply -f validation-job.yaml

echo ""
echo "################ concurrency evidence ################"
echo "Watching for concurrently Running pods. Capture this output."
for i in $(seq 1 40); do
    running=$(kubectl get pods -l job-name=shard-validation \
        --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    echo "t=${i}s  running=${running}"
    if [ "$running" -ge 4 ]; then
        echo ""
        echo ">>> parallelism 4 reached, capturing kubectl get pods -o wide:"
        kubectl get pods -l job-name=shard-validation -o wide
        break
    fi
    sleep 1
done

echo ""
echo "################ wait for completion ################"
kubectl wait --for=condition=complete --timeout=300s job/shard-validation
kubectl get job shard-validation
echo ""
kubectl get pods -l job-name=shard-validation -o wide

echo ""
echo "################ results via the Kubernetes API ################"
python collect_results.py

echo ""
echo "################ check against expected ################"
python - <<'PYEOF'
import json
exp = dict(l.strip().split(",") for l in open("expected_counts.txt"))
res = {r["shard_index"]: r["invalid_rows"] for r in json.load(open("results.json"))}
ok = True
for i in range(8):
    e, g = int(exp[f"shard_{i}"]), res.get(i)
    ok &= (e == g)
    print(f"shard {i}: job={g}  expected={e}  {'OK' if e==g else 'MISMATCH'}")
print("\nall counts match" if ok else "\nMISMATCH present")
PYEOF
