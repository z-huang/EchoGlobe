from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("/")  # Redirect to the base URL
        else:
            return render(request, "login.html", {"form": form})  # Form will include error messages
    else:
        form = AuthenticationForm()
        return render(request, "login.html", {"form": form})
   
def logout_view(request):
    logout(request)
    return redirect("/")  # Redirect to the base URL after logout

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after successful registration
            return redirect("/")  # Redirect to the base URL
        else:
            return render(request, "register.html", {"form": form})
    else:
        form = UserCreationForm()
        return render(request, "register.html", {"form": form})