#!/bin/bash
# Copyright (c) 2026, Digital Asset (Switzerland) GmbH and/or its affiliates. All rights reserved.
# SPDX-License-Identifier: 0BSD

set -eo pipefail

generate_jwt() {
  local sub="$1"
  local aud="$2"
  jwt-cli encode hs256 --s unsafe --p '{"sub": "'"$sub"'", "aud": "'"$aud"'"}'
}

share_file() {
  local relative_path="$1"
  write_to_file "/onboarding/${relative_path}"
}

write_to_file() {
  local absolute_path="$1"
  echo ">>>> writing to ${absolute_path}" >&2
  mkdir -p "$(dirname "${absolute_path}")"
  cat > "${absolute_path}"
}

get_admin_token() {
  local secret=$1
  local clientId=$2
  local tokenUrl=$3

  echo "get_admin_token $clientId $tokenUrl" >&2

  curl -f -s -S "${tokenUrl}" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'client_id='${clientId} \
    -d 'client_secret='${secret} \
    -d 'grant_type=client_credentials' \
    -d 'scope=openid' | jq -r .access_token
}

create_user() {
  local token=$1
  local userId=$2
  local userName=$3
  local party=$4
  local participant=$5
  echo "create_user $userId $userName $party $participant" >&2

  local code
  code=$(curl_status_code "http://$participant/v2/users/$userId" "$token" "application/json")
  case "$code" in
    200) return 0 ;;
    404) ;; # Continue with user creation.
    *)
      echo "Cannot check ledger user $userId: HTTP $code" >&2
      return 1
      ;;
  esac
  curl_check "http://$participant/v2/users" "$token" "application/json" \
      --data-raw '{
        "user" : {
            "id" : "'$userId'",
            "isDeactivated": false,
            "primaryParty" : "'$party'",
            "identityProviderId": "",
            "metadata": {
               "resourceVersion": "",
                "annotations": {
                    "username" : "'$userName'"
                }
            }
        },
          "rights": [
          ]
      }' | jq -r .user.id
}

delete_user() {
  local token=$1
  local userId=$2
  local participant=$3
  echo "delete_user $userId $participant" >&2

  code=$(curl_status_code "http://$participant/v2/users/$userId" "$token" "application/json")
  if  [ "$code" == "200" ]; then
    curl_check "http://$participant/v2/users/$userId" "$token" "application/json" -X DELETE
  fi
}

joinByChar() {
  local IFS="$1"
  shift
  echo "$*"
}

function grant_rights() {
  local token=$1
  local userId=$2
  local partyId=$3
  local rights=$4
  local participant=$5
  echo "grant_rights user:$userId party:$partyId $rights $participant" >&2

  read -ra rightsAsArr <<< "$rights"
  local rightsArr=()
  for right in "${rightsAsArr[@]}"; do
    case "$right" in
      "ParticipantAdmin")
        rightsArr+=('{"kind":{"ParticipantAdmin":{"value":{}}}}')
        ;;
      "ActAs")
        rightsArr+=('{"kind":{"CanActAs":{"value":{"party":"'$partyId'"}}}}')
        ;;
      "ReadAs")
        rightsArr+=('{"kind":{"CanReadAs":{"value":{"party":"'$partyId'"}}}}')
        ;;
    esac
  done

  local rightsJson=$(joinByChar "," "${rightsArr[@]}")
  curl_check "http://$participant/v2/users/$userId/rights" "$token" "application/json" \
    --data-raw '{
        "userId": "'$userId'",
        "identityProviderId": "",
        "rights": ['$rightsJson']
    }'
}

update_user() {

  local token=$1
  local userId=$2
  local userName=$3
  local party=$4
  local participant=$5
  echo "update_user $userId $userName $party $participant" >&2
  curl_check "http://$participant/v2/users/$userId" "$token" "application/json" \
    -X PATCH \
    --data-raw '{
      "user" : {
          "id" : "'$userId'",
          "isDeactivated": false,
          "primaryParty" : "'$party'",
          "identityProviderId": "",
          "metadata": {
             "resourceVersion": "",
              "annotations": {
                  "username" : "'$userName'"
              }
          }
      },
      "updateMask": {
          "paths": ["primary_party", "metadata"],
          "unknownFields": {
             "fields": {}
          }
      }
    }' | jq -r .user.id
}

upload_dars() {
  local token=$1
  local participant=$2
  [ -d /canton/dars ] || return 0
  find /canton/dars -type f -name "*.dar" | while read -r file; do
    echo "uploadDar $file $participant" >&2
    curl_check "http://$participant/v2/packages" "$token" "application/octet-stream" \
      --data-binary @"$file"
    echo "Uploaded $file"
  done
}

get_user_party() {
  local token=$1
  local user=$2
  local participant=$3
  echo "get_user_party $user $participant" >&2
  curl_check "http://$participant/v2/users/$user" "$token" "application/json" | jq -r .user.primaryParty
}

curl_check() {
  local url=$1
  local token=$2
  local contentType=${3:-application/json}
  shift 3
  local args=("$@")
  echo "$url" >&2
  if [ ${#args[@]} -ne 0 ]; then
    echo "${args[@]}" >&2
  fi

  curlArgs=(-s -S -w "\n%{http_code}" "$url")
  if [ -n "$token" ]; then
    curlArgs+=(-H "Authorization: Bearer $token")
  fi
  curlArgs+=(-H "Content-Type: $contentType")
  curlArgs+=("${args[@]}")
  response=$(curl "${curlArgs[@]}")

  local httpCode=$(echo "$response" | tail -n1 | tr -d '\r')
  local responseBody=$(echo "$response" | sed '$d')

  if [ "$httpCode" -ne "200" ] && [ "$httpCode" -ne "201" ] && [ "$httpCode" -ne "204" ]; then
    echo "Request failed with HTTP status code $httpCode" >&2
    echo "Response body: $responseBody" >&2
    exit 1
  fi

  echo "$responseBody"
}

curl_status_code() {
  local url=$1
  local token=$2
  local contentType=${3:-application/json}
  shift 3
  local args=("$@")
  echo "$url" >&2
  if [ ${#args[@]} -ne 0 ]; then
    echo "${args[@]}" >&2
  fi

  response=$(curl -s -S -w "\n%{http_code}" "$url" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: $contentType" \
      "${args[@]}"
      )

  echo "$response" | tail -n1 | tr -d '\r'
}
