

#### Set mondodb password
 - Set password
 ```bash
    export TF_VAR_mongo_root_username="mongodb_username"
    export TF_VAR_mongo_root_password="mongodb_password"
 ```
 - Push changes to terraform
 ```bash
    terraform apply
 ```

 - when prompted
 ```bash
    var.mongo_root_password
 ```

### Other needed files
 - sensitive.tfvars

This file is where all the sensitive and non-sensitive variables goes. 