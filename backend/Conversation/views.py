from django.shortcuts import render
from Conversation.models import Conversation  # Import the model

# Create your views here.
def single_chat(request, slug):
    conversations = Conversation.objects.filter(creator=request.user)
    # if not conversations.exists():
    #     new_conv = Conversation.objects.create(
    #         title="New Conversation",
    #         creator=request.user,
    #         slug="new-conversation"
    #     )
    #     conversations = [new_conv]
    chat_content = Conversation.objects.filter(slug=slug).first()
    return render(request, 'index.html', {'conversations': conversations, 'content': chat_content})