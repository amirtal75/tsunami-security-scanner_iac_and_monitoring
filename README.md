# tsunami-security-scanner_iac_and_monitoring

# how to deploy the solution:
    # 0. install packages for python3, git, terraform
    # 1. clone the repo https://github.com/amirtal75/tsunami-security-scanner_iac_and_monitoring.git
    # 2. configure your local env in aws cli with aws credentials in sufficient permissions
    # 3. make sure that aws credentials are for a dev account
    # 4. cd env_setup_and_clean and run create_terraform_backend_with_arn.py 
    # 5. cd ../ && terraform init
    # 6. terraform plan to check the resources to be created (EKS, VPC, IAM, etc)
    # 7. terraform apply
    # 8. terraform output > env_setup_and_clean\output_tf.txt
    # 9. cat env_setup_and_clean\output_tf.txt | grep sg-
    # 10. in monitoring\grafana and monitoring\prometheus open the values.yaml and replace teh string <put_the_sg>  with the id you got from step 9
    # 11. aws eks update-kubeconfig --name TsunamiClusterTest --region us-west-2
    # 12. run the workflow install_keda in github
    # 13. helm upgrade --install prometheus-operator prometheus-community/kube-prometheus-stack -f ./monitoring/prometheus/values.yaml -f .monitoring/grafana/values.yaml --namespace monitoring --create-namespace
    # 14. helm upgrade --install tsunami-scanner ./tsunami-scanner
    # 15. aws sqs send-message-batch --queue-url https://sqs.us-west-2.amazonaws.com/<your_account_id>/tsunami_ip_list_queue --entries ./env_setup_and_clean/messages.json
    # 16. pod_name=$(k get pods -n default| grep tsunami | grep -i run | awk '{print $1}') && k logs -f $pod_name -n default 
# Monitoring   
    # 1. k get svc -n monitoring
    # 2. put the endpoint of the service in the browser to connect to teh ui
    # 3. configure a data source for cloudwatch with role or credentials for region us-west-2
    # 4. create daboard with panels:
        # a. AWS/SQS:
            # 1. metricName:"ApproximateNumberOfMessagesVisible"
            # 2. namespace:"AWS/SQS"
            # 3. region:"us-west-2"
            # 4. statistic:"Average"
        # b. Tsunami pod memory usage percentage:
            # (container_memory_usage_bytes{namespace="default", container!="POD", pod=~".*tsunami.*"}) / on (namespace, pod) group_left kube_pod_container_resource_limits{namespace="default", resource="memory", pod=~".*tsunami.*"} * 100
        # c. Tsunami pod memory usage in Mib
            # (container_memory_usage_bytes{namespace="default", container!="POD", pod=~".*tsunami.*"}) / 10240/1024
        # d. Tsunami pod cpu throttle:
            # sum by(namespace,pod)(rate(container_cpu_usage_seconds_total{namespace="default", pod!=""}[1m])) / sum by(namespace,pod)(kube_pod_container_resource_limits{namespace="default", pod!="", unit="core"})

# To do Dev:  
    # 1. understand how to finish configuration for scraping metrics from teh tsunami pod to prometheus to 
    # 2. understand how to get more plugins and use them to expand the errors tracked and additiional custom metrics   
    # 3. improve infrustructure creation to be more automated
        # a. understand how to create the custom dash board as a default
        # b. pull outputs from the terraform output to feed variables in the terraform files
        # c. create full patches for prometheus to scrape metrics and add them as a workflow
    # 4. etc
# To do Monitoring
    # 1. create cisualization for the custom metircs in the file tsunami_build/poll_and_scan.py 
    # 2. create notification channels in grafana and alerts for various required thresholds of custom metrics and other infrustructure
    # 3. understand how to configure fluent.d to feed coralogix and move the custom metrics creation to there from the app logs insterad of the python script
    # 4. track performance to optimize pod resource request and limit strategy and the scaling object logic
# Think of more stuff as I go....
# Cleanup
    # 1. terraform destroy (may be stuck in a few phases and need some manual delete of security-groups ot nat depnds on the way the helm was deployed)
    # 2. python env_setup_and_clean\cleanup_terraform_backend_with_arn.py

