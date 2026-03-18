# 🌐 Vehicle Counter - Cloud Deployment Guides

## Table of Contents
1. [AWS EC2 Deployment](#aws-ec2-deployment)
2. [Google Cloud Run Deployment](#google-cloud-run-deployment)
3. [Azure Container Instances](#azure-container-instances)
4. [Docker Swarm](#docker-swarm)
5. [Kubernetes](#kubernetes)
6. [Serverless Deployment (AWS Lambda)](#serverless-deployment)

---

## AWS EC2 Deployment

### 1. Launch EC2 Instance

```bash
# Using AWS CLI
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \  # Ubuntu 22.04 LTS
  --instance-type t3.large \
  --key-name your-key-pair \
  --security-groups allow-8000-5000 \
  --block-device-mappings DeviceName=/dev/xvda,Ebs={VolumeSize=50,VolumeType=gp3}
```

### 2. SSH into Instance

```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

### 3. Install Dependencies

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and Node.js
sudo apt-get install -y python3.11 python3-pip nodejs npm

# Install Docker
sudo apt-get install -y docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install NVIDIA GPU support (optional)
curl https://get.nvidia.com/nvidia-docker | sh
```

### 4. Deploy Application

```bash
# Clone repository
git clone <your-repo> vehicle-counter
cd vehicle-counter

# Create .env file
cat > .env << EOF
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
YOLO_MODEL=yolov8n.pt
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:password@db:5432/vehicle_counter
EOF

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f backend
```

### 5. Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt-get install -y nginx

# Create config
sudo tee /etc/nginx/sites-available/vehicle-counter << EOF
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Frontend
    location / {
        proxy_pass http://frontend/;
        proxy_set_header Host \$host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
}
EOF

# Enable config
sudo ln -s /etc/nginx/sites-available/vehicle-counter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Setup SSL (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Cost Estimation (AWS)
- **EC2 t3.large**: ~$0.08/hour = ~$59/month
- **Data transfer**: ~$0.09/GB
- **Storage**: $0.10/GB-month
- **Total**: ~$100-150/month for small-medium load

---

## Google Cloud Run Deployment

### 1. Setup Google Cloud Project

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Initialize
gcloud init
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Build Container Image

```bash
# Build locally
docker build -t vehicle-counter:latest .

# Tag for Google Cloud
docker tag vehicle-counter:latest gcr.io/YOUR_PROJECT_ID/vehicle-counter:latest

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/vehicle-counter:latest
```

### 3. Deploy to Cloud Run

```bash
gcloud run deploy vehicle-counter \
  --image gcr.io/YOUR_PROJECT_ID/vehicle-counter:latest \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --timeout 3600 \
  --set-env-vars DATABASE_URL=postgresql://... \
  --allow-unauthenticated
```

### 4. Setup Cloud SQL (Database)

```bash
# Create PostgreSQL instance
gcloud sql instances create vehicle-counter-db \
  --database-version POSTGRES_15 \
  --tier db-f1-micro \
  --region us-central1

# Create database
gcloud sql databases create vehicle_counter \
  --instance=vehicle-counter-db

# Create user
gcloud sql users create dbuser \
  --instance=vehicle-counter-db \
  --password
```

### 5. Setup Cloud Storage (for uploads)

```bash
# Create bucket
gsutil mb gs://vehicle-counter-uploads/

# Set permissions
gsutil iam ch serviceAccount:YOUR-SERVICE-ACCOUNT@appspot.gserviceaccount.com:objectCreator gs://vehicle-counter-uploads/
```

### Cost Estimation (Google Cloud)
- **Cloud Run**: $0.00001667/GB-second
- **Cloud SQL**: ~$10-50/month
- **Cloud Storage**: $0.020/GB
- **Total**: ~$50-100/month

---

## Azure Container Instances

### 1. Login to Azure

```bash
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

### 2. Create Resource Group

```bash
az group create \
  --name vehicle-counter-rg \
  --location eastus
```

### 3. Create Container Registry

```bash
az acr create \
  --resource-group vehicle-counter-rg \
  --name vehiclecounterregistry \
  --sku Basic
```

### 4. Build and Push Image

```bash
# Build in Azure
az acr build \
  --registry vehiclecounterregistry \
  --image vehicle-counter:latest .

# Or push locally built image
docker tag vehicle-counter:latest vehiclecounterregistry.azurecr.io/vehicle-counter:latest
docker push vehiclecounterregistry.azurecr.io/vehicle-counter:latest
```

### 5. Deploy Container

```bash
az container create \
  --resource-group vehicle-counter-rg \
  --name vehicle-counter \
  --image vehiclecounterregistry.azurecr.io/vehicle-counter:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables BACKEND_PORT=8000 \
  --registry-login-server vehiclecounterregistry.azurecr.io \
  --registry-username USERNAME \
  --registry-password PASSWORD
```

### 6. Setup Azure Database

```bash
az postgres server create \
  --resource-group vehicle-counter-rg \
  --name vehicle-counter-db \
  --location eastus \
  --admin-user dbadmin \
  --admin-password SecurePassword123!
```

### Cost Estimation (Azure)
- **Container Instances**: ~$0.015/GB-second
- **PostgreSQL**: ~$20-50/month
- **Storage**: $0.0184/GB
- **Total**: ~$40-80/month

---

## Docker Swarm Deployment

### 1. Initialize Swarm

```bash
# On manager node
docker swarm init --advertise-addr YOUR_IP

# On worker nodes
docker swarm join \
  --token SWMTKN-1-xxx \
  YOUR_IP:2377
```

### 2. Create Overlay Network

```bash
docker network create --driver overlay vehicle-counter-net
```

### 3. Deploy Stack

```bash
# Create docker-stack.yml
cat > docker-stack.yml << 'EOF'
version: '3.8'
services:
  backend:
    image: vehicle-counter:latest
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/vehicle_counter
      REDIS_URL: redis://cache:6379
    deploy:
      replicas: 3
      placement:
        constraints: [node.role == worker]
    networks:
      - vehicle-counter-net

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: vehicle_counter
    volumes:
      - db_data:/var/lib/postgresql/data
    deploy:
      placement:
        constraints: [node.role == manager]
    networks:
      - vehicle-counter-net

  cache:
    image: redis:7-alpine
    networks:
      - vehicle-counter-net

volumes:
  db_data:

networks:
  vehicle-counter-net:
    driver: overlay
EOF

# Deploy
docker stack deploy -c docker-stack.yml vehicle-counter

# Check status
docker stack ps vehicle-counter
```

---

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace vehicle-counter
```

### 2. Create Secrets

```bash
kubectl create secret generic vehicle-counter-secrets \
  --from-literal=db-password=SecurePassword123! \
  --from-literal=db-user=vcuser \
  -n vehicle-counter
```

### 3. Create ConfigMap

```bash
kubectl create configmap vehicle-counter-config \
  --from-literal=BACKEND_HOST=0.0.0.0 \
  --from-literal=BACKEND_PORT=8000 \
  --from-literal=YOLO_MODEL=yolov8n.pt \
  -n vehicle-counter
```

### 4. Create Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vehicle-counter-backend
  namespace: vehicle-counter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vehicle-counter
  template:
    metadata:
      labels:
        app: vehicle-counter
    spec:
      containers:
      - name: backend
        image: gcr.io/your-project/vehicle-counter:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: vehicle-counter-secrets
              key: db-url
        - name: BACKEND_PORT
          valueFrom:
            configMapKeyRef:
              name: vehicle-counter-config
              key: BACKEND_PORT
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      nodeSelector:
        gpu: "true"  # For GPU nodes (optional)
```

### 5. Create Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: vehicle-counter-service
  namespace: vehicle-counter
spec:
  type: LoadBalancer
  selector:
    app: vehicle-counter
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

### 6. Deploy

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Check status
kubectl get pods -n vehicle-counter
kubectl get services -n vehicle-counter
```

---

## Serverless Deployment (AWS Lambda)

### 1. Package Application

```bash
# Create Lambda function package
mkdir lambda-package
cd lambda-package
pip install -r ../requirements.txt -t .
cp ../vehicle_counter_backend.py .
zip -r lambda_function.zip .
```

### 2. Create Lambda Function

```bash
aws lambda create-function \
  --function-name vehicle-counter \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \
  --handler vehicle_counter_backend.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 900 \
  --memory-size 3008 \
  --environment Variables={PYTHONUNBUFFERED=1}
```

### 3. Setup API Gateway

```bash
# Create REST API
aws apigateway create-rest-api \
  --name vehicle-counter-api \
  --description "Vehicle Counter API"

# Create resources and methods
# Connect to Lambda
# Deploy API
```

---

## Monitoring & Logging

### CloudWatch Logs (AWS)

```bash
# View logs
aws logs tail /aws/lambda/vehicle-counter --follow

# Create alarm
aws cloudwatch put-metric-alarm \
  --alarm-name high-processing-time \
  --alarm-description "Alert when processing takes >5 minutes" \
  --metric-name ProcessingTime \
  --namespace VehicleCounter \
  --statistic Average \
  --period 300 \
  --threshold 300 \
  --comparison-operator GreaterThanThreshold
```

### Prometheus (Kubernetes)

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'vehicle-counter'
    static_configs:
      - targets: ['vehicle-counter-service:8000']
    metrics_path: '/metrics'
```

---

## Performance Optimization

### Caching Strategy

```python
# Redis caching
redis_client.setex(
    f"job:{job_id}",
    3600,  # 1 hour
    json.dumps(results)
)
```

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_job_id ON processing_jobs(id);
CREATE INDEX idx_created_at ON processing_jobs(created_at DESC);
CREATE INDEX idx_status ON processing_jobs(status);
```

### Auto-Scaling

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vehicle-counter-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vehicle-counter-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Cost Comparison

| Platform | Small Load | Medium Load | Large Load |
|----------|-----------|------------|-----------|
| **AWS EC2** | $60 | $200 | $500+ |
| **Google Cloud** | $50 | $150 | $400+ |
| **Azure** | $55 | $180 | $450+ |
| **Kubernetes (Self-hosted)** | $100 | $300 | $800+ |

---

## Security Best Practices

### 1. Environment Variables
```bash
# Use secrets management
aws secretsmanager create-secret --name vehicle-counter-db-password
```

### 2. HTTPS/SSL
```bash
# Let's Encrypt
certbot certonly --standalone -d your-domain.com
```

### 3. Authentication
```python
# Add API key requirement
@app.post("/upload")
async def upload_video(api_key: str = Header(...)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401)
```

### 4. Rate Limiting
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/upload")
@limiter.limit("10/minute")
async def upload_video(...):
    pass
```

---

## Monitoring & Alerts

### Health Checks
```bash
# Kubernetes
kubectl get pods -n vehicle-counter --watch
```

### Performance Metrics
- Processing time per video
- GPU/CPU utilization
- Memory usage
- API response time
- Database query time

### Logs
- All requests logged
- Error tracking
- Performance profiling
- User analytics

---

## Backup & Recovery

### Database Backups
```bash
# AWS RDS
aws rds create-db-snapshot \
  --db-instance-identifier vehicle-counter-db \
  --db-snapshot-identifier vehicle-counter-backup-$(date +%Y%m%d)
```

### File Uploads Backup
```bash
# S3 backup
aws s3 sync s3://vehicle-counter-uploads s3://vehicle-counter-backups/$(date +%Y%m%d)/
```

---

This guide covers all major cloud platforms. Choose based on your:
- **Budget**: AWS/Google typically cheaper at scale
- **Features**: Kubernetes for maximum flexibility
- **Simplicity**: Cloud Run / Container Instances for ease
- **Existing infrastructure**: Deploy to your preferred cloud

Start with Docker Compose locally, then scale to cloud as needed!
