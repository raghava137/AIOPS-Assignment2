# Module 3 — how to run everything

Four questions, one spam-detection API running through all of them. Each folder
has a `run_qN.sh` that does the work and prints the evidence you need.

## Prerequisites

```bash
docker --version
minikube version
kubectl version --client
pip install kubernetes requests
```

For Q3 and Q4 you need a **2-node** minikube cluster with 2 CPUs each:

```bash
minikube start --nodes 2 --cpus 2 --memory 2048
kubectl get nodes -o wide
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.allocatable.cpu}{"\n"}{end}'
```

That last command is worth screenshotting for Q3 — it evidences the 4-CPU
constraint your parallelism argument rests on.

---

# Q1 — single-stage vs multi-stage (10 marks)

```bash
cd q1
python generate_dataset.py
python train_model.py
bash build_and_measure.sh
```

Builds both images, **starts each and curls `/healthz` and `/predict`** so you
can show they serve rather than merely build, then prints sizes, the percentage
reduction, and the evidence for the written answer.

### What to capture

- the size table from `docker images`
- the computed reduction
- the `gcc` / pip-cache comparison between the two images
- `docker history` for both

### Q1.3 — the written answer (3 marks)

The rubric wants specifics about *your* image. Structure it as: the naive image
keeps the full `python:3.12` base, which carries gcc, the dev headers, the apt
package lists and pip's build machinery; it also keeps `~/.cache/pip`, the
wheel cache left behind by installing scikit-learn, pandas, numpy and scipy.
The multi-stage final image starts from `python:3.12-slim` and receives only
`/opt/venv`, so none of that is present in any layer.

Quote your own numbers. Don't paraphrase this paragraph.

---

# Q2 — Docker Compose + Redis (10 marks)

```bash
cd q2
bash run_q2.sh
```

Brings up both services, proves the API resolves `cache` by service name,
flushes Redis, then benchmarks miss vs hit.

### What to capture

- `docker compose ps` showing both services up
- the DNS proof: `REDIS_HOST=cache resolves to 172.x.x.x` and `PING -> True`
- the benchmark table with per-message miss/hit times and the speedup
- `redis-cli DBSIZE` and the `spam:*` keys

### Q2.4 — the written answer (1 mark)

Compose solves multi-container orchestration **on a single host**: it creates a
shared network so containers find each other by service name, sequences startup
through `depends_on` and healthchecks, and brings the whole stack up or down
with one command. A single Dockerfile produces one image and has no way to
express a relationship between two.

Kubernetes does the same job **across a cluster of machines**, and adds
scheduling onto nodes, self-healing, rolling updates and horizontal scaling.
Compose is a development and single-host tool; Kubernetes is the production,
multi-node one.

---

# Q3 — Kubernetes Indexed Job (10 marks)

```bash
cd q3
bash run_q3.sh
```

Generates 8 shards with known invalid counts, builds the validator image into
minikube's daemon, applies the Job, watches for 4 concurrently Running pods,
then collects results through the Kubernetes API.

### Q3.1 — the parallelism justification (3 marks)

This is the biggest single chunk of marks and it must be an argument, not a
number.

The cluster has 2 nodes x 2 CPUs = **4000m allocatable**. Each validator pod
requests **900m** with requests equal to limits, which puts it in the
Guaranteed QoS class so the scheduler's arithmetic and the runtime ceiling
agree.

```
4 pods x 900m = 3600m  <= 4000m   schedules
5 pods x 900m = 4500m  >  4000m   the 5th pod stays Pending
```

So `parallelism: 4`, and the 8 shards run as two waves of four. 900m rather
than a full 1000m leaves headroom for kubelet, kube-proxy and CNI pods, which
also consume allocatable CPU; requesting a clean 1000m each would mean only
three pods actually fit.

### Q3.2 — concurrency evidence (2 marks)

The script polls until 4 pods are simultaneously `Running` and captures
`kubectl get pods -o wide` at that moment. A manifest permitting parallelism 4
is not the same as 4 pods actually running, which is what the rubric asks for.

### Q3.3 — why the API, not a shared volume (2 marks)

minikube's default provisioner is `standard`, backed by hostPath. A
PersistentVolume it creates lives on the filesystem of one specific node and is
bound there. With pods spread across 2 nodes, a pod scheduled onto the other
node cannot read or write that volume.

Pod stdout has no such constraint: the kubelet on each node captures it
locally, and `read_namespaced_pod_log` through the API server returns it
regardless of where the pod ran. That is why each validator prints one JSON
line and `collect_results.py` reads it back over the API.

### Q3.4 — with 6 CPUs instead (1 mark)

Yes, raise it. 6000m allocatable divided by 900m per pod gives 6 concurrent
pods (5400m used, 600m spare); a 7th would need 6300m and stay Pending. That
turns two waves of four into one wave of six plus one of two, cutting wall
clock time. Beyond 8 there is nothing to gain, since `completions: 8` caps the
work — extra capacity would sit idle.

---

# Q4 — Deployment, self-healing, rolling update (10 marks)

```bash
cd q4
bash run_q4.sh
```

Deploys 2 replicas behind a Service, deletes a pod to show self-healing, then
rolls out v2 while continuously polling `/healthz` to prove no downtime.

### Q4.2 — which controller, and how it decides (3 marks)

The **Deployment** does not manage pods directly. It creates a **ReplicaSet**,
and the **ReplicaSet controller** inside kube-controller-manager owns the pods.

It runs a reconciliation loop: it watches the API server for pods matching its
label selector, compares the count of live pods against `spec.replicas`, and
acts on the difference. Deleting a pod drops the observed count from 2 to 1,
the loop sees 1 != 2, and it creates a replacement with a fresh name. Nothing
"restarts" the old pod — it is gone, and a new one is created to satisfy the
desired count.

### Q4.3 — what if this were a Job (3 marks)

A Job is run-to-completion. It has no rolling-update machinery at all: changing
a Job's pod template is largely immutable, and there is no second ReplicaSet to
shift traffic onto, no `maxSurge`/`maxUnavailable`, and no `kubectl rollout`
subcommand. You would have to delete the Job and create a new one, which means
every pod stops before any new pod starts — a full outage. A Job also stops
once its pods succeed, so it would never stay up to serve requests in the first
place.

### Q4.4 — Deployment vs Job (1 mark)

A serving workload has no natural end: success means staying available, so the
right controller is one that holds a replica count steady forever, replaces
failures, and can swap versions without a gap. That is a Deployment.

A batch workload does have an end: success means every shard was processed
exactly once and then nothing runs. Restarting a finished validator pod would
be wrong, not helpful. That is a Job, and `completions: 8` with
`restartPolicy: Never` encodes precisely that.

---

## Write-up checklist (2 pages)

- [ ] Q1: both image sizes, % reduction, specific explanation
- [ ] Q2: cache hit/miss evidence, Compose vs Kubernetes scope
- [ ] Q3: parallelism arithmetic, concurrency screenshot, per-shard counts, 6-CPU answer
- [ ] Q4: self-healing evidence + controller explanation, rollout status/history, Job contrast
