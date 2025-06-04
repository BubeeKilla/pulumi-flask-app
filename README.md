# Pulumi Flask App Deployment 🚀

This project demonstrates how to deploy a containerized Flask application on AWS Fargate using Pulumi and automate the deployment using GitHub Actions.

## 🔧 Tech Stack

- **Flask** – Python micro web framework
- **Docker** – Containerize the Flask app
- **Pulumi** – Infrastructure as Code (IaC) to deploy AWS resources
- **AWS Fargate** – Serverless compute for containers
- **GitHub Actions** – CI/CD pipeline for automated deployment

## 📁 Project Structure
.
├── app.py # Flask application
├── Dockerfile # Docker image for Flask app
├── requirements.txt # Python dependencies
├── main.py # Pulumi infrastructure code
├── Pulumi.yaml # Pulumi project config
├── .github/workflows # GitHub Actions workflow
└── templates/index.html # HTML template

## 🚀 Deployment

### 1. Infrastructure with Pulumi

Pulumi provisions:
- VPC, subnet, route table, and internet gateway
- Security group exposing port `5000`
- ECS cluster with Fargate service
- CloudWatch log group
- ECR repository and container image push

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

-----------------------------------------------------------------------

🔐 Secrets (GitHub Actions)

Set these in your repo under Settings > Secrets and variables > Actions:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- PULUMI_ACCESS_TOKEN

🌐 Access

Once deployed, your Flask app will be accessible via:
- http://<public-ip>:5000
The public IP is exported by Pulumi after deployment.