#!/bin/bash

# ========== 설정 (여기만 수정) ==========
START_TIME="2025-05-14T00:00:00Z"   # 행사 시작일
END_TIME="2025-05-17T00:00:00Z"     # 행사 종료일
PERIOD=60                           # 1분 단위
REGION="ap-northeast-2"             # 서울 리전
OUTPUT_DIR="./cloudwatch_data"

ALB_SUFFIX="app/your-alb-name/1234567890abcdef" # ALB ARN 뒷부분
EC2_INSTANCE_ID="i-xxxxxxxxxxxxxxxxx"
RDS_IDENTIFIER="your-rds-identifier"
CACHE_CLUSTER_ID="your-elasticache-id"
# =========================================

mkdir -p $OUTPUT_DIR

fetch_metric() {
  local namespace=$1
  local metric=$2
  local dims=$3
  local stat=$4
  local filename=$5

  echo "Downloading $metric..."
  aws cloudwatch get-metric-statistics \
    --namespace "$namespace" \
    --metric-name "$metric" \
    --dimensions $dims \
    --start-time "$START_TIME" \
    --end-time "$END_TIME" \
    --period "$PERIOD" \
    --statistics "$stat" \
    --region "$REGION" \
    --output json > "$OUTPUT_DIR/$filename.json"
}

# ALB
fetch_metric "AWS/ApplicationELB" "ActiveConnectionCount" \
  "Name=LoadBalancer,Value=$ALB_SUFFIX" "Maximum" "alb_active_connections"

fetch_metric "AWS/ApplicationELB" "RequestCount" \
  "Name=LoadBalancer,Value=$ALB_SUFFIX" "Sum" "alb_request_count"

fetch_metric "AWS/ApplicationELB" "TargetResponseTime" \
  "Name=LoadBalancer,Value=$ALB_SUFFIX" "Average" "alb_response_time"

fetch_metric "AWS/ApplicationELB" "HTTPCode_Target_5XX_Count" \
  "Name=LoadBalancer,Value=$ALB_SUFFIX" "Sum" "alb_5xx"

fetch_metric "AWS/ApplicationELB" "HTTPCode_Target_4XX_Count" \
  "Name=LoadBalancer,Value=$ALB_SUFFIX" "Sum" "alb_4xx"

# EC2
fetch_metric "AWS/EC2" "CPUUtilization" \
  "Name=InstanceId,Value=$EC2_INSTANCE_ID" "Maximum" "ec2_cpu"

fetch_metric "AWS/EC2" "NetworkIn" \
  "Name=InstanceId,Value=$EC2_INSTANCE_ID" "Sum" "ec2_network_in"

fetch_metric "AWS/EC2" "NetworkOut" \
  "Name=InstanceId,Value=$EC2_INSTANCE_ID" "Sum" "ec2_network_out"

# CWAgent (Memory - Agent 설치한 경우)
fetch_metric "CWAgent" "mem_used_percent" \
  "Name=InstanceId,Value=$EC2_INSTANCE_ID" "Maximum" "ec2_memory"

# RDS
fetch_metric "AWS/RDS" "DatabaseConnections" \
  "Name=DBInstanceIdentifier,Value=$RDS_IDENTIFIER" "Maximum" "rds_connections"

fetch_metric "AWS/RDS" "CPUUtilization" \
  "Name=DBInstanceIdentifier,Value=$RDS_IDENTIFIER" "Maximum" "rds_cpu"

fetch_metric "AWS/RDS" "ReadLatency" \
  "Name=DBInstanceIdentifier,Value=$RDS_IDENTIFIER" "Average" "rds_read_latency"

fetch_metric "AWS/RDS" "WriteLatency" \
  "Name=DBInstanceIdentifier,Value=$RDS_IDENTIFIER" "Average" "rds_write_latency"

# ElastiCache
fetch_metric "AWS/ElastiCache" "CurrConnections" \
  "Name=CacheClusterId,Value=$CACHE_CLUSTER_ID" "Maximum" "cache_connections"

fetch_metric "AWS/ElastiCache" "CacheHits" \
  "Name=CacheClusterId,Value=$CACHE_CLUSTER_ID" "Sum" "cache_hits"

fetch_metric "AWS/ElastiCache" "CacheMisses" \
  "Name=CacheClusterId,Value=$CACHE_CLUSTER_ID" "Sum" "cache_misses"

fetch_metric "AWS/ElastiCache" "Evictions" \
  "Name=CacheClusterId,Value=$CACHE_CLUSTER_ID" "Sum" "cache_evictions"

echo "✅ 완료! $OUTPUT_DIR 폴더를 확인하세요."
