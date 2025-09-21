# ======================================================
# Imports necesarios para el admin de Django
# ======================================================
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Importación de modelos y formularios personalizados
from .models import Producto, Categoria, Carrito, CarritoProducto, ProductoImagen, Usuario
from .forms import UsuarioCreationForm


# ======================================================
# Registro de modelos simples sin configuración especial
# ======================================================
admin.site.register(Categoria)
admin.site.register(Carrito)
admin.site.register(CarritoProducto)


# ======================================================
# Inline para imágenes de productos
# Permite agregar varias imágenes directamente en el admin de Producto
# ======================================================
class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1  # Número de formularios extra al crear un Producto
    fields = ["imagen"]  # Campos a mostrar en línea


# ======================================================
# Configuración del admin de Producto
# Permite personalizar la visualización, filtros y búsqueda
# ======================================================
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "categoria")  # Columnas mostradas en la lista
    search_fields = ("nombre", "descripcion")  # Campos que se pueden buscar
    list_filter = ("categoria",)  # Filtros laterales
    inlines = [ProductoImagenInline]  # Asociar las imágenes al admin

# Registro del admin de Producto con la configuración personalizada
admin.site.register(Producto, ProductoAdmin)


# ======================================================
# Admin personalizado para el modelo Usuario
# Incluye formularios de creación y edición, y configuración de campos
# ======================================================
class CustomUserAdmin(UserAdmin):
    add_form = UsuarioCreationForm  # Formulario para crear usuarios
    model = Usuario

    # Campos mostrados en la lista de usuarios
    list_display = ["username", "email", "telefono", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_active"]  # Filtros laterales

    # Configuración de los fieldsets (secciones) para editar un usuario
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "email", "telefono")}),
        ("Permisos", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )

    # Configuración de los campos mostrados al crear un nuevo usuario
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "first_name", "last_name", "email", "telefono", 
                       "password1", "password2", "is_staff", "is_active"),
        }),
    )

    search_fields = ("username", "email", "first_name", "last_name")  # Campos de búsqueda
    ordering = ("username",)  # Orden por defecto


# Registro del admin personalizado para Usuario
admin.site.register(Usuario, CustomUserAdmin)
