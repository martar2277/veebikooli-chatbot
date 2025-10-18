#!/usr/bin/env python3
"""
Training Video Chatbot Demo Application
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from openai import OpenAI
from sqlalchemy import create_engine, text
import json
import uuid
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'demo-secret-key')
CORS(app)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not set!")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
db_engine = create_engine(DATABASE_URL, pool_pre_ping=True)


# ============================================
# CONVERSATION MANAGER
# ============================================

class ConversationManager:
    """Manages conversation state and database operations"""
    
    def __init__(self):
        self.required_fields = [
            'role',
            'experience_months',
            'primary_challenges',
            'learning_goals'
        ]
    
    def create_conversation(self, user_id=None):
        """Initialize a new conversation"""
        conversation_id = str(uuid.uuid4())
        
        initial_state = {
            "conversation_id": conversation_id,
            "user_id": user_id or f"anon_{uuid.uuid4().hex[:8]}",
            "started_at": datetime.now().isoformat(),
            "profile": {
                "role": None,
                "experience_months": None,
                "team_size": None,
                "industry": None,
                "primary_challenges": [],
                "learning_goals": [],
                "time_available_hours_per_week": None,
                "emotional_state": None,
                "urgency": None
            },
            "collected_fields": [],
            "missing_fields": self.required_fields.copy(),
            "messages": [],
            "exchange_count": 0,
            "completion_percentage": 0,
            "status": "active"
        }
        
        with db_engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO conversations 
                (conversation_id, user_id, status, state_json, exchange_count, completion_percentage)
                VALUES (:conversation_id, :user_id, :status, :state_json, :exchange_count, :completion_percentage)
            """), {
                'conversation_id': conversation_id,
                'user_id': initial_state["user_id"],
                'status': 'active',
                'state_json': json.dumps(initial_state),
                'exchange_count': 0,
                'completion_percentage': 0
            })
            conn.commit()
        
        return initial_state
    
    def load_conversation(self, conversation_id):
        """Load conversation state from database"""
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT state_json 
                FROM conversations 
                WHERE conversation_id = :conversation_id
            """), {'conversation_id': conversation_id})
            
            row = result.fetchone()
            if row:
                return json.loads(row[0])
        return None
    
    def save_conversation(self, conversation_state):
        """Save conversation state to database"""
        with db_engine.connect() as conn:
            conn.execute(text("""
                UPDATE conversations 
                SET state_json = :state_json,
                    last_activity_at = CURRENT_TIMESTAMP,
                    exchange_count = :exchange_count,
                    completion_percentage = :completion_percentage,
                    status = :status,
                    matched_persona_id = :matched_persona_id,
                    recommended_collection_id = :recommended_collection_id,
                    confidence_score = :confidence_score
                WHERE conversation_id = :conversation_id
            """), {
                'state_json': json.dumps(conversation_state),
                'exchange_count': conversation_state['exchange_count'],
                'completion_percentage': conversation_state['completion_percentage'],
                'status': conversation_state['status'],
                'matched_persona_id': conversation_state.get('matched_persona_id'),
                'recommended_collection_id': conversation_state.get('recommended_collection_id'),
                'confidence_score': conversation_state.get('confidence_score'),
                'conversation_id': conversation_state['conversation_id']
            })
            conn.commit()
    
    def save_message(self, conversation_id, speaker, content, extracted_data=None):
        """Save individual message to database"""
        with db_engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO conversation_messages 
                (conversation_id, speaker, message_content, extracted_data)
                VALUES (:conversation_id, :speaker, :message_content, :extracted_data)
            """), {
                'conversation_id': conversation_id,
                'speaker': speaker,
                'message_content': content,
                'extracted_data': json.dumps(extracted_data) if extracted_data else None
            })
            conn.commit()
    
    def update_completion_status(self, conversation_state):
        """Calculate what fields are collected vs missing"""
        profile = conversation_state['profile']
        collected = []
        missing = []
        
        for field in self.required_fields:
            value = profile.get(field)
            
            if value is not None and value != [] and value != "":
                collected.append(field)
            else:
                missing.append(field)
        
        conversation_state['collected_fields'] = collected
        conversation_state['missing_fields'] = missing
        conversation_state['completion_percentage'] = int(
            (len(collected) / len(self.required_fields)) * 100
        )
        
        return conversation_state


# ============================================
# AI SERVICE
# ============================================

class AIService:
    """Handles all AI-related operations"""

    def __init__(self, client):
        self.client = client
        self.model = "gpt-4o"
    
    def extract_profile_info(self, user_message, current_profile):
        """Extract structured profile information from user's message"""
        
        if not self.client:
            return {}
        
        system_prompt = """You are a data extraction assistant. Extract relevant profile information from the user's message.

Return ONLY information that is clearly stated or strongly implied. If information is ambiguous or not present, return null for that field.

Return in this exact JSON format:
{
    "role": "manager" or "engineer" or "specialist" or other role (or null),
    "experience_months": number or null,
    "team_size": number or null,
    "industry": "tech" or "healthcare" or other industry (or null),
    "primary_challenges": [list of specific challenges mentioned],
    "learning_goals": [list of specific goals mentioned],
    "time_available_hours_per_week": number or null,
    "emotional_state": "stressed" or "confident" or "overwhelmed" or other emotion (or null),
    "urgency": "high" or "medium" or "low" (or null)
}

Be conservative - only extract what you're confident about."""

        user_prompt = f"""Current profile state:
{json.dumps(current_profile, indent=2)}

User's message:
"{user_message}"

Extract any new or updated information from this message."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            extracted_text = response.choices[0].message.content

            if "```json" in extracted_text:
                extracted_text = extracted_text.split("```json")[1].split("```")[0].strip()
            elif "```" in extracted_text:
                extracted_text = extracted_text.split("```")[1].split("```")[0].strip()

            extracted_data = json.loads(extracted_text)
            return extracted_data

        except Exception as e:
            print(f"Error in extraction: {e}")
            return {}
    
    def generate_next_question(self, conversation_state):
        """Generate natural next question based on conversation state"""
        
        if not self.client:
            return "Could you tell me more about your background and what you're looking for?"
        
        profile = conversation_state['profile']
        missing = conversation_state['missing_fields']
        messages = conversation_state['messages']
        exchange_count = conversation_state['exchange_count']
        
        message_history = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages[-6:]
        ])
        
        profile_summary = "\n".join([
            f"- {key}: {value}"
            for key, value in profile.items()
            if value is not None and value != [] and value != ""
        ])
        
        missing_fields_text = ", ".join(missing) if missing else "None - all information collected!"
        
        system_prompt = f"""You are Videa, a warm and empathetic training advisor for a professional training company.

CONVERSATION CONTEXT:
{message_history}

PROFILE INFORMATION COLLECTED SO FAR:
{profile_summary if profile_summary else "(Nothing collected yet)"}

STILL NEED TO LEARN ABOUT:
{missing_fields_text}

CONVERSATION RULES:
1. Be warm, empathetic, and conversational
2. Ask ONE question at a time
3. Don't ask about information you already know
4. Match the emotional tone of the user
5. If user seems stressed, acknowledge it before asking
6. Keep questions brief and natural
7. After {exchange_count} exchanges, we need to wrap up soon

YOUR TASK:
Generate your next message to the user. Either:
- Ask about the next missing field naturally, OR
- If exchange count > 8, gently suggest moving to recommendations

Keep it conversational and human."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=300,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate your next message to the user."}
                ]
            )

            bot_message = response.choices[0].message.content.strip()
            return bot_message

        except Exception as e:
            print(f"Error generating question: {e}")
            return "Could you tell me a bit more about what you're looking for?"
    
    def match_persona(self, profile, personas_data):
        """Match profile to best persona using AI"""
        
        if not self.client:
            # Fallback: simple keyword matching
            return self._simple_persona_match(profile, personas_data)
        
        system_prompt = """You are an expert at matching user profiles to learning personas.

Given a user profile and available personas, determine the best match and explain why.

Return in this JSON format:
{
    "matched_persona_id": "persona_001",
    "confidence_score": 85,
    "reasoning": "Brief explanation of why this persona matches"
}"""

        personas_summary = "\n\n".join([
            f"Persona ID: {p['persona_id']}\nName: {p['name']}\nDescription: {p['description']}"
            for p in personas_data
        ])

        user_prompt = f"""User Profile:
{json.dumps(profile, indent=2)}

Available Personas:
{personas_summary}

Determine the best matching persona."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            result_text = response.choices[0].message.content
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()

            match_result = json.loads(result_text)
            return match_result

        except Exception as e:
            print(f"Error in persona matching: {e}")
            return self._simple_persona_match(profile, personas_data)
    
    def _simple_persona_match(self, profile, personas_data):
        """Simple fallback persona matching based on keywords"""
        role = profile.get('role', '').lower() if profile.get('role') else ''
        experience = profile.get('experience_months', 0) or 0
        
        # Simple matching logic
        if 'manager' in role or 'team lead' in role or 'supervisor' in role:
            if experience < 24:
                return {
                    'matched_persona_id': 'persona_001',
                    'confidence_score': 75,
                    'reasoning': 'New manager with limited experience'
                }
        
        if 'engineer' in role or 'developer' in role or 'technical' in role:
            if experience >= 60:
                return {
                    'matched_persona_id': 'persona_002',
                    'confidence_score': 80,
                    'reasoning': 'Senior technical professional'
                }
        
        if 'hr' in role or 'human resources' in role or 'recruiter' in role:
            return {
                'matched_persona_id': 'persona_004',
                'confidence_score': 85,
                'reasoning': 'HR professional'
            }
        
        if 'sales' in role or 'account' in role or 'business development' in role:
            return {
                'matched_persona_id': 'persona_005',
                'confidence_score': 80,
                'reasoning': 'Sales professional'
            }
        
        # Default to career changer for beginners
        if experience < 12:
            return {
                'matched_persona_id': 'persona_003',
                'confidence_score': 70,
                'reasoning': 'Limited experience in field'
            }
        
        # Default fallback
        return {
            'matched_persona_id': 'persona_001',
            'confidence_score': 60,
            'reasoning': 'General professional development'
        }


# ============================================
# DATABASE SERVICES
# ============================================

class PersonaService:
    @staticmethod
    def get_all_personas():
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT persona_id, name, description, characteristics, diagnostic_rules
                FROM personas
                ORDER BY persona_id
            """))
            
            personas = []
            for row in result:
                personas.append({
                    'persona_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'characteristics': json.loads(row[3]) if row[3] else {},
                    'diagnostic_rules': json.loads(row[4]) if row[4] else {}
                })
            return personas
    
    @staticmethod
    def get_persona_by_id(persona_id):
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM personas WHERE persona_id = :persona_id
            """), {'persona_id': persona_id})
            
            row = result.fetchone()
            if row:
                return {
                    'persona_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'characteristics': json.loads(row[3]) if row[3] else {},
                    'diagnostic_rules': json.loads(row[4]) if row[4] else {}
                }
        return None


class CollectionService:
    @staticmethod
    def get_collection_by_persona(persona_id):
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM video_collections 
                WHERE target_persona_id = :persona_id AND is_active = TRUE
                LIMIT 1
            """), {'persona_id': persona_id})
            
            row = result.fetchone()
            if row:
                return {
                    'collection_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'target_persona_id': row[3],
                    'total_videos': row[4],
                    'estimated_duration_minutes': row[5],
                    'learning_path_type': row[6]
                }
        return None
    
    @staticmethod
    def get_collection_videos(collection_id):
        with db_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    cv.sequence_position,
                    cv.is_required,
                    v.video_id,
                    v.title,
                    v.description,
                    v.youtube_url,
                    v.duration_minutes,
                    v.difficulty,
                    v.topic
                FROM collection_videos cv
                JOIN videos v ON cv.video_id = v.video_id
                WHERE cv.collection_id = :collection_id
                ORDER BY cv.sequence_position
            """), {'collection_id': collection_id})
            
            videos = []
            for row in result:
                videos.append({
                    'sequence_position': row[0],
                    'is_required': row[1],
                    'video_id': row[2],
                    'title': row[3],
                    'description': row[4],
                    'youtube_url': row[5],
                    'duration_minutes': row[6],
                    'difficulty': row[7],
                    'topic': row[8]
                })
            return videos


# Initialize services
conversation_manager = ConversationManager()
ai_service = AIService(openai_client)


# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Main page with chat interface"""
    return render_template('index.html')


@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    """Initialize a new conversation"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    conversation_state = conversation_manager.create_conversation(user_id)
    
    initial_message = {
        "role": "assistant",
        "content": "Hi! I'm Videa, your personal training advisor. I'm here to help you find the perfect learning path for your professional development. Tell me, what brings you here today? What are you hoping to learn or improve?"
    }
    
    conversation_state['messages'].append(initial_message)
    conversation_manager.save_conversation(conversation_state)
    conversation_manager.save_message(
        conversation_state['conversation_id'],
        'assistant',
        initial_message['content']
    )
    
    return jsonify({
        "conversation_id": conversation_state['conversation_id'],
        "message": initial_message['content']
    })


@app.route('/api/chat/message', methods=['POST'])
def handle_message():
    """Process user message and generate response"""
    data = request.json
    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    
    if not conversation_id or not user_message:
        return jsonify({"error": "Missing conversation_id or message"}), 400
    
    conversation_state = conversation_manager.load_conversation(conversation_id)
    if not conversation_state:
        return jsonify({"error": "Conversation not found"}), 404
    
    # Add user message
    conversation_state['messages'].append({
        "role": "user",
        "content": user_message
    })
    conversation_state['exchange_count'] += 1
    
    conversation_manager.save_message(conversation_id, 'user', user_message)
    
    # Extract information
    extracted_data = ai_service.extract_profile_info(
        user_message,
        conversation_state['profile']
    )
    
    # Update profile
    for key, value in extracted_data.items():
        if value is not None:
            if isinstance(value, list) and isinstance(conversation_state['profile'].get(key), list):
                existing = conversation_state['profile'][key]
                conversation_state['profile'][key] = list(set(existing + value))
            else:
                conversation_state['profile'][key] = value
    
    # Update completion status
    conversation_state = conversation_manager.update_completion_status(conversation_state)
    
    # Determine next action
    should_recommend = (
        conversation_state['completion_percentage'] >= 60 or
        conversation_state['exchange_count'] >= 10
    )
    
    if should_recommend:
        # Generate recommendation
        personas = PersonaService.get_all_personas()
        match_result = ai_service.match_persona(
            conversation_state['profile'],
            personas
        )
        
        if match_result:
            persona_id = match_result['matched_persona_id']
            confidence_score = match_result['confidence_score']
            
            persona = PersonaService.get_persona_by_id(persona_id)
            collection = CollectionService.get_collection_by_persona(persona_id)
            
            if collection:
                videos = CollectionService.get_collection_videos(collection['collection_id'])
                
                # Format video list
                video_list = "\n".join([
                    f"  {i+1}. {v['title']} ({v['duration_minutes']} min)"
                    for i, v in enumerate(videos)
                ])
                
                bot_message = f"""Based on everything you've shared, I believe you match the **{persona['name']}** profile.

{match_result['reasoning']}

I recommend our **{collection['name']}** learning path:

📚 {collection['total_videos']} videos • {collection['estimated_duration_minutes']} minutes total

{video_list}

This collection is designed to {collection['description'].lower()}.

Would you like to enroll in this learning path?"""
                
                conversation_state['status'] = 'recommendation_made'
                conversation_state['matched_persona_id'] = persona_id
                conversation_state['recommended_collection_id'] = collection['collection_id']
                conversation_state['confidence_score'] = confidence_score
            else:
                bot_message = "I have a good sense of what you need, but I'm having trouble finding the perfect collection. Let me connect you with a human advisor who can help."
        else:
            bot_message = "Based on what you've told me, let me connect you with a human advisor who can provide personalized recommendations."
    else:
        # Continue conversation
        bot_message = ai_service.generate_next_question(conversation_state)
    
    # Add bot response
    conversation_state['messages'].append({
        "role": "assistant",
        "content": bot_message
    })
    
    # Save everything
    conversation_manager.save_conversation(conversation_state)
    conversation_manager.save_message(
        conversation_id,
        'assistant',
        bot_message,
        extracted_data
    )
    
    return jsonify({
        "message": bot_message,
        "completion_percentage": conversation_state['completion_percentage'],
        "status": conversation_state.get('status', 'active'),
        "exchange_count": conversation_state['exchange_count']
    })


@app.route('/api/chat/confirm', methods=['POST'])
def confirm_recommendation():
    """User confirms the recommendation"""
    data = request.json
    conversation_id = data.get('conversation_id')
    confirmed = data.get('confirmed', False)
    
    if not conversation_id:
        return jsonify({"error": "Missing conversation_id"}), 400
    
    conversation_state = conversation_manager.load_conversation(conversation_id)
    if not conversation_state:
        return jsonify({"error": "Conversation not found"}), 404
    
    if confirmed and conversation_state.get('recommended_collection_id'):
        # Create user profile record
        profile = conversation_state['profile']
        
        with db_engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO user_profiles 
                (user_id, conversation_id, role, experience_months, team_size, industry,
                 primary_challenges, learning_goals, time_available_hours_per_week,
                 emotional_state, urgency, matched_persona_id, assigned_collection_id,
                 confidence_score)
                VALUES (:user_id, :conversation_id, :role, :experience_months, :team_size, :industry,
                        :primary_challenges, :learning_goals, :time_available_hours_per_week,
                        :emotional_state, :urgency, :matched_persona_id, :assigned_collection_id,
                        :confidence_score)
            """), {
                'user_id': conversation_state['user_id'],
                'conversation_id': conversation_id,
                'role': profile.get('role'),
                'experience_months': profile.get('experience_months'),
                'team_size': profile.get('team_size'),
                'industry': profile.get('industry'),
                'primary_challenges': json.dumps(profile.get('primary_challenges', [])),
                'learning_goals': json.dumps(profile.get('learning_goals', [])),
                'time_available_hours_per_week': profile.get('time_available_hours_per_week'),
                'emotional_state': profile.get('emotional_state'),
                'urgency': profile.get('urgency'),
                'matched_persona_id': conversation_state['matched_persona_id'],
                'assigned_collection_id': conversation_state['recommended_collection_id'],
                'confidence_score': conversation_state.get('confidence_score')
            })
            
            # Get videos in the collection
            collection_id = conversation_state['recommended_collection_id']
            result = conn.execute(text("""
                SELECT video_id FROM collection_videos 
                WHERE collection_id = :collection_id
                ORDER BY sequence_position
            """), {'collection_id': collection_id})
            
            # Enroll user in each video
            for row in result:
                conn.execute(text("""
                    INSERT INTO user_enrollments 
                    (user_id, video_id, collection_id, status)
                    VALUES (:user_id, :video_id, :collection_id, 'enrolled')
                """), {
                    'user_id': conversation_state['user_id'],
                    'video_id': row[0],
                    'collection_id': collection_id
                })
            
            conn.commit()
        
        # Update conversation status
        conversation_state['status'] = 'completed'
        conversation_manager.save_conversation(conversation_state)
        
        return jsonify({
            "success": True,
            "message": "🎉 Perfect! You're all enrolled.\n\n📧 Check your email for access details and next steps. We've sent you:\n\n✓ Login credentials for your personalized learning portal\n✓ Links to all your videos\n✓ A getting started guide\n\nWelcome aboard, and happy learning!"
        })
    else:
        return jsonify({
            "success": False,
            "message": "No problem! Would you like to tell me more about what you're looking for, or would you prefer to speak with a human advisor?"
        })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "database": "connected",
        "ai_service": "available" if openai_client else "unavailable"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)