#!/bin/bash

# ========== 설정 (여기만 수정) ==========
START_TIME="2026-05-16T16:00:00+09:00"  # 시작 일시
END_TIME="2026-05-22T23:59:59+09:00"    # 종료 일시
PERIOD=60                               # 1분 단위
BASE_OUTPUT_DIR="./cloudwatch_data"

REGION="ap-northeast-2"
ALB_SUFFIX="app/your-alb-name/1234567890abcdef" # ALB ARN 뒷부분
EC2_INSTANCE_ID="i-xxxxxxxxxxxxxxxxx"
RDS_IDENTIFIER="your-rds-identifier"
CACHE_CLUSTER_IDS=("ewhafesta2026-001" "ewhafesta2026-002")
# =========================================


# ========== 메트릭 정의 (namespace|metric|stat|filename) ==========
ALB_METRICS=(
  "AWS/ApplicationELB|ActiveConnectionCount|Maximum|alb_active_connections"
  "AWS/ApplicationELB|RequestCount|Sum|alb_request_count"
  "AWS/ApplicationELB|TargetResponseTime|Average|alb_response_time"
  "AWS/ApplicationELB|HTTPCode_Target_5XX_Count|Sum|alb_5xx"
  "AWS/ApplicationELB|HTTPCode_Target_4XX_Count|Sum|alb_4xx"
)
EC2_METRICS=(
  "AWS/EC2|CPUUtilization|Maximum|ec2_cpu"
  "AWS/EC2|NetworkIn|Sum|ec2_network_in"
  "AWS/EC2|NetworkOut|Sum|ec2_network_out"
  "CWAgent|mem_used_percent|Maximum|ec2_memory"
)
RDS_METRICS=(
  "AWS/RDS|DatabaseConnections|Maximum|rds_connections"
  "AWS/RDS|CPUUtilization|Maximum|rds_cpu"
  "AWS/RDS|ReadLatency|Average|rds_read_latency"
  "AWS/RDS|WriteLatency|Average|rds_write_latency"
)
CACHE_METRICS=(
  "AWS/ElastiCache|CurrConnections|Maximum|cache_connections"
  "AWS/ElastiCache|CacheHits|Sum|cache_hits"
  "AWS/ElastiCache|CacheMisses|Sum|cache_misses"
  "AWS/ElastiCache|Evictions|Sum|cache_evictions"
)

# ========== 슬라이싱 중 공유되는 상태 (전역) ==========
CURRENT_OUTPUT_DIR=""
CURRENT_START=""
CURRENT_END=""

# ========== 함수 ==========
fetch_metric() {
  local namespace=$1 metric=$2 dim_name=$3 dim_value=$4 stat=$5 filename=$6

  echo "  Downloading $metric..."
  aws cloudwatch get-metric-statistics \
    --namespace "$namespace" \
    --metric-name "$metric" \
    --dimensions "Name=$dim_name,Value=$dim_value" \
    --start-time "$CURRENT_START" \
    --end-time "$CURRENT_END" \
    --period "$PERIOD" \
    --statistics "$stat" \
    --region "$REGION" \
    --output json \
  | jq '.Datapoints |= sort_by(.Timestamp)' > "$CURRENT_OUTPUT_DIR/$filename.json"
}

fetch_metrics_from_list() {
  local -n metric_list=$1
  local dim_name=$2 dim_value=$3 filename_suffix=${4:-""}  # suffix 선택적 파라미터

  for entry in "${metric_list[@]}"; do
    IFS='|' read -r namespace metric stat filename <<< "$entry"
    fetch_metric "$namespace" "$metric" "$dim_name" "$dim_value" "$stat" "${filename}${filename_suffix}"
  done
}

fetch_all_metrics() {
  mkdir -p "$CURRENT_OUTPUT_DIR"

  fetch_metrics_from_list ALB_METRICS  "LoadBalancer"         "$ALB_SUFFIX"
  fetch_metrics_from_list EC2_METRICS  "InstanceId"           "$EC2_INSTANCE_ID"
  fetch_metrics_from_list RDS_METRICS  "DBInstanceIdentifier" "$RDS_IDENTIFIER"

  for i in "${!CACHE_CLUSTER_IDS[@]}"; do
    local cluster_id="${CACHE_CLUSTER_IDS[$i]}"
    local idx=$((i + 1))
    fetch_metrics_from_list CACHE_METRICS "CacheClusterId" "$cluster_id" "_${idx}"
  done
}

# ========== KST 기준 하루 단위 슬라이싱 ==========
to_epoch() { date -d "$1" +%s; }

current_date=$(echo "$START_TIME" | sed 's/T.*//')
start_of_day="$START_TIME"
end_epoch=$(to_epoch "$END_TIME")

while true; do
  next_date=$(date -d "$current_date + 1 day" +"%Y-%m-%d")
  next_start="${next_date}T00:00:00+09:00"

  if (( $(to_epoch "$next_start") >= end_epoch )); then
    end_of_day="$END_TIME"
  else
    end_of_day="$next_start"
  fi

  CURRENT_OUTPUT_DIR="$BASE_OUTPUT_DIR/$(echo "$current_date" | tr -d '-')"
  CURRENT_START="$start_of_day"
  CURRENT_END="$end_of_day"

  echo "📅 [$(echo "$current_date" | tr -d '-')] $start_of_day ~ $end_of_day"
  fetch_all_metrics

  (( $(to_epoch "$end_of_day") >= end_epoch )) && break

  current_date="$next_date"
  start_of_day="$next_start"
done

echo "✅ 완료! $BASE_OUTPUT_DIR 폴더를 확인하세요."
