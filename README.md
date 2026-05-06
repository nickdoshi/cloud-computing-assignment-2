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
│   ├── login/                       # POST /login handler  ⚠️ not yet implemented
│   ├── register/                    # POST /register handler  ⚠️ not yet implemented
│   ├── music/                       # GET /music handler  ⚠️ not yet implemented
│   └── subscriptions/               # GET/POST/DELETE handler  ⚠️ not yet implemented
│
├── frontend/                        # Static site — hosted on S3
│   ├── login.html                   # Login page
│   ├── register.html                # Register page
│   ├── main.html                    # Main page (query + subscriptions) ⚠️ not yet built
│   ├── css/styles.css               # Spotify-dark shared stylesheet
│   └── js/config.js                 # BACKEND_URL switcher — change this for each demo
│
├── init/                            # One-off AWS initialisation scripts ⚠️ not yet built
│   ├── create_login_table.py        # Task 1 — create + seed login table
│   ├── create_music_table.py        # Task 2 — create music table with GSI/LSI
│   ├── load_music_data.py           # Task 3 — load 2026a2_songs.json → DynamoDB
│   └── upload_images_s3.py          # Task 4 — download artist images → S3
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

### Phase 1 — AWS Setup (do first, everything else depends on this)

- [ ] Start AWS Academy Lab session, confirm region `us-east-1`
- [ ] Create S3 bucket for artist images (private — no public ACLs)
- [ ] Set `aws.s3.bucket-name` in `src/main/resources/application.properties`
- [ ] Note the `LabRole` ARN (used for EC2 instance profile, ECS task role, Lambda execution role)

---

### Phase 2 — Database & Storage Initialisation (`init/`)

> These are standalone Python scripts run once to set up AWS resources. They do not need to be part of the Spring Boot app.

#### Task 1 — Login table
- [ ] `create_login_table.py` — create DynamoDB table `login`
  - Partition key: `email` (String)
  - Seed with the 10 provided user records (plain text passwords are permitted for this assignment)

#### Task 2 — Music table schema design (marks depend on this)
- [ ] Analyse `2026a2_songs.json` — identify cardinality of title/artist/album
- [ ] Key schema: partition key = `artist`, sort key = `title` (ensures no overwrites on import)
- [ ] GSI: `YearArtistIndex` — PK: `year`, SK: `artist` (enables query by year)
- [ ] LSI: `ArtistAlbumIndex` — PK: `artist`, SK: `album` (enables query by artist + album)
- [ ] `create_music_table.py` — create the `music` table with the above schema

#### Task 3 — Load music data
- [ ] `load_music_data.py` — parse `2026a2_songs.json`, batch-write all records to DynamoDB
- [ ] Verify record count matches JSON (no silent overwrites)

#### Task 4 — Upload artist images to S3
- [ ] `upload_images_s3.py` — for each unique `image_url` in the JSON:
  - Download the image from the original URL
  - Upload to the S3 bucket (key = e.g. `artist-images/<artist-slug>.jpg`)
  - Update the DynamoDB `image_url` attribute on each song to store the S3 object key

---

### Phase 3 — Frontend (`frontend/`)

Hosted on **S3 static website hosting**. All API calls are made from JavaScript using `fetch()`.

#### Login page — `login.html` ✅ done
- Email field, Password field, Login button, Register link
- Shows `"email or password is invalid"` on failure
- Saves `email` and `user_name` to `sessionStorage` on success, redirects to `main.html`

#### Register page — `register.html` ✅ done
- Email field, Username field, Password field, Create account button, Login link
- Shows `"The email already exists"` on duplicate email
- Shows success banner then redirects to `login.html`

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

#### 4a — EC2 (Spring Boot on EC2)

The Spring Boot app at the repo root is the EC2 backend.

- [ ] Launch EC2 instance (Amazon Linux 2023), attach `LabRole` as instance profile
- [ ] Build the JAR: `./mvnw package -DskipTests`
- [ ] Copy JAR to EC2, then run `sudo bash backend-ec2/setup.sh`
  - Installs Java 17 + Nginx, configures Nginx to proxy port 80 → 8080, registers a systemd service
- [ ] Confirm `http://<EC2_PUBLIC_IP>/health` returns `{"status":"ok"}`
- [ ] Complete `MusicService.java` and `MusicController.java` TODOs
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

- [ ] Write handler for each subfolder (`login/`, `register/`, `music/`, `subscriptions/`)
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
| `title` | String | Sort Key |
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
