# ======================================================
# Imports necesarios para formularios de Django
# ======================================================
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario


# ======================================================
# Formulario para registrar usuarios desde el frontend
# ======================================================
class RegistroForm(UserCreationForm):
    # Campos adicionales al formulario estándar de creación de usuario
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo electrónico")
    telefono = forms.CharField(max_length=20, required=True, label="Teléfono")

    class Meta:
        model = Usuario
        # Campos que se mostrarán en el formulario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'password1', 'password2']

    def save(self, commit=True):
        """
        Sobrescribe el método save para asegurarse de guardar
        los campos personalizados correctamente en el modelo Usuario.
        """
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.telefono = self.cleaned_data['telefono']
        if commit:
            user.save()
        return user


# ======================================================
# Formulario para agregar usuarios desde el admin
# ======================================================
class UsuarioCreationForm(UserCreationForm):
    # Campos adicionales requeridos al crear un usuario en admin
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=20, required=True)

    class Meta:
        model = Usuario
        # Campos que se mostrarán en el formulario de creación
        fields = ("username", "first_name", "last_name", "email", "telefono", "password1", "password2")



