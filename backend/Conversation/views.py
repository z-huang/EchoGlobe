from django.shortcuts import render, redirect
from Conversation.models import Conversation  # Import the model
import requests

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