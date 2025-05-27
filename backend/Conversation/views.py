from django.shortcuts import render, redirect
from Conversation.models import Conversation  # Import the model
import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def new_conversation(request):
    if request.method == "GET":
        # You can customize these defaults as needed
        default_title = "New Conversation"
        default_src_language = "en"
        default_media_url = "https://example.com/media.mp3"
        default_source_text = "This is a default source transcription."

        conversation = Conversation.objects.create(
            creator=request.user,
            title=default_title,
            src_language=default_src_language,
            media_url=default_media_url,
            source_transcription=default_source_text,
        )
        conversation.save()
        return redirect(f'/conversation/{conversation.slug}')
    else:
        # Optionally render a form or just redirect
        return HttpResponse("Create a new conversation here.")
    
    
@login_required
def single_chat(request, slug):
    conversations = Conversation.objects.filter(creator=request.user)
    chat_content = Conversation.objects.filter(slug=slug).first()

    if request.method == "POST" and chat_content:
        new_source = request.POST.get("source_transcription", "").strip()
        if new_source != "":
            chat_content.source_transcription = new_source

            # Call the translation API
            try:
                resp = requests.post(
                    "http://localhost:8000/api/translate/",
                    json={"text": new_source},
                    timeout=10
                )
                if resp.status_code == 200:
                    translations = resp.json()
                    chat_content.en_transcription = translations.get("en", "")
                    chat_content.cn_transcription = translations.get("cn", "")
                    chat_content.de_transcription = translations.get("de", "")
                    chat_content.jp_transcription = translations.get("jp", "")
            except Exception as e:
                # Optionally log the error or handle it as needed
                pass

            chat_content.save()
        # Redirect to avoid resubmission on refresh
        return redirect(request.path)

    return render(
        request,
        'index.html',
        {
            'conversations': conversations,
            'content': chat_content,
            'title': chat_content.title if chat_content else "Conversation",
        }
    )