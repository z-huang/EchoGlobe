from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from Conversation.models import Conversation  # Import the model

@login_required(login_url='login')  # Redirects to 'login' URL if not authenticated
def homepage(request):
    conversations = Conversation.objects.filter(creator=request.user)
    return render(request, 'index.html', {'conversations': conversations})