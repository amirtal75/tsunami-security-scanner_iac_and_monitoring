module "sqs" {
  source = "./modules/sqs"
  queue_name = var.sqs_queue_name
  visibility_timeout_seconds = var.sqs_visibility_timeout_seconds
  message_retention_seconds = var.sqs_message_retention_seconds
}

module "s3" {
  source = "./modules/s3"

  retention_hours = 24

  tags = {
    Environment = "Dev"
    Project     = "TerraformPlanBlock"
  }
  my_terraform_plan_block_apply_bucket = "my-terraform-plan-block-apply-bucket"
}

module "vpc" {
  source = "./modules/vpc"
  
  aws_region           = var.aws_region
  vpc_cidr             = var.vpc_cidr
  public_subnet_a_cidr = var.public_subnet_a_cidr
  public_subnet_b_cidr = var.public_subnet_b_cidr
  private_subnet_a_cidr = var.private_subnet_a_cidr
  private_subnet_b_cidr = var.private_subnet_b_cidr
  availability_zone_a  = var.availability_zone_a
  availability_zone_b  = var.availability_zone_b
}

module "iam_roles" {
  source = "./modules/iam_roles"
  aws_region = var.aws_region
  aws_iam_eks_group_name = var.aws_iam_eks_group_name
  aws_iam_eks_user = var.aws_iam_eks_user
}

module "eks" {
  source = "./modules/eks"

  aws_region         = var.aws_region
  cluster_name       = var.eks_cluster_name
  node_group_name    = var.node_group_name
  desired_size       = var.desired_size
  max_size           = var.max_size
  min_size           = var.min_size
  subnet_ids         = module.vpc.private_subnets
  vpc_id             = module.vpc.vpc_id
  cluster_role_arn   = module.iam_roles.eks_cluster_role_arn
  node_role_arn      = module.iam_roles.eks_node_role_arn
}

module "github_oidc" {
  source = "./modules/github_oidc"

  aws_region             = var.aws_region
  github_username        = var.github_username
  github_repo_name       = var.github_repo_name
  github_actions_role_name = var.github_actions_role_name
  github_actions_policy_name = var.github_actions_policy_name
}
