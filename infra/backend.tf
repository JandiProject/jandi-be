terraform {
    backend "gcs" {
        bucket = "jandi-bucket-tfstate"
        prefix = "terraform/state"
    }
} 