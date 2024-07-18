output "github_actions_role_arn" {
  value = aws_iam_role.github_actions_role.arn
}

output "github_actions_policy_arn" {
  value = aws_iam_policy.github_actions_policy.arn
}

output "github_actions_service_account_name" {
  value = kubernetes_service_account.github_actions.metadata[0].name
}

output "github_actions_cluster_role_binding_name" {
  value = kubernetes_cluster_role_binding.github_actions.metadata[0].name
}
