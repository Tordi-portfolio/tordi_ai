from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import TordiSignUpForm, TordiLoginForm

User = get_user_model()


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("chat:dashboard")

    if request.method == "POST":
        form = TordiSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Welcome to Tordi! Your account has been created.")
            return redirect("chat:dashboard")
    else:
        form = TordiSignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("chat:dashboard")

    if request.method == "POST":
        form = TordiLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"].strip()
            password = form.cleaned_data["password"]

            username = identifier
            if "@" in identifier:
                try:
                    username = User.objects.get(email__iexact=identifier).username
                except User.DoesNotExist:
                    username = identifier

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                return redirect("chat:dashboard")
            messages.error(request, "Incorrect username/email or password.")
    else:
        form = TordiLoginForm()

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You've been logged out. See you soon!")
    return redirect(reverse("accounts:login"))


@login_required
def set_theme(request):
    """AJAX endpoint: persist the user's chosen theme (light/dark/brown)."""
    if request.method == "POST":
        theme = request.POST.get("theme")
        if theme in dict(User.THEME_CHOICES):
            request.user.theme_preference = theme
            request.user.save(update_fields=["theme_preference"])
            return _json_ok()
    return _json_ok(False)


def _json_ok(ok=True):
    from django.http import JsonResponse

    return JsonResponse({"ok": ok})
