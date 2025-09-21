from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import Producto, Carrito, CarritoProducto, Categoria, Pedido, PedidoProducto
from .forms import RegistroForm, UsuarioChangeForm
import mercadopago
from django.conf import settings
from django.http import HttpResponse


# Vista principal de "Mi Cuenta"
@login_required
def mi_cuenta(request):
    return render(request, 'productos/mi_cuenta.html')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def ver_datos_usuario(request):
    user = request.user
    return render(request, 'productos/ver_datos_usuario.html', {'user': user})



# Vista para historial de compras
@login_required
def historial_compras(request):
    pedidos = request.user.pedido_set.order_by('-fecha').all()
    return render(request, 'productos/historial_compras.html', {'pedidos': pedidos})


def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    productos_similares = Producto.objects.filter(categoria=producto.categoria).exclude(id=producto.id)[:8]
    return render(request, 'productos/detalle_producto.html', {
        'producto': producto,
        'productos_similares': productos_similares,
    })



def lista_productos(request):
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


@login_required
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if producto.stock <= 0:
        return redirect('lista_productos')  # Si no hay stock, vuelve a la lista de productos

    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    carrito_producto, created = CarritoProducto.objects.get_or_create(
        carrito=carrito,
        producto=producto
    )
    if not created:
        if carrito_producto.cantidad < producto.stock:
            carrito_producto.cantidad += 1
            carrito_producto.save()
    
    # ← Quitamos el redirect al carrito
    # return redirect('ver_carrito')

    # En su lugar, podemos volver a la página anterior:
    return redirect(request.META.get('HTTP_REFERER', 'lista_productos'))



@login_required
def ver_carrito(request):
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    total = carrito.total()
    return render(request, 'productos/carrito.html', {'carrito': carrito, 'total': total})


@login_required
def eliminar_del_carrito(request, producto_id):
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    producto = get_object_or_404(Producto, id=producto_id)
    item = CarritoProducto.objects.filter(carrito=carrito, producto=producto).first()

    if item:
        if item.cantidad > 1:
            item.cantidad -= 1
            item.save()
        else:
            # Si queda 1 y se disminuye, eliminar del carrito
            item.delete()
    
    return redirect('ver_carrito')


@login_required
def vaciar_carrito(request):
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    carrito.carritoproducto_set.all().delete()
    return redirect('ver_carrito')




from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from .models import Carrito, Pedido, PedidoProducto, Producto

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Carrito, Pedido, PedidoProducto, Producto

@login_required
def checkout(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    total = carrito.total()

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        direccion = request.POST.get('direccion', '')

        # Guardar la dirección en session para usarla luego
        request.session['direccion_envio'] = direccion

        # Inicializar SDK de Mercado Pago
        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

        # Armar items según el carrito
        items = []
        for item in carrito.carritoproducto_set.all():
            items.append({
                "title": item.producto.nombre,
                "quantity": item.cantidad,
                "unit_price": float(item.producto.precio),
                "currency_id": "ARS",
            })

        preference_data = {
            "items": items,
            "payer": {"email": request.user.email},
            "back_urls": {
                "success": request.build_absolute_uri("/checkout/success/manual/"),
                "failure": request.build_absolute_uri("/checkout/failure/"),
                "pending": request.build_absolute_uri("/checkout/pending/"),
            },
            # "auto_return": "approved",
        }

        try:
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response.get("response", {})

            print("=== Respuesta completa de Mercado Pago ===")
            print(preference_response)
            print("=== URL sandbox que se intentará enviar al frontend ===")
            print(preference.get("sandbox_init_point"))

            url = preference.get("sandbox_init_point")
            if not url:
                return HttpResponse("Error")
            return HttpResponse(url)
        except Exception as e:
            print("Error al crear preferencia de Mercado Pago:", e)
            return HttpResponse("Error")

    return render(request, 'productos/checkout.html', {'carrito': carrito, 'total': total})


from django.http import HttpResponse
from reportlab.pdfgen import canvas

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Carrito, Pedido, PedidoProducto, Producto
from reportlab.pdfgen import canvas
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Carrito, Pedido, PedidoProducto

from django.utils import timezone

@login_required
def pago_aprobado(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    direccion = request.session.get('direccion_envio', '')  # Tomamos la dirección de la session

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            if not carrito.carritoproducto_set.exists():
                return JsonResponse({'status': 'error', 'message': 'No hay productos en el carrito.'})

            # 1️⃣ Crear pedido en DB
            pedido = Pedido.objects.create(
                usuario=request.user,
                total=carrito.total(),
                pagado=True,
                direccion_envio=direccion
            )

            # 2️⃣ Crear items del pedido y descontar stock
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

            # 3️⃣ Vaciar carrito
            carrito.carritoproducto_set.all().delete()

            # 4️⃣ Limpiar dirección de la session
            if 'direccion_envio' in request.session:
                del request.session['direccion_envio']

            # 5️⃣ Generar PDF tipo factura
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            # Obtener fecha local
            fecha_local = timezone.localtime(pedido.fecha)
            fecha_str = fecha_local.strftime("%d/%m/%Y %H:%M")

            # Título
            elements.append(Paragraph(f"Factura - Pedido #{pedido.numero_pedido_formateado()}", styles['Title']))
            elements.append(Spacer(1, 12))

            # Datos del cliente
            elements.append(Paragraph(f"<b>Cliente:</b> {pedido.usuario.first_name} {pedido.usuario.last_name}", styles['Normal']))
            elements.append(Paragraph(f"<b>Email:</b> {pedido.usuario.email}", styles['Normal']))
            elements.append(Paragraph(f"<b>Dirección:</b> {pedido.direccion_envio}", styles['Normal']))
            elements.append(Paragraph(f"<b>Fecha:</b> {fecha_str}", styles['Normal']))  # <-- Hora local
            elements.append(Spacer(1, 12))

            # Tabla de productos
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

            # Guardar PDF en media/pedidos
            pdf_filename = f"pedido_{pedido.numero_pedido_formateado()}.pdf"
            with open(f"static/media/pedidos/{pdf_filename}", "wb") as f:
                f.write(buffer.getbuffer())

            # 6️⃣ Devolver JSON con éxito y link al PDF
            return JsonResponse({
                'status': 'ok',
                'message': 'Pedido generado correctamente.',
                'pdf_url': f"/static/media/pedidos/{pdf_filename}"
            })

        except Exception as e:
            print("Error en pago_aprobado:", e)
            return JsonResponse({'status': 'error', 'message': 'Ocurrió un error al generar el pedido. Intenta nuevamente.'})

    # GET → mostrar la página con botón
    return render(request, "productos/pago_aprobado.html", {'carrito': carrito})



@login_required
def checkout_success_manual(request):
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


    # Vaciar carrito
    carrito.carritoproducto_set.all().delete()

    # Redirigir a la página principal de la tienda
    return redirect('lista_productos')

@login_required
def checkout_failure(request):
    return render(request, "productos/checkout_failure.html")


@login_required
def checkout_pending(request):
    # Si querés, podés guardar que el pago está en estado "pendiente"
    return render(request, "productos/checkout_pending.html")


def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()  # Guarda el usuario en la DB con la contraseña hasheada
            login(request, usuario)  # Loguea automáticamente al usuario
            return redirect('lista_productos')  # Redirige después del registro
        else:
            print(form.errors)  # Esto ayuda a depurar errores del form
    else:
        form = RegistroForm()
    
    return render(request, 'productos/registro.html', {'form': form})



def login_usuario(request):
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
    logout(request)
    return redirect('login_usuario')


@login_required
def historial_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'productos/historial.html', {'pedidos': pedidos})
