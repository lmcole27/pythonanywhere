import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add parent directory to Python path so we can import flask_app
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set dummy environment variables for testing
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['ORGANIZATION'] = 'test-org'
os.environ['PROJECT'] = 'test-project'
os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
os.environ['TELEGRAM_BOT_TOKEN'] = 'test-token'
os.environ['TELEGRAM_CHAT_ID'] = 'test-chat-id'
