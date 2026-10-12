#!/usr/bin/env bash
# Build dist/ and publish it to a storage static website. A dedicated Front Door is opt-in.
#
#   ./infra/deploy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUBSCRIPTION="${SUBSCRIPTION:-1e238434-310b-4bcd-ab1f-a9381d170243}"
RG="${RG:-rg-bluemask-wehi-sandbox}"
PREFIX="${PREFIX:-bluemask}"
LOCATION="${LOCATION:-centralindia}"
DEPLOYMENT="${PREFIX}-static"
DEPLOY_FRONT_DOOR="${DEPLOY_FRONT_DOOR:-false}"

if [[ "$DEPLOY_FRONT_DOOR" != true && "$DEPLOY_FRONT_DOOR" != false ]]; then
  echo "DEPLOY_FRONT_DOOR must be true or false" >&2
  exit 1
fi

az account set --subscription "$SUBSCRIPTION"

echo "Building dist/..."
python3 "$ROOT/build.py"

deploy_storage() {
  az deployment group create \
    --resource-group "$RG" \
    --name "$DEPLOYMENT" \
    --template-file "$ROOT/infra/main.bicep" \
    --parameters \
      prefix="$PREFIX" \
      location="$LOCATION" \
      deployFrontDoor=false \
    --query "properties.outputs" \
    --output json
}

echo "Deploying storage account..."
OUTPUTS="$(deploy_storage)"
ACCOUNT="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["storageAccountName"]["value"])' "$OUTPUTS")"
ORIGIN_URL="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["staticWebsiteUrl"]["value"])' "$OUTPUTS")"

AUTH=(--account-name "$ACCOUNT" --auth-mode key)
echo "Enabling static website on ${ACCOUNT}..."
az storage blob service-properties update \
  "${AUTH[@]}" \
  --static-website \
  --index-document index.html \
  --output none

echo "Uploading dist/ to \$web..."
az storage blob upload-batch \
  "${AUTH[@]}" \
  --source "$ROOT/dist" \
  --destination '$web' \
  --overwrite \
  --output none

keep_file="$(mktemp)"
(
  cd "$ROOT/dist"
  find . -type f ! -name '_headers' ! -name '_redirects' -print | sed 's|^\./||' | sort
) > "$keep_file"
while IFS= read -r blob; do
  [ -n "$blob" ] || continue
  if ! grep -Fxq -- "$blob" "$keep_file"; then
    echo "Removing stale blob ${blob}"
    az storage blob delete \
      "${AUTH[@]}" \
      --container-name '$web' \
      --name "$blob" \
      --output none
  fi
done < <(az storage blob list "${AUTH[@]}" --container-name '$web' --query '[].name' --output tsv)
rm -f "$keep_file"

for page in index.html privacy.html terms.html support.html about tests offline guides/redact-sensitive-information-from-screenshots privacy terms support; do
  az storage blob update \
    "${AUTH[@]}" \
    --container-name '$web' \
    --name "$page" \
    --content-type 'text/html; charset=utf-8' \
    --content-cache-control 'public, max-age=0, must-revalidate' \
    --output none
done

az storage blob update \
  "${AUTH[@]}" \
  --container-name '$web' \
  --name BlueMask.html \
  --content-type 'text/html; charset=utf-8' \
  --content-disposition 'attachment; filename="BlueMask.html"' \
  --content-cache-control 'public, max-age=0, must-revalidate' \
  --output none

az storage blob update "${AUTH[@]}" --container-name '$web' --name llms.txt --content-type 'text/plain; charset=utf-8' --content-cache-control 'public, max-age=0, must-revalidate' --output none
az storage blob update "${AUTH[@]}" --container-name '$web' --name robots.txt --content-type 'text/plain; charset=utf-8' --content-cache-control 'public, max-age=0, must-revalidate' --output none
az storage blob update "${AUTH[@]}" --container-name '$web' --name SHA256SUMS --content-type 'text/plain; charset=utf-8' --content-cache-control 'public, max-age=0, must-revalidate' --output none
az storage blob update "${AUTH[@]}" --container-name '$web' --name sitemap.xml --content-type 'application/xml; charset=utf-8' --content-cache-control 'public, max-age=0, must-revalidate' --output none
az storage blob update "${AUTH[@]}" --container-name '$web' --name manifest.json --content-type 'application/json; charset=utf-8' --content-cache-control 'public, max-age=0, must-revalidate' --output none

while IFS= read -r asset; do
  blob="${asset#"$ROOT/dist/"}"
  az storage blob update \
    "${AUTH[@]}" \
    --container-name '$web' \
    --name "$blob" \
    --content-cache-control 'public, max-age=31536000, immutable' \
    --output none
done < <(find "$ROOT/dist/assets" "$ROOT/dist/og" -type f -print)

echo "Checking origin ${ORIGIN_URL}..."
curl -fsS -o /dev/null --max-time 30 "${ORIGIN_URL}"

echo "Reconciling infrastructure (dedicated Front Door: ${DEPLOY_FRONT_DOOR})..."
set +e
FD_OUTPUTS="$(az deployment group create \
  --resource-group "$RG" \
  --name "$DEPLOYMENT" \
  --template-file "$ROOT/infra/main.bicep" \
  --parameters \
    prefix="$PREFIX" \
    location="$LOCATION" \
    deployFrontDoor="$DEPLOY_FRONT_DOOR" \
  --query "properties.outputs" \
  --output json 2>/tmp/bluemask-frontdoor.err)"
FD_STATUS=$?
set -e

if [[ "$FD_STATUS" -ne 0 ]]; then
  cat /tmp/bluemask-frontdoor.err >&2
  echo
  echo "Infrastructure deployment failed. Storage origin is live:"
  echo "  ${ORIGIN_URL}"
  if [[ "$DEPLOY_FRONT_DOOR" == true ]]; then
    echo
    echo "Forward this to the resource group owner:"
    echo
    cat <<'EOF'
Please update policy definition bluethroat-bluemask-allowed-provider-namespaces
(assignment bluemask-wehi-allowed-provider-namespaces on rg-bluemask-wehi-sandbox)
so Azure Front Door Standard can be created.

Add this deny-exception to the policyRule.if.allOf list:

  {
    "field": "type",
    "notLike": "Microsoft.Cdn/*"
  }

BlueMask is a static site on Microsoft.Storage. Front Door is Microsoft.Cdn
(profile, endpoint, origin group, origin, route, and header rule set).
The current policy allows Storage and Container Apps, but denies Microsoft.Cdn.

If you would rather list resource types explicitly, allow:

  Microsoft.Cdn/profiles
  Microsoft.Cdn/profiles/afdendpoints
  Microsoft.Cdn/profiles/origingroups
  Microsoft.Cdn/profiles/origingroups/origins
  Microsoft.Cdn/profiles/afdendpoints/routes
  Microsoft.Cdn/profiles/rulesets
  Microsoft.Cdn/profiles/rulesets/rules

No extra role is needed for the existing Contributor on this resource group.
Front Door profiles use location "global"; this resource group has no location deny.
EOF
  fi
elif [[ "$DEPLOY_FRONT_DOOR" == true ]]; then
  FD_URL="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["frontDoorUrl"]["value"])' "$FD_OUTPUTS")"
  echo "Waiting for Front Door to serve ${FD_URL}..."
  for _ in $(seq 1 18); do
    if curl -fsS -o /dev/null --max-time 30 "$FD_URL"; then
      break
    fi
    sleep 10
  done
  curl -fsS -o /dev/null --max-time 45 "$FD_URL"
  echo "Front Door is live: ${FD_URL}"
else
  echo "Dedicated Front Door unchanged; existing edge routing is managed separately."
fi

echo "Removing Container Apps stack..."
az containerapp delete --resource-group "$RG" --name "${PREFIX}-web" --yes --output none || true
az containerapp env delete --resource-group "$RG" --name "${PREFIX}-env" --yes --output none || true
az monitor log-analytics workspace delete --resource-group "$RG" --workspace-name "${PREFIX}-logs" --yes --output none || true

echo "Origin: ${ORIGIN_URL}"
if [[ "$FD_STATUS" -eq 0 && "$DEPLOY_FRONT_DOOR" == true ]]; then
  echo "Front Door: ${FD_URL}"
fi
