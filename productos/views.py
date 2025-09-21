# ======================================================
# Imports necesarios
# ======================================================
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import io
import mercadopago
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from .models import Producto, Carrito, CarritoProducto, Categoria, Pedido, PedidoProducto
from .forms import RegistroForm
from django.conf import settings


# ======================================================
# Vistas de usuario / cuenta
# ======================================================

@login_required
def mi_cuenta(request):
    """Página principal del área de usuario 'Mi Cuenta'"""
    return render(request, 'productos/mi_cuenta.html')


@login_required
def ver_datos_usuario(request):
    """Vista para ver y editar datos del usuario"""
    user = request.user
    return render(request, 'productos/ver_datos_usuario.html', {'user': user})


@login_required
def historial_compras(request):
    """Muestra los pedidos realizados por el usuario"""
    pedidos = request.user.pedido_set.order_by('-fecha').all()
    return render(request, 'productos/historial_compras.html', {'pedidos': pedidos})


# ======================================================
# Vistas de productos
# ======================================================

def detalle_producto(request, producto_id):
    """Detalle de un producto y productos similares"""
    producto = get_object_or_404(Producto, id=producto_id)
    productos_similares = Producto.objects.filter(
        categoria=producto.categoria
    ).exclude(id=producto.id)[:8]
    return render(request, 'productos/detalle_producto.html', {
        'producto': producto,
        'productos_similares': productos_similares,
    })


def lista_productos(request):
    """Listado de productos con filtrado por búsqueda o categoría"""
    query = request.GET.get('q')
    categoria_id = request.GET.get('categoria')

    productos = Producto.objects.all()
    categorias = Categoria.objects.all()

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    return render(request, 'productos/lista.html', {
        'productos': productos,
        'categorias': categorias,
    })


# ======================================================
# Vistas de carrito
# ======================================================

@login_required
def agregar_al_carrito(request, producto_id):
    """Agrega un producto al carrito"""
    producto = get_object_or_404(Producto, id=producto_id)

    if producto.stock <= 0:
        return redirect('lista_productos')  # Sin stock, vuelve a la lista

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    carrito_producto, created = CarritoProducto.objects.get_or_create(
        carrito=carrito,
        producto=producto
    )
    if not created:
        if carrito_producto.cantidad < producto.stock:
            carrito_producto.cantidad += 1
            carrito_producto.save()

    # Redirige a la página anterior o lista de productos
    return redirect(request.META.get('HTTP_REFERER', 'lista_productos'))


@login_required
def ver_carrito(request):
    """Vista del carrito del usuario"""
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    total = carrito.total()
    return render(request, 'productos/carrito.html', {'carrito': carrito, 'total': total})


@login_required
def eliminar_del_carrito(request, producto_id):
    """Elimina o reduce la cantidad de un producto en el carrito"""
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    producto = get_object_or_404(Producto, id=producto_id)
    item = CarritoProducto.objects.filter(carrito=carrito, producto=producto).first()

    if item:
        if item.cantidad > 1:
            item.cantidad -= 1
            item.save()
        else:
            item.delete()

    return redirect('ver_carrito')


@login_required
def vaciar_carrito(request):
    """Vacía todos los productos del carrito"""
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    carrito.carritoproducto_set.all().delete()
    return redirect('ver_carrito')


# ======================================================
# Vistas de checkout y pago
# ======================================================

@login_required
def checkout(request):
    """Vista de checkout y creación de preferencia de pago con Mercado Pago"""
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    total = carrito.total()

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        direccion = request.POST.get('direccion', '')
        request.session['direccion_envio'] = direccion

        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        items = [{
            "title": item.producto.nombre,
            "quantity": item.cantidad,
            "unit_price": float(item.producto.precio),
            "currency_id": "ARS",
        } for item in carrito.carritoproducto_set.all()]

        preference_data = {
            "items": items,
            "payer": {"email": request.user.email},
            "back_urls": {
                "success": request.build_absolute_uri("/checkout/success/manual/"),
                "failure": request.build_absolute_uri("/checkout/failure/"),
                "pending": request.build_absolute_uri("/checkout/pending/"),
            },
        }

        try:
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response.get("response", {})
            url = preference.get("sandbox_init_point")
            if not url:
                return HttpResponse("Error")
            return HttpResponse(url)
        except Exception as e:
            print("Error al crear preferencia de Mercado Pago:", e)
            return HttpResponse("Error")

    return render(request, 'productos/checkout.html', {'carrito': carrito, 'total': total})


@login_required
def pago_aprobado(request):
    """Procesa el pago aprobado, genera pedido y PDF de factura"""
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    direccion = request.session.get('direccion_envio', '')

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            if not carrito.carritoproducto_set.exists():
                return JsonResponse({'status': 'error', 'message': 'No hay productos en el carrito.'})

            # Crear pedido
            pedido = Pedido.objects.create(
                usuario=request.user,
                total=carrito.total(),
                pagado=True,
                direccion_envio=direccion
            )

            # Crear items y descontar stock
            for item in carrito.carritoproducto_set.all():
                PedidoProducto.objects.create(
                    pedido=pedido,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.producto.precio
                )
                producto = item.producto
                producto.stock -= item.cantidad
                if producto.stock < 0:
                    producto.stock = 0
                producto.save()

            # Vaciar carrito
            carrito.carritoproducto_set.all().delete()
            request.session.pop('direccion_envio', None)

            # Generar PDF de factura
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            fecha_local = timezone.localtime(pedido.fecha)
            fecha_str = fecha_local.strftime("%d/%m/%Y %H:%M")

            elements.append(Paragraph(f"Factura - Pedido #{pedido.numero_pedido_formateado()}", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"<b>Cliente:</b> {pedido.usuario.first_name} {pedido.usuario.last_name}", styles['Normal']))
            elements.append(Paragraph(f"<b>Email:</b> {pedido.usuario.email}", styles['Normal']))
            elements.append(Paragraph(f"<b>Dirección:</b> {pedido.direccion_envio}", styles['Normal']))
            elements.append(Paragraph(f"<b>Fecha:</b> {fecha_str}", styles['Normal']))
            elements.append(Spacer(1, 12))

            data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
            for item in pedido.pedidoproducto_set.all():
                subtotal = item.cantidad * item.precio_unitario
                nombre_paragraph = Paragraph(item.producto.nombre, styles['Normal'])
                data.append([nombre_paragraph, str(item.cantidad), f"${item.precio_unitario:.2f}", f"${subtotal:.2f}"])
            data.append(['', '', 'Total:', f"${pedido.total:.2f}"])

            table = Table(data, colWidths=[200, 60, 100, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('TEXTCOLOR',(0,0),(-1,0),colors.black),
                ('ALIGN',(1,1),(-1,-1),'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ]))
            elements.append(table)

            doc.build(elements)
            buffer.seek(0)

            pdf_filename = f"pedido_{pedido.numero_pedido_formateado()}.pdf"
            with open(f"static/media/pedidos/{pdf_filename}", "wb") as f:
                f.write(buffer.getbuffer())

            return JsonResponse({
                'status': 'ok',
                'message': 'Pedido generado correctamente.',
                'pdf_url': f"/static/media/pedidos/{pdf_filename}"
            })

        except Exception as e:
            print("Error en pago_aprobado:", e)
            return JsonResponse({'status': 'error', 'message': 'Ocurrió un error al generar el pedido. Intenta nuevamente.'})

    return render(request, "productos/pago_aprobado.html", {'carrito': carrito})


@login_required
def checkout_success_manual(request):
    """Simula un checkout exitoso manual, genera pedido y descuenta stock"""
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    if not carrito.carritoproducto_set.exists():
        return redirect('lista_productos')

    pedido = Pedido.objects.create(usuario=request.user, pagado=True, total=carrito.total())

    for item in carrito.carritoproducto_set.all():
        PedidoProducto.objects.create(
            pedido=pedido,
            producto=item.producto,
            cantidad=item.cantidad,
        )
        producto = item.producto
        producto.stock -= item.cantidad
        if producto.stock < 0:
            producto.stock = 0
        producto.save()

    carrito.carritoproducto_set.all().delete()
    return render(request, "productos/checkout_success.html")


@login_required
def checkout_failure(request):
    """Vista para checkout fallido"""
    return render(request, "productos/checkout_failure.html")


@login_required
def checkout_pending(request):
    """Vista para checkout pendiente"""
    return render(request, "productos/checkout_pending.html")


# ======================================================
# Registro y login de usuarios
# ======================================================

def registro(request):
    """Registro de usuario desde frontend"""
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('lista_productos')
        else:
            print(form.errors)
    else:
        form = RegistroForm()
    
    return render(request, 'productos/registro.html', {'form': form})


def login_usuario(request):
    """Login de usuario"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            return redirect('lista_productos')
    else:
        form = AuthenticationForm()
    return render(request, 'productos/login.html', {'form': form})


@login_required
def logout_usuario(request):
    """Logout de usuario"""
    logout(request)
    return redirect('login_usuario')


@login_required
def historial_pedidos(request):
    """Otra vista para historial de pedidos (posible duplicado con historial_compras)"""
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'productos/historial.html', {'pedidos': pedidos})
