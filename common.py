import logging
from supabase import create_client, Client
from dotenv import load_dotenv
from openai import OpenAI
import os

from supabase._sync.client import SyncClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize Supabase and OpenAI
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai = OpenAI(
    api_key=OPENAI_API_KEY,
)


def get_logger() -> logging.Logger:
    return logger


def get_supabase_client() -> SyncClient:
    return supabase


def get_openai_client() -> OpenAI:
    return openai
