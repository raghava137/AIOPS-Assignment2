#!/usr/bin/env bash
# Q2 evidence: cache MISS vs cache HIT, median over N rounds.
# Each round uses a different text, so the first call is a real miss.

N=${N:-10}
URL=http://localhost:8080

docker compose up -d --build
sleep 5

echo ""
echo "GET /healthz"
curl -s -w '\n  http_code=%{http_code}\n' $URL/healthz

# Abort early if the API is not actually answering, otherwise the timings
# below would just be measuring how fast curl fails.
CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST $URL/predict \
       -H 'Content-Type: application/json' -d '{"text":"warmup"}')
if [ "$CODE" != "200" ]; then
    echo ""
    echo "ERROR: /predict returned http_code=$CODE, not 200."
    echo "Nothing is being measured. Check:"
    docker compose ps
    docker compose logs api | tail -20
    exit 1
fi

post () {   # $1 = text ; prints "time_total http_code"
    curl -s -o /dev/null -w '%{time_total} %{http_code}' \
         -X POST $URL/predict \
         -H 'Content-Type: application/json' \
         -d "{\"text\":\"$1\"}"
}

echo ""
printf "%-6s %12s %12s %8s\n" "round" "miss(s)" "hit(s)" "code"
echo "-----------------------------------------"

MISSES=""
HITS=""
for i in $(seq 1 "$N"); do
    TEXT="WIN a FREE iPhone number $i! Click here: bit.ly/xyz$i"
    read -r M CODE_M <<< "$(post "$TEXT")"
    read -r H CODE_H <<< "$(post "$TEXT")"
    MISSES="$MISSES $M"
    HITS="$HITS $H"
    printf "%-6s %12s %12s %8s\n" "$i" "$M" "$H" "$CODE_M/$CODE_H"
done

echo ""
python3 -c "
import statistics
miss = [float(x) for x in '''$MISSES'''.split()]
hit  = [float(x) for x in '''$HITS'''.split()]
mm, mh = statistics.median(miss), statistics.median(hit)
print(f'median MISS : {mm*1000:.3f} ms')
print(f'median HIT  : {mh*1000:.3f} ms')
print(f'speedup     : {mm/mh:.2f}x')
"

echo ""
echo "full response, showing the cached flag and server-side timing:"
curl -s -X POST $URL/predict -H 'Content-Type: application/json' \
     -d '{"text":"WIN a FREE iPhone number 1! Click here: bit.ly/xyz1"}'
echo ""
