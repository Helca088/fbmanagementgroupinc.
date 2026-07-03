from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

#Login Function
def email_login(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            return render(request, "login.html", {
                "error": "Username and password required"
            })

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")

        return render(request, "login.html", {
            "error": "Invalid username or password"
        })

    return render(request, "login.html")

#Logout Function
@require_POST
def logout_view(request):
        
        print("LOGGING OUT USER:", request.user)
        logout(request)
        return redirect('login')

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')
