"""
Setup Configuration
Creates a minimal .env file for the RAG service.
"""
import os
def create_env_file():
    """Create .env file with configuration."""
    env_content = """# AI Provider Configuration
HUGGINGFACE_API_TOKEN=
HF_MODEL=Qwen/Qwen2.5-7B-Instruct
# RAG Configuration
TOP_K_SIMILAR=5
MIN_SIMILARITY=0.2
AI_TIMEOUT_SECONDS=20
# Service Configuration
PORT=8000
# Comma-separated allowed origins for CORS ("*" for local development)
CORS_ORIGINS=*
# Set to enable POST /api/reload-knowledge-base (send as X-Admin-Token header)
ADMIN_TOKEN=
"""
    if os.path.exists(".env"):
        print("! .env already exists - not overwritten")
        return
    with open(".env", "w") as f:
        f.write(env_content)
    print("✓ .env file created successfully")
    print("\nConfiguration written to .env (edit values as needed):")
    print("  HUGGINGFACE_API_TOKEN=")
    print("  HF_MODEL=Qwen/Qwen2.5-7B-Instruct")
    print("  TOP_K_SIMILAR=5")
    print("  MIN_SIMILARITY=0.2")
    print("  PORT=8000")
if __name__ == "__main__":
    print("=" * 60)
    print("CREATING RAG SERVICE CONFIGURATION")
    print("=" * 60)
    print()
    create_env_file()
    print("\n✅ Setup complete!")
    print("\nNext step: python scripts/build_knowledge_base_tfidf.py  (optional check), then: uvicorn app:app --reload")
