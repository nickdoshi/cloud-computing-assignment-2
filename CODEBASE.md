# Codebase Walkthrough

A file-by-file explanation of every source file in this repository.

---

## Repository Layout

```
.
├── pom.xml                          # Maven build + dependencies
├── Dockerfile                       # Container image for ECS
├── backend-ec2/
│   └── setup.sh                     # EC2 install script
├── frontend/
│   ├── login.html                   # Login page
│   ├── register.html                # Register page
│   ├── css/styles.css               # Shared dark stylesheet
│   └── js/config.js                 # Backend URL switcher
└── src/main/java/com/a2/backend/
    ├── BackendApplication.java      # Spring Boot entry point
    ├── config/
    │   ├── AwsConfig.java           # AWS SDK beans
    │   └── CorsConfig.java          # CORS rules
    ├── controller/
    │   ├── AuthController.java      # POST /login, POST /register
    │   ├── MusicController.java     # GET /music  [STUB - team to complete]
    │   └── SubscriptionController.java  # GET/POST/DELETE /subscriptions
    ├── model/
    │   ├── LoginRequest.java        # Request body for login
    │   ├── RegisterRequest.java     # Request body for register
    │   └── SubscribeRequest.java    # Request body for subscribe
    └── service/
        ├── AuthService.java         # Login/register DynamoDB logic
        ├── MusicService.java        # Music query logic [STUB - team to complete]
        └── SubscriptionService.java # Subscription DynamoDB logic
```

---

## Root Files

---

### `pom.xml`
Maven's project configuration file — the equivalent of `package.json` in Node.

**Key contents:**
- **Spring Boot 4.0.6** — the web framework. Provides the embedded Tomcat server, dependency injection, and REST annotations.
- **Java 17** — the language version target.
- **`spring-boot-starter-webmvc`** — pulls in Spring MVC, Jackson (JSON serialisation), and the embedded Tomcat server.
- **`spring-boot-devtools`** — development-only tool that auto-restarts the server when code changes. Not included in the production JAR.
- **`software.amazon.awssdk:dynamodb 2.25.0`** — AWS SDK v2 client for DynamoDB (reading/writing tables).
- **`software.amazon.awssdk:s3 2.25.0`** — AWS SDK v2 client for S3 (also includes the pre-signer for generating temporary image URLs).
- **`spring-boot-maven-plugin`** — enables `./mvnw package` to produce a fat JAR containing all dependencies, which is what gets deployed to EC2 and ECS.

---

### `Dockerfile`
Used to build the **ECS** container image. It is a four-line file:

```
FROM eclipse-temurin:17-jre-alpine   ← small Java 17 base image
WORKDIR /app
COPY target/backend-0.0.1-SNAPSHOT.jar app.jar   ← the fat JAR built by Maven
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

**Workflow:** build the JAR locally with `./mvnw package -DskipTests`, then `docker build`, push to ECR, and reference the image in an ECS task definition. The ECS task maps container port 8080 to the load balancer on port 80.

---

### `src/main/resources/application.properties`
Spring Boot's main configuration file. Values here are injected into beans using `@Value("${key}")`.

| Property | Purpose |
|----------|---------|
| `server.port=8080` | Port the embedded Tomcat listens on |
| `aws.region=us-east-1` | AWS region used by all SDK clients |
| `aws.s3.bucket-name=YOUR_BUCKET_NAME` | **Must be set** to your actual S3 bucket name |
| `aws.dynamodb.table.login=login` | DynamoDB table name for user accounts |
| `aws.dynamodb.table.music=music` | DynamoDB table name for songs |
| `aws.dynamodb.table.subscriptions=subscriptions` | DynamoDB table name for subscriptions |

When deployed to EC2 or ECS, the AWS credentials are provided automatically by the **LabRole** attached to the instance/task — no access keys in this file.

---

## Spring Boot Source

---

### `BackendApplication.java`
The entry point. The single `main` method calls `SpringApplication.run(...)` which:
1. Starts the embedded Tomcat server on port 8080.
2. Scans all classes in the `com.a2.backend` package for Spring annotations (`@RestController`, `@Service`, `@Configuration`, etc.) and wires them together.

Nothing needs to change here.

---

## `config/` — Configuration Beans

---

### `AwsConfig.java`
A `@Configuration` class that creates three **Spring beans** (singleton objects managed by Spring). These beans are injected wherever they are needed using constructor injection.

| Bean | Type | Purpose |
|------|------|---------|
| `dynamoDbClient()` | `DynamoDbClient` | Used by all services to read/write DynamoDB tables |
| `s3Client()` | `S3Client` | Available for direct S3 operations (uploads etc.) |
| `s3Presigner()` | `S3Presigner` | Generates temporary signed URLs for artist images |

All three use `DefaultCredentialsProvider` — this automatically picks up credentials from the EC2 instance profile / ECS task role (LabRole) without any hardcoded keys.

---

### `CorsConfig.java`
Allows the **frontend** (served from S3 or another origin) to call the backend without being blocked by the browser's same-origin policy.

- Applies to all routes (`/**`).
- Allows `GET`, `POST`, `DELETE`, `OPTIONS` from any origin (`*`).

This must be present or every browser request from the frontend will fail with a CORS error.

---

## `controller/` — HTTP Endpoints

Controllers receive HTTP requests and return HTTP responses. They do not contain business logic — they delegate to services.

---

### `AuthController.java`

| Method | Path | What it does |
|--------|------|-------------|
| `POST` | `/login` | Validates credentials, returns `user_name` on success |
| `POST` | `/register` | Creates a new user, rejects duplicate emails |

**Login response (success — HTTP 200):**
```json
{ "success": true, "user_name": "Alice" }
```

**Login response (failure — HTTP 401):**
```json
{ "success": false, "message": "email or password is invalid" }
```

**Register response (duplicate email — HTTP 409):**
```json
{ "success": false, "message": "The email already exists" }
```

The exact message strings match what the assignment specification requires to be shown on the frontend.

---

### `MusicController.java` ⚠️ STUB

| Method | Path | What it does |
|--------|------|-------------|
| `GET` | `/music` | Returns songs matching the query parameters |

**Query parameters** (all optional, ANDed together):
- `title` — partial match
- `year` — exact match
- `artist` — exact match (also determines whether Query or Scan is used)
- `album` — partial match

**Currently returns an empty list.** The body of `queryMusic()` contains a `TODO` comment — a teammate needs to replace it with `return musicService.query(title, year, artist, album);`. The full logic already exists in `MusicService.java` waiting to be wired up.

---

### `SubscriptionController.java`

| Method | Path | What it does |
|--------|------|-------------|
| `GET` | `/subscriptions/{email}` | Fetches all subscriptions for a user |
| `POST` | `/subscriptions` | Adds a song to a user's subscriptions |
| `DELETE` | `/subscriptions/{email}/{subscriptionId}` | Removes a subscription |

The `subscriptionId` in the DELETE path is in the format `artist#title` (URL-encoded as `artist%23title` in the request). This format is what gets stored as the sort key in DynamoDB — see `SubscriptionService` for details.

---

## `model/` — Request Body Records

These are Java 17 **records** — immutable data classes that Jackson deserialises incoming JSON into. They have no logic.

---

### `LoginRequest.java`
```java
record LoginRequest(String email, String password)
```
Maps from: `{ "email": "...", "password": "..." }`

---

### `RegisterRequest.java`
```java
record RegisterRequest(String email, String userName, String password)
```
Maps from: `{ "email": "...", "user_name": "...", "password": "..." }`

The `@JsonProperty("user_name")` annotation is needed because the JSON field uses snake_case (`user_name`) but the Java field uses camelCase (`userName`).

---

### `SubscribeRequest.java`
```java
record SubscribeRequest(String email, String title, String artist, String year, String album)
```
Maps from: `{ "email": "...", "title": "...", "artist": "...", "year": "...", "album": "..." }`

Note: no `image_url` field — the backend looks up the S3 image key directly from the music table using the artist + title, so the frontend does not need to pass it.

---

## `service/` — Business Logic

Services contain all database operations. They are injected into controllers.

---

### `AuthService.java`

**`login(email, password)`**
1. Calls `dynamoDb.getItem()` with `email` as the key on the `login` table.
2. If no item is found, returns `Optional.empty()`.
3. Compares the stored password to the supplied one.
4. Returns `Optional.of(user_name)` on success, `Optional.empty()` on mismatch.

**`register(email, userName, password)`**
1. Calls `dynamoDb.getItem()` to check if the email already exists.
2. Returns `false` if it does (controller sends 409).
3. Calls `dynamoDb.putItem()` to insert the new user record.
4. Returns `true` on success.

---

### `MusicService.java` ⚠️ STUB

Contains stub methods with detailed `TODO` comments for a teammate to implement. The infrastructure (injected `DynamoDbClient`, `S3Presigner`, table name, bucket name) is all wired up — only the method bodies need filling in.

| Method | Status | Purpose |
|--------|--------|---------|
| `query(title, year, artist, album)` | TODO | Dispatches to Query or Scan, returns list of songs |
| `getImageKey(artist, title)` | TODO | Looks up S3 key for an artist image from the music table |
| `generatePresignedUrl(s3Key)` | TODO | Converts an S3 object key into a 1-hour signed URL |
| `buildFilterParts(...)` | TODO | Builds DynamoDB `FilterExpression` parts for title/year/album |
| `toSongMap(item)` | TODO | Converts a raw DynamoDB item into a `Map<String, String>` |
| `getString(item, key)` | **Done** | Helper to safely read a String attribute from a DynamoDB item |

**Key design note:** `year` is a reserved word in DynamoDB and cannot be used directly in expressions. The `buildFilterParts` method must alias it as `#yr` in the expression attribute names map.

---

### `SubscriptionService.java`

**`getSubscriptions(email)`**
Runs a DynamoDB `Query` on the `subscriptions` table with `email` as the partition key. Returns all matching items mapped to `Map<String, String>`, with fresh pre-signed S3 URLs for images generated via `MusicService.generatePresignedUrl()`.

**`addSubscription(email, title, artist, year, album)`**
1. Builds `subscriptionId = artist + "#" + title` — this acts as the sort key and prevents the same song being subscribed twice (a second subscribe just overwrites with the same data).
2. Calls `MusicService.getImageKey(artist, title)` to look up the S3 image key from the music table.
3. Calls `dynamoDb.putItem()` to write the subscription record.

**`removeSubscription(email, subscriptionId)`**
Calls `dynamoDb.deleteItem()` with the `email` (PK) and `subscriptionId` (SK).

**Dependency:** `SubscriptionService` depends on `MusicService` to get the image key. Once `MusicService.getImageKey()` is implemented, image display in subscriptions will work automatically.

---

## `frontend/`

The frontend is **static HTML/CSS/JS** — no framework. It is designed to be hosted on **S3 static website hosting** (not on EC2/ECS). It communicates with whichever backend is active via `fetch()` calls.

---

### `frontend/js/config.js`
A single line file containing the backend base URL:

```js
const BACKEND_URL = 'http://localhost:8080';
```

**This is the only file you need to change when switching backends for the demo.** Comment/uncomment the relevant line:
```js
// const BACKEND_URL = 'http://<EC2_PUBLIC_IP>';
// const BACKEND_URL = 'http://<ALB_DNS_NAME>';
// const BACKEND_URL = 'https://<API_GW_ID>.execute-api.us-east-1.amazonaws.com/prod';
```

Both `login.html` and `register.html` load this file first with `<script src="js/config.js">`, so `BACKEND_URL` is available globally.

---

### `frontend/css/styles.css`
Shared stylesheet used by all pages. Spotify-inspired dark theme.

| CSS variable | Value | Used for |
|-------------|-------|---------|
| `--bg` | `#000000` | Page background |
| `--card-bg` | `#121212` | Form card background |
| `--green` | `#1DB954` | Primary button colour |
| `--green-hover` | `#1ed760` | Button hover state |
| `--error-red` | `#e91429` | Error message border/text |
| `--muted` | `#a7a7a7` | Footer text and placeholders |

Key classes:
- `.card` — centred white-on-dark form container, max-width 440px.
- `.btn-primary` — green pill-shaped button, full width.
- `.alert-error` — hidden by default, shown via `style.display = 'block'` in JS on failure.
- `.alert-success` — same but green, shown on successful register before redirect.

---

### `frontend/login.html`
The login page.

**HTML structure:** logo icon → "Welcome back" heading → hidden error div → form (email + password + button) → register link.

**JavaScript behaviour:**
1. On page load: if `sessionStorage` already has an `email` key, redirects straight to `main.html` (already logged in).
2. On form submit: POSTs `{ email, password }` to `BACKEND_URL/login`.
3. On success (`data.success === true`): saves `email` and `user_name` to `sessionStorage`, redirects to `main.html`.
4. On failure or network error: reveals the error div (`"email or password is invalid"`).

---

### `frontend/register.html`
The register page.

**HTML structure:** logo icon → "Sign up to start listening" heading → hidden error div → hidden success div → form (email + username + password + button) → login link.

**JavaScript behaviour:**
1. On form submit: POSTs `{ email, user_name, password }` to `BACKEND_URL/register`.
2. On success: shows the green success banner (`"Account created! Redirecting to login…"`), then redirects to `login.html` after 1.5 seconds.
3. On failure (HTTP 409): reveals the error div (`"The email already exists"`).

---

## `backend-ec2/`

---

### `backend-ec2/setup.sh`
A bash script run once on a fresh **Amazon Linux 2023 EC2 instance** to install and configure everything.

**What it does, step by step:**

1. **Installs Java 17** (`java-17-amazon-corretto`) and **Nginx** via `dnf`.
2. **Copies the JAR** from `target/backend-0.0.1-SNAPSHOT.jar` (built by Maven) to `/opt/backend.jar`.
3. **Configures Nginx** as a reverse proxy: writes a config file that forwards all traffic on port 80 to `localhost:8080` where Spring Boot is listening. This satisfies the assignment requirement that the app runs on port 80.
4. **Creates a systemd service** (`/etc/systemd/system/backend.service`) so Spring Boot starts automatically on boot and restarts on failure.

**Usage:**
```bash
# 1. Build the JAR on your local machine
./mvnw package -DskipTests

# 2. Copy the JAR to EC2 (via scp or S3), then on the EC2 instance:
sudo bash backend-ec2/setup.sh
```

The EC2 instance must have the **LabRole** attached as its IAM instance profile so the AWS SDK can authenticate.

---

## Files Not Covered Above

| File | Purpose |
|------|---------|
| `.gitignore` | Excludes `target/`, IDE files, and build outputs from git |
| `.gitattributes` | Normalises line endings across OS |
| `mvnw` / `mvnw.cmd` | Maven wrapper scripts — run `./mvnw` instead of requiring Maven installed |
| `HELP.md` | Auto-generated by Spring Initializr — not relevant to the project |
| `BackendApplicationTests.java` | Auto-generated test stub — no tests written yet |
| `backend-lambda/` | Empty subfolders for Lambda function handlers — not yet implemented |
| `init/` | Empty folder for DynamoDB/S3 initialisation scripts — not yet implemented |
| `report/` | Empty folder for the architecture diagram and written report |
