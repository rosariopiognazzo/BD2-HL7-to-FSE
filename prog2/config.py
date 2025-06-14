# HL7 Framework Configuration

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://rosariopiognazzo:MO22HSgdEdNdh2fF@cluster0.vim0kda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "DATABASE1"

# Collection Names
COLLECTIONS = {
    "MDM": "mdm_documents",
    "OUL": "oul_lab_results",
    "ORU": "oru_patient_monitoring"
}

# Server Configuration
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 5000
FRONTEND_PORT = 3000

# HL7 Parser Configuration
HL7_DELIMITERS = {
    "field": "|",
    "component": "^", 
    "subcomponent": "&",
    "repetition": "~",
    "escape": "\\"
}

# Supported HL7 Message Types
SUPPORTED_MESSAGE_TYPES = ["MDM", "OUL", "ORU"]

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = [".txt"]

# API Configuration
API_PREFIX = "/api"
CORS_ORIGINS = ["http://localhost:3000"]

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
