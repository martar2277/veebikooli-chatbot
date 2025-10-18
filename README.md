# Training Video Chatbot Demo

AI-powered chatbot that recommends personalized training video collections based on user profiles.

## Features

- 🤖 **AI-Powered Conversations**: Natural language interaction using Claude AI
- 👥 **5 Persona Types**: Automatic matching to user profiles
- 📚 **25 Training Videos**: Curated collections for each persona
- 💾 **MySQL Database**: Persistent storage of conversations and recommendations
- 🎨 **Modern UI**: Responsive chat interface
- 🐳 **Docker Ready**: One-command deployment

## Prerequisites

- GitHub Codespaces (or Docker + Docker Compose locally)
- Anthropic API Key (get one at https://console.anthropic.com/)

## Quick Start

### 1. Clone & Open in Codespaces
```bash
# Open this repository in GitHub Codespaces
# OR clone locally:
git clone <your-repo-url>
cd training-video-chatbot
```

### 2. Set Up Environment

Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Start the Application
```bash
docker-compose up --build
```

Wait for:
- ✓ MySQL to be ready
- ✓ Database schema created
- ✓ Dummy data seeded
- ✓ Flask app running

### 4. Access the Application

Open your browser to:
- **Codespaces**: Click "Open in Browser" when prompted
- **Local**: http://localhost:5000

## The 5 Personas

1. **New Manager Transitioning to Leadership**
   - First-time managers with <2 years experience
   - Collection: Essential Manager Foundations (5 videos)

2. **Senior Technical Specialist Upskilling**
   - Experienced engineers/developers (5+ years)
   - Collection: Advanced Technical Mastery (5 videos)

3. **Career Changer Entering Field**
   - Professionals transitioning careers
   - Collection: Career Transition Bootcamp (5 videos)

4. **HR Professional Developing Skills**
   - Human resources professionals
   - Collection: Modern HR Excellence (5 videos)

5. **Sales Leader Growing Team**
   - Sales professionals and managers
   - Collection: Sales Leadership Masterclass (5 videos)

## Testing the Demo

### Test Scenario 1: New Manager
```
User: "Hi, I just got promoted to team lead 3 months ago. I'm managing 5 people but struggling with delegation."
Expected: Match to Persona 001 - New Manager
```

### Test Scenario 2: Senior Engineer
```
User: "I'm a senior software engineer with 8 years experience. Looking to learn advanced system design patterns."
Expected: Match to Persona 002 - Senior Technical Specialist
```

### Test Scenario 3: Career Changer
```
User: "I'm switching careers from teaching to tech. Complete beginner, need to start from scratch."
Expected: Match to Persona 003 - Career Changer
```

## Project Structure
```
training-video-chatbot/
├── docker-compose.yml      # Docker orchestration
├── Dockerfile             # Python app container
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── init_db.py            # Database schema creation
├── seed_data.py          # Dummy data population
├── app.py                # Main Flask application
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── chat.js       # Frontend logic
└── templates/
    └── index.html        # Main page
```

## API Endpoints

- `GET /` - Main chat interface
- `POST /api/chat/start` - Initialize conversation
- `POST /api/chat/message` - Send user message
- `POST /api/chat/confirm` - Confirm enrollment
- `GET /api/health` - Health check

## Database Schema

### Main Tables
- `personas` - 5 persona definitions
- `videos` - 25 training videos
- `video_collections` - 5 curated collections
- `collection_videos` - Video-to-collection mappings
- `conversations` - Chat sessions
- `conversation_messages` - Message history
- `user_profiles` - Matched user profiles
- `user_enrollments` - Video enrollments

## Customization

### Add More Videos

Edit `seed_data.py` and add to the `VIDEOS` list:
```python
{'video_id': 'vid_026', 'title': 'Your New Video', 'duration': 30, ...}
```

### Modify Personas

Edit persona characteristics in `seed_data.py`:
```python
PERSONAS = [
    {
        'persona_id': 'persona_001',
        'name': 'Your Persona Name',
        'characteristics': {...},
        ...
    }
]
```

### Change AI Behavior

Modify system prompts in `app.py`:
- `AIService.extract_profile_info()` - Extraction logic
- `AIService.generate_next_question()` - Conversation flow
- `AIService.match_persona()` - Persona matching

## Troubleshooting

### Database Connection Issues
```bash
# Check MySQL is running
docker-compose ps

# View logs
docker-compose logs mysql

# Restart services
docker-compose restart
```

### AI Not Responding
```bash
# Check API key is set
echo $ANTHROPIC_API_KEY

# View app logs
docker-compose logs web
```

### Reset Everything
```bash
# Stop and remove all containers
docker-compose down -v

# Rebuild and restart
docker-compose up --build
```

## Production Considerations

This is a **demo application**. For production:

- [ ] Add authentication (OAuth, JWT)
- [ ] Implement rate limiting
- [ ] Add GDPR compliance (data retention, deletion)
- [ ] Use production database (managed MySQL/PostgreSQL)
- [ ] Add monitoring and logging
- [ ] Implement caching (Redis)
- [ ] Add automated testing
- [ ] Set up CI/CD pipeline
- [ ] Use environment-specific configurations
- [ ] Implement real email sending (not simulated)
- [ ] Add video progress tracking
- [ ] Integrate with real LearnDash API

## License

MIT License - feel free to use for learning and demos!

## Support

For issues or questions, open a GitHub issue.