# config.py
LLM_API_BASE = "http://localhost:8080"  # Where llama-server is running
LLM_COMPLETION_ENDPOINT = "/completion"

ETHREA_PROMPT_FILE = "prompts/etherea-system.txt"

# Model info
MODEL_NAME = "Phi-3-Mini-3.8B-Instruct-Q4_K_M"  # Based on your .gguf file

# Default generation params
DEFAULT_N_PREDICT = 512
DEFAULT_TEMP = 0.7
DEFAULT_TOP_P = 0.9