### Set credentials (if using localhost and wants to deploy app to AWS)
 - Store sensitve and non-sensitive variables to aws
 ```bash
  aws ssm put-parameter --name "YOUR_VARIABLE_NAME" --value "YOUR_VALUE" --type "String" --region "YOUR_REGION"
 ```

 - Get variable (on the ec2 instance or cloudshell)
 ```bash
  aws ssm get-parameter --name "YOUR_VARIABLE_
 ```

### Setup workspace within a server 

 - Step 1, given enough permissions
  ```bash
    chmod +x scripts/*
  ```
 - Step 2, run setup script 
 ```bash
   ./scripts/setup_server.sh
 ```
 
### Setup using Terraform

 - Go to terraform infrastructure
 ```bash
  cd infra/terraform/
 ```

 - Apply configuration (you have yo configure your provider, in this case I use AWS as a provider)
 ```bash
  terraform apply
 ```
**Considerations**
  - Consider to enter your subnet and vpc id.
  - If you deploy this application for the first time, you might wait more than you think