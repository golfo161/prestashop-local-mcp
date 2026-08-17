# Guia operativa para asistentes PrestaShop MCP

Este documento define como debe trabajar un asistente cuando usa este MCP para operar una tienda PrestaShop. No sustituye al `README.md`: el README explica instalacion, configuracion y herramientas; esta guia explica el flujo seguro de trabajo con productos, categorias y operaciones masivas.

## Principios generales

- Usa primero herramientas de lectura antes de ejecutar acciones que creen, modifiquen o borren datos.
- Resuelve nombres ambiguos antes de actuar. Si el usuario indica una categoria por nombre, busca su ID antes de crear o modificar productos.
- Para acciones de escritura, muestra el alcance de la accion y pide confirmacion cuando haya riesgo de crear, borrar o modificar muchos datos.
- Tras cada accion de escritura, verifica el resultado con una consulta fresca.
- Devuelve respuestas breves: que se ha hecho, sobre que IDs, y que se ha verificado.
- No inventes IDs, rutas de imagen, categorias, reglas fiscales ni stock. Consultalos o pide el dato si no se puede inferir con seguridad.

## Productos

### Alta de productos

Antes de llamar a `create_product`, el asistente debe mostrar una previsualizacion con:

- nombre final por idioma cuando aplique
- precio sin impuestos
- categoria o ID de categoria
- stock inicial
- referencia/SKU
- peso
- ruta de imagen
- resumen renderizado o contenido HTML basico
- SEO: meta title, meta description, meta keywords y URL amigable
- caracteristicas, si las hay

El producto solo se crea despues de confirmacion explicita del usuario.

Flujo recomendado:

1. Leer y normalizar la ficha recibida.
2. Resolver categoria por nombre si el usuario no aporta ID.
3. Verificar que la imagen local existe cuando se use `image_path`.
4. Preparar traducciones para espanol, ingles y frances si el usuario solo aporta texto en espanol.
5. Preparar resumen como HTML basico seguro: `p`, `strong`, `ul`, `li` o `br`.
6. Mostrar previsualizacion final.
7. Esperar confirmacion explicita.
8. Crear el producto.
9. Verificar producto creado, categoria, precio, imagen, stock y campos principales.

Notas:

- Los productos creados por este MCP pueden quedar desactivados inicialmente. Si el usuario quiere publicarlos, usa `update_product` con `active=true` despues de revisar la ficha.
- Si el stock inicial no queda reflejado en la respuesta resumida de categoria, verifica con la herramienta especifica de stock o actualiza con `update_product_stock`.
- Si se crean varios productos parecidos, usa referencias unicas para evitar colisiones.

### Modificacion de productos

Antes de modificar un producto, identifica claramente el producto afectado:

- por ID, si el usuario lo proporciona
- por referencia/SKU
- por nombre, usando lectura previa si hay ambiguedad
- por categoria, cuando sea una operacion masiva

Para modificaciones individuales, confirma cuando cambien campos sensibles:

- precio
- stock
- categoria
- estado activo
- imagen
- SEO
- descripcion
- borrado

Para modificaciones masivas:

1. Lista los productos afectados.
2. Muestra cantidad de productos e IDs.
3. Explica el cambio exacto.
4. Ejecuta solo cuando el usuario confirme o cuando su instruccion sea inequivoca.
5. Verifica con una lectura posterior.

Ejemplo: si el usuario pide "actualiza el precio de todos los productos de CAT-TEST a 80 euros sin impuestos", primero lista `CAT-TEST`, toma sus IDs, actualiza precio base a `80` y verifica que todos reflejan `80.000000`.

### Baja de productos

El borrado es irreversible desde el MCP. Antes de llamar a `delete_product`:

- lista el producto o productos afectados
- muestra IDs, nombres y referencias
- pide confirmacion explicita de borrado
- no borres por busquedas ambiguas

Cuando sea suficiente para el caso de uso, recomienda desactivar el producto con `update_product(active=false)` en lugar de borrarlo.

## Categorias y subcategorias

### Alta de categorias

Antes de crear una categoria:

- verifica si ya existe una categoria con ese nombre
- resuelve el ID de la categoria padre
- prepara URL amigable y SEO si el usuario no los aporta
- confirma nombre, padre, estado activo y SEO

Si la categoria debe aparecer en menu, crea o actualiza primero la categoria y despues usa las herramientas de menu correspondientes.

### Modificacion de categorias

Campos habituales:

- nombre
- descripcion
- categoria padre
- URL amigable
- meta title
- meta description
- meta keywords
- estado activo

Antes de mover una categoria a otro padre, confirma el cambio porque puede afectar navegacion, URLs y agrupacion de productos.

### Baja de categorias

Antes de borrar una categoria:

- consulta si tiene productos asociados
- consulta si tiene subcategorias
- muestra el alcance del borrado
- pide confirmacion explicita

Si hay productos o subcategorias, no borres sin una instruccion muy clara del usuario.

## SEO y traducciones

La tienda trabaja habitualmente con espanol, ingles y frances.

Si el usuario da contenido solo en espanol:

- conserva el espanol como fuente principal
- traduce nombre, resumen y SEO a ingles y frances cuando sea razonable
- genera `link_rewrite` limpio y diferente por idioma
- evita sobreoptimizar keywords

Meta description recomendada:

- clara y comercial
- sin relleno
- longitud razonable para buscadores
- incluir composicion, formato, uso o atributo principal si aplica

## Imagenes

Para subir imagenes:

- usa rutas locales absolutas
- verifica que el fichero existe antes de crear o actualizar
- informa si la ruta no existe o no es accesible
- despues de crear, revisa que PrestaShop devuelve `id_default_image` o asociacion de imagen

Ejemplo de ruta valida en Windows:

```text
C:\Users\usuario\Downloads\producto.jpg
```

## Stock y precios

Precio:

- interpreta "sin impuestos" como precio base de PrestaShop.
- usa `update_product_price` para cambios simples de precio.
- verifica despues con lectura de productos o categoria.

Stock:

- usa `update_product_stock` para fijar cantidad exacta.
- si un listado resumido muestra stock distinto, comprueba con una consulta especifica de producto/stock antes de concluir que el cambio fallo.

## Comprobaciones posteriores

Despues de crear o modificar productos, verifica al menos:

- ID de producto
- nombre
- precio
- categoria por defecto
- referencia
- peso, si se modifico
- imagen, si se subio
- SEO o resumen, si se modificaron
- stock, si se modifico

Despues de crear o modificar categorias, verifica al menos:

- ID de categoria
- nombre
- categoria padre
- estado activo
- URL amigable
- SEO, si se modifico

## Limitaciones conocidas

- Algunas respuestas resumidas de categoria pueden mostrar `quantity: 0` aunque `stock_available` se haya actualizado correctamente. Verifica el stock con una herramienta especifica cuando el stock sea importante.
- La regla fiscal se identifica por ID interno de PrestaShop, no por nombre visible del back office.
- Los permisos del Webservice determinan que operaciones funcionan. Para crear productos con imagen y stock hacen falta permisos sobre `products`, `images` y `stock_availables`.
- Los cambios de herramientas MCP pueden requerir reiniciar Codex, Claude Desktop o la conversacion para refrescar esquemas.

## Frase recomendada para usuarios

Cuando uses este MCP desde un asistente, puedes empezar con:

```text
Usa la guia docs/PRESTASHOP_OPERATIONS.md como protocolo operativo para trabajar con este MCP de PrestaShop.
```

Para acciones criticas, el asistente debe aplicar igualmente las reglas de seguridad descritas en las herramientas MCP aunque el usuario no mencione esta guia.
