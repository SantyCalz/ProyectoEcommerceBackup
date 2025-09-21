# ProyectoEcommerce

## Tutorial de Inicio Rápido

Sigue estos pasos para arrancar el proyecto en tu máquina local:

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/ProyectoEcommerce.git
cd ProyectoEcommerce
```

### 2. Crear y activar un entorno virtual (recomendado)
En Windows:
```powershell
python -m venv env
env\Scripts\Activate.ps1
```
En Linux/Mac:
```bash
python3 -m venv env
source env/bin/activate
```

### 3. Instalar dependencias
```bash
pip install django
```

### 4. Aplicar migraciones
```bash
python manage.py migrate
```

### 5. Crear un superusuario (opcional, para acceder al admin)
```bash
python manage.py createsuperuser
```

### 6. Iniciar el servidor de desarrollo
```bash
python manage.py runserver
```

Abre tu navegador en http://127.0.0.1:8000/ para ver la tienda.

---

**Notas:**
- El archivo de base de datos `db.sqlite3` se crea automáticamente al migrar.
- Si agregas nuevas dependencias, instálalas con `pip install <paquete>` y considera usar un `requirements.txt`.
- Para dudas, revisa la documentación oficial de Django: https://docs.djangoproject.com/