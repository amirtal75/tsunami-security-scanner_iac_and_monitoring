resource "aws_iam_openid_connect_provider" "github" {
  url                   = "https://token.actions.githubusercontent.com"
  client_id_list        = ["sts.amazonaws.com"]
  thumbprint_list       = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions_role" {
  name = var.github_actions_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        "Effect": "Allow",
        "Principal": {
            "Federated": "arn:aws:iam::654654392619:oidc-provider/oidc.eks.us-west-2.amazonaws.com/id/CF5AA0FEA732CB79C49248DEE36EA77A"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
            "StringEquals": {
                "oidc.eks.us-west-2.amazonaws.com/id/CF5AA0FEA732CB79C49248DEE36EA77A:sub": "system:serviceaccount:default:tsunami-scanner-sa"
            }
        }
      },
      {
        Effect = "Allow",
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        },
        Action = "sts:AssumeRoleWithWebIdentity",
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
            "token.actions.githubusercontent.com:sub": "repo:${var.github_username}/${var.github_repo_name}:ref:refs/heads/main"
          }
        }
      },
      {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::654654392619:user/almalinux"
      },
      "Action": "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "github_actions_policy" {
  name        = var.github_actions_policy_name
  description = "Policy for GitHub Actions to deploy to AWS"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:*",
          "ec2:*",
          "eks:*",
          "dynamodb:*",
          "iam:*",
          "sqs:*"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions_attachment" {
  role       = aws_iam_role.github_actions_role.name
  policy_arn = aws_iam_policy.github_actions_policy.arn
}

resource "aws_iam_role_policy_attachment" "eks_service_policy" {
  role       = aws_iam_role.github_actions_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
}
resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  role       = aws_iam_role.github_actions_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}
resource "aws_iam_role_policy_attachment" "eks_node_policy" {
  role       = aws_iam_role.github_actions_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}


