agents-cli deploy \
  --project gem-creation \
  --region us-east1 \
  --service-account barred-fleet-runtime@gem-creation.iam.gserviceaccount.com \
  --min-instances 0 \
  --max-instances 1 \
  --concurrency 1 \
  --no-confirm-project


make verify-demo



# query for dry run

SERVICE_URL="https://barred-fleet-837262597425.us-east1.run.app"
TOKEN="$(gcloud auth print-identity-token)"
RUN_ID="safety-receipt-smoke-$(date +%Y%m%d%H%M%S)"

curl -sS \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  "$SERVICE_URL/runs" \
  -d "{
    \"seed_id\": \"fixture:first\",
    \"run_id\": \"$RUN_ID\",
    \"dry_run\": true,
    \"max_attempts\": 1
  }" | python3 -m json.tool

curl -sS \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  "$SERVICE_URL/runs/$RUN_ID/report" \
  | python3 -m json.tool









make verify-demo



token="$(gcloud auth print-identity-token)"

curl -sS \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json" \
  "https://barred-fleet-837262597425.us-east1.run.app/seeds/manifest" \
  | python3 -m json.tool



SERVICE_URL="https://barred-fleet-837262597425.us-east1.run.app"
TOKEN="$(gcloud auth print-identity-token)"

curl -sS \
  -H "Authorization: Bearer $TOKEN" \
  "$SERVICE_URL/demo" \
  | head -40


SERVICE_URL="https://barred-fleet-837262597425.us-east1.run.app"
TOKEN="$(gcloud auth print-identity-token)"

curl -sS \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  "$SERVICE_URL/demo/report" \
  | python3 -m json.tool



curl -sS \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" \
  "$SERVICE_URL/seeds/manifest" \
  | python3 -m json.tool



cd /Users/surfiniaburger/Desktop/modular-metacog-swarm-v3/agent_training/silver-one/barred-fleet
make verify-demo


gcloud projects add-iam-policy-binding gem-creation \
  --member=user:jdmasciano2@gmail.com \
  --role=roles/modelarmor.admin \
  --quiet \
  --condition=None


gcloud model-armor templates create barred-seed-screen-v1 \
  --project=gem-creation \
  --location=us-east1 \
  --malicious-uri-filter-settings-enforcement=enabled \
  --quiet \
  --condition=None  





## Model Armor for seed input screening and Agent Gateway for route egress verification.