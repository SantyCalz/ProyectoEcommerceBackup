from django.contrib import admin
from .models import Producto, Categoria, Carrito, CarritoProducto, ProductoImagen
from django.contrib.auth.admin import UserAdmin
from .models import Usuario
from .forms import UsuarioCreationForm, UsuarioChangeForm


admin.site.register(Categoria)
admin.site.register(Carrito)
admin.site.register(CarritoProducto)


class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1
    fields = ["imagen"]
    readonly_fields = []

class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "categoria")
    search_fields = ("nombre", "descripcion")
    list_filter = ("categoria",)
    inlines = [ProductoImagenInline]


admin.site.register(Producto, ProductoAdmin)


class CustomUserAdmin(UserAdmin):
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    model = Usuario
    list_display = ["username", "email", "telefono", "is_staff"]

admin.site.register(Usuario, CustomUserAdmin)