from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class TordiSignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "tordi-input", "placeholder": "Email address"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "tordi-input", "placeholder": "Username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "tordi-input", "placeholder": "Password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "tordi-input", "placeholder": "Confirm password"}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class TordiLoginForm(forms.Form):
    identifier = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(attrs={"class": "tordi-input", "placeholder": "Username or email", "autofocus": True}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "tordi-input", "placeholder": "Password"})
    )
