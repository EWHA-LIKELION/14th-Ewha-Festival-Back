#!/bin/bash
set -uo pipefail

# ========== 설정 (여기만 수정) ==========
START_TIME="2026-05-16T16:00:00+09:00"  # 시작 일시
END_TIME="2026-05-23T00:00:00+09:00"    # 종료 일시
PERIOD=60                               # 1분 단위
BASE_OUTPUT_DIR="./cloudwatch_data"

REGION="ap-northeast-2"
ALB_SUFFIX="app/your-alb-name/1234567890abcdef" # ALB ARN 뒷부분
EC2_INSTANCE_ID="i-xxxxxxxxxxxxxxxxx"
EC2_IMAGE_ID="ami-xxxxxxxxxxxxxxxxx"
EC2_INSTANCE_TYPE="t3.micro"
RDS_IDENTIFIER="your-rds-identifier"
CACHE_CLUSTER_IDS=("ewhafesta2026-001" "ewhafesta2026-002")
# =========================================


# ========== 메트릭 정의 (namespace|metric|stat|filename) ==========
ALB_METRICS=(
  "AWS/ApplicationELB|ActiveConnectionCount|Maximum|alb_active_connections"
  "AWS/ApplicationELB|RequestCount|Sum|alb_request_count"
  "AWS/ApplicationELB|TargetResponseTime|Average|alb_response_time"
  "AWS/ApplicationELB|HTTPCode_Target_2XX_Count|Sum|alb_2xx"
  "AWS/ApplicationELB|HTTPCode_Target_3XX_Count|Sum|alb_3xx"
  "AWS/ApplicationELB|HTTPCode_Target_4XX_Count|Sum|alb_4xx"
  "AWS/ApplicationELB|HTTPCode_Target_5XX_Count|Sum|alb_5xx"
  "AWS/ApplicationELB|HTTPCode_ELB_3XX_Count|Sum|alb_elb_3xx"
  "AWS/ApplicationELB|HTTPCode_ELB_4XX_Count|Sum|alb_elb_4xx"
  "AWS/ApplicationELB|HTTPCode_ELB_5XX_Count|Sum|alb_elb_5xx"
  "AWS/ApplicationELB|RejectedConnectionCount|Sum|alb_rejected_connections"
  "AWS/ApplicationELB|NewConnectionCount|Sum|alb_new_connections"
  "AWS/ApplicationELB|ProcessedBytes|Sum|alb_processed_bytes"
  "AWS/ApplicationELB|ConsumedLCUs|Sum|alb_consumed_lcus"
  "AWS/ApplicationELB|HealthyHostCount|Minimum|alb_healthy_hosts"
  "AWS/ApplicationELB|UnHealthyHostCount|Maximum|alb_unhealthy_hosts"
)
EC2_METRICS=(
  "AWS/EC2|CPUUtilization|Maximum|ec2_cpu"
  "AWS/EC2|NetworkIn|Sum|ec2_network_in"
  "AWS/EC2|NetworkOut|Sum|ec2_network_out"
  "AWS/EC2|NetworkPacketsIn|Sum|ec2_packets_in"
  "AWS/EC2|NetworkPacketsOut|Sum|ec2_packets_out"
  "AWS/EC2|DiskReadBytes|Sum|ec2_disk_read_bytes"
  "AWS/EC2|DiskWriteBytes|Sum|ec2_disk_write_bytes"
  "AWS/EC2|DiskReadOps|Sum|ec2_disk_read_ops"
  "AWS/EC2|DiskWriteOps|Sum|ec2_disk_write_ops"
  "AWS/EC2|StatusCheckFailed|Maximum|ec2_status_check_failed"
  "AWS/EC2|StatusCheckFailed_Instance|Maximum|ec2_status_check_instance"
  "AWS/EC2|StatusCheckFailed_System|Maximum|ec2_status_check_system"
  "AWS/EC2|CPUCreditUsage|Sum|ec2_cpu_credit_usage"
  "AWS/EC2|CPUCreditBalance|Minimum|ec2_cpu_credit_balance"
)
CWAGENT_METRICS=(
  "CWAgent|mem_used_percent|Maximum|ec2_memory"
)
RDS_METRICS=(
  "AWS/RDS|DatabaseConnections|Maximum|rds_connections"
  "AWS/RDS|CPUUtilization|Maximum|rds_cpu"
  "AWS/RDS|FreeableMemory|Minimum|rds_freeable_memory"
  "AWS/RDS|FreeStorageSpace|Minimum|rds_free_storage"
  "AWS/RDS|SwapUsage|Maximum|rds_swap"
  "AWS/RDS|ReadLatency|Average|rds_read_latency"
  "AWS/RDS|WriteLatency|Average|rds_write_latency"
  "AWS/RDS|ReadThroughput|Average|rds_read_throughput"
  "AWS/RDS|WriteThroughput|Average|rds_write_throughput"
  "AWS/RDS|ReadIOPS|Average|rds_read_iops"
  "AWS/RDS|WriteIOPS|Average|rds_write_iops"
  "AWS/RDS|DiskQueueDepth|Maximum|rds_disk_queue_depth"
  "AWS/RDS|NetworkReceiveThroughput|Average|rds_network_receive"
  "AWS/RDS|NetworkTransmitThroughput|Average|rds_network_transmit"
  "AWS/RDS|DBLoad|Average|rds_db_load"
  "AWS/RDS|DBLoadCPU|Average|rds_db_load_cpu"
  "AWS/RDS|DBLoadNonCPU|Average|rds_db_load_noncpu"
  "AWS/RDS|DBLoadRelativeToNumVCPUs|Average|rds_db_load_per_vcpu"
)
CACHE_METRICS=(
  "AWS/ElastiCache|CurrConnections|Maximum|cache_connections"
  "AWS/ElastiCache|NewConnections|Sum|cache_new_connections"
  "AWS/ElastiCache|CacheHits|Sum|cache_hits"
  "AWS/ElastiCache|CacheMisses|Sum|cache_misses"
  "AWS/ElastiCache|CacheHitRate|Average|cache_hit_rate"
  "AWS/ElastiCache|Evictions|Sum|cache_evictions"
  "AWS/ElastiCache|BytesUsedForCache|Maximum|cache_bytes_used"
  "AWS/ElastiCache|EngineCPUUtilization|Maximum|cache_engine_cpu"
  "AWS/ElastiCache|CPUUtilization|Maximum|cache_cpu"
  "AWS/ElastiCache|NetworkBytesIn|Sum|cache_network_in"
  "AWS/ElastiCache|NetworkBytesOut|Sum|cache_network_out"
  "AWS/ElastiCache|CurrItems|Maximum|cache_curr_items"
  "AWS/ElastiCache|GetTypeCmds|Sum|cache_get_cmds"
  "AWS/ElastiCache|SetTypeCmds|Sum|cache_set_cmds"
  "AWS/ElastiCache|ReplicationLag|Maximum|cache_replication_lag"
  "AWS/ElastiCache|MemoryFragmentationRatio|Average|cache_memory_fragmentation"
)

# ========== 전역 변수 ==========
CURRENT_OUTPUT_DIR=""
CURRENT_START=""
CURRENT_END=""
ERROR_COUNT=0

# ========== 함수 ==========
fetch_metric() {
  local namespace=$1 metric=$2 stat=$3 filename=$4
  shift 4
  local outfile="$CURRENT_OUTPUT_DIR/$filename.json"

  echo "  Downloading $metric..."
  if aws cloudwatch get-metric-statistics \
    --namespace "$namespace" \
    --metric-name "$metric" \
    --dimensions "$@" \
    --start-time "$CURRENT_START" \
    --end-time "$CURRENT_END" \
    --period "$PERIOD" \
    --statistics "$stat" \
    --region "$REGION" \
    --output json \
  | jq '.Datapoints |= sort_by(.Timestamp)' > "$outfile"
  then
    :
  else
    echo "  ⚠️  FAILED: $metric ($filename.json)" >&2
    rm -f "$outfile"
    (( ERROR_COUNT++ )) || true
  fi
}

fetch_metrics_from_list() {
  local -n metric_list=$1
  local filename_suffix=${2:-""}
  shift 2
  # 나머지 인자: 모든 Dimension ("Name=k,Value=v" 형태)
  local dims=("$@")

  for entry in "${metric_list[@]}"; do
    IFS='|' read -r namespace metric stat filename <<< "$entry"
    fetch_metric "$namespace" "$metric" "$stat" \
      "${filename}${filename_suffix}" "${dims[@]+"${dims[@]}"}"
  done
}

fetch_all_metrics() {
  mkdir -p "$CURRENT_OUTPUT_DIR"

  fetch_metrics_from_list ALB_METRICS   "" "Name=LoadBalancer,Value=$ALB_SUFFIX"
  fetch_metrics_from_list EC2_METRICS   "" "Name=InstanceId,Value=$EC2_INSTANCE_ID"
  fetch_metrics_from_list CWAGENT_METRICS "" \
    "Name=InstanceId,Value=$EC2_INSTANCE_ID" \
    "Name=ImageId,Value=$EC2_IMAGE_ID" \
    "Name=InstanceType,Value=$EC2_INSTANCE_TYPE"
  fetch_metrics_from_list RDS_METRICS   "" "Name=DBInstanceIdentifier,Value=$RDS_IDENTIFIER"

  for i in "${!CACHE_CLUSTER_IDS[@]}"; do
    local cluster_id="${CACHE_CLUSTER_IDS[$i]}"
    local idx=$((i + 1))
    fetch_metrics_from_list CACHE_METRICS "_${idx}" "Name=CacheClusterId,Value=$cluster_id"
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
  next_epoch=$(to_epoch "$next_start")

  if (( next_epoch >= end_epoch )); then
    end_of_day="$END_TIME"
    is_last=1
  else
    end_of_day="$next_start"
    is_last=0
  fi

  date_label=$(echo "$current_date" | tr -d '-')
  CURRENT_OUTPUT_DIR="$BASE_OUTPUT_DIR/$date_label"
  CURRENT_START="$start_of_day"
  CURRENT_END="$end_of_day"

  echo "📅 [$date_label] $start_of_day ~ $end_of_day"
  fetch_all_metrics

  (( is_last )) && break

  current_date="$next_date"
  start_of_day="$next_start"
done

if (( ERROR_COUNT > 0 )); then
  echo "⚠️  완료 (에러 ${ERROR_COUNT}건). $BASE_OUTPUT_DIR 폴더를 확인하세요."
else
  echo "✅ 완료! $BASE_OUTPUT_DIR 폴더를 확인하세요."
fi
