@echo off
echo 🚀 Starting Etherea OS - Professional Module Architecture
echo ========================================================

cd /d C:\Users\istan\Etherea_OS

echo 🎤 Starting Voice Service...
start "Voice-Service" cmd /k "python -m backend-services.voice-service.voice_server"

echo 💬 Starting Phi-3 Conversation...
start "Phi3-Chat" cmd /k "python -m backend-services.phi3-conversation.phi3_backend"

echo 💼 Starting HRM-Danube Business...
start "HRM-Business" cmd /k "python -m backend-services.hrm-danube.main_http"

echo ✅ All Etherea services started as proper Python modules!
echo 🎭 Open index.html to experience your AI companion!
pause
