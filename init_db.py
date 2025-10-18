#!/usr/bin/env python3
"""
Initialize MySQL database schema for the demo application
"""

from sqlalchemy import create_engine, text
import os
import time

DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://demo_user:demo_password@mysql:3306/training_videos')

def wait_for_db(engine, max_retries=30):
    """Wait for database to be ready"""
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✓ Database is ready!")
            return True
        except Exception as e:
            print(f"Waiting for database... ({i+1}/{max_retries})")
            time.sleep(2)
    return False

def init_database():
    """Create all tables"""
    print("Initializing database...")
    
    engine = create_engine(DATABASE_URL)
    
    if not wait_for_db(engine):
        print("✗ Could not connect to database")
        return
    
    with engine.connect() as conn:
        # Drop existing tables (for demo reset)
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        tables = [
            'user_enrollments', 'user_profiles', 'conversation_messages',
            'conversations', 'collection_videos', 'video_collections', 
            'videos', 'personas'
        ]
        for table in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
        
        print("Creating tables...")
        
        # 1. Personas table
        conn.execute(text("""
            CREATE TABLE personas (
                persona_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                characteristics JSON NOT NULL,
                diagnostic_rules JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        
        # 2. Videos table
        conn.execute(text("""
            CREATE TABLE videos (
                video_id VARCHAR(50) PRIMARY KEY,
                title VARCHAR(300) NOT NULL,
                description TEXT,
                youtube_url VARCHAR(500),
                duration_minutes INT,
                difficulty VARCHAR(50),
                topic VARCHAR(100),
                feature_1 VARCHAR(50),
                feature_2 VARCHAR(50),
                feature_3 VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_features (feature_1, feature_2, feature_3),
                INDEX idx_topic (topic)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        
        # 3. Video Collections table
        conn.execute(text("""
            CREATE TABLE video_collections (
                collection_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                target_persona_id VARCHAR(50),
                total_videos INT DEFAULT 0,
                estimated_duration_minutes INT DEFAULT 0,
                learning_path_type VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (target_persona_id) REFERENCES personas(persona_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        
        # 4. Collection Videos (junction table)
        conn.execute(text("""
            CREATE TABLE collection_videos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                collection_id VARCHAR(50),
                video_id VARCHAR(50),
                sequence_position INT NOT NULL,
                is_required BOOLEAN DEFAULT TRUE,
                notes TEXT,
                FOREIGN KEY (collection_id) REFERENCES video_collections(collection_id) ON DELETE CASCADE,
                FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
                UNIQUE KEY unique_collection_video (collection_id, video_id),
                UNIQUE KEY unique_collection_position (collection_id, sequence_position),
                INDEX idx_collection (collection_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        
        # 5. Conversations table
        conn.execute(text("""
            CREATE TABLE conversations (
                conversation_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(50),
                status VARCHAR(50) DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                state_json JSON NOT NULL,
                exchange_count INT DEFAULT 0,
                completion_percentage INT DEFAULT 0,
                matched_persona_id VARCHAR(50),
                recommended_collection_id VARCHAR(50),
                confidence_score INT,
                INDEX idx_user (user_id),
                INDEX idx_status (status),
                INDEX idx_activity (last_activity_at),
                FOREIGN KEY (matched_persona_id) REFERENCES personas(persona_id),
                FOREIGN KEY (recommended_collection_id) REFERENCES video_collections(collection_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        
        # 6. Conversation Messages table
        conn.execute(text("""
            CREATE TABLE conversation_messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                conversation_id VARCHAR(50),
                speaker VARCHAR(20) NOT NULL,
                message_content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extracted_data JSON,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
                INDEX idx_conversation (conversation_id),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        
        # 7. User Profiles table
        conn.execute(text("""
            CREATE TABLE user_profiles (
                profile_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                conversation_id VARCHAR(50),
                role VARCHAR(100),
                experience_months INT,
                team_size INT,
                industry VARCHAR(100),
                primary_challenges JSON,
                learning_goals JSON,
                time_available_hours_per_week INT,
                emotional_state VARCHAR(50),
                urgency VARCHAR(50),
                matched_persona_id VARCHAR(50),
                assigned_collection_id VARCHAR(50),
                confidence_score INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_conversation (user_id, conversation_id),
                INDEX idx_user (user_id),
                INDEX idx_persona (matched_persona_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
                FOREIGN KEY (matched_persona_id) REFERENCES personas(persona_id),
                FOREIGN KEY (assigned_collection_id) REFERENCES video_collections(collection_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        
        # 8. User Enrollments table
        conn.execute(text("""
            CREATE TABLE user_enrollments (
                enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                video_id VARCHAR(50),
                collection_id VARCHAR(50),
                status VARCHAR(50) DEFAULT 'enrolled',
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_status (status),
                FOREIGN KEY (video_id) REFERENCES videos(video_id),
                FOREIGN KEY (collection_id) REFERENCES video_collections(collection_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        
        conn.commit()
        print("✓ All tables created successfully!")

if __name__ == '__main__':
    init_database()