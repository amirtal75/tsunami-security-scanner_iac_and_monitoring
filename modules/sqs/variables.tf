variable "queue_name" {
  description = "The name of the SQS queue"
  type        = string
}

variable "visibility_timeout_seconds" {
  description = "The visibility timeout for the SQS queue"
  type        = number
}

variable "message_retention_seconds" {
  description = "The number of seconds to retain a message in the SQS queue"
  type        = number
}
