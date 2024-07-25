from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from PIL import ImageGrab, Image
import google.generativeai as genai
import pyperclip
import cv2
import time
from requests.exceptions import RequestException

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust to your needs
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including OPTIONS
    allow_headers=["*"],  # Allows all headers
)

groq_client = Groq(api_key='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')
genai.configure(api_key='AIzaSyAgxqFm4gBblFNIvZ6w--_x6JBM_cNujoA')
web_cam = cv2.VideoCapture(0)

sys_msg = (
    'You are a friendly and warm multi-modal AI voice assistant. Your user may or may not have attached a photo for context '
    '(either a screenshot or a webcam capture). Any photo has already been processed into a highly detailed '
    'text prompt that will be attached to their transcribed voice prompt. Generate the most useful and '
    'factual response possible, carefully considering all previous generated text in your response before '
    'adding new tokens to the response. Do not expect or request images, just use the context if added. '
    'Use all of the context of this conversation so your response is relevant to the conversation. Additionally, '
    'incorporate humor and wit where appropriate. Recognize and respond to sarcasm, puns, and clever wordplay. '
    'Make your response clear and concise but not stiff and friendly, avoiding any verbosity'
)

convo = [{'role': 'system', 'content': sys_msg}]

generation_config = {
    'temperature': 0.7,
    'top_p': 1,
    'top_k': 1,
    'max_output_tokens': 2048
}

safety_settings = [
    {
        'category': 'HARM_CATEGORY_HARASSMENT',
        'threshold': 'BLOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_HATE_SPEECH',
        'threshold': 'BLOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
        'threshold': 'BLOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
        'threshold': 'BLOCK_NONE'
    },
]

model = genai.GenerativeModel('gemini-1.5-flash-latest',
                              generation_config=generation_config,
                              safety_settings=safety_settings)

class Prompt(BaseModel):
    prompt: str

def groq_prompt(prompt, img_context):
    if img_context:
        prompt = f'USER PROMPT: {prompt}\n\n    IMAGE CONTEXT: {img_context}'
    convo.append({'role': 'user', 'content': prompt})
    chat_completion = groq_client.chat.completions.create(messages=convo, model='llama3-70b-8192')
    response = chat_completion.choices[0].message
    convo.append(response)

    return response.content

def function_call(prompt):
    sys_msg = (
        'You are an AI function calling model. You will determine whether extracting the users clipboard content, '
        'taking a screenshot, capturing the webcam, or calling no function is best for a voice assistant to respond '
        'to the users prompt. The webcam can be assumed to be a normal laptop webcam facing the user. You will '
        'respond with only one selcetion from this list: ["extract clipboard", "take screenshot", "capture webcam", "None"] \n'
        'Do not respond with anythin but the most logical selection from that list with no explanations. Format the'
        'function call name exactly as i listed.'
    )

    function_convo = [{'role': 'system', 'content': sys_msg},
                      {'role': 'user', 'content': prompt}]

    retries = 3
    delay = 5

    for attempt in range(retries):
        try:
            chat_completion = groq_client.chat.completions.create(messages=function_convo, model='llama3-70b-8192')
            response = chat_completion.choices[0].message
            return response.content
        except RequestException as e:
            print(f"Request failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "Error occurred"

    return "Service unavailable after multiple attempts"

def take_screenshot():
    path = 'screenshot.jpg'
    screenshot = ImageGrab.grab()
    rgb_screenshot = screenshot.convert('RGB')
    rgb_screenshot.save(path, quality=15)

def web_cam_capture():
    if not web_cam.isOpened():
        print('ERROR')
        exit()
    path = 'webcam.jpg'
    ret, frame = web_cam.read()
    cv2.imwrite(path, frame)

def get_clipboard_text():
    clipboard_content = pyperclip.paste()
    if isinstance(clipboard_content, str):
        return clipboard_content
    else:
        print('No clipboard text to copy')
        return None

def vision_prompt(prompt, photo_path):
    img = Image.open(photo_path)
    prompt = (
        'You are the vision analysis AI that provides semtantic meaning from images to provide context '
        'to send to another AI that will create a response to the user. Do not respond as the AI assistant '
        'to the user. Instead take the user prompt input and try to extract all meaning from the photo '
        'relevant to the user prompt. Then generates as much objective data about the image for the AI '
        f'assistant who will repond to the user. \nUSER PROMPT: {prompt}'
    )
    response = model.generate_content([prompt, img])
    return response.text

@app.post("/chat")
def chat(prompt: Prompt):
    call = function_call(prompt.prompt)

    if 'take screenshot' in call:
        print('Taking screenshot')
        take_screenshot()
        visual_context = vision_prompt(prompt=prompt.prompt, photo_path='screenshot.jpg')
    elif 'capture webcam' in call:
        print('capturing webcam')
        web_cam_capture()
        visual_context = vision_prompt(prompt=prompt.prompt, photo_path='webcam.jpg')
    elif 'extract clipboard' in call:
        print('copying clipboard')
        paste = get_clipboard_text()
        prompt.prompt = f'{prompt.prompt}\n\n CLIPBOARD CONTENT: {paste}'
        visual_context = None
    else:
        visual_context = None

    response = groq_prompt(prompt=prompt.prompt, img_context=visual_context)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
