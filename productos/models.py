from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)


    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'categorias_productos'


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.PositiveIntegerField(default=0)  # en porcentaje
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to="img_productos/", blank=True, null=True)
    categoria = models.ForeignKey(  # 🔹 relación con categoría
        Categoria,
        on_delete=models.CASCADE,
        related_name="productos",
        null=True,
        blank=True
    )

    @property
    def precio_con_descuento(self):
        """Devuelve el precio final con descuento aplicado"""
        if self.descuento > 0:
            return self.precio - (self.precio * self.descuento / 100)
        return self.precio

    @property
    def ahorro(self):
        """Monto exacto de dinero que el cliente ahorra"""
        if self.descuento > 0:
            return self.precio * self.descuento / 100
        return 0


    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'productos'


class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, related_name="imagenes", on_delete=models.CASCADE)
    # productos/models.py
    imagen = models.ImageField(upload_to='img_productos/', blank=True, null=True)


    def __str__(self):
        return f"Imagen de {self.producto.nombre}"

    class Meta:
        db_table = 'imagenes_productos'


class Carrito(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    productos = models.ManyToManyField(Producto, through='CarritoProducto', blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def total(self):
        return sum(item.subtotal() for item in self.carritoproducto_set.all())

    class Meta:
        db_table = 'carritos_usuarios'

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class CarritoProducto(models.Model):
    carrito = models.ForeignKey('Carrito', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.producto.precio * self.cantidad


    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    class Meta:
        db_table = 'carritos_productos'


class Pedido(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    productos = models.ManyToManyField('Producto', through='PedidoProducto')
    direccion_envio = models.CharField(max_length=255, blank=True, null=True)
    pagado = models.BooleanField(default=False)

    # Número de pedido secuencial
    numero_pedido = models.PositiveIntegerField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            ultimo = Pedido.objects.order_by('-numero_pedido').first()
            self.numero_pedido = (ultimo.numero_pedido + 1) if ultimo and ultimo.numero_pedido else 1
        super().save(*args, **kwargs)

    def numero_pedido_formateado(self):
        """Devuelve el número de pedido con ceros a la izquierda, ej: 00003"""
        return str(self.numero_pedido).zfill(5)

    def __str__(self):
        return f"Pedido #{self.numero_pedido_formateado()} - {self.usuario.username}"

    class Meta:
        db_table = 'pedidos_usuarios'


class PedidoProducto(models.Model):
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def subtotal(self):
        return (self.precio_unitario or 0) * (self.cantidad or 0)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    class Meta:
        db_table = 'pedidos_productos'


# 🔹 Perfil extendido del usuario
class Perfil(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telefono_codigo = models.CharField(max_length=5, blank=True, null=True, help_text="Ej: +54")
    telefono_numero = models.CharField(max_length=15, blank=True, null=True, help_text="Ej: 113456789")


    def __str__(self):
        return f"Perfil de {self.user.username}"

    class Meta:
        db_table = 'perfiles_usuarios'



class Usuario(AbstractUser):
    # El orden de los campos en la base de datos será:
    # id, is_superuser, first_name, last_name, email, telefono, password
    telefono = models.CharField(max_length=20, blank=True, null=True)
    # Los campos id, is_superuser, first_name, last_name, email, password ya existen en AbstractUser
    # El resto de campos de permisos se mantienen al final
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='productos_usuario_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='productos_usuario_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'datos_usuarios'