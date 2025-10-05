# Global Load Balancer Module using Route53
# Provides health-check based routing to multiple regions

variable "domain_name" {
  description = "Domain name for the global load balancer"
  type        = string
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
}

variable "regions" {
  description = "Map of regions with their endpoint configurations"
  type = map(object({
    endpoint    = string
    weight      = number
    health_check = object({
      enabled             = bool
      path                = string
      port                = number
      protocol            = string
      failure_threshold   = number
      request_interval    = number
    })
  }))
}

variable "failover_config" {
  description = "Failover configuration"
  type = object({
    primary_region = string
    evaluate_target_health = bool
  })
  default = {
    primary_region = "us-west-2"
    evaluate_target_health = true
  }
}

# Health checks for each region
resource "aws_route53_health_check" "region" {
  for_each = {
    for k, v in var.regions : k => v
    if v.health_check.enabled
  }

  fqdn              = each.value.endpoint
  port              = each.value.health_check.port
  type              = each.value.health_check.protocol
  resource_path     = each.value.health_check.path
  failure_threshold = each.value.health_check.failure_threshold
  request_interval  = each.value.health_check.request_interval

  measure_latency = true

  tags = {
    Name   = "${var.domain_name}-${each.key}-health"
    Region = each.key
  }
}

# Weighted routing policy for load distribution
resource "aws_route53_record" "weighted" {
  for_each = var.regions

  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  weighted_routing_policy {
    weight = each.value.weight
  }

  set_identifier = each.key
  alias {
    name                   = each.value.endpoint
    zone_id                = data.aws_lb.region[each.key].zone_id
    evaluate_target_health = var.failover_config.evaluate_target_health
  }

  health_check_id = each.value.health_check.enabled ? aws_route53_health_check.region[each.key].id : null
}

# Latency-based routing (alternative to weighted)
resource "aws_route53_record" "latency" {
  for_each = var.regions

  zone_id = var.hosted_zone_id
  name    = "latency.${var.domain_name}"
  type    = "A"

  latency_routing_policy {
    region = each.key
  }

  set_identifier = each.key
  alias {
    name                   = each.value.endpoint
    zone_id                = data.aws_lb.region[each.key].zone_id
    evaluate_target_health = true
  }

  health_check_id = each.value.health_check.enabled ? aws_route53_health_check.region[each.key].id : null
}

# Geolocation routing for data residency compliance
resource "aws_route53_record" "geo_us" {
  zone_id = var.hosted_zone_id
  name    = "geo.${var.domain_name}"
  type    = "A"

  geolocation_routing_policy {
    continent = "NA" # North America
  }

  set_identifier = "geo-us"
  alias {
    name                   = var.regions["us-west-2"].endpoint
    zone_id                = data.aws_lb.region["us-west-2"].zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "geo_eu" {
  zone_id = var.hosted_zone_id
  name    = "geo.${var.domain_name}"
  type    = "A"

  geolocation_routing_policy {
    continent = "EU" # Europe
  }

  set_identifier = "geo-eu"
  alias {
    name                   = var.regions["eu-west-1"].endpoint
    zone_id                = data.aws_lb.region["eu-west-1"].zone_id
    evaluate_target_health = true
  }
}

# Default geolocation (fallback)
resource "aws_route53_record" "geo_default" {
  zone_id = var.hosted_zone_id
  name    = "geo.${var.domain_name}"
  type    = "A"

  geolocation_routing_policy {
    country = "*"
  }

  set_identifier = "geo-default"
  alias {
    name                   = var.regions[var.failover_config.primary_region].endpoint
    zone_id                = data.aws_lb.region[var.failover_config.primary_region].zone_id
    evaluate_target_health = true
  }
}

# Data source for Load Balancers
data "aws_lb" "region" {
  for_each = var.regions

  provider = aws.${each.key}
  name     = "somaagent-${each.key}-lb"
}

# CloudWatch Alarms for health check failures
resource "aws_cloudwatch_metric_alarm" "health_check" {
  for_each = aws_route53_health_check.region

  alarm_name          = "${var.domain_name}-${each.key}-health-alarm"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = 60
  statistic           = "Minimum"
  threshold           = 1
  alarm_description   = "Health check failed for ${each.key}"
  treat_missing_data  = "breaching"

  dimensions = {
    HealthCheckId = each.value.id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.domain_name}-health-alerts"

  tags = {
    Name = "${var.domain_name}-alerts"
  }
}

# Outputs
output "global_endpoint" {
  description = "Global load balancer endpoint"
  value       = var.domain_name
}

output "latency_endpoint" {
  description = "Latency-based routing endpoint"
  value       = "latency.${var.domain_name}"
}

output "geo_endpoint" {
  description = "Geolocation-based routing endpoint"
  value       = "geo.${var.domain_name}"
}

output "health_check_ids" {
  description = "Map of health check IDs by region"
  value       = { for k, v in aws_route53_health_check.region : k => v.id }
}

output "alert_topic_arn" {
  description = "SNS topic ARN for health alerts"
  value       = aws_sns_topic.alerts.arn
}
