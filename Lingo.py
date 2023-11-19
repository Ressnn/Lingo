#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 18 19:08:53 2023

@author: prdev
"""

import base64
import google.auth
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.cloud import texttospeech
import google.generativeai as palm
import re
from streamlit_mic_recorder import speech_to_text
import streamlit as st
import time

palm2_api_key = st.secrets["PALM_KEY"]
prompt = "SYSTEM: You are an assistant with access to two outputs. You can talk directly to the user or output results to a text box. To modify the text box begin your changes with <BOX> and end them with </BOX>:. Otherwise the text box will not be modified. If the user asks you to verbally do something ignore the box tags! The user response will send you the current state of the text box and some requests to modify it. If the user asks you to write or modify box items MAKE SURE TO PUT BOX TAGS AROUND YOUR WRITTEN RESPONSE otherwise it will be spoken to the user"
model = "models/text-bison-001"
palm.configure(api_key=palm2_api_key)

tts_client = texttospeech.TextToSpeechClient()
mode = st.secrets["MODE"] # "debug" or "prod"

def extract_box_content(text):
    box_content = re.search(r"<BOX>(.*?)</BOX>", text, re.DOTALL)
    outside_box = re.sub(r"<BOX>.*?</BOX>", "", text, flags=re.DOTALL)
    return box_content.group(1) if box_content else None, outside_box

def google_tts(text, speed):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speed
    )

    response = tts_client.synthesize_speech(
        input=synthesis_input, 
        voice=voice, 
        audio_config=audio_config
    )

    # Convert the response to an audio file in base64
    audio_data = base64.b64encode(response.audio_content).decode("utf-8")
    audio_html = f'<audio autoplay><source src="data:audio/mp3;base64,{audio_data}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)

def google_docs_authenticate():
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.readonly'],
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')

    auth_url, _ = flow.authorization_url(prompt='consent')
    st.write(f'Please go to this URL and authorize the app: {auth_url}')
    auth_code = st.text_input('Enter the authorization code:')
    
    if auth_code:
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        st.session_state['credentials'] = credentials
        docs_service = build('docs', 'v1', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        return docs_service, drive_service

def read_google_doc(docs_service, document_id):
    doc = docs_service.documents().get(documentId=document_id).execute()
    doc_content = doc.get('body').get('content')
    
    text = ""
    for element in doc_content:
        if 'paragraph' in element:
            paragraph_elements = element.get('paragraph').get('elements')
            for elem in paragraph_elements:
                if 'textRun' in elem:
                    text += elem.get('textRun').get('content')
    return text

def get_document_end_index(doc):
    # The endIndex of the last element in the body is the length of the content.
    content = doc.get('body').get('content')
    if not content:
        return 1  # Empty document
    return content[-1].get('endIndex', 1)

def update_google_doc(docs_service, document_id, text):
    # Read the document to find the length of the content
    doc = docs_service.documents().get(documentId=document_id).execute()
    content_length = get_document_end_index(doc)

    # If the document is not empty, delete its content
    requests = []
    if content_length > 1:  # 1 accounts for the initial empty paragraph
        requests.append({
            'deleteContentRange': {
                'range': {
                    'startIndex': 1,
                    'endIndex': content_length - 1  # Adjusted end index
                }
            }
        })

    # Insert the new text
    requests.append({
        'insertText': {
            'location': {
                'index': 1,
            },
            'text': text
        }
    })

    # Execute the update requests
    docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()

def fetch_user_docs(drive_service):
    results = drive_service.files().list(
        pageSize=10,  # Adjust the number of documents fetched
        fields="nextPageToken, files(id, name)",
        q="mimeType='application/vnd.google-apps.document'"
    ).execute()
    items = results.get('files', [])

    if not items:
        return []
    else:
        return [(item['name'], item['id']) for item in items]

st.title("Lingo")

class NoAuthException(Exception):
    pass


# Google Docs Authentication
if 'credentials' not in st.session_state:
    auth = google_docs_authenticate()
    docs_service, drive_service = None, None
    if auth:
        docs_service, drive_service = auth
    else:
        raise NoAuthException("Credentials Invalid")
    
else:
    docs_service = build('docs', 'v1', credentials=st.session_state['credentials'])
    drive_service = build('drive', 'v3', credentials=st.session_state['credentials'])

# Dropdown for document selection and reading content
doc_content = ""
doc_id = None
if drive_service and docs_service:
    time.sleep(1)
    doc_list = fetch_user_docs(drive_service)
    selected_doc = st.selectbox("Select a Document", options=doc_list, format_func=lambda x: x[0])
    doc_id = selected_doc[1] if selected_doc else None

    if doc_id:
        doc_content = read_google_doc(docs_service, doc_id)
        st.session_state.box_text = doc_content

# TTS Speed Slider
tts_speed = st.slider("Adjust TTS Speed", 0.5, 2.0, 1.0)

# Speech to Text
user_speech = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT')

# Automatically send a request when user speech is received
if user_speech and doc_id and docs_service:
    formatted_prompt = f"{prompt} BOX: {doc_content} \nUSER SPEECH: {user_speech}"
    
    print("<PROMPT>: " + formatted_prompt)
    
    completion = palm.generate_text(
        model=model,
        prompt=formatted_prompt,
        temperature=0,
        max_output_tokens=1200,
    )
    
    try:
        model_output = completion.result
        box_content, outside_box = extract_box_content(model_output)
        print("<OUTPUT>: " + model_output)
        if box_content is not None:
            update_google_doc(docs_service, doc_id, box_content)
        if doc_id:
            doc_content = read_google_doc(docs_service, doc_id)
            st.session_state.box_text = doc_content
        # Read out loud the text outside <BOX> tags using Google TTS
        if outside_box.strip():
            google_tts(outside_box, tts_speed)
    except Exception as e:
        st.error(f"Error in API request: {e}")

# Display the content of the Google Doc as the main text box
if mode == "debug":
    st.text_area("Your Input:", value=doc_content, height=200, key="box")