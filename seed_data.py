#!/usr/bin/env python3
"""
Seed the database with dummy personas, videos, and collections
"""

from sqlalchemy import create_engine, text
import json
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://demo_user:demo_password@mysql:3306/training_videos')

# Define 5 personas
PERSONAS = [
    {
        'persona_id': 'persona_001',
        'name': 'New Manager Transitioning to Leadership',
        'description': 'Individual contributors recently promoted to management roles',
        'characteristics': {
            'role': ['manager', 'team_lead', 'supervisor'],
            'experience_months': {'min': 0, 'max': 24},
            'team_size': {'min': 2, 'max': 15},
            'pain_points': ['delegation', 'difficult_conversations', 'time_management', 'confidence', 'team_conflict'],
            'learning_goals': ['leadership_basics', 'people_management', 'assertiveness']
        },
        'diagnostic_rules': {
            'keywords': ['manager', 'team lead', 'promoted', 'first time', 'new role'],
            'experience_indicators': ['months', 'new', 'recently', 'just started'],
            'scoring_weights': {
                'role_match': 30,
                'experience_match': 25,
                'pain_point_match': 15,
                'team_size_match': 10
            }
        }
    },
    {
        'persona_id': 'persona_002',
        'name': 'Senior Technical Specialist Upskilling',
        'description': 'Experienced professionals deepening expertise in specific technical areas',
        'characteristics': {
            'role': ['engineer', 'developer', 'architect', 'specialist', 'technical lead'],
            'experience_months': {'min': 60, 'max': 999},
            'skill_level': 'intermediate_to_advanced',
            'pain_points': ['staying_current', 'advanced_techniques', 'limited_time', 'technical_depth'],
            'learning_goals': ['master_advanced_topics', 'industry_trends', 'specialization']
        },
        'diagnostic_rules': {
            'keywords': ['senior', 'engineer', 'developer', 'technical', 'expert', 'advanced'],
            'experience_indicators': ['years', 'experienced', 'senior', 'lead'],
            'scoring_weights': {
                'role_match': 30,
                'experience_match': 30,
                'skill_level_match': 20
            }
        }
    },
    {
        'persona_id': 'persona_003',
        'name': 'Career Changer Entering Field',
        'description': 'Professionals transitioning from different industry or role',
        'characteristics': {
            'role': ['career_changer', 'beginner', 'student', 'entry_level'],
            'experience_months': {'min': 0, 'max': 6},
            'skill_level': 'beginner',
            'pain_points': ['dont_know_where_to_start', 'overwhelmed', 'need_structure', 'career_transition'],
            'learning_goals': ['foundational_knowledge', 'industry_basics', 'job_ready_skills']
        },
        'diagnostic_rules': {
            'keywords': ['career change', 'new to', 'beginner', 'starting out', 'transition', 'switch'],
            'experience_indicators': ['no experience', 'new', 'beginner', 'first time'],
            'scoring_weights': {
                'role_match': 25,
                'experience_match': 30,
                'pain_point_match': 20
            }
        }
    },
    {
        'persona_id': 'persona_004',
        'name': 'HR Professional Developing Skills',
        'description': 'Human resources professionals looking to enhance their capabilities',
        'characteristics': {
            'role': ['hr', 'human_resources', 'recruiter', 'talent', 'people_operations'],
            'experience_months': {'min': 12, 'max': 120},
            'pain_points': ['employee_engagement', 'conflict_resolution', 'performance_management', 'compliance'],
            'learning_goals': ['modern_hr_practices', 'employee_development', 'strategic_hr']
        },
        'diagnostic_rules': {
            'keywords': ['hr', 'human resources', 'recruiting', 'talent', 'people', 'hiring'],
            'experience_indicators': ['year', 'years'],
            'scoring_weights': {
                'role_match': 35,
                'experience_match': 20,
                'pain_point_match': 20
            }
        }
    },
    {
        'persona_id': 'persona_005',
        'name': 'Sales Leader Growing Team',
        'description': 'Sales professionals and leaders looking to improve team performance',
        'characteristics': {
            'role': ['sales', 'sales_manager', 'account_executive', 'business_development'],
            'experience_months': {'min': 24, 'max': 999},
            'team_size': {'min': 3, 'max': 50},
            'pain_points': ['team_performance', 'closing_deals', 'pipeline_management', 'coaching_sales_team'],
            'learning_goals': ['sales_leadership', 'advanced_techniques', 'team_development']
        },
        'diagnostic_rules': {
            'keywords': ['sales', 'account', 'business development', 'revenue', 'deals', 'pipeline'],
            'experience_indicators': ['years', 'experienced'],
            'scoring_weights': {
                'role_match': 35,
                'experience_match': 20,
                'team_size_match': 15
            }
        }
    }
]

# Define dummy videos (5 per persona = 25 total)
VIDEOS = [
    # Persona 001 - New Manager
    {'video_id': 'vid_001', 'title': 'Your First 90 Days as a Manager', 'duration': 25, 'difficulty': 'beginner', 'topic': 'leadership_transition', 'feature_1': 'beginner', 'feature_2': 'short', 'feature_3': 'soft_skills'},
    {'video_id': 'vid_002', 'title': 'Delegation Framework: When and How', 'duration': 35, 'difficulty': 'beginner', 'topic': 'delegation', 'feature_1': 'beginner', 'feature_2': 'medium', 'feature_3': 'soft_skills'},
    {'video_id': 'vid_003', 'title': 'One-on-One Meetings that Matter', 'duration': 30, 'difficulty': 'beginner', 'topic': 'communication', 'feature_1': 'beginner', 'feature_2': 'medium', 'feature_3': 'soft_skills'},
    {'video_id': 'vid_004', 'title': 'Giving Constructive Feedback', 'duration': 40, 'difficulty': 'intermediate', 'topic': 'feedback', 'feature_1': 'intermediate', 'feature_2': 'medium', 'feature_3': 'soft_skills'},
    {'video_id': 'vid_005', 'title': 'Building Team Trust and Psychological Safety', 'duration': 32, 'difficulty': 'intermediate', 'topic': 'team_building', 'feature_1': 'intermediate', 'feature_2': 'medium', 'feature_3': 'soft_skills'},
    
    # Persona 002 - Senior Technical Specialist
    {'video_id': 'vid_006', 'title': 'Advanced System Design Patterns', 'duration': 50, 'difficulty': 'advanced', 'topic': 'architecture', 'feature_1': 'advanced', 'feature_2': 'long', 'feature_3': 'technical'},
    {'video_id': 'vid_007', 'title': 'Microservices Architecture Deep Dive', 'duration': 55, 'difficulty': 'advanced', 'topic': 'microservices', 'feature_1': 'advanced', 'feature_2': 'long', 'feature_3': 'technical'},
    {'video_id': 'vid_008', 'title': 'Performance Optimization at Scale', 'duration': 45, 'difficulty': 'advanced', 'topic': 'performance', 'feature_1': 'advanced', 'feature_2': 'medium', 'feature_3': 'technical'},
    {'video_id': 'vid_009', 'title': 'Advanced Database Optimization Techniques', 'duration': 48, 'difficulty': 'advanced', 'topic': 'database', 'feature_1': 'advanced', 'feature_2': 'medium', 'feature_3': 'technical'},
    {'video_id': 'vid_010', 'title': 'Cloud-Native Application Design', 'duration': 42, 'difficulty': 'advanced', 'topic': 'cloud', 'feature_1': 'advanced', 'feature_2': 'medium', 'feature_3': 'technical'},
    
    # Persona 003 - Career Changer
    {'video_id': 'vid_011', 'title': 'Industry Fundamentals: Getting Started', 'duration': 28, 'difficulty': 'beginner', 'topic': 'foundations', 'feature_1': 'beginner', 'feature_2': 'short', 'feature_3': 'foundational'},
    {'video_id': 'vid_012', 'title': 'Essential Skills for Career Transition', 'duration': 35, 'difficulty': 'beginner', 'topic': 'career_change', 'feature_1': 'beginner', 'feature_2': 'medium', 'feature_3': 'foundational'},
    {'video_id': 'vid_013', 'title': 'Building Your Professional Portfolio', 'duration': 30, 'difficulty': 'beginner', 'topic': 'portfolio', 'feature_1': 'beginner', 'feature_2': 'medium', 'feature_3': 'foundational'},
    {'video_id': 'vid_014', 'title': 'Networking and Job Search Strategies', 'duration': 33, 'difficulty': 'beginner', 'topic': 'job_search', 'feature_1': 'beginner', 'feature_2': 'medium', 'feature_3': 'foundational'},
    {'video_id': 'vid_015', 'title': 'Interview Preparation and Best Practices', 'duration': 38, 'difficulty': 'beginner', 'topic': 'interviews', 'feature_1': 'beginner', 'feature_2': 'medium', 'feature_3': 'foundational'},
    
    # Persona 004 - HR Professional
    {'video_id': 'vid_016', 'title': 'Modern Performance Management Systems', 'duration': 40, 'difficulty': 'intermediate', 'topic': 'performance', 'feature_1': 'intermediate', 'feature_2': 'medium', 'feature_3': 'strategic'},
    {'video_id': 'vid_017', 'title': 'Employee Engagement Strategies', 'duration': 36, 'difficulty': 'intermediate', 'topic': 'engagement', 'feature_1': 'intermediate', 'feature_2': 'medium', 'feature_3': 'strategic'},
    {'video_id': 'vid_018', 'title': 'Conflict Resolution and Mediation', 'duration': 42, 'difficulty': 'intermediate', 'topic': 'conflict', 'feature_1': 'intermediate', 'feature_2': 'medium', 'feature_3': 'soft_skills'},
    {'video_id': 'vid_019', 'title': 'Diversity, Equity, and Inclusion Practices', 'duration': 45, 'difficulty': 'intermediate', 'topic': 'dei', 'feature_1': 'intermediate', 'feature_2': 'medium', 'feature_3': 'strategic'},
    {'video_id': 'vid_020', 'title': 'Strategic HR and Business Partnership', 'duration': 38, 'difficulty': 'advanced', 'topic': 'strategic_hr', 'feature_1': 'advanced', 'feature_2': 'medium', 'feature_3': 'strategic'},
    
    # Persona 005 - Sales Leader
    {'video_id': 'vid_021', 'title': 'Advanced Sales Negotiation Techniques', 'duration': 44, 'difficulty': 'advanced', 'topic': 'negotiation', 'feature_1': 'advanced', 'feature_2': 'medium', 'feature_3': 'strategic'},
    {'video_id': 'vid_022', 'title': 'Building High-Performance Sales Teams', 'duration': 40, 'difficulty': 'advanced', 'topic': 'team_building', 'feature_1': 'advanced', 'feature_2': 'medium', 'feature_3': 'strategic'},
    {'video_id': 'vid_023', 'title': 'Sales Pipeline Management and Forecasting', 'duration': 38, 'difficulty': 'intermediate', 'topic': 'pipeline', 'feature_1': 'intermediate', 'feature_2': 'medium', 'feature_3': 'strategic'},
    {'video_id': 'vid_024', 'title': 'Coaching Sales Representatives for Success', 'duration': 42, 'difficulty': 'advanced', 'topic': 'coaching', 'feature_1': 'advanced', 'feature_2': 'medium', 'feature_3': 'soft_skills'},
    {'video_id': 'vid_025', 'title': 'Strategic Account Management', 'duration': 46, 'difficulty': 'advanced', 'topic': 'account_management', 'feature_1': 'advanced', 'feature_2': 'medium', 'feature_3': 'strategic'},
]

# Define collections (one per persona)
COLLECTIONS = [
    {'collection_id': 'collection_001', 'name': 'Essential Manager Foundations', 'target_persona_id': 'persona_001', 'description': 'Core skills for new managers in their first year', 'learning_path_type': 'linear'},
    {'collection_id': 'collection_002', 'name': 'Advanced Technical Mastery', 'target_persona_id': 'persona_002', 'description': 'Deep technical skills for senior engineers and architects', 'learning_path_type': 'modular'},
    {'collection_id': 'collection_003', 'name': 'Career Transition Bootcamp', 'target_persona_id': 'persona_003', 'description': 'Complete guide for professionals entering a new field', 'learning_path_type': 'linear'},
    {'collection_id': 'collection_004', 'name': 'Modern HR Excellence', 'target_persona_id': 'persona_004', 'description': 'Contemporary HR practices and strategic people management', 'learning_path_type': 'modular'},
    {'collection_id': 'collection_005', 'name': 'Sales Leadership Masterclass', 'target_persona_id': 'persona_005', 'description': 'Advanced techniques for sales leaders and managers', 'learning_path_type': 'modular'},
]

# Map videos to collections (5 videos per collection)
COLLECTION_VIDEOS = [
    # Collection 001
    {'collection_id': 'collection_001', 'video_id': 'vid_001', 'sequence_position': 1},
    {'collection_id': 'collection_001', 'video_id': 'vid_002', 'sequence_position': 2},
    {'collection_id': 'collection_001', 'video_id': 'vid_003', 'sequence_position': 3},
    {'collection_id': 'collection_001', 'video_id': 'vid_004', 'sequence_position': 4},
    {'collection_id': 'collection_001', 'video_id': 'vid_005', 'sequence_position': 5},
    
    # Collection 002
    {'collection_id': 'collection_002', 'video_id': 'vid_006', 'sequence_position': 1},
    {'collection_id': 'collection_002', 'video_id': 'vid_007', 'sequence_position': 2},
    {'collection_id': 'collection_002', 'video_id': 'vid_008', 'sequence_position': 3},
    {'collection_id': 'collection_002', 'video_id': 'vid_009', 'sequence_position': 4},
    {'collection_id': 'collection_002', 'video_id': 'vid_010', 'sequence_position': 5},
    
    # Collection 003
    {'collection_id': 'collection_003', 'video_id': 'vid_011', 'sequence_position': 1},
    {'collection_id': 'collection_003', 'video_id': 'vid_012', 'sequence_position': 2},
    {'collection_id': 'collection_003', 'video_id': 'vid_013', 'sequence_position': 3},
    {'collection_id': 'collection_003', 'video_id': 'vid_014', 'sequence_position': 4},
    {'collection_id': 'collection_003', 'video_id': 'vid_015', 'sequence_position': 5},
    
    # Collection 004
    {'collection_id': 'collection_004', 'video_id': 'vid_016', 'sequence_position': 1},
    {'collection_id': 'collection_004', 'video_id': 'vid_017', 'sequence_position': 2},
    {'collection_id': 'collection_004', 'video_id': 'vid_018', 'sequence_position': 3},
    {'collection_id': 'collection_004', 'video_id': 'vid_019', 'sequence_position': 4},
    {'collection_id': 'collection_004', 'video_id': 'vid_020', 'sequence_position': 5},
    
    # Collection 005
    {'collection_id': 'collection_005', 'video_id': 'vid_021', 'sequence_position': 1},
    {'collection_id': 'collection_005', 'video_id': 'vid_022', 'sequence_position': 2},
    {'collection_id': 'collection_005', 'video_id': 'vid_023', 'sequence_position': 3},
    {'collection_id': 'collection_005', 'video_id': 'vid_024', 'sequence_position': 4},
    {'collection_id': 'collection_005', 'video_id': 'vid_025', 'sequence_position': 5},
]

def seed_database():
    """Populate database with demo data"""
    print("Seeding database with demo data...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Insert personas
        print("Inserting personas...")
        for persona in PERSONAS:
            conn.execute(text("""
                INSERT INTO personas (persona_id, name, description, characteristics, diagnostic_rules)
                VALUES (:persona_id, :name, :description, :characteristics, :diagnostic_rules)
            """), {
                'persona_id': persona['persona_id'],
                'name': persona['name'],
                'description': persona['description'],
                'characteristics': json.dumps(persona['characteristics']),
                'diagnostic_rules': json.dumps(persona['diagnostic_rules'])
            })
        
        # Insert videos
        print("Inserting videos...")
        for video in VIDEOS:
            conn.execute(text("""
                INSERT INTO videos (video_id, title, description, youtube_url, duration_minutes, 
                                    difficulty, topic, feature_1, feature_2, feature_3)
                VALUES (:video_id, :title, :description, :youtube_url, :duration_minutes,
                        :difficulty, :topic, :feature_1, :feature_2, :feature_3)
            """), {
                'video_id': video['video_id'],
                'title': video['title'],
                'description': f"Demo description for {video['title']}",
                'youtube_url': f"https://youtube.com/watch?v=demo_{video['video_id']}",
                'duration_minutes': video['duration'],
                'difficulty': video['difficulty'],
                'topic': video['topic'],
                'feature_1': video['feature_1'],
                'feature_2': video['feature_2'],
                'feature_3': video['feature_3']
            })
        
        # Insert collections
        print("Inserting collections...")
        for collection in COLLECTIONS:
            conn.execute(text("""
                INSERT INTO video_collections (collection_id, name, description, target_persona_id, learning_path_type)
                VALUES (:collection_id, :name, :description, :target_persona_id, :learning_path_type)
            """), collection)
        
        # Insert collection-video mappings
        print("Inserting collection-video mappings...")
        for cv in COLLECTION_VIDEOS:
            conn.execute(text("""
                INSERT INTO collection_videos (collection_id, video_id, sequence_position, is_required)
                VALUES (:collection_id, :video_id, :sequence_position, TRUE)
            """), cv)
        
        # Update collection metadata
        print("Updating collection metadata...")
        for collection in COLLECTIONS:
            conn.execute(text("""
                UPDATE video_collections vc
                SET total_videos = (
                    SELECT COUNT(*) FROM collection_videos 
                    WHERE collection_id = :collection_id
                ),
                estimated_duration_minutes = (
                    SELECT SUM(v.duration_minutes)
                    FROM collection_videos cv
                    JOIN videos v ON cv.video_id = v.video_id
                    WHERE cv.collection_id = :collection_id
                )
                WHERE vc.collection_id = :collection_id
            """), {'collection_id': collection['collection_id']})
        
        conn.commit()
        print("✓ Database seeded successfully!")
        print(f"  - {len(PERSONAS)} personas")
        print(f"  - {len(VIDEOS)} videos")
        print(f"  - {len(COLLECTIONS)} collections")

if __name__ == '__main__':
    seed_database()