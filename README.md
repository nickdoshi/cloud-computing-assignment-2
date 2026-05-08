# COSC2626 Assessment 2 — AWS Music Subscription App

A cloud-based music subscription web application built on AWS. Users can register, log in, query a song catalogue, and manage personal subscriptions. Three independent backends (EC2, ECS, Lambda) share a common DynamoDB data layer and S3 image store.

---

## Project Structure

```
.
├── frontent/                        # Static frontend (S3-hosted)
│   ├── login.html
│   ├── register.html
│   ├── main.html
│   ├── css/styles.css
│   └── js/
│       ├── config.js                # Set BACKEND_URL here to switch backends
│       └── main.js
│
├── src/main/java/com/a2/backend/    # Spring Boot app — used for EC2 and ECS
│   ├── config/                      # AWS client beans, CORS config
│   ├── controller/                  # AuthController, MusicController, SubscriptionController
│   ├── model/                       # Request records (LoginRequest, etc.)
│   └── service/                     # AuthService, MusicService, SubscriptionService
│
├── src/main/resources/
│   └── application.properties       # Region, table names, S3 bucket
│
├── backend-lambda/                  # Lambda handlers (Python)
│   ├── login/POST_lambda_function.py
│   ├── register/POST_lambda_function.py
│   ├── music/GET_lambda_function.py
│   └── subscriptions/
│       ├── GET_lambda_function.py
│       ├── POST_lambda_function.py
│       └── DELETE_lambda_function.py
│
├── init/                            # One-off setup scripts
│   ├── create_login_table.py
│   ├── create_music_table.py
│   ├── create_subscriptions_table.py
│   ├── load_music_data.py
│   ├── upload_images_s3.py
│   └── requirements.txt
│
├── backend-ec2/setup.sh             # EC2 provisioning (Java 17, Nginx, systemd)
├── Dockerfile                       # ECS container image
├── pom.xml
└── scripts/test_backend.sh          # End-to-end API test script
```

---

## DynamoDB Tables

### `login`
| Attribute | Type | Key |
|-----------|------|-----|
| `email` | String | Partition key |
| `user_name` | String | |
| `password` | String | |

### `music`
| Attribute | Type | Key |
|-----------|------|-----|
| `artist` | String | Partition key |
| `title_year_album` | String | Sort key (`title#year#album`) |
| `title`, `year`, `album` | String | |
| `image_url` | String | S3 object key |

The composite sort key exists because the dataset contains songs that share the same artist and title but differ by year or album. Using `artist` + `title` alone would overwrite those records on import.

### `subscriptions`
| Attribute | Type | Key |
|-----------|------|-----|
| `email` | String | Partition key |
| `subscription_id` | String | Sort key (`artist#title#year#album`) |
| `title`, `artist`, `year`, `album`, `image_url` | String | |

---

## API

All three backends expose the same endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/login` | Authenticate user |
| POST | `/register` | Register new user |
| GET | `/music?title=&year=&artist=&album=` | Query songs (AND logic, case-insensitive) |
| GET | `/subscriptions/{email}` | Get user subscriptions |
| POST | `/subscriptions` | Add subscription |
| DELETE | `/subscriptions/{email}/{subscriptionId}` | Remove subscription |

---

## Setup

### 1. Initialise AWS resources (run once)

```bash
pip install -r init/requirements.txt
python init/create_login_table.py
python init/create_music_table.py
python init/create_subscriptions_table.py
python init/load_music_data.py
python init/upload_images_s3.py
```

### 2. EC2 backend

```bash
# Build
./mvnw package -DskipTests

# Copy JAR to instance
scp -i music-app-key.pem target/backend-0.0.1-SNAPSHOT.jar ec2-user@<EC2_IP>:~/target/

# Deploy
ssh -i music-app-key.pem ec2-user@<EC2_IP> \
  "sudo cp ~/target/backend-0.0.1-SNAPSHOT.jar /opt/backend.jar && sudo systemctl restart backend"
```

Nginx reverse-proxies port 80 to Spring Boot on 8080. The EC2 instance must have the `LabRole` instance profile attached.

### 3. ECS backend

```bash
./mvnw package -DskipTests

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 176769085672.dkr.ecr.us-east-1.amazonaws.com

docker build -t music-backend .
docker tag music-backend:latest 176769085672.dkr.ecr.us-east-1.amazonaws.com/music-backend-211:aws-v2
docker push 176769085672.dkr.ecr.us-east-1.amazonaws.com/music-backend-211:aws-v2

aws ecs update-service \
  --cluster music-app-211 \
  --service music-app-task-definition-service-rbdovzkk \
  --force-new-deployment \
  --region us-east-1
```

### 4. Lambda backend

Deploy each function in `backend-lambda/` via the AWS console or CLI. Attach `LabRole` as the execution role. The API Gateway stage URL goes into `frontent/js/config.js` as `BACKEND_URL`.

### 5. Switch backends

Edit `frontent/js/config.js`:

```js
const BACKEND_URL = 'http://54.162.84.110';        // EC2
// const BACKEND_URL = 'http://32.197.14.240:8080'; // ECS
// const BACKEND_URL = 'https://ghp10za5f0.execute-api.us-east-1.amazonaws.com/test'; // Lambda
```

---

## Running locally (Spring Boot)

```bash
./mvnw spring-boot:run
# http://localhost:8080
```

AWS credentials are read from `~/.aws/credentials` locally, or from the `LabRole` instance profile on EC2/ECS.

---

## Testing

```bash
bash scripts/test_backend.sh
```

The script reads `BACKEND_URL` from `frontent/js/config.js` and runs a sequence of authenticated requests against all endpoints, reporting pass/fail for each.
