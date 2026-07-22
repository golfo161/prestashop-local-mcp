# PrestaShop Local MCP

Servidor MCP local para gestionar una tienda PrestaShop desde clientes compatibles con Model Context Protocol.

Este fork esta adaptado para alojamientos donde la cabecera `Authorization` no llega correctamente a PrestaShop. En lugar de depender de Basic Auth, el cliente envia la clave del Webservice como parametro `ws_key`, que es compatible con la API de PrestaShop.

## 1. Overview

Este MCP permite consultar y administrar una tienda PrestaShop desde asistentes como Codex en ChatGPT Desktop o Claude Desktop.

Herramientas principales:

- `test_connection`: prueba la conexion con la API de PrestaShop.
- `get_shop_info`: muestra informacion general de la tienda.
- `get_products`: lista y consulta productos.
- `create_product`, `update_product`, `delete_product`: gestion de productos.
- `update_product_stock`, `update_product_price`: cambios de stock y precio.
- `get_categories`, `create_category`, `update_category`, `delete_category`: gestion de categorias.
- `get_customers`, `create_customer`, `update_customer`: gestion de clientes.
- `get_orders`, `update_order_status`, `get_order_states`: gestion de pedidos.
- `get_modules`, `get_module_by_name`, `install_module`, `update_module_status`: gestion de modulos.
- `get_main_menu_links`, `update_main_menu_link`, `add_main_menu_link`: gestion del menu principal.
- `clear_cache`, `get_cache_status`: cache de PrestaShop.
- `get_themes`, `update_theme_setting`: informacion y ajustes del tema.

Recomendacion: empieza siempre con herramientas de lectura antes de usar acciones que creen, modifiquen o borren datos.

## 2. Requisitos

Estos programas deben existir en el ordenador donde ejecutes el MCP.

- Windows 10/11.
- Python 3.10 o superior.
- Git, o descarga manual del ZIP desde GitHub.
- Acceso al back office de PrestaShop para crear una clave de Webservice.
- ChatGPT Desktop con Codex, Claude Desktop, o ambos.

## 3. Preparar PrestaShop

Antes de instalar el MCP, activa la API en tu tienda.

1. Entra en el back office de PrestaShop.
2. Ve a `Parametros avanzados` -> `Webservice`.
3. Activa el servicio web.
4. Crea una clave de Webservice de 32 caracteres.
5. Marca la clave como activa.
6. Asigna permisos a los recursos que quieras usar.

Para una primera prueba de lectura, concede al menos:

- `GET` en `configurations`.
- `GET` en `products`.
- `GET` en `categories`.
- `GET` en `customers`.
- `GET` en `orders`.
- `GET` en `stock_availables`.
- `GET` en `languages`.

Para modificar datos, tendras que conceder tambien `POST`, `PUT`, `PATCH` o `DELETE` en los recursos correspondientes.

## 4. Instalar el MCP local

Estos pasos descargan el repositorio, crean un entorno virtual aislado e instalan las dependencias.

```powershell
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON"
git clone https://github.com/golfo161/prestashop-local-mcp.git PRESTASHOP-LOCAL-MCP
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP"
python -m venv venv_prestashop
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv_prestashop\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Si PowerShell no permite activar el entorno virtual, puedes ejecutar el binario del MCP directamente desde `venv_prestashop\Scripts` sin activar nada.

Comprueba que el paquete carga:

```powershell
python -c "import prestashop_mcp; print('Installation successful')"
```

## 5. Crear el fichero de configuracion `.env`

El fichero `.env` guarda la URL de la tienda y la clave del Webservice. No se debe subir a Git.

Crea este archivo:

```text
C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP\.env
```

Contenido:

```env
PRESTASHOP_SHOP_URL=https://tu-tienda.com
PRESTASHOP_API_KEY=TU_API_KEY_DE_PRESTASHOP
LOG_LEVEL=INFO
```

Ejemplo:

```env
PRESTASHOP_SHOP_URL=https://ovillos.com
PRESTASHOP_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
LOG_LEVEL=INFO
```

## 6. Probar la API directamente

Esta prueba confirma que PrestaShop acepta la clave antes de arrancar el MCP.

```powershell
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP"
$key = (Get-Content .env | Where-Object { $_ -like "PRESTASHOP_API_KEY=*" }).Split("=",2)[1]
Invoke-WebRequest -Uri "https://tu-tienda.com/api/configurations?output_format=JSON&ws_key=$key" -UseBasicParsing
```

Resultado esperado:

```text
StatusCode : 200
```

Si recibes `401 Unauthorized`, revisa que el Webservice este activo, que la clave sea correcta y que tenga permisos `GET` en `configurations`.

## 7. Ejecutar el MCP local por primera vez

Esta prueba arranca el servidor MCP manualmente. Sirve para comprobar que el modulo funciona antes de conectarlo a un cliente.

```powershell
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv_prestashop\Scripts\Activate.ps1
.\venv_prestashop\Scripts\prestashop-mcp.exe --log-level DEBUG
```

Salida esperada:

```text
Testing API connection with extended functionality...
API connection successful with extended functionality
Starting Enhanced PrestaShop MCP server...
Server ready with full CRUD operations + Navigation Tree management
```

Para detenerlo, pulsa `Ctrl+C`.

Nota: si usas Codex o Claude Desktop, normalmente no tienes que dejar este comando abierto. El cliente arrancara el MCP automaticamente cuando lea su fichero de configuracion.

## 8. Configurar ChatGPT Desktop con Codex

Esta opcion es para usar el MCP desde Codex en ChatGPT Desktop. Codex lee sus servidores MCP desde `config.toml`.

Edita o crea este fichero:

```text
C:\Users\TU_USUARIO\.codex\config.toml
```

Copia este bloque al final del archivo y cambia `TU_USUARIO` por tu usuario real:

```toml
[mcp_servers.prestashop]
command = 'C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP\venv_prestashop\Scripts\python.exe'
args = ['-m', 'prestashop_mcp.prestashop_mcp_server']
cwd = 'C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP'
startup_timeout_sec = 30
tool_timeout_sec = 120
default_tools_approval_mode = 'writes'
```

Que hace cada campo:

- `command`: Python del entorno virtual que arrancara el MCP.
- `args`: modulo Python del servidor MCP.
- `cwd`: carpeta del proyecto; desde aqui se lee el `.env`.
- `startup_timeout_sec`: tiempo maximo para arrancar.
- `tool_timeout_sec`: tiempo maximo para ejecutar una herramienta.
- `default_tools_approval_mode = 'writes'`: pide aprobacion para acciones de escritura o modificacion.

No pongas la API key en `config.toml`; se lee desde `.env`.

Despues de guardar el archivo, reinicia ChatGPT Desktop/Codex o abre una nueva tarea.

Prueba desde Codex:

```text
Usa el MCP de prestashop para probar la conexion.
```

Pruebas seguras:

```text
Lista 5 productos de la tienda.
Muestra las categorias principales.
Dame informacion general de la tienda.
```

## 9. Configurar Claude Desktop

Esta opcion es para usar el MCP desde Claude Desktop. Claude lee sus servidores MCP desde `claude_desktop_config.json`.

Edita o crea este fichero:

```text
C:\Users\TU_USUARIO\AppData\Roaming\Claude\claude_desktop_config.json
```

Copia este contenido, adaptando `TU_USUARIO`:

```json
{
  "mcpServers": {
    "prestashop": {
      "command": "C:\\Users\\TU_USUARIO\\OneDrive\\Documentos\\PYTHON\\PRESTASHOP-LOCAL-MCP\\venv_prestashop\\Scripts\\python.exe",
      "args": ["-m", "prestashop_mcp.prestashop_mcp_server"],
      "cwd": "C:\\Users\\TU_USUARIO\\OneDrive\\Documentos\\PYTHON\\PRESTASHOP-LOCAL-MCP"
    }
  }
}
```

Que hace cada campo:

- `command`: Python del entorno virtual que arrancara el MCP.
- `args`: modulo Python del servidor MCP.
- `cwd`: carpeta del proyecto; desde aqui se lee el `.env`.

No pongas la API key en el JSON si ya tienes `.env` en el proyecto.

Despues de guardar el archivo, cierra Claude Desktop completamente y vuelve a abrirlo.

Prueba desde Claude:

```text
Use prestashop:test_connection
```

Luego prueba lecturas:

```text
List 5 products from my PrestaShop store.
Show the main categories.
Get general shop information.
```

## 10. ChatGPT Apps y MCP remoto

ChatGPT Apps no se conecta directamente a servidores MCP locales `stdio`. Para usar este MCP como app de ChatGPT fuera de Codex, debes exponerlo como servidor MCP remoto o usar Secure MCP Tunnel.

Resumen:

- Codex en ChatGPT Desktop: usa `C:\Users\TU_USUARIO\.codex\config.toml`.
- Claude Desktop: usa `C:\Users\TU_USUARIO\AppData\Roaming\Claude\claude_desktop_config.json`.
- ChatGPT Apps: requiere MCP remoto o Secure MCP Tunnel.

## 11. Actualizaciones y reconexion

Si modificas ficheros del modulo, reinicia el cliente para que vuelva a cargar el servidor MCP.

Reinicia especialmente si cambias:

- `src/prestashop_mcp/prestashop_mcp_server.py`
- definiciones de herramientas
- nombres de herramientas
- parametros de herramientas
- permisos o configuracion del cliente MCP

En Codex o Claude Desktop, lo normal es cerrar y volver a abrir el cliente o iniciar una nueva tarea/conversacion.

En ChatGPT Apps/MCP remoto, los cambios de herramientas no se aplican automaticamente. Hay que refrescar o escanear herramientas otra vez. Si la app ya esta publicada en un workspace, un administrador debe revisar y publicar la actualizacion. En planes Business, puede ser necesario recrear y republicar la app.

## 12. Comandos utiles

Arrancar manualmente el MCP:

```powershell
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv_prestashop\Scripts\Activate.ps1
.\venv_prestashop\Scripts\prestashop-mcp.exe --log-level DEBUG
```

Arrancar sin activar el entorno virtual:

```powershell
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP"
.\venv_prestashop\Scripts\prestashop-mcp.exe --log-level DEBUG
```

Ver ayuda:

```powershell
.\venv_prestashop\Scripts\prestashop-mcp.exe --help
```

Ejecutar tests seguros:

```powershell
.\venv_prestashop\Scripts\python.exe -m pytest tests\test_config.py tests\test_prestashop_client.py
```

## 13. Seguridad

- No subas `.env` a Git.
- Usa una clave de Webservice con los permisos minimos necesarios.
- Empieza con permisos `GET` y amplia solo cuando necesites escribir.
- Revisa las acciones de escritura antes de aprobarlas desde el cliente.
- Haz copia de seguridad de la tienda antes de probar acciones masivas.

## 14. Referencias

- Repositorio del fork: https://github.com/golfo161/prestashop-local-mcp
- Repositorio original: https://github.com/latinogino/prestashop-mcp
- Documentacion de PrestaShop Webservice: https://devdocs.prestashop-project.org/
- OpenAI Help: Developer mode and MCP apps in ChatGPT: https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt
