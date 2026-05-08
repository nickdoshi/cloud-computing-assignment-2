# COSC2626 Assessment 2 — AWS Music Subscription App

**Due:** 11:59 PM Friday, 8 May 2026  
**Weight:** 40% (100 marks)  
**Group size:** Up to 4 students

---

## Project Structure

```
.
├── pom.xml                          # Maven build — dependencies and Spring Boot config
├── Dockerfile                       # ECS container image (builds from the Maven JAR)
├── mvnw / mvnw.cmd                  # Maven wrapper — use instead of system Maven
│
├── src/main/java/com/a2/backend/    # Spring Boot application (EC2 + ECS backend)
│   ├── BackendApplication.java      # Entry point — starts embedded Tomcat on :8080
│   ├── config/
│   │   ├── AwsConfig.java           # DynamoDB, S3, S3Presigner Spring beans
│   │   └── CorsConfig.java          # CORS — allows frontend origin to call the API
│   ├── controller/
│   │   ├── AuthController.java      # POST /login, POST /register
│   │   ├── MusicController.java     # GET /music  ⚠️ stub — team to complete
│   │   └── SubscriptionController.java  # GET/POST/DELETE /subscriptions
│   ├── model/
│   │   ├── LoginRequest.java        # { email, password }
│   │   ├── RegisterRequest.java     # { email, user_name, password }
│   │   └── SubscribeRequest.java    # { email, title, artist, year, album }
│   └── service/
│       ├── AuthService.java         # Login/register DynamoDB logic
│       ├── MusicService.java        # Music query logic  ⚠️ stub — team to complete
│       └── SubscriptionService.java # Subscription DynamoDB logic
│
├── src/main/resources/
│   └── application.properties       # AWS region, table names, S3 bucket name
│
├── backend-ec2/
│   └── setup.sh                     # EC2 install: Java 17, Nginx (port 80→8080), systemd
│
├── backend-lambda/                  # API Gateway + Lambda — separate from Spring Boot
│   ├── login/                       # POST /login handler  
│   ├── register/                    # POST /register handler  
│   ├── music/                       # GET /music handler  
│   └── subscriptions/               # GET/POST/DELETE handler  
│
├── frontend/                        # Static site — hosted on S3
│   ├── login.html                   # Login page  ✅ done
│   ├── register.html                # Register page  ✅ done
│   ├── main.html                    # Main page (query + subscriptions) ⚠️ not yet built
│   ├── css/styles.css               # Spotify-dark shared stylesheet
│   └── js/config.js                 # BACKEND_URL switcher — change this for each demo
│
├── init/                            # One-off AWS initialisation scripts
│   ├── create_login_table.py        # Task 1 — create + seed login table
│   ├── create_music_table.py        # Task 2 — create music table with GSI/LSI
│   ├── load_music_data.py           # Task 3 — load 2026a2_songs.json → DynamoDB
│   ├── upload_images_s3.py          # Task 4 — download artist images → S3
│   └── requirements.txt             # boto3, requests
│
├── report/
│   └── design_choices.md            # Draft report content (frontend/backend/DynamoDB rationale)
│
├── CODEBASE.md                      # File-by-file explanation of the whole repo
└── README.md
```

---

## Running the Spring Boot Backend Locally

```bash
# 1. Set your bucket name in application.properties first
# 2. Build
./mvnw package -DskipTests

# 3. Run
./mvnw spring-boot:run
# Server starts on http://localhost:8080
```

AWS credentials are picked up automatically from `~/.aws/credentials` locally, or from the LabRole instance profile on EC2/ECS.

---

## Task Checklist

### Phase 1 — AWS Setup ✅

- [x] Start AWS Academy Lab session, confirm region `us-east-1`
- [x] Create S3 bucket for artist images (`music-app-images-211-rmit`, private — no public ACLs)
- [x] Set `aws.s3.bucket-name=music-app-images-211-rmit` in `src/main/resources/application.properties`
- [x] Note the `LabRole` ARN (used for EC2 instance profile, ECS task role, Lambda execution role)

---

### Phase 2 — Database & Storage Initialisation (`init/`)

> Standalone Python scripts — run once to set up AWS resources.
> Requires fresh AWS Academy credentials in `~/.aws/credentials` before each run.

```bash
pip install -r init/requirements.txt
```

#### Task 1 — Login table
- [x] `create_login_table.py` written — creates DynamoDB table `login`, seeds 10 user records
- [ ] Run: `python init/create_login_table.py`

#### Task 2 — Music table
- [x] `create_music_table.py` written — PK: `artist`, SK: `title`, GSI: `YearArtistIndex`, LSI: `ArtistAlbumIndex`
- [ ] Run: `python init/create_music_table.py`

#### Task 3 — Load music data
- [x] `load_music_data.py` written — batch-writes all songs from `2026a2_songs.json`
- [ ] Run: `python init/load_music_data.py`

#### Task 4 — Upload artist images to S3
- [x] `upload_images_s3.py` written — downloads images, uploads to S3, updates DynamoDB `image_url`
- [ ] Run: `python init/upload_images_s3.py`

---

### Phase 3 — Frontend (`frontend/`)

Hosted on **S3 static website hosting**. All API calls made from JavaScript using `fetch()`.  
Set `BACKEND_URL` in `frontend/js/config.js` to point at the active backend before testing.

#### Login page — `login.html` ✅ done
- Email + password form, shows `"email or password is invalid"` on failure
- Saves `email` and `user_name` to `sessionStorage`, redirects to `main.html`

#### Register page — `register.html` ✅ done
- Email + username + password form
- Shows `"The email already exists"` on duplicate, success banner → redirect to `login.html`

#### Main page — `main.html` ⚠️ not yet built
- [ ] **User area** — display `sessionStorage.getItem('user_name')`, Logout link
- [ ] **Subscription area**
  - [ ] On page load: `GET /subscriptions/{email}`, render each song with image + Remove button
  - [ ] Remove button: `DELETE /subscriptions/{email}/{subscriptionId}`, remove from UI
- [ ] **Query area**
  - [ ] Fields: Title, Year, Artist, Album + Query button
  - [ ] Validate at least one field is filled before submitting
  - [ ] `GET /music?title=&year=&artist=&album=` — AND logic across supplied fields
  - [ ] Show results with artist image + Subscribe button
  - [ ] Show `"No result is retrieved. Please query again"` when results are empty
  - [ ] Subscribe: `POST /subscriptions`, add song to subscription area
- [ ] **Logout** — `sessionStorage.clear()`, redirect to `login.html`

---

### Phase 4 — Backend

All three backends expose the **same REST API**. Change `BACKEND_URL` in `frontend/js/config.js` to switch between them for the demo.

#### API surface

| Method | Path | Description |
|--------|------|-------------|
| POST | `/login` | Validate credentials against `login` table |
| POST | `/register` | Create new user (unique email enforced) |
| GET | `/music` | Query music table (`?title=&year=&artist=&album=`, AND logic) |
| GET | `/subscriptions/{email}` | Get all subscriptions for a user |
| POST | `/subscriptions` | Add a subscription |
| DELETE | `/subscriptions/{email}/{subscriptionId}` | Remove a subscription |

---

#### 4a — EC2 (Spring Boot on EC2) ⚠️ in progress

**1. Build the JAR locally:**
```bash
./mvnw package -DskipTests
```

**2. Copy JAR to EC2:**
```bash
ssh -i music-app-key.pem ec2-user@<EC2_PUBLIC_IP> "mkdir -p ~/target"
scp -i music-app-key.pem target/backend-0.0.1-SNAPSHOT.jar ec2-user@<EC2_PUBLIC_IP>:~/target/
```

**3. SSH in and run setup (installs Java 17 + Nginx, registers systemd service):**
```bash
ssh -i music-app-key.pem ec2-user@<EC2_PUBLIC_IP>
sudo bash setup.sh
```

> If setup.sh fails on the `cp` step, run these manually instead:
> ```bash
> sudo cp ~/target/backend-0.0.1-SNAPSHOT.jar /opt/backend.jar
> sudo tee /etc/nginx/conf.d/backend.conf > /dev/null <<'EOF'
> server {
>     listen 80;
>     server_name _;
>     location / {
>         proxy_pass         http://127.0.0.1:8080;
>         proxy_set_header   Host $host;
>         proxy_set_header   X-Real-IP $remote_addr;
>         proxy_read_timeout 60s;
>     }
> }
> EOF
> sudo sed -i '/listen.*80/d' /etc/nginx/nginx.conf 2>/dev/null || true
> sudo systemctl enable --now nginx
> sudo tee /etc/systemd/system/backend.service > /dev/null <<'EOF'
> [Unit]
> Description=Music App Spring Boot Backend
> After=network.target
> [Service]
> ExecStart=/usr/bin/java -jar /opt/backend.jar
> Restart=on-failure
> StandardOutput=journal
> StandardError=journal
> [Install]
> WantedBy=multi-user.target
> EOF
> sudo systemctl daemon-reload
> sudo systemctl enable --now backend
> ```

**4. Verify:**
```bash
curl http://<EC2_PUBLIC_IP>/health
# Expected: {"status":"ok"}
```

**5. Update config.js:**
```js
const BACKEND_URL = 'http://<EC2_PUBLIC_IP>';
```

- [x] Launch EC2 instance (Amazon Linux 2023 t3.micro), attach `LabRole` as instance profile
- [x] Build JAR and copy to EC2
- [ ] Confirm `/health` returns `{"status":"ok"}`
- [ ] Complete `MusicService.java` and `MusicController.java` TODOs (teammate)
- [ ] Test all six endpoints

#### 4b — ECS (Spring Boot in a container)

Same Spring Boot app, Dockerised. `Dockerfile` is at the repo root.

- [ ] Build the JAR: `./mvnw package -DskipTests`
- [ ] Build and push Docker image to ECR:
  ```bash
  docker build -t music-backend .
  docker tag music-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/music-backend:latest
  docker push <account>.dkr.ecr.us-east-1.amazonaws.com/music-backend:latest
  ```
- [ ] Create ECS cluster + task definition (attach `LabRole` as task role, expose port 8080)
- [ ] Expose on port 80 via ALB or public IP
- [ ] Test all six endpoints (must be functionally equivalent to EC2)

#### 4c — Lambda + API Gateway

Separate from Spring Boot — small standalone handlers in `backend-lambda/`. Can be written in Python or any supported runtime.

- [X] Write handler for each subfolder (`login/`, `register/`, `music/`, `subscriptions/`)
- [ ] Each handler calls DynamoDB / S3 directly via the AWS SDK
- [ ] Create a REST API in API Gateway
- [ ] Map `GET`, `POST`, `DELETE` HTTP methods to the correct Lambda (no all-POST shortcuts)
- [ ] Enable CORS on API Gateway
- [ ] Attach `LabRole` as the Lambda execution role
- [ ] Deploy API, note the invoke URL, paste into `config.js` for testing
- [ ] Test all six endpoints

---

### Phase 5 — Report

- [ ] AWS architecture diagram — service boxes and arrows showing data flow
- [ ] Frontend hosting justification (see `report/design_choices.md` §1)
- [ ] Backend comparison + recommended architecture (see `report/design_choices.md` §2)
- [ ] DynamoDB key schema rationale (see `report/design_choices.md` §3)

---

### Phase 6 — Submission

- [ ] All code zipped as `GroupLeaderStudentID_Group<N>.zip`
- [ ] Report as `GroupLeaderStudentID_Group<N>_report.pdf`
- [ ] Work log as `GroupLeaderStudentID_Group<N>_worklog.pdf`
- [ ] Submit on Canvas before 11:59 PM 8 May 2026
- [ ] Book **one** demo slot in Week 9 (overbooking = 10% penalty)

---

## Key AWS Constraints

| Constraint | Detail |
|-----------|--------|
| IAM roles | Use `LabRole` only — no custom role creation |
| Ports | App must be reachable on port 80 or 443 |
| Elastic Beanstalk | Not allowed |
| S3 access | Must be secure — use pre-signed URLs (already implemented in `MusicService`) |
| DynamoDB | Must include ≥1 GSI and ≥1 LSI, use both `Query` and `Scan` |
| API Gateway | Must use `GET`/`POST`/`DELETE` correctly — no all-POST shortcuts |

---

## DynamoDB Tables

### `login`
| Attribute | Type | Key |
|-----------|------|-----|
| `email` | String | Partition Key |
| `user_name` | String | — |
| `password` | String | — |

### `music`
| Attribute | Type | Key |
|-----------|------|-----|
| `artist` | String | Partition Key |
| `title_year_album` | String | Sort Key (composite: `title#year#album`)
| `title` | String | — |
| `year` | String | — |
| `album` | String | — |
| `image_url` | String | S3 object key (set by init script) |

Indexes:
- **GSI** `YearArtistIndex` — PK: `year`, SK: `artist`
- **LSI** `ArtistAlbumIndex` — PK: `artist`, SK: `album`

### `subscriptions`
| Attribute | Type | Key |
|-----------|------|-----|
| `email` | String | Partition Key |
| `subscription_id` | String | Sort Key (`"artist#title"`) |
| `title`, `artist`, `year`, `album`, `image_url` | String | — |
