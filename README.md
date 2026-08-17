# PrestaShop Local MCP

Servidor MCP local para gestionar una tienda PrestaShop desde clientes compatibles con Model Context Protocol.

Esta distribucion esta adaptada para alojamientos donde la cabecera `Authorization` no llega correctamente a PrestaShop. En lugar de depender de Basic Auth, el cliente envia la clave del Webservice como parametro `ws_key`, que es compatible con la API de PrestaShop.

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

Cuando trabajes con la tienda desde un asistente, las respuestas deben ser operativas y breves: validar datos, pedir confirmacion si hace falta, ejecutar la accion y devolver solo el resultado necesario.

Para crear productos, el asistente debe mostrar siempre una previsualizacion antes de llamar a `create_product`. Si el usuario confirma la previsualizacion, crea el producto. Si no la confirma, pide los cambios necesarios o espera una nueva ficha.

Guia operativa para asistentes: consulta `docs/PRESTASHOP_OPERATIONS.md` para el protocolo recomendado de altas, modificaciones, bajas, verificaciones, SEO, traducciones, imagenes, stock y operaciones masivas.

## 2. Funcionalidades disponibles

Estas son las operaciones que expone actualmente el MCP.

### Conexion y estado de tienda

- `test_connection`: prueba la conexion con la API de PrestaShop.
- `get_shop_info`: muestra informacion general y estadisticas basicas de la tienda.

### Productos

- `get_products`: consulta productos por ID o lista productos con filtros.
- `get_products_by_category`: lista productos asociados a una categoria por ID o nombre, incluyendo categorias secundarias.
- `create_product`: crea un producto nuevo desactivado inicialmente. Antes de usarla, el asistente debe mostrar una previsualizacion y esperar confirmacion explicita. Tambien puede subir imagen, resumen, campos SEO y caracteristicas.
- `update_product`: actualiza un producto existente. Permite modificar nombre, precio, precio mayorista, resumen, descripcion larga, campos SEO, URL amigable, categoria por defecto, referencia, peso, regla fiscal, estado activo, caracteristicas e imagen adicional.
- `delete_product`: elimina un producto.
- `update_product_stock`: cambia la cantidad de stock de un producto.
- `update_product_price`: cambia precio y precio mayorista.

Campos habituales que puedes consultar o modificar segun la herramienta:

- nombre
- precio
- resumen: se guarda en el campo resumen de PrestaShop, hasta 1500 caracteres. Si necesita estructura visual, usa HTML basico seguro como `<p>`, `<strong>`, `<ul>`, `<li>` o `<br>`.
- SEO: meta title, meta description, keywords y URL amigable
- categoria
- referencia/SKU
- peso
- estado activo
- stock
- caracteristicas del producto, como composicion, formato, metros, grosor, origen o galga
- informacion de categorias asociadas
- imagen inicial durante la creacion

Para subir una imagen al crear un producto, usa `create_product` con una ruta local absoluta en `image_path`, por ejemplo `C:\Users\usuario\Pictures\producto.jpg`. El Webservice de PrestaShop debe tener permisos sobre el recurso de imagenes/productos.

Para crear o asociar caracteristicas por nombre y valor, el Webservice debe tener permisos de lectura y escritura sobre `product_features` y `product_feature_values`. Si usas IDs ya existentes, igualmente necesita poder leerlos y asociarlos al producto.

Los productos creados con `create_product` quedan desactivados por defecto. Activalos mas adelante con `update_product` cuando ya esten revisados.

### Plantilla recomendada para crear productos

La forma mas segura de crear productos desde el asistente es preparar una ficha de producto y pedirle que la revise antes de crear nada. El repositorio incluye una plantilla base en `templates/product.create.yaml`.

Campos de la plantilla:

- `nombre`: obligatorio. Nombre visible del producto. Puede ser texto simple o un bloque por idioma.
- `precio`: obligatorio. Precio de venta.
- `resumen`: opcional, pero recomendable. Es el texto del producto y se guarda en el campo resumen de PrestaShop. Longitud maxima recomendada: 1500 caracteres. Si el texto necesita bloques, destacados o puntos, usa HTML basico seguro para que PrestaShop lo muestre con formato.
- `seo`: opcional. Permite aportar `meta_title`, `meta_description`, `meta_keywords` o `link_rewrite`. Si no se indica, el asistente lo genera siguiendo buenas practicas SEO.
- `categoria_id`: opcional. Si no se indica, PrestaShop usara la categoria por defecto configurada por el MCP.
- `cantidad`: opcional. Stock inicial.
- `referencia`: opcional. Referencia interna o SKU.
- `peso`: opcional. Peso del producto.
- `caracteristicas`: opcional. Lista de caracteristicas visibles en la ficha tecnica del producto. Puedes indicar `nombre` y `valor`; el MCP buscara o creara la caracteristica y su valor. Si ya conoces los IDs de PrestaShop, tambien puedes usar `feature_id` y `feature_value_id`.
- `imagen`: opcional. Ruta local absoluta de la imagen inicial.

Ejemplo:

```yaml
producto:
  nombre:
    es: "Lana Merino Azul 100g"
    en: "Blue Merino Wool 100g"
    fr: "Laine merinos bleue 100g"
  precio: 5.95
  resumen:
    es: |
      <p>Ovillo de lana merino suave, ideal para prendas de invierno.</p>
      <p><strong>Caracteristicas:</strong></p>
      <ul>
        <li>Formato 100 g.</li>
        <li>Tacto suave y calido.</li>
        <li>Apto para punto y crochet.</li>
      </ul>
    en: |
      <p>Soft merino wool ball, ideal for winter garments.</p>
      <p><strong>Features:</strong></p>
      <ul>
        <li>100 g format.</li>
        <li>Soft and warm feel.</li>
        <li>Suitable for knitting and crochet.</li>
      </ul>
    fr: |
      <p>Pelote de laine merinos douce, ideale pour les vetements d'hiver.</p>
      <p><strong>Caracteristiques:</strong></p>
      <ul>
        <li>Format 100 g.</li>
        <li>Toucher doux et chaud.</li>
        <li>Convient au tricot et au crochet.</li>
      </ul>
  seo:
    meta_title:
      es: "Lana Merino Azul 100g"
      en: "Blue Merino Wool 100g"
      fr: "Laine merinos bleue 100g"
    meta_description:
      es: "Compra lana merino azul 100g, suave y calida para punto y crochet."
      en: "Buy blue merino wool 100g, soft and warm for knitting and crochet."
      fr: "Achetez une laine merinos bleue 100g, douce et chaude pour tricot et crochet."
  categoria_id: "12"
  cantidad: 20
  referencia: "MERINO-AZUL-100"
  peso: 0.10
  caracteristicas:
    - nombre: "Composicion"
      valor: "100% lana merino"
    - nombre: "Formato"
      valor: "Ovillo 100 g"
    - nombre: "Uso recomendado"
      valor: "Punto y crochet"
  imagen: "C:\\Users\\usuario\\Pictures\\productos\\merino-azul.jpg"
```

Antes de crear el producto, pide al asistente:

```text
Revisa esta plantilla de producto. Muestrame una previsualizacion con los datos finales, el resumen y el SEO. Si falta algun dato importante, preguntame antes de crearlo. No lo crees hasta que confirme la previsualizacion.
```

Idiomas:

- La tienda usa espanol, ingles y frances.
- Si el usuario especifica `es`, `en` y `fr`, el MCP usa esas traducciones.
- Si el usuario solo escribe un texto en espanol, el asistente debe traducirlo a ingles y frances antes de llamar a `create_product`.
- Si falta alguna traduccion, el MCP usa el texto espanol como respaldo para que PrestaShop reciba siempre todos los idiomas activos.

El asistente debe convertir la plantilla a los parametros de `create_product`:

```json
{
  "name": {
    "es": "Lana Merino Azul 100g",
    "en": "Blue Merino Wool 100g",
    "fr": "Laine merinos bleue 100g"
  },
  "price": 5.95,
  "summary": {
    "es": "<p>Ovillo de lana merino suave, ideal para prendas de invierno.</p><p><strong>Caracteristicas:</strong></p><ul><li>Formato 100 g.</li><li>Tacto suave y calido.</li><li>Apto para punto y crochet.</li></ul>",
    "en": "<p>Soft merino wool ball, ideal for winter garments.</p><p><strong>Features:</strong></p><ul><li>100 g format.</li><li>Soft and warm feel.</li><li>Suitable for knitting and crochet.</li></ul>",
    "fr": "<p>Pelote de laine merinos douce, ideale pour les vetements d'hiver.</p><p><strong>Caracteristiques:</strong></p><ul><li>Format 100 g.</li><li>Toucher doux et chaud.</li><li>Convient au tricot et au crochet.</li></ul>"
  },
  "meta_title": {
    "es": "Lana Merino Azul 100g",
    "en": "Blue Merino Wool 100g",
    "fr": "Laine merinos bleue 100g"
  },
  "meta_description": {
    "es": "Compra lana merino azul 100g, suave y calida para punto y crochet.",
    "en": "Buy blue merino wool 100g, soft and warm for knitting and crochet.",
    "fr": "Achetez une laine merinos bleue 100g, douce et chaude pour tricot et crochet."
  },
  "category_id": "12",
  "quantity": 20,
  "reference": "MERINO-AZUL-100",
  "weight": 0.10,
  "features": [
    {
      "name": "Composicion",
      "value": "100% lana merino"
    },
    {
      "name": "Formato",
      "value": "Ovillo 100 g"
    },
    {
      "name": "Uso recomendado",
      "value": "Punto y crochet"
    }
  ],
  "image_path": "C:\\Users\\usuario\\Pictures\\productos\\merino-azul.jpg"
}
```

Flujo recomendado:

1. Copia la plantilla y rellena los datos del producto.
2. Comprueba que la imagen existe en esa ruta local si vas a subir imagen.
3. Pide al asistente que valide la ficha antes de crearla.
4. El asistente adapta el resumen con el formato mas claro para el cliente. Cuando use puntos o bloques, debe enviarlo como HTML basico seguro, no como saltos de linea planos.
5. El asistente muestra una previsualizacion operativa con nombre, precio, categoria, stock, referencia, peso, caracteristicas, imagen, resumen y SEO.
6. El usuario confirma si esta de acuerdo.
7. Si confirma, el asistente llama a `create_product`. Si no confirma, el asistente pide los cambios o espera una nueva ficha.
8. El MCP crea el producto desactivado y, si se indico `image_path`, sube la imagen al producto creado.
9. Revisa el ID del producto y el resultado de `image_upload` en la respuesta.

### Categorias

- `get_categories`: lista categorias y permite filtrar por categoria padre.
- `create_category`: crea una categoria.
- `update_category`: actualiza nombre, descripcion, categoria padre, URL amigable, SEO o estado activo.
- `delete_category`: elimina una categoria.

### Clientes

- `get_customers`: lista clientes y permite filtrar por email.
- `create_customer`: crea un cliente.
- `update_customer`: actualiza email, nombre, apellidos o estado activo.

### Pedidos

- `get_orders`: lista pedidos y permite filtrar por cliente o estado.
- `get_order_states`: consulta los estados de pedido disponibles.
- `update_order_status`: cambia el estado de un pedido.

### Modulos

- `get_modules`: lista modulos instalados.
- `get_module_by_name`: consulta un modulo por nombre tecnico.
- `install_module`: instala un modulo.
- `update_module_status`: activa o desactiva un modulo.

### Menu principal y navegacion

- `get_main_menu_links`: consulta enlaces del menu principal.
- `update_main_menu_link`: actualiza un enlace del menu principal.
- `add_main_menu_link`: anade un enlace al menu principal.
- `get_menu_tree`: consulta el arbol de categorias usado en la navegacion.
- `add_category_to_menu`: anade una categoria al menu.
- `remove_category_from_menu`: quita una categoria del menu.
- `update_menu_tree`: actualiza el orden completo del arbol del menu.
- `get_menu_tree_status`: muestra el estado combinado de enlaces y categorias del menu.

### Cache

- `get_cache_status`: consulta la configuracion actual de cache.
- `clear_cache`: limpia la cache de PrestaShop.

### Tema

- `get_themes`: consulta temas disponibles y ajustes del tema actual.
- `update_theme_setting`: actualiza una configuracion del tema.

### Instalacion, configuracion y mantenimiento

- Instalador asistido para Windows.
- Eleccion de carpeta de instalacion.
- Creacion automatica de entorno virtual.
- Configuracion segura de credenciales en `%APPDATA%\prestashop-local-mcp\.env`.
- Conexion automatica con Codex en ChatGPT Desktop.
- Conexion automatica con Claude Desktop.
- Generacion manual de configuracion para Codex o Claude.
- Diagnostico de conexion.
- Actualizacion con `update-mcp.bat`.
- Desinstalacion local con `uninstall-mcp.bat`.

## 3. Requisitos

Estos programas deben existir en el ordenador donde ejecutes el MCP.

- Windows 10/11.
- Python 3.10 o superior.
- Acceso al back office de PrestaShop para crear una clave de Webservice.
- ChatGPT Desktop con Codex, Claude Desktop, o ambos.

No hace falta tener Git instalado para la instalacion recomendada.

### Instalar Python en un Windows nuevo

Si el equipo no tiene Python instalado, puedes instalar la ultima version disponible de Python 3 desde PowerShell con `winget`:

```powershell
winget install python3 --source winget --silent --accept-package-agreements --accept-source-agreements
```

Cierra y vuelve a abrir PowerShell. Despues comprueba que Python y `pip` estan disponibles:

```powershell
py --version
py -m pip --version
```

No hace falta instalar Git ni GitHub Desktop. El instalador del MCP descarga el proyecto desde el ZIP generado por GitHub.

## 4. Preparar PrestaShop

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

Para crear productos con stock inicial e imagen, concede al menos:

- `POST` en `products`.
- `GET` y `PUT` en `stock_availables`.
- `POST` en `images`.

Si falta `PUT` en `stock_availables`, el producto se crea, pero PrestaShop no permite aplicar la cantidad inicial. El MCP devuelve ese error en `stock_update` para que no pase desapercibido.

La regla de impuestos no se calcula por nombre: PrestaShop espera el ID interno de `id_tax_rules_group`. En el back office puede aparecer como `ES Standard rate (21%)`, pero el MCP necesita su ID numerico. Ese ID depende de cada tienda: en una instalacion puede ser `15`, en otra `1` u otro valor. Indica siempre el ID real de tu tienda en el asistente o en `PRESTASHOP_TAX_RULES_GROUP_ID`.

## 5. Instalar el MCP local

Hay dos formas de instalar este MCP. Para usuarios finales, usa la instalacion asistida. La instalacion manual queda para usuarios que prefieren controlar los comandos o integrar el paquete en un entorno Python existente.

### Opcion A: instalacion asistida de Windows (recomendada)

Esta es la opcion recomendada. No requiere Git, permite elegir la carpeta de instalacion, crea un entorno virtual aislado y puede conectar automaticamente el MCP con Codex en ChatGPT Desktop o Claude Desktop.

Pasos:

1. Abre PowerShell.
2. Descarga el instalador oficial desde GitHub.
3. Ejecuta el instalador con Python.

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/golfo161/prestashop-local-mcp/main/scripts/install_windows.py" -OutFile "$env:TEMP\prestashop-local-mcp-install.py"
py "$env:TEMP\prestashop-local-mcp-install.py"
```

Que descarga cada comando:

1. `Invoke-WebRequest` descarga solamente el instalador:

```text
https://raw.githubusercontent.com/golfo161/prestashop-local-mcp/main/scripts/install_windows.py
```

2. El instalador descarga despues el MCP completo desde el ZIP automatico de GitHub:

```text
https://github.com/golfo161/prestashop-local-mcp/archive/refs/heads/main.zip
```

Ese ZIP no aparece como fichero dentro del repositorio. GitHub lo genera automaticamente con el contenido actual de la rama `main`, igual que cuando pulsas `Code` -> `Download ZIP`.

Durante la instalacion, el asistente preguntara:

1. La carpeta donde quieres instalar el MCP.
2. La URL de la tienda PrestaShop.
3. La API key del Webservice con entrada oculta.
4. `ID regla fiscal productos nuevos (ej. 15 = ES Standard rate (21%))`.
5. Si quieres conectar Codex en ChatGPT Desktop.
6. Si quieres conectar Claude Desktop.

Al terminar, el codigo y el entorno virtual quedan en la carpeta elegida. Las credenciales se guardan fuera de esa carpeta, en el perfil seguro del usuario:

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

Flujo interno de la instalacion asistida:

1. El instalador crea `venv\` dentro de la carpeta elegida.
2. Actualiza `pip` dentro de ese entorno virtual.
3. `pip` descarga temporalmente el ZIP de GitHub.
4. `pip` lee `pyproject.toml`.
5. `pip` instala las dependencias.
6. `pip` copia el paquete Python dentro de `venv\Lib\site-packages\prestashop_mcp\`.
7. El instalador crea los `.bat` y `README-INSTALACION.txt`.
8. El instalador lanza el asistente `setup` desde el Python del entorno virtual.
9. El asistente prueba la conexion y, si lo eliges, conecta Codex o Claude Desktop.

Los `.bat` creados sirven para:

1. `start-mcp.bat`: arrancar el MCP manualmente.
2. `setup-mcp.bat`: volver a configurar la conexion, la tienda o los clientes.
3. `update-mcp.bat`: actualizar el MCP desde GitHub.
4. `uninstall-mcp.bat`: desinstalar la carpeta local.

Si necesitas repetir la configuracion despues de instalar, ejecuta desde la carpeta elegida:

```powershell
.\setup-mcp.bat
```

### Opcion B: instalacion manual con pip

Usa esta opcion si no quieres usar el instalador asistido o si prefieres instalar el paquete directamente en un Python ya existente. Tampoco requiere Git si instalas desde el ZIP de GitHub.

Pasos:

1. Abre PowerShell.
2. Actualiza `pip`.
3. Instala el paquete desde el ZIP de GitHub.
4. Comprueba que el modulo carga.
5. Ejecuta el asistente de configuracion.

```powershell
py -m pip install --upgrade pip
py -m pip install "https://github.com/golfo161/prestashop-local-mcp/archive/refs/heads/main.zip"
py -m prestashop_mcp.cli --help
py -m prestashop_mcp.cli setup
```

El asistente de configuracion manual hara estos pasos:

1. Solicita la URL de la tienda PrestaShop.
2. Solicita la API key con entrada oculta.
3. Solicita el ID de regla fiscal para productos nuevos.
4. Guarda las credenciales y parametros locales en `%APPDATA%\prestashop-local-mcp\.env`.
5. Prueba la conexion con la API.
6. Pregunta si quieres conectar Codex en ChatGPT Desktop.
7. Si respondes que si, actualiza automaticamente `%USERPROFILE%\.codex\config.toml`.
8. Pregunta si quieres conectar Claude Desktop.
9. Si respondes que si, actualiza automaticamente `%APPDATA%\Claude\claude_desktop_config.json`.
10. Crea copias de seguridad de los ficheros de cliente si ya existian.

El asistente no copia la API key en Codex ni Claude Desktop. La clave solo queda en el fichero local `.env` del usuario.

En una instalacion manual, usa `py -m prestashop_mcp.cli ...` para ejecutar el MCP. Esta forma no depende de que la carpeta `Scripts` de Python este en el `PATH`, pero si depende de que el paquete este instalado en el Python que usa el lanzador `py`.

Equivalencias de comandos:

| Si ves este comando | En Windows ejecuta este |
| --- | --- |
| `prestashop-local-mcp --help` | `py -m prestashop_mcp.cli --help` |
| `prestashop-local-mcp setup` | `py -m prestashop_mcp.cli setup` |
| `prestashop-local-mcp install-codex` | `py -m prestashop_mcp.cli install-codex` |
| `prestashop-local-mcp install-claude` | `py -m prestashop_mcp.cli install-claude` |

El comando publicado por este proyecto es `prestashop-local-mcp`. Tambien puedes usar `py -m prestashop_mcp.cli ...`, que suele ser mas fiable en Windows.

Si ya has ejecutado `setup` y solo quieres reinstalar la conexion con un cliente:

```powershell
py -m prestashop_mcp.cli install-codex
py -m prestashop_mcp.cli install-claude
```

### Instalacion manual alternativa con Git

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
pip install -e ".[dev]"
```

Si PowerShell no permite activar el entorno virtual, puedes ejecutar el modulo con el Python del entorno virtual sin activar nada.

Comprueba que el paquete carga:

```powershell
py -c "import prestashop_mcp; print('Installation successful')"
```

## 6. Crear el fichero de configuracion `.env`

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

Si el fichero `.env` ya existe, el asistente pregunta que quieres hacer antes de pedir nuevas credenciales:

- `overwrite`: sobrescribe el `.env` con una URL y API key nuevas.
- `omit`: conserva el `.env` actual y continua con el resto del asistente.
- `cancel`: cancela el asistente sin cambiar nada.

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
PRESTASHOP_TAX_RULES_GROUP_ID=1
LOG_LEVEL=INFO
```

Ejemplo:

```env
PRESTASHOP_SHOP_URL=https://ovillos.com
PRESTASHOP_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
PRESTASHOP_TAX_RULES_GROUP_ID=1
LOG_LEVEL=INFO
```

## 7. Probar la API directamente

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

## 8. Ejecutar el MCP local por primera vez

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
Starting PrestaShop Local MCP server...
Server ready
```

Para detenerlo, pulsa `Ctrl+C`.

Nota: si usas Codex o Claude Desktop, normalmente no tienes que dejar este comando abierto. El cliente arrancara el MCP automaticamente cuando lea su fichero de configuracion.

## 9. Configurar ChatGPT Desktop con Codex

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

## 10. Configurar Claude Desktop

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

## 11. Buscar productos por categoria real

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

## 12. ChatGPT Apps y MCP remoto

ChatGPT Apps no se conecta directamente a servidores MCP locales `stdio`. Para usar este MCP como app de ChatGPT fuera de Codex, debes exponerlo como servidor MCP remoto o usar Secure MCP Tunnel.

Resumen:

- Codex en ChatGPT Desktop: usa `C:\Users\TU_USUARIO\.codex\config.toml`.
- Claude Desktop: usa `C:\Users\TU_USUARIO\AppData\Roaming\Claude\claude_desktop_config.json`.
- ChatGPT Apps: requiere MCP remoto o Secure MCP Tunnel.

## 13. Actualizaciones y reconexion

Si modificas ficheros del modulo, reinicia el cliente para que vuelva a cargar el servidor MCP.

Reinicia especialmente si cambias:

- `src/prestashop_mcp/prestashop_mcp_server.py`
- definiciones de herramientas
- nombres de herramientas
- parametros de herramientas
- permisos o configuracion del cliente MCP

En Codex o Claude Desktop, lo normal es cerrar y volver a abrir el cliente o iniciar una nueva tarea/conversacion.

En ChatGPT Apps/MCP remoto, los cambios de herramientas no se aplican automaticamente. Hay que refrescar o escanear herramientas otra vez. Si la app ya esta publicada en un workspace, un administrador debe revisar y publicar la actualizacion. En planes Business, puede ser necesario recrear y republicar la app.

## 14. Comandos utiles

En una instalacion asistida, usa los `.bat` creados dentro de la carpeta elegida. En una instalacion manual con `pip`, usa `py -m prestashop_mcp.cli ...`. El comando `prestashop-local-mcp ...` solo funciona si la carpeta `Scripts` de Python esta en el `PATH`.

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
.\venv_prestashop\Scripts\python.exe -m pytest tests\test_config.py tests\test_prestashop_client.py tests\test_cli.py tests\test_windows_installer.py
```

## 15. Seguridad

- No subas `.env` a Git.
- Usa una clave de Webservice con los permisos minimos necesarios.
- Empieza con permisos `GET` y amplia solo cuando necesites escribir.
- Revisa las acciones de escritura antes de aprobarlas desde el cliente.
- Haz copia de seguridad de la tienda antes de probar acciones masivas.

## 16. Referencias y creditos

- Repositorio del proyecto: https://github.com/golfo161/prestashop-local-mcp
- Basado originalmente en: https://github.com/latinogino/prestashop-mcp
- Documentacion de PrestaShop Webservice: https://devdocs.prestashop-project.org/
- OpenAI Help: Developer mode and MCP apps in ChatGPT: https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt
