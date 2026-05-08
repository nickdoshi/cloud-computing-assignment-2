#!/usr/bin/env bash

set -u

CONFIG_FILE="${1:-frontent/js/config.js}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Config file not found: $CONFIG_FILE"
    exit 1
fi

BACKEND_URL="$(python3 - "$CONFIG_FILE" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
match = re.search(r"BACKEND_URL\s*=\s*['\"]([^'\"]+)['\"]", text)
if not match:
    raise SystemExit("Could not find BACKEND_URL in config file")
print(match.group(1).rstrip("/"))
PY
)"

PASS_COUNT=0
FAIL_COUNT=0

urlencode() {
    python3 - "$1" <<'PY'
import sys
from urllib.parse import quote

print(quote(sys.argv[1], safe=""))
PY
}

json_get() {
    python3 - "$1" "$2" <<'PY'
import json
import sys

path = sys.argv[2].split(".")
try:
    value = json.loads(sys.argv[1])
    for part in path:
        if part == "len":
            value = len(value)
        elif isinstance(value, list):
            value = value[int(part)]
        else:
            value = value[part]
    print(value)
except Exception:
    print("")
PY
}

json_list_len() {
    python3 - "$1" <<'PY'
import json
import sys

try:
    value = json.loads(sys.argv[1])
    print(len(value) if isinstance(value, list) else 0)
except Exception:
    print(0)
PY
}

record_pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    echo "PASS: $1"
}

record_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "FAIL: $1"
}

request() {
    local label="$1"
    local method="$2"
    local path="$3"
    local expected_status="$4"
    local body="${5:-}"
    local url="${BACKEND_URL}${path}"
    local response_file
    local status

    response_file="$(mktemp)"

    echo
    echo "== $label =="
    if [ -n "$body" ]; then
        echo "curl -X $method '$url' -H 'Content-Type: application/json' -d '$body'"
        status="$(curl -sS -o "$response_file" -w "%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$body")"
    else
        echo "curl -X $method '$url'"
        status="$(curl -sS -o "$response_file" -w "%{http_code}" -X "$method" "$url")"
    fi

    local response
    response="$(cat "$response_file")"
    rm -f "$response_file"

    echo "HTTP $status"
    echo "$response"

    if [ "$status" = "$expected_status" ]; then
        record_pass "$label returned $expected_status"
    else
        record_fail "$label expected $expected_status but got $status"
    fi

    LAST_STATUS="$status"
    LAST_RESPONSE="$response"
}

echo "Using backend URL: $BACKEND_URL"

TEST_EMAIL="backend-test-$(date +%s)@test.com"
TEST_USER="Backend Test"
TEST_PASSWORD="test"
SEEDED_EMAIL="test1@student.rmit.edu.au"
SEEDED_PASSWORD="0123456789"
BAD_PASSWORD="wrong-password"
SONG_TITLE="Love Story"
SONG_ARTIST="Taylor Swift"
SONG_YEAR="2008"
SONG_ALBUM="Fearless"
ENCODED_SEEDED_EMAIL="$(urlencode "$SEEDED_EMAIL")"
SUBSCRIPTION_ID="${SONG_ARTIST}#${SONG_TITLE}"
ENCODED_SUBSCRIPTION_ID="$(urlencode "$SUBSCRIPTION_ID")"

request "health" "GET" "/health" "200"
if [ "$(json_get "$LAST_RESPONSE" "status")" = "ok" ]; then
    record_pass "health body status is ok"
else
    record_fail "health body status is not ok"
fi

request "valid login" "POST" "/login" "200" "{\"email\":\"$SEEDED_EMAIL\",\"password\":\"$SEEDED_PASSWORD\"}"
if [ "$(json_get "$LAST_RESPONSE" "success")" = "True" ]; then
    record_pass "valid login success true"
else
    record_fail "valid login did not return success true"
fi

request "invalid login" "POST" "/login" "401" "{\"email\":\"$SEEDED_EMAIL\",\"password\":\"$BAD_PASSWORD\"}"

request "register unique user" "POST" "/register" "201" "{\"email\":\"$TEST_EMAIL\",\"user_name\":\"$TEST_USER\",\"password\":\"$TEST_PASSWORD\"}"

request "register duplicate user" "POST" "/register" "409" "{\"email\":\"$TEST_EMAIL\",\"user_name\":\"$TEST_USER\",\"password\":\"$TEST_PASSWORD\"}"

request "music query Taylor Swift Fearless" "GET" "/music?artist=Taylor%20Swift&album=Fearless" "200"
RESULT_COUNT="$(json_list_len "$LAST_RESPONSE")"
if [ "${RESULT_COUNT:-0}" -gt 0 ] 2>/dev/null; then
    record_pass "music query returned $RESULT_COUNT result(s)"
else
    record_fail "music query returned no results"
fi

request "get subscriptions before subscribe" "GET" "/subscriptions/$ENCODED_SEEDED_EMAIL" "200"

request "subscribe Love Story" "POST" "/subscriptions" "201" "{\"email\":\"$SEEDED_EMAIL\",\"title\":\"$SONG_TITLE\",\"artist\":\"$SONG_ARTIST\",\"year\":\"$SONG_YEAR\",\"album\":\"$SONG_ALBUM\"}"

request "get subscriptions after subscribe" "GET" "/subscriptions/$ENCODED_SEEDED_EMAIL" "200"

request "remove Love Story subscription" "DELETE" "/subscriptions/$ENCODED_SEEDED_EMAIL/$ENCODED_SUBSCRIPTION_ID" "200"

echo
echo "Summary: $PASS_COUNT passed, $FAIL_COUNT failed"

if [ "$FAIL_COUNT" -ne 0 ]; then
    exit 1
fi
