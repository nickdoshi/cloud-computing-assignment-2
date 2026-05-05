# COSC2626 Assessment 2 — AWS Music Subscription App

**Due:** 11:59 PM Friday, 8 May 2026  
**Weight:** 40% (100 marks)  
**Group size:** Up to 4 students

---

## Project Structure

```
.
├── init/                        # One-off AWS initialisation scripts
│   ├── create_login_table.py    # Task 1 – create & seed login table
│   ├── create_music_table.py    # Task 2 – create music table (with GSI/LSI)
│   ├── load_music_data.py       # Task 3 – load 2026a2_songs.json → DynamoDB
│   └── upload_images_s3.py      # Task 4 – download artist images → S3
│
├── frontend/                    # Static site (HTML/CSS/JS)
│   ├── index.html               # Login page
│   ├── register.html            # Register page
│   ├── main.html                # Main page (query + subscriptions)
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js               # Calls whichever backend is active
│
├── backend-ec2/                 # EC2 virtual-server backend
│   ├── app.py                   # Flask/FastAPI REST API
│   ├── requirements.txt
│   └── setup.sh                 # Apache/Nginx + app install script
│
├── backend-ecs/                 # ECS containerised backend
│   ├── app.py                   # Same API surface as EC2 backend
│   ├── requirements.txt
│   └── Dockerfile
│
├── backend-lambda/              # API Gateway + Lambda serverless backend
│   ├── login/
│   │   └── handler.py           # POST /login
│   ├── register/
│   │   └── handler.py           # POST /register
│   ├── music/
│   │   └── handler.py           # GET /music (query), GET /music/{id}
│   └── subscriptions/
│       └── handler.py           # GET/POST/DELETE /subscriptions
│
├── 2026a2_songs.json            # Provided dataset (add to repo)
├── report/                      # Architecture diagram + written report assets
└── README.md
```

---

## Task Checklist

### Phase 1 — AWS Setup (do first, everything else depends on this)

- [ ] Create AWS Academy session and note region (us-east-1)
- [ ] Create S3 bucket for artist images (private, use pre-signed URLs or bucket policy)
- [ ] Note `LabRole` ARN (no custom IAM roles allowed)

---

### Phase 2 — Database & Storage Initialisation (`init/`)

#### Task 1 — Login table
- [ ] `create_login_table.py` — create DynamoDB table `login`
  - Partition key: `email` (String)
  - Seed with 10 provided user records (plain text passwords permitted for this assignment)

#### Task 2 — Music table schema design (marks depend on this)
- [ ] Analyse `2026a2_songs.json` — identify cardinality of title/artist/album
- [ ] Design key schema so **no songs are overwritten** on import
  - Likely: partition key = `artist`, sort key = `title` (or composite)
- [ ] Add **at least one GSI** (e.g., query by `year` or `album`)
- [ ] Add **at least one LSI** (must share partition key with base table)
- [ ] Document key design rationale in report
- [ ] `create_music_table.py` — create the `music` table with chosen schema

#### Task 3 — Load music data
- [ ] `load_music_data.py` — parse `2026a2_songs.json`, batch-write all records
- [ ] Verify no records silently overwritten (check record count before/after)

#### Task 4 — Upload artist images to S3
- [ ] `upload_images_s3.py` — for each unique `image_url` in JSON:
  - Download image
  - Upload to S3 with key derived from artist name
  - Store S3 key/URL back in DynamoDB record (`image_url` attribute)

---

### Phase 3 — Frontend (`frontend/`)

Hosted on **S3 static website** (justify this choice in report vs EC2/ECS).

#### Login page (`index.html`)
- [ ] Email field, Password field, Login button, Register link
- [ ] On submit: POST credentials to backend `/login`
- [ ] Display `"email or password is invalid"` on failure
- [ ] Redirect to `main.html` on success (store session token/cookie)

#### Register page (`register.html`)
- [ ] Email field, Username field, Password field, Register button
- [ ] On submit: POST to backend `/register`
- [ ] Display `"The email already exists"` if duplicate email
- [ ] Redirect to `index.html` on success

#### Main page (`main.html`)
- [ ] **User area** — display logged-in username
- [ ] **Subscription area**
  - [ ] Fetch user's subscriptions from backend on page load
  - [ ] Display: title, artist, year, album, artist image (from S3), Remove button
  - [ ] Remove button: DELETE subscription from DynamoDB + remove from UI
- [ ] **Query area**
  - [ ] Fields: Title, Year, Artist, Album + Query button
  - [ ] At least one field must be filled (validate client-side)
  - [ ] Multi-field query uses AND logic
  - [ ] Display results with artist image + Subscribe button
  - [ ] `"No result is retrieved. Please query again"` when empty
  - [ ] Subscribe button: POST to DynamoDB subscriptions table + add to subscription area
- [ ] **Logout link** — clear session, redirect to login page

---

### Phase 4 — Backend (all three must be fully functional)

> All three backends expose the **same REST API surface**. The frontend JS swaps the base URL to test each one.

#### API surface (implement in all three backends)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/login` | Validate credentials against login table |
| POST | `/register` | Create new user (unique email check) |
| GET | `/music` | Query music table (title/year/artist/album params, AND logic) |
| GET | `/subscriptions/{email}` | Get user's subscriptions |
| POST | `/subscriptions` | Add subscription |
| DELETE | `/subscriptions/{email}/{id}` | Remove subscription |

#### 4a — EC2 Backend (`backend-ec2/`)
- [ ] Launch EC2 instance (Amazon Linux 2 or Ubuntu), port 80
- [ ] Install Python + Flask (or Node.js/Express) via `setup.sh`
- [ ] Attach `LabRole` to EC2 instance profile
- [ ] Implement all API routes with DynamoDB SDK calls
- [ ] Use both `Query` and `Scan` operations appropriately
- [ ] Run behind Apache or Nginx on port 80
- [ ] Test all endpoints

#### 4b — ECS Backend (`backend-ecs/`)
- [ ] Write `Dockerfile` based on `backend-ec2/app.py`
- [ ] Push image to ECR
- [ ] Create ECS cluster + task definition (attach `LabRole`)
- [ ] Expose service on port 80 via ALB or public IP
- [ ] Test all endpoints (functionally equivalent to EC2)

#### 4c — Lambda + API Gateway (`backend-lambda/`)
- [ ] Create Lambda functions for each route (attach `LabRole`)
- [ ] Create REST API in API Gateway
- [ ] Map HTTP methods correctly: GET/POST/DELETE → correct Lambda
- [ ] Enable CORS on API Gateway
- [ ] Deploy API and note invoke URL
- [ ] Test all endpoints

---

### Phase 5 — Report (`report/`)

- [ ] AWS architecture diagram (service boxes + arrows showing data flow)
- [ ] **Frontend hosting justification** — S3 static site vs EC2/ECS trade-offs (performance, cost, scalability, ops overhead, security)
- [ ] **Backend comparison table** — EC2 vs ECS vs Lambda+APIGW across: scalability, cost, ops complexity, performance, maintainability
- [ ] **Recommended architecture** — pick one and justify with technical reasoning
- [ ] **DynamoDB key schema rationale** — why chosen PK/SK, GSI/LSI design and query patterns they support

---

### Phase 6 — Submission

- [ ] All code zipped as `GroupLeaderStudentID_Group<N>.zip`
- [ ] Report as `GroupLeaderStudentID_Group<N>_report.pdf`
- [ ] Work log as `GroupLeaderStudentID_Group<N>_worklog.pdf`
- [ ] Submit on Canvas before 11:59 PM 8 May 2026
- [ ] Book demo slot in Week 9 (one slot only — overbooking = 10% penalty)

---

## Key AWS Constraints

| Constraint | Detail |
|-----------|--------|
| IAM roles | Use `LabRole` only — no custom role creation |
| Ports | Run on port 80 or 443 only |
| Elastic Beanstalk | **Not allowed** |
| S3 access | Must be secure (pre-signed URLs or bucket policy — no public ACLs) |
| DynamoDB | Must include ≥1 GSI and ≥1 LSI, use both Query and Scan |
| API Gateway | Must use GET/POST/DELETE correctly — no all-POST shortcuts |

---

## DynamoDB Tables

### `login`
| Attribute | Type | Key |
|-----------|------|-----|
| email | String | Partition Key |
| user_name | String | — |
| password | String | — |

### `music` (schema TBD after data analysis)
| Attribute | Type | Key |
|-----------|------|-----|
| artist | String | Partition Key (proposed) |
| title | String | Sort Key (proposed) |
| year | String | — |
| album | String | — |
| image_url | String | — |

### `subscriptions` (new table)
| Attribute | Type | Key |
|-----------|------|-----|
| email | String | Partition Key |
| subscription_id | String | Sort Key |
| title, artist, year, album, image_url | String | — |

---

## Notes

- Analyse `2026a2_songs.json` before creating the music table — the key schema decision is worth marks.
- Artist images in S3 must be accessed securely (pre-signed URLs recommended).
- The frontend JS should make it easy to switch the backend base URL between EC2/ECS/Lambda for demo purposes.
- Source any borrowed code with an inline comment citing the source.
