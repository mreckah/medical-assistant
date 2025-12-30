import os
import json
import base64
import asyncio
import shutil
import time
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import edge_tts
from fastapi.responses import FileResponse
import shutil
import time

# --- IMPORTS ---
from models.LLM import ask_llm
from consultation import ConsultationManager, MessageItem
from ingest_files import process_documents
from models.vision_model import load_vision_model, analyze_image
from models.reporter import generate_doctor_report
from models.audio_model import load_audio_model, transcribe_audio

# --- BACKGROUND TASK ---
async def schedule_knowledge_update():
    """ Runs the document processing once at startup, then every 24 hours. """
    while True:
        print("Starting scheduled knowledge base update...")
        try:
            # Wrap the synchronous function in a thread to prevent blocking the event loop
            await asyncio.to_thread()
            print("Knowledge base update completed.")
        except Exception as e:
            print(f"Error during scheduled update: {e}")

        # Sleep for 24 hours (24 * 60 * 60 seconds)
        await asyncio.sleep(24 * 3600)


# --- LIFESPAN MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background task
    task = asyncio.create_task(schedule_knowledge_update())

    print("Initiating Vision Model Load...")
    await asyncio.to_thread(load_vision_model)

    print("Initiating Audio Model Load...")
    await asyncio.to_thread(load_audio_model)

    yield
    # Shutdown: Cancel the task if the server stops
    task.cancel()


app = FastAPI(lifespan=lifespan)

# --- Configuration ---
VOICE_ID = "en-US-GuyNeural"
UPLOAD_DIR = "uploads"
AUDIO_DIR = "audios"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# --- CORS ---
origins = ["http://localhost:5173", "http://localhost:3000", "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Response Models ---
class ChatResponse(BaseModel):
    messages: List[MessageItem]
    report: Optional[dict] = None
    imageProcessed: Optional[bool] = False


# --- Helper Functions ---
async def generate_audio_locally(text: str, output_file: str):
    """
    Generates audio with a retry mechanism to handle network timeouts.
    """
    retries = 3
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, VOICE_ID)
            await communicate.save(output_file)
            return  # Success, exit function
        except Exception as e:
            print(f"TTS Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2)  # Wait 2 seconds before retrying
            else:
                # If all retries fail, we raise the error so the main loop handles it
                raise e


async def exec_command(command: str):
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        print(f"Warning: Command failed: {stderr.decode(errors='ignore')}")


def audio_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode('utf-8')


def read_json_transcript(file_path: str) -> dict:
    if os.path.exists(file_path):
        with open(file_path, "r") as f: return json.load(f)
    return None


async def lip_sync_message(message_id: int):
    unique_id = int(time.time() * 1000)
    input_mp3 = os.path.join(AUDIO_DIR, f"{unique_id}_{message_id}.mp3")
    output_wav = os.path.join(AUDIO_DIR, f"{unique_id}_{message_id}.wav")
    output_json = os.path.join(AUDIO_DIR, f"{unique_id}_{message_id}.json")
    return input_mp3, output_wav, output_json


# --- AI Stubs ---

def analyze_skin_image(image_path: str) -> str:
    """
    This function now acts as a bridge.
    It passes the image to your ML package and returns the result.
    """
    # Call the heavy logic from your separate file
    result = analyze_image(image_path)

    return result


# ==========================================
#      MANAGEMENT ENDPOINTS
# ==========================================

@app.get("/chats")
async def get_chats():
    return ConsultationManager.get_all_summaries()


@app.post("/chats")
async def create_chat():
    return ConsultationManager.create_chat()


@app.get("/chats/{chat_id}")
async def get_chat_details(chat_id: str):
    chat = ConsultationManager.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    success = ConsultationManager.delete_chat(chat_id)
    if success:
        return {"success": True}
    return {"error": "Not found"}


class ReportRequest(BaseModel):
    chatId: str


@app.post("/report")
async def generate_report_endpoint(request: ReportRequest):
    # 1. Get Chat Data
    chat = ConsultationManager.get_chat(request.chatId)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = chat.get("messages", [])

    # 2. Extract ALL System Analyses (Chronological)
    # Instead of taking just the last one, we collect every instance.
    collected_analyses = []
    analysis_count = 0

    for msg in messages:
        text = msg.get("text", "")
        if "System Analysis" in text:
            analysis_count += 1
            # We label them clearly for the LLM
            collected_analyses.append(f"--- IMAGE SCAN #{analysis_count} ---\n{text}")

    # Join them into one big text block
    if collected_analyses:
        system_analysis_data = "\n\n".join(collected_analyses)
    else:
        system_analysis_data = "No image analysis available."

    # 3. Generate Report
    pdf_path = generate_doctor_report(
        chat_id=request.chatId,
        history=messages,
        system_analysis=system_analysis_data  # Now contains ALL scans
    )

    if pdf_path and os.path.exists(pdf_path):
        return FileResponse(
            path=pdf_path,
            filename=os.path.basename(pdf_path),
            media_type='application/pdf'
        )
    else:
        return {"error": "Failed to generate report"}
# ==========================================
#      CHAT ENDPOINT
# ==========================================


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
        chatId: str = Form(...),
        message: str = Form(None),
        image: UploadFile = File(None),
        audio: UploadFile = File(None)
 ):
    # 1. Validate Chat ID
    current_chat = ConsultationManager.get_chat(chatId)
    if not current_chat:
        raise HTTPException(status_code=404, detail="Chat ID not found")

    user_text_input = ""
    saved_image_path = None
    image_processed = False

    # 2. Process Audio Input
    if audio:
        # Save the file temporarily
        audio_filename = f"voice_{int(time.time())}.wav"
        audio_path = os.path.join(UPLOAD_DIR, audio_filename)

        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Transcribe
        transcription = transcribe_audio(audio_path)
        # --- DEBUG PRINT ---
        print(f"\n [DEBUG] Audio Content: \"{transcription}\"\n")
        # -------------------

        # If user said something, add it to their text
        if transcription:
            # If they typed AND spoke, combine them. Otherwise just use speech.
            if user_text_input:
                user_text_input += f" (Voice Note: {transcription})"
            else:
                user_text_input = transcription

    # 3. Process Image Input
    if image:
        safe_filename = "".join(x for x in image.filename if x.isalnum() or x in "._-")
        saved_image_path = os.path.join(UPLOAD_DIR, f"user_image_{safe_filename}")
        with open(saved_image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        vision_analysis = analyze_skin_image(saved_image_path)

            # We give the result to the LLM
        user_text_input += f" [System Analysis: {vision_analysis}]"

        image_processed = True

    # 4. Process Text Input
    if message:
        user_text_input += f" {message}"

    # Default fallback
    if not user_text_input.strip() and not saved_image_path:
        user_text_input = "Hello."

    print(f"Chat {chatId} - Text: {user_text_input}, Image: {saved_image_path}")

    # --- NEW: Capture History ---
    # We create a shallow copy of the messages list BEFORE adding the current one.
    # This prevents the AI from seeing the current message twice (once in history, once as new input).
    previous_messages = list(current_chat["messages"])

    # 5. Save USER Message to DB
    ConsultationManager.add_message(
        chatId,
        role="user",
        text=user_text_input
    )

    # 6. Get AI Response (PASSING HISTORY)
    # Ensure your ask_llm function in models/LLM.py accepts the 'history' argument now
    response_messages = ask_llm(
        user_text_input,
        image_path=saved_image_path,
        history=previous_messages
    )

    # 7. Process AI Responses (TTS/Lipsync)
    final_messages = []

    for i, msg_data in enumerate(response_messages):
        input_mp3, output_wav, output_json = await lip_sync_message(i)

        new_msg = MessageItem(**msg_data)
        new_msg.role = "models"

        try:
            # Generate Audio
            await generate_audio_locally(new_msg.text, input_mp3)

            # Generate Lipsync (Ensure bin folder exists)
            if os.path.exists("bin/ffmpeg.exe") and os.path.exists("bin/rhubarb.exe"):
                await exec_command(f"bin\\ffmpeg.exe -y -i {input_mp3} {output_wav}")
                await exec_command(f"bin\\rhubarb.exe -f json -o {output_json} {output_wav} -r phonetic")
                new_msg.lipsync = read_json_transcript(output_json)
            else:
                # Optional: Log warning only once per batch to avoid clutter
                pass

            new_msg.audio = audio_file_to_base64(input_mp3)

        except Exception as e:
            print(f"Error processing audio: {e}")

        # Add to local list and DB
        final_messages.append(new_msg)
        ConsultationManager.add_message(
            chatId,
            role="models",
            text=new_msg.text,
            audio=new_msg.audio,
            lipsync=new_msg.lipsync
        )

    return {
        "messages": final_messages,
        "report": None,
        "imageProcessed": image_processed
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3000)