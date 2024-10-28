# Setup Guide
### Prerequisites
You must have Docker installed on your machine!
> 💡 Without Docker, you cannot run this application. Download and install from Docker's official website.

### Installation Steps
**1. Start Quiz Service (Backend)**
Navigate to the quiz service directory:
```bash
cd quiz-service
```
Create and configure environment variables:
```bash
cp .env.example .env
vi .env  # or use any text editor
```
Start the service:
```bash
docker compose up --build
```
Wait until you see:
```
quiz-service-1  | INFO:     Application startup complete.
```

**2. Start Quiz Client (Frontend)**
Open a new terminal, navigate to the quiz client directory:
```bash
cd quiz-client
docker compose up --build
```
Wait until you see:
```
quiz_client  | webpack compiled with 1 warning
quiz_client  | No issues found.
```

### Getting Started Application Setup Steps
**1. Create a Question**
```
curl --location 'http://localhost:8000/api/v1/quizzes/' \
--header 'Content-Type: application/json' \
--data '{
    "title": "Python Basics",
    "description": "Test your Python knowledge",
    "questions": [
        {
            "id": "q1",
            "text": "What is Python?",
            "type": "multiple_choice",
            "options": [
                "Language",
                "Framework",
                "Library",
                "OS"
            ],
            "correct_answer": "Language",
            "points": 10
        }
    ]
}'
```

**2. Create a Session**
```
curl --location --request POST 'http://localhost:8000/api/v1/quizzes/sessions?quiz_id=671cab20f2df1be155e00062'
```

**3. Update Session ID in Client Code**
After creating a session and receiving the sessionId, you need to:
- Open the file: quiz-client/src/App.tsx
- Locate the sessionId variable
- Replace the existing value with your new sessionId

**4. Access the Application**
Open your browser and navigate to:
```http://localhost:3000/```

Now - Have Fun! 😊

### Troubleshooting
If containers don't start properly, try:
```bash
docker compose down
docker compose up --build
```

Ensure all required ports are available on your machine

Check Docker logs if any issues occur

Additional Notes
```
Backend runs on: <port number>
Frontend runs on: <port number>
```
Make sure all services are running before using the application
