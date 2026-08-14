# PrestaShop Local MCP

Servidor MCP local para gestionar una tienda PrestaShop desde clientes compatibles con Model Context Protocol.

Este fork esta adaptado para alojamientos donde la cabecera `Authorization` no llega correctamente a PrestaShop. En lugar de depender de Basic Auth, el cliente envia la clave del Webservice como parametro `ws_key`, que es compatible con la API de PrestaShop.

## 1. Overview

Este MCP permite consultar y administrar una tienda PrestaShop desde asistentes como Codex en ChatGPT Desktop o Claude Desktop.

Herramientas principales:

- `test_connection`: prueba la conexion con la API de PrestaShop.
- `get_shop_info`: muestra informacion general de la tienda.
- `get_products`: lista y consulta productos.
- `get_products_by_category`: lista productos asociados a una categoria, aunque no sea su categoria por defecto.
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
- Acceso al back office de PrestaShop para crear una clave de Webservice.
- ChatGPT Desktop con Codex, Claude Desktop, o ambos.

No hace falta tener Git instalado para la instalacion recomendada.

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

La forma recomendada para usuarios finales es usar el instalador asistido de Windows. No requiere Git, permite elegir la carpeta donde se instalara el MCP y crea un entorno virtual aislado con todas las dependencias.

Descarga y ejecuta el instalador:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/golfo161/prestashop-local-mcp/main/scripts/install_windows.py" -OutFile "$env:TEMP\prestashop-local-mcp-install.py"
py "$env:TEMP\prestashop-local-mcp-install.py"
```

Este primer comando descarga solamente el instalador desde GitHub:

```text
https://raw.githubusercontent.com/golfo161/prestashop-local-mcp/main/scripts/install_windows.py
```

Despues, el instalador usa esta URL para instalar el MCP completo:

```text
https://github.com/golfo161/prestashop-local-mcp/archive/refs/heads/main.zip
```

Ese ZIP no aparece como fichero dentro del repositorio. GitHub lo genera automaticamente con el contenido actual de la rama `main`, igual que cuando pulsas `Code` -> `Download ZIP`.

El instalador preguntara:

1. La carpeta donde quieres instalar el MCP.
2. La URL de la tienda PrestaShop.
3. La API key del Webservice con entrada oculta.
4. Si quieres conectar Codex en ChatGPT Desktop.
5. Si quieres conectar Claude Desktop.

El codigo y el entorno virtual quedan en la carpeta elegida. Las credenciales se guardan fuera de esa carpeta, en el perfil seguro del usuario:

```text
C:\Users\TU_USUARIO\AppData\Roaming\prestashop-local-mcp\.env
```

La carpeta elegida tendra una estructura parecida a esta:

```text
prestashop-local-mcp\
  venv\
  README-INSTALACION.txt
  start-mcp.bat
  setup-mcp.bat
  update-mcp.bat
  uninstall-mcp.bat
```

Los ficheros Python del MCP instalados por `pip` quedan dentro del entorno virtual, no como una carpeta `src` visible en la raiz de la instalacion:

```text
venv\Lib\site-packages\prestashop_mcp\prestashop_client.py
venv\Lib\site-packages\prestashop_mcp\prestashop_mcp_server.py
```

Flujo interno de la instalacion:

1. El instalador crea `venv\` dentro de la carpeta elegida.
2. Actualiza `pip` dentro de ese entorno virtual.
3. `pip` descarga temporalmente el ZIP de GitHub.
4. `pip` lee `pyproject.toml`.
5. `pip` instala las dependencias.
6. `pip` copia el paquete Python dentro de `venv\Lib\site-packages\prestashop_mcp\`.
7. El instalador crea los `.bat` y `README-INSTALACION.txt`.
8. El instalador lanza el asistente `setup` desde el Python del entorno virtual.

Los `.bat` sirven para arrancar el MCP manualmente, volver a configurar la conexion, actualizar desde GitHub o desinstalar la carpeta local.

Si prefieres instalar manualmente el paquete desde el ZIP de GitHub, puedes hacerlo asi. Esta opcion tampoco requiere Git y `pip` instala tambien las dependencias necesarias.

```powershell
py -m pip install --upgrade pip
py -m pip install "https://github.com/golfo161/prestashop-local-mcp/archive/refs/heads/main.zip"
```

Comprueba que el modulo existe:

```powershell
py -m prestashop_mcp.cli --help
```

En una instalacion manual, usa `py -m prestashop_mcp.cli ...` para ejecutar el MCP. Esta forma no depende de que la carpeta `Scripts` de Python este en el `PATH`, pero si depende de que el paquete este instalado en el Python que usa el lanzador `py`.

Equivalencias de comandos:

| Si ves este comando | En Windows ejecuta este |
| --- | --- |
| `prestashop-local-mcp --help` | `py -m prestashop_mcp.cli --help` |
| `prestashop-mcp --help` | `py -m prestashop_mcp.cli --help` |
| `prestashop-local-mcp setup` | `py -m prestashop_mcp.cli setup` |
| `prestashop-local-mcp install-codex` | `py -m prestashop_mcp.cli install-codex` |
| `prestashop-local-mcp install-claude` | `py -m prestashop_mcp.cli install-claude` |

Los comandos `prestashop-local-mcp` y `prestashop-mcp` se mantienen como atajos de compatibilidad, pero solo funcionaran si Python ha dejado sus scripts accesibles en el `PATH`.

### Auto-deploy asistido

Si usas el instalador asistido de Windows, este paso se ejecuta automaticamente al final de la instalacion. Si necesitas repetirlo mas adelante, usa el fichero creado en la carpeta elegida:

```powershell
.\setup-mcp.bat
```

Si hiciste una instalacion manual con `pip`, ejecuta:

```powershell
py -m prestashop_mcp.cli setup
```

El asistente hace todo el despliegue local:

1. Solicita la URL de la tienda PrestaShop.
2. Solicita la API key con entrada oculta.
3. Guarda las credenciales en `%APPDATA%\prestashop-local-mcp\.env`.
4. Prueba la conexion con la API.
5. Pregunta si quieres conectar Codex en ChatGPT Desktop.
6. Si respondes que si, actualiza automaticamente `%USERPROFILE%\.codex\config.toml`.
7. Pregunta si quieres conectar Claude Desktop.
8. Si respondes que si, actualiza automaticamente `%APPDATA%\Claude\claude_desktop_config.json`.
9. Crea copias de seguridad de los ficheros de cliente si ya existian.

El asistente no copia la API key en Codex ni Claude Desktop. La clave solo queda en el fichero local `.env` del usuario.

Si ya has ejecutado `setup` y solo quieres reinstalar la conexion con un cliente desde una instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli install-codex
py -m prestashop_mcp.cli install-claude
```

Si usaste el instalador asistido, puedes ejecutar `setup-mcp.bat` otra vez y elegir el cliente que quieras conectar.

### Instalacion alternativa con Git

Usa esta opcion solo si tienes Git instalado y disponible en el PATH.

```powershell
py -m pip install git+https://github.com/golfo161/prestashop-local-mcp.git
```

### Instalacion para desarrollo

Usa estos pasos si quieres modificar el codigo fuente.

```powershell
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON"
git clone https://github.com/golfo161/prestashop-local-mcp.git PRESTASHOP-LOCAL-MCP
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP"
py -m venv venv_prestashop
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv_prestashop\Scripts\Activate.ps1
py -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Si PowerShell no permite activar el entorno virtual, puedes ejecutar el modulo con el Python del entorno virtual sin activar nada.

Comprueba que el paquete carga:

```powershell
py -c "import prestashop_mcp; print('Installation successful')"
```

## 5. Crear el fichero de configuracion `.env`

La forma recomendada es usar el asistente completo. Pregunta la URL de la tienda, la clave del Webservice, crea el fichero local de configuracion y puede conectar el MCP con Codex o Claude Desktop sin copiar rutas manualmente.

Si usaste el instalador asistido:

```powershell
.\setup-mcp.bat
```

Si hiciste una instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli setup
```

La clave se pide con entrada oculta y no se imprime completa por pantalla. El asistente guarda las credenciales solo en el equipo del usuario.

Por defecto, en Windows el asistente guarda la configuracion aqui:

```text
C:\Users\TU_USUARIO\AppData\Roaming\prestashop-local-mcp\.env
```

Ese fichero queda fuera del repositorio y es la opcion mas segura para distribuir la aplicacion.

Si solo quieres crear el `.env` y no conectar ningun cliente todavia:

Instalacion asistida, desde la carpeta elegida:

```powershell
.\venv\Scripts\python.exe -m prestashop_mcp.cli init
```

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli init
```

Si usas `setup-mcp.bat`, el asistente tambien puede reinstalar la conexion con Codex o Claude Desktop.

### Configuracion manual

Tambien puedes crear el fichero manualmente. El fichero `.env` guarda la URL de la tienda y la clave del Webservice. No se debe subir a Git.

Crea este archivo:

```text
C:\Users\TU_USUARIO\AppData\Roaming\prestashop-local-mcp\.env
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

Con instalacion asistida, desde la carpeta elegida:

```powershell
.\venv\Scripts\python.exe -m prestashop_mcp.cli doctor
```

Con instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli doctor
```

O con una llamada directa:

```powershell
$envFile = "$env:APPDATA\prestashop-local-mcp\.env"
$key = (Get-Content $envFile | Where-Object { $_ -like "PRESTASHOP_API_KEY=*" }).Split("=",2)[1]
Invoke-WebRequest -Uri "https://tu-tienda.com/api/configurations?output_format=JSON&ws_key=$key" -UseBasicParsing
```

Resultado esperado:

```text
StatusCode : 200
```

Si recibes `401 Unauthorized`, revisa que el Webservice este activo, que la clave sea correcta y que tenga permisos `GET` en `configurations`.

## 7. Ejecutar el MCP local por primera vez

Esta prueba arranca el servidor MCP manualmente. Sirve para comprobar que el modulo funciona antes de conectarlo a un cliente.

Si usaste el instalador asistido, abre la carpeta elegida y ejecuta:

```powershell
.\start-mcp.bat
```

Si hiciste una instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli --log-level DEBUG
```

Si estas trabajando desde el repositorio:

```powershell
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv_prestashop\Scripts\Activate.ps1
python -m prestashop_mcp.cli --log-level DEBUG
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

Genera el bloque automaticamente:

```powershell
py -m prestashop_mcp.cli print-codex-config
```

O instala la configuracion automaticamente:

```powershell
py -m prestashop_mcp.cli install-codex
```

Edita o crea este fichero:

```text
C:\Users\TU_USUARIO\.codex\config.toml
```

Si usaste el instalador asistido, el bloque tendra una forma parecida a esta. Cambia `TU_USUARIO` y `CARPETA_ELEGIDA` por tus rutas reales:

```toml
[mcp_servers.prestashop]
command = 'C:\Users\TU_USUARIO\CARPETA_ELEGIDA\venv\Scripts\python.exe'
args = ['-m', 'prestashop_mcp.prestashop_mcp_server']
cwd = 'C:\Users\TU_USUARIO\AppData\Roaming\prestashop-local-mcp'
startup_timeout_sec = 30
tool_timeout_sec = 120
default_tools_approval_mode = 'writes'
```

Que hace cada campo:

- `command`: Python del entorno virtual que arrancara el MCP.
- `args`: modulo Python del servidor MCP.
- `cwd`: carpeta local de configuracion del usuario. El `.env` seguro se guarda ahi.
- `startup_timeout_sec`: tiempo maximo para arrancar.
- `tool_timeout_sec`: tiempo maximo para ejecutar una herramienta.
- `default_tools_approval_mode = 'writes'`: pide aprobacion para acciones de escritura o modificacion.

No pongas la API key en `config.toml`; se lee desde `.env`.

Si trabajas desde un clon de desarrollo, entonces `command` debe apuntar a `venv_prestashop\Scripts\python.exe` y `cwd` puede ser la carpeta del repositorio.

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
Lista los 10 primeros productos de la categoria AGOTADOS usando get_products_by_category.
```

## 9. Configurar Claude Desktop

Esta opcion es para usar el MCP desde Claude Desktop. Claude lee sus servidores MCP desde `claude_desktop_config.json`.

Genera el bloque automaticamente:

```powershell
py -m prestashop_mcp.cli print-claude-config
```

O instala la configuracion automaticamente:

```powershell
py -m prestashop_mcp.cli install-claude
```

Edita o crea este fichero:

```text
C:\Users\TU_USUARIO\AppData\Roaming\Claude\claude_desktop_config.json
```

Copia este contenido, adaptando `TU_USUARIO` y `CARPETA_ELEGIDA`:

```json
{
  "mcpServers": {
    "prestashop": {
      "command": "C:\\Users\\TU_USUARIO\\CARPETA_ELEGIDA\\venv\\Scripts\\python.exe",
      "args": ["-m", "prestashop_mcp.prestashop_mcp_server"],
      "cwd": "C:\\Users\\TU_USUARIO\\AppData\\Roaming\\prestashop-local-mcp"
    }
  }
}
```

Que hace cada campo:

- `command`: Python del entorno virtual que arrancara el MCP.
- `args`: modulo Python del servidor MCP.
- `cwd`: carpeta local de configuracion del usuario. El `.env` seguro se guarda ahi.

No pongas la API key en el JSON; se lee desde el `.env` seguro del usuario.

Si trabajas desde un clon de desarrollo, entonces `command` debe apuntar a `venv_prestashop\Scripts\python.exe` y `cwd` puede ser la carpeta del repositorio.

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
Use prestashop:get_products_by_category for category AGOTADOS and return 10 products.
```

## 10. Buscar productos por categoria real

PrestaShop permite que un producto este asociado a varias categorias. La herramienta `get_products` filtra por `id_category_default`, por lo que puede no encontrar productos que pertenecen a una categoria secundaria.

Para esos casos usa `get_products_by_category`.

La herramienta resuelve la categoria por `category_id` o `category_name` y combina dos fuentes:

- productos cuya categoria por defecto es la categoria solicitada
- productos asociados directamente en `categories/{id}.associations.products`

Esto evita escanear todo el catalogo producto por producto y hace que la respuesta sea rapida incluso en tiendas grandes.

Ejemplos:

```text
Lista los 10 primeros productos de la categoria AGOTADOS.
```

```text
Usa get_products_by_category con category_name="AGOTADOS" y limit=10.
```

```text
Usa get_products_by_category con category_id="145" y limit=10.
```

Parametros:

- `category_id`: ID de categoria. Es la opcion mas exacta y rapida.
- `category_name`: nombre de la categoria, por ejemplo `AGOTADOS`. La busqueda tolera mayusculas/minusculas y acentos.
- `limit`: numero maximo de productos que quieres recibir.
- `scan_limit`: parametro conservado por compatibilidad. La implementacion actual no escanea todo el catalogo.

La respuesta incluye:

- datos de la categoria encontrada
- lista de productos coincidentes
- `default_category_matches`: productos encontrados por categoria por defecto
- `associated_product_ids`: productos asociados desde la categoria
- `detail_fetches`: productos asociados que requirieron consulta individual
- `scanned_products`: siempre `0` en la implementacion optimizada
- `scan_limit`: valor recibido por compatibilidad

Nota: esta herramienta es de solo lectura.

## 11. ChatGPT Apps y MCP remoto

ChatGPT Apps no se conecta directamente a servidores MCP locales `stdio`. Para usar este MCP como app de ChatGPT fuera de Codex, debes exponerlo como servidor MCP remoto o usar Secure MCP Tunnel.

Resumen:

- Codex en ChatGPT Desktop: usa `C:\Users\TU_USUARIO\.codex\config.toml`.
- Claude Desktop: usa `C:\Users\TU_USUARIO\AppData\Roaming\Claude\claude_desktop_config.json`.
- ChatGPT Apps: requiere MCP remoto o Secure MCP Tunnel.

## 12. Actualizaciones y reconexion

Si modificas ficheros del modulo, reinicia el cliente para que vuelva a cargar el servidor MCP.

Reinicia especialmente si cambias:

- `src/prestashop_mcp/prestashop_mcp_server.py`
- definiciones de herramientas
- nombres de herramientas
- parametros de herramientas
- permisos o configuracion del cliente MCP

En Codex o Claude Desktop, lo normal es cerrar y volver a abrir el cliente o iniciar una nueva tarea/conversacion.

En ChatGPT Apps/MCP remoto, los cambios de herramientas no se aplican automaticamente. Hay que refrescar o escanear herramientas otra vez. Si la app ya esta publicada en un workspace, un administrador debe revisar y publicar la actualizacion. En planes Business, puede ser necesario recrear y republicar la app.

## 13. Comandos utiles

En una instalacion asistida, usa los `.bat` creados dentro de la carpeta elegida. En una instalacion manual con `pip`, usa `py -m prestashop_mcp.cli ...`. Los ejemplos con `prestashop-local-mcp ...` solo funcionan si la carpeta `Scripts` de Python esta en el `PATH`.

Instalacion asistida con carpeta elegida por el usuario:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/golfo161/prestashop-local-mcp/main/scripts/install_windows.py" -OutFile "$env:TEMP\prestashop-local-mcp-install.py"
py "$env:TEMP\prestashop-local-mcp-install.py"
```

Arrancar manualmente el MCP:

Instalacion asistida:

```powershell
.\start-mcp.bat
```

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli --log-level DEBUG
```

Asistente de configuracion:

Instalacion asistida:

```powershell
.\setup-mcp.bat
```

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli setup
```

Actualizar instalacion asistida:

```powershell
.\update-mcp.bat
```

Desinstalar instalacion asistida:

```powershell
.\uninstall-mcp.bat
```

Crear solo el fichero de credenciales:

Instalacion asistida:

```powershell
.\venv\Scripts\python.exe -m prestashop_mcp.cli init
```

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli init
```

Diagnostico:

Instalacion asistida:

```powershell
.\venv\Scripts\python.exe -m prestashop_mcp.cli doctor
```

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli doctor
```

Mostrar ruta del fichero seguro de configuracion:

Instalacion asistida:

```powershell
.\venv\Scripts\python.exe -m prestashop_mcp.cli show-config-path
```

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli show-config-path
```

Generar configuracion para Codex:

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli print-codex-config
```

Instalar configuracion para Codex:

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli install-codex
```

Generar configuracion para Claude Desktop:

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli print-claude-config
```

Instalar configuracion para Claude Desktop:

Instalacion manual con `pip`:

```powershell
py -m prestashop_mcp.cli install-claude
```

Arrancar manualmente desde un clon de desarrollo:

```powershell
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv_prestashop\Scripts\Activate.ps1
python -m prestashop_mcp.cli --log-level DEBUG
```

Arrancar sin activar el entorno virtual:

```powershell
cd "C:\Users\TU_USUARIO\OneDrive\Documentos\PYTHON\PRESTASHOP-LOCAL-MCP"
.\venv_prestashop\Scripts\python.exe -m prestashop_mcp.cli --log-level DEBUG
```

Ver ayuda:

```powershell
.\venv_prestashop\Scripts\python.exe -m prestashop_mcp.cli --help
```

Ejecutar tests seguros:

```powershell
.\venv_prestashop\Scripts\python.exe -m pytest tests\test_config.py tests\test_prestashop_client.py
```

## 14. Seguridad

- No subas `.env` a Git.
- Usa una clave de Webservice con los permisos minimos necesarios.
- Empieza con permisos `GET` y amplia solo cuando necesites escribir.
- Revisa las acciones de escritura antes de aprobarlas desde el cliente.
- Haz copia de seguridad de la tienda antes de probar acciones masivas.

## 15. Referencias

- Repositorio del fork: https://github.com/golfo161/prestashop-local-mcp
- Repositorio original: https://github.com/latinogino/prestashop-mcp
- Documentacion de PrestaShop Webservice: https://devdocs.prestashop-project.org/
- OpenAI Help: Developer mode and MCP apps in ChatGPT: https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt
