from fastapi import FastAPI, Response, UploadFile, File
from src.response_generation import generate_response
from src.text_to_speech import synthesize_speech
from src.transcribe_audio import transcribe_audio
import gradio as gr
import tempfile
import os
import soundfile as sf
import numpy as np

app = FastAPI()

@app.post("/chat")
async def chat_endpoint(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    user_text = transcribe_audio(audio_bytes)
    print(user_text)
    generated_text = generate_response(user_text)
    print(generated_text)
    response_audio = synthesize_speech(generated_text)
    return Response(content=response_audio, media_type="audio/wav")

# Gradio interface function
def chat_interface(input_data, history):
    # Determine if input is text or audio
    if isinstance(input_data, str) and input_data.strip():
        # Text input provided
        user_text = input_data.strip()
    elif input_data is not None:
        # Audio input provided
        # Read the audio file
        with open(input_data, "rb") as f:
            audio_bytes = f.read()

        # Process through your pipeline
        user_text = transcribe_audio(audio_bytes)
    else:
        # No input provided
        return history, None
    print(f"User said: {user_text}")
    
    # Initialize history if None
    if history is None:
        history = []
    
    # Add user message to history (new format with role and content)
    history.append({"role": "user", "content": user_text})
    
    # Generate response
    generated_text = generate_response(user_text)
    print(f"Generated: {generated_text}")
    
    # Add assistant response to history (new format)
    history.append({"role": "assistant", "content": generated_text})
    
    # Synthesize speech
    audio_data = synthesize_speech(generated_text)
    
    # Save synthesized audio to temporary file for Gradio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        sf.write(tmp_file.name, audio_data, samplerate=16000)
        response_audio_path = tmp_file.name
    
    # Return updated history and audio file path
    # Gradio's audio_output component with autoplay=True will play it in the browser
    return history, response_audio_path

# Create Gradio interface with conversation dialog
with gr.Blocks(title="Voice Chat Assistant") as demo:
    gr.Markdown("# Voice Chat Assistant")
    gr.Markdown("Record your voice or upload an audio file to chat with the AI assistant. Your transcribed text and the AI's response will be displayed in the conversation.")
    
    chatbot = gr.Chatbot(
        label="Conversation",
        height=400,
        show_label=True
    )
    
    with gr.Row():
        text_input = gr.Textbox(
            label="Type your message",
            placeholder="Or type your message here...",
            show_label=True,
            interactive=True,
            lines=1,
            container=True,
            elem_id="text_input_box"
        )
        send_btn = gr.Button("Send")

        audio_input = gr.Audio(
            sources=["microphone", "upload"],
            type="filepath",
            label="Record or Upload Audio",
            show_label=True
        )
        audio_output = gr.Audio(
            label="Response Audio",
            show_label=True,
            autoplay=True
        )
    
    # Clear button
    clear_btn = gr.Button("Clear Conversation", variant="secondary")
    
    # Process text input
    send_btn.click(
        fn=chat_interface,
        inputs=[text_input, chatbot],
        outputs=[chatbot, audio_output]
    )

    # Process audio input
    audio_input.change(
        fn=chat_interface,
        inputs=[audio_input, chatbot],
        outputs=[chatbot, audio_output]
    )
    
    # Clear conversation
    clear_btn.click(
        fn=lambda: ([], None),
        outputs=[chatbot, audio_output]
    )

# Mount Gradio on FastAPI
app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)