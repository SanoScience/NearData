resource "aws_dynamodb_table" "NearData_db" {
  name                        = "neardata-tissues-salmon-metadata"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "SRR_id"
  deletion_protection_enabled = true

  attribute {
    name = "SRR_id"
    type = "S"
  }

  tags = {
    Name = "NearData_db"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_dynamodb_table" "NearData_test_db" {
  name         = "neardata-test-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "SRR_id"

  attribute {
    name = "SRR_id"
    type = "S"
  }

  tags = {
    Name = "NearData_test_db"
  }
}