# Pulumi Flask App Deployment 🚀

This project demonstrates how to deploy a containerized Flask application on AWS Fargate using Pulumi and automate the deployment using GitHub Actions.
What is optional means you have to comment out if you dont want to use those services(like AMP), otherwise leave as is.

## 🔧 Tech Stack

- **Flask** – Python micro web framework
- **Docker** – Containerize the Flask app
- **Pulumi** – Infrastructure as Code (IaC) to deploy AWS resources
- **AWS Fargate** – Serverless compute for containers
- **GitHub Actions** – CI/CD pipeline for automated deployment
- **Prometheus and Grafana for monitoring(optional) - this you will have to download, install and configure your self on your machines.

## 📁 Project Structure

```text
.
├── app.py               # Flask application
├── Dockerfile           # Docker image for Flask app
├── .dockerignore        # Files excluded from the build context
├── requirements.txt     # Python dependencies
├── __main__.py          # Pulumi infrastructure code
├── Pulumi.yaml          # Pulumi project config
├── Pulumi.dev.yaml      # Pulumi stack config for local development
├── .github/workflows    # GitHub Actions workflow
├── tests/
│   └── test_app.py      # Unit tests
└── templates/
    └── index.html       # HTML template
```

## 🚀 Deployment

### 1. Infrastructure with Pulumi

Pulumi provisions:
- VPC, subnet, route table, and internet gateway
- Security group exposing port `5000`
- ECS cluster with Fargate service
- CloudWatch log group
- ECR repository and container image push
- AMP (Amazon Managed Prometheus) workspace(optional)

To deploy manually:

```bash
pulumi up
```

### 2. CI/CD with GitHub Actions

The pipeline does:
- Checkout and build
- Install Python + Pulumi
- Authenticate with AWS
- Deploy using pulumi up
- Trigger: On push to main branch.

🔐 Secrets (GitHub Actions)

Set these in your repo under Settings > Secrets and variables > Actions:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- PULUMI_ACCESS_TOKEN

🌐 Access

Once deployed, your Flask app will be accessible via the public IP and the port 5000.
First you need to find out your cluster name:

```bash
aws ecs list-clusters
```

Use the output here:

```bash
CLUSTER_NAME="insert here the output"
```
Second you need to find out your cluster service name:

```bash
aws ecs list-services --cluster $CLUSTER_NAME
```

Use the output here:

```bash
SERVICE_NAME="insert here the output"
```

Now we will use these two variables in the code below to get the output of our public IP:

```bash
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --desired-status RUNNING --query "taskArns[0]" --output text)

ENI_ID=$(aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $TASK_ARN --query "tasks[0].attachments[0].details[?name==\'networkInterfaceId\'].value" --output text)

PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --query "NetworkInterfaces[0].Association.PublicIp" --output text)

echo "ECS Task Public IP: $PUBLIC_IP:5000
```

You will get output >> `<your-public-ip>:5000`.
Copy/Paste it in browser to visit your Flask index page.
