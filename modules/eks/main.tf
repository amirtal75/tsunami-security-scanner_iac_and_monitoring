resource "aws_eks_cluster" "eks_cluster" {
  name     = var.cluster_name
  role_arn = var.cluster_role_arn

  vpc_config {
    subnet_ids = var.subnet_ids
  }
}

resource "aws_eks_node_group" "node_group" {
  cluster_name    = var.cluster_name
  node_group_name = var.node_group_name
  node_role_arn   = var.node_role_arn
  subnet_ids      = var.subnet_ids

  scaling_config {
    desired_size = var.desired_size
    max_size     = var.max_size
    min_size     = var.min_size
  }

  depends_on = [
    aws_eks_cluster.eks_cluster,
  ]
}

resource "kubernetes_config_map" "aws_auth" {
  metadata {
    name      = "aws-auth"
    namespace = "kube-system"
  }

  data = {
    mapRoles = yamlencode([
      {
        groups   = ["system:bootstrappers", "system:nodes"]
        rolearn  = aws_eks_node_group.node_group.arn
        username = "system:node:{{EC2PrivateDNSName}}"
      },
      {
        groups   = ["system:masters"]
        rolearn  = var.github_actions_role_arn
        username = "github-actions"
      }
    ])
  }

  depends_on = [
    aws_eks_cluster.eks_cluster,
    aws_eks_node_group.node_group,
    kubernetes_config_map.aws_auth
  ]
}
