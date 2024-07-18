resource "aws_s3_bucket" "this" {
  bucket = var.my-terraform-plan-block-apply-bucket
  tags = var.tags
}

resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Deny",
        Principal = "*",
        Action = "s3:*",
        Resource = [
          "arn:aws:s3:::${var.my-terraform-plan-block-apply-bucket}",
          "arn:aws:s3:::${var.my-terraform-plan-block-apply-bucket}/*"
        ],
        Condition = {
          Bool: {
            "aws:SecureTransport": "false"
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_acl" "this" {
  bucket = aws_s3_bucket.this.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "retention"
    status = "Enabled"

    expiration {
      days = var.retention_hours
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

output "bucket_name" {
  value = aws_s3_bucket.this.id
}
