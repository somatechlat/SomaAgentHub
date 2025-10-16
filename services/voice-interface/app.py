"""
Voice Interface Service
Speech-to-text and text-to-speech for KAMACHIQ.

Uses OpenAI Whisper for ASR and OpenAI TTS for voice synthesis.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import logging
import openai
import os
import io
import tempfile

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai.api_key = OPENAI_API_KEY

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TranscriptionResponse(BaseModel):
    """Response from speech-to-text."""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None


class TTSRequest(BaseModel):
    """Request for text-to-speech."""
    text: str
    voice: str = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    model: str = "tts-1"  # tts-1 or tts-1-hd
    speed: float = 1.0  # 0.25 to 4.0


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Voice Interface Service",
    description="Speech-to-text and text-to-speech for KAMACHIQ",
    version="1.0.0"
)

# ============================================================================
# SPEECH-TO-TEXT (Whisper)
# ============================================================================

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file (mp3, wav, m4a, etc.)"),
    language: Optional[str] = None,
    prompt: Optional[str] = None
):
    """
    Transcribe audio to text using Whisper.
    
    Args:
        audio: Audio file upload
        language: Optional language code (e.g., 'en', 'es')
        prompt: Optional context to guide transcription
    """
    try:
        # Read audio file
        audio_data = await audio.read()
        
        # Save to temp file (Whisper API requires file)
        with tempfile.NamedTemporaryFile(suffix=f".{audio.filename.split('.')[-1]}", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        # Transcribe with Whisper
        with open(temp_path, "rb") as audio_file:
            params = {"file": audio_file, "model": "whisper-1"}
            if language:
                params["language"] = language
            if prompt:
                params["prompt"] = prompt
            
            transcript = openai.Audio.transcribe(**params)
        
        # Cleanup
        os.remove(temp_path)
        
        logger.info(f"Transcribed audio: {len(transcript.text)} characters")
        
        return TranscriptionResponse(
            text=transcript.text,
            language=transcript.get("language"),
            duration=transcript.get("duration")
        )
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/transcribe-stream", response_model=TranscriptionResponse)
async def transcribe_stream(
    audio: UploadFile = File(...),
    language: Optional[str] = None
):
    """
    Real-time transcription with streaming support.
    (Simplified version - full streaming requires WebSocket)
    """
    # For now, use same endpoint as regular transcription
    # In production, implement WebSocket-based streaming
    return await transcribe_audio(audio, language)


# ============================================================================
# TEXT-TO-SPEECH (OpenAI TTS)
# ============================================================================

@app.post("/speak")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using OpenAI TTS.
    
    Returns streaming audio response.
    """
    try:
        # Generate speech
        response = openai.Audio.speech.create(
            model=request.model,
            voice=request.voice,
            input=request.text,
            speed=request.speed
        )
        
        # Stream audio
        audio_stream = io.BytesIO(response.content)
        
        logger.info(f"Generated speech: {len(request.text)} characters, voice={request.voice}")
        
        return StreamingResponse(
            audio_stream,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
        
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@app.post("/speak-stream")
async def text_to_speech_stream(request: TTSRequest):
    """
    Streaming TTS for real-time voice synthesis.
    """
    try:
        # OpenAI TTS streaming
        response = openai.Audio.speech.create(
            model=request.model,
            voice=request.voice,
            input=request.text,
            speed=request.speed,
            response_format="opus"  # Better for streaming
        )
        
        # Create streaming generator
        def audio_generator():
            chunk_size = 4096
            audio_data = response.content
            for i in range(0, len(audio_data), chunk_size):
                yield audio_data[i:i+chunk_size]
        
        return StreamingResponse(
            audio_generator(),
            media_type="audio/opus",
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming TTS failed: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming TTS failed: {str(e)}")


# ============================================================================
# VOICE COMMAND PARSING
# ============================================================================

@app.post("/parse-voice-command")
async def parse_voice_command(
    audio: UploadFile = File(...),
    context: Optional[str] = None
):
    """
    Parse voice command into structured intent.
    
    Combines Whisper transcription with GPT-4 intent parsing.
    """
    try:
        # Transcribe audio
        transcription = await transcribe_audio(audio, prompt=context)
        
        # Parse intent with GPT-4
        intent_prompt = f"""
Parse this voice command into a structured intent:

Command: "{transcription.text}"
Context: {context or "General KAMACHIQ command"}

Extract:
- action: What the user wants to do
- entity: What they want to act on
- parameters: Any additional details

Return JSON.
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a voice command parser for KAMACHIQ."},
                {"role": "user", "content": intent_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        intent_text = response.choices[0].message.content
        
        # Extract JSON
        import json
        if "```json" in intent_text:
            intent_text = intent_text.split("```json")[1].split("```")[0].strip()
        
        intent = json.loads(intent_text)
        
        logger.info(f"Parsed voice command: {transcription.text} → {intent}")
        
        return {
            "transcription": transcription.text,
            "intent": intent
        }
        
    except Exception as e:
        logger.error(f"Voice command parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")


# ============================================================================
# VOICE-TO-PROJECT (Complete workflow)
# ============================================================================

@app.post("/voice-to-project")
async def voice_to_project(
    audio: UploadFile = File(..., description="Voice description of project to create")
):
    """
    Complete voice-to-project workflow.
    
    User speaks project description → KAMACHIQ creates it.
    """
    try:
        # Transcribe
        transcription = await transcribe_audio(
            audio,
            prompt="User describing a software project to create"
        )
        
        # Parse project requirements with GPT-4
        project_prompt = f"""
The user described a project in voice:

"{transcription.text}"

Extract structured project requirements:
- name: Project name
- description: Brief description
- type: Project type (web, mobile, api, etc.)
- features: List of features
- tech_stack: Suggested technologies

Return JSON.
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are KAMACHIQ's voice interface parsing project descriptions."},
                {"role": "user", "content": project_prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        
        import json
        project_spec_text = response.choices[0].message.content
        if "```json" in project_spec_text:
            project_spec_text = project_spec_text.split("```json")[1].split("```")[0].strip()
        
        project_spec = json.loads(project_spec_text)
        
        logger.info(f"Voice-to-project: {project_spec.get('name', 'Unknown')}")
        
        return {
            "transcription": transcription.text,
            "project_spec": project_spec,
            "message": "Project specification parsed from voice. Ready for KAMACHIQ creation."
        }
        
    except Exception as e:
        logger.error(f"Voice-to-project failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice-to-project failed: {str(e)}")


@app.get("/voices")
def list_voices():
    """List available TTS voices."""
    return {
        "voices": [
            {"id": "alloy", "description": "Neutral, balanced voice"},
            {"id": "echo", "description": "Warm, friendly voice"},
            {"id": "fable", "description": "Expressive, storytelling voice"},
            {"id": "onyx", "description": "Deep, authoritative voice"},
            {"id": "nova", "description": "Energetic, youthful voice"},
            {"id": "shimmer", "description": "Soft, calm voice"}
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "voice-interface",
        "whisper": "ready",
        "tts": "ready"
    }


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT"))
    uvicorn.run(app, host="0.0.0.0", port=port)
