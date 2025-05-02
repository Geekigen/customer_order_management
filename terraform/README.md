## How It Works

1. Changes are pushed to the repository
2. GitHub Actions workflow is triggered
3. Terraform initializes and validates the configuration
4. Terraform applies the changes to provision:
   - EC2 Ubuntu server
   - Configured security groups