# AIOps Assignment2

Raghava · DA24B021

link for video recording:https://drive.google.com/file/d/1ndvMXfRVBExD6d2QnXg2j1T9F0YJv5U-/view?usp=sharing
Docker and Kubernetes coursework, built around a spam-detection API.
Write-up for all four questions is `report.pdf`.

## Layout

```
report.pdf    the write-up
q1/           naive vs multi-stage Docker build
q2/           Compose: the API plus a Redis cache
q3/           Kubernetes Indexed Job over 8 CSV shards
q4/           Kubernetes Deployment, self-healing, rolling update
```

In each of the question folder there is a folder with name (#nameproof) folder containing screenshot proofs
## q1

The API itself: `app.py` serves `/predict` and `/healthz`,
`train_model.py` writes the `model.joblib` it loads. `Dockerfile.naive` is the
single-stage build, `Dockerfile` the multi-stage one.

```bash
python generate_dataset.py && python train_model.py
bash build_and_measure.sh
```

Builds both images, checks each one serves, prints the sizes.

## q2

Same API with Redis in front of the model. `app.py` here is not the same file as
q1's, it has the cache logic and `requirements.txt` adds `redis`.

```bash
bash run_q2.sh
```

Brings the stack up and times ten cache miss / hit pairs.

## q3

Unrelated to the spam API. `generate_shards.py` writes 8 CSVs with a known
number of bad rows, `validate_shard.py` checks one of them chosen by
`JOB_COMPLETION_INDEX`, and `collect_results.py` reads the results back out of
pod logs through the Kubernetes API.

```bash
bash run_q3.sh
```

Rebuilds the cluster with 2 CPUs per node, since `--cpus` is only read at
creation time.

## q4

q1's API deployed to Kubernetes with 2 replicas behind a Service.

```bash
bash run_q4.sh
```

Deploys, deletes a pod to show it come back, then rolls out v2.

## Notes

`model.joblib`, `spam_dataset.csv` and `q3/shards/` are gitignored. The scripts
that make them are seeded, so running them gives the same files back.

AI use is disclosed in `AI_DISCLOSURE.md`.
