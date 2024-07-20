output "random_id" {
  value = random_id.bucket_suffix.hex
}
output "monitoring_security_group_arn" {
  value = module.eks.monitoring_security_group_arn.id
}

output "tsunami_queue_url" {
  value = module.sqs.queue_url
}

output "cluster_oidc" {
  value = module.eks.cluster_oidc
}
