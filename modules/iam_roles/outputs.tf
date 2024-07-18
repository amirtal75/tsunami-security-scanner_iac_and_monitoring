output "eks_cluster_role_arn" {
  value = aws_iam_role.eks_cluster_role.arn
}

output "eks_node_role_arn" {
  value = aws_iam_role.eks_node_role.arn
}

output "eks_user_access_key" {
  value = aws_iam_access_key.eks_user_key.id
  sensitive = true
}

output "eks_user_secret_key" {
  value = aws_iam_access_key.eks_user_key.secret
  sensitive = true
}
