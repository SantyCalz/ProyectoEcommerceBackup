from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario

# Formulario para registrar usuarios desde el frontend
class RegistroForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo electrónico")
    telefono = forms.CharField(max_length=20, required=True, label="Teléfono")

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.telefono = self.cleaned_data['telefono']
        if commit:
            user.save()
        return user

# Formulario para agregar usuarios desde el admin
class UsuarioCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=20, required=True)

    class Meta:
        model = Usuario
        fields = ("username", "first_name", "last_name", "email", "telefono", "password1", "password2")

# Formulario para editar usuarios desde admin o frontend
class UsuarioChangeForm(UserChangeForm):
    password = None  # Oculta el campo password original
    class Meta:
        model = Usuario
        fields = ("username", "first_name", "last_name", "email", "telefono", "is_active", "is_staff")
