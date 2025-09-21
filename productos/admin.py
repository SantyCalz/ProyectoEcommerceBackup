from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Producto, Categoria, Carrito, CarritoProducto, ProductoImagen, Usuario
from .forms import UsuarioCreationForm, UsuarioChangeForm

# Registro de modelos simples
admin.site.register(Categoria)
admin.site.register(Carrito)
admin.site.register(CarritoProducto)

# Inline para imágenes de productos
class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1
    fields = ["imagen"]

# Admin de Producto
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "categoria")
    search_fields = ("nombre", "descripcion")
    list_filter = ("categoria",)
    inlines = [ProductoImagenInline]

admin.site.register(Producto, ProductoAdmin)

# Admin personalizado para Usuario
class CustomUserAdmin(UserAdmin):
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    model = Usuario
    list_display = ["username", "email", "telefono", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_active"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "email", "telefono")}),
        ("Permisos", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "first_name", "last_name", "email", "telefono", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

admin.site.register(Usuario, CustomUserAdmin)
