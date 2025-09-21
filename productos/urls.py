# ======================================================
# Imports necesarios para rutas de Django
# ======================================================
from django.urls import path
from . import views


# ======================================================
# Definición de las URLs de la aplicación 'productos'
# ======================================================
urlpatterns = [
    # ---------- Página principal y listado de productos ----------
    path('', views.lista_productos, name='lista_productos'),

    # ---------- Carrito de compras ----------
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('vaciar/', views.vaciar_carrito, name='vaciar_carrito'),

    # ---------- Checkout y pagos ----------
    path('checkout/', views.checkout, name='checkout'),
    path("checkout/success/manual/", views.checkout_success_manual, name="checkout_success_manual"),
    path("checkout/failure/", views.checkout_failure, name="checkout_failure"),
    path("checkout/pending/", views.checkout_pending, name="checkout_pending"),
    path('pago_aprobado/', views.pago_aprobado, name='pago_aprobado'),

    # ---------- Registro y autenticación ----------
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_usuario, name='login_usuario'),
    path('logout/', views.logout_usuario, name='logout_usuario'),

    # ---------- Detalle de producto ----------
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),

    # ---------- Área de usuario ----------
    path('mi_cuenta/', views.mi_cuenta, name='mi_cuenta'),
    path('mi_cuenta/editar/', views.ver_datos_usuario, name='editar_datos_usuario'),
    path('mi_cuenta/historial/', views.historial_compras, name='historial_compras'),
]
