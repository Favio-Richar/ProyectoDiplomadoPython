# Indicadores del Dashboard 360

## Estado

Módulo `src/indicadores.py` implementado y ejecutado por el estudiante.
Codex revisó el código, el punto de entrada y las tablas SQLite en modo
de solo lectura. Este cierre corresponde al cálculo inicial de los cinco
indicadores, no al dashboard visual ni al proyecto completo.

## Ejecución y flujo

Desde Dashboard360, con el entorno activado:

```bash
python pipeline.py
```

El punto de entrada llama primero a `ejecutar_etl(raiz)` y después a
`generar_indicadores(raiz)`. No hace falta ejecutar la exploración.

Fuentes utilizadas en este paso: pedidos, ítems, reseñas, productos
y traducciones de categorías. La integración posterior de clientes,
pagos, vendedores y geolocalización está comprobada y documentada
en `05_contexto_nueve_tablas.md`.

## Reglas de cálculo

- Población: 96478 pedidos entregados.
- GMV: suma de precios de productos, sin flete; no representa utilidad.
- Ticket: GMV dividido por pedidos de la misma población.
- Satisfacción: primero media de reseñas por pedido, después media entre
  pedidos con reseña. Cada pedido evaluado tiene el mismo peso. Las
  puntuaciones nulas o fuera de 1 a 5 detienen el proceso.
- Entregas: comparación de días calendario, no horas, entre fecha real
  y estimada. Se requieren fechas presentes y no anteriores al día de
  compra. Los no evaluables se conservan sin clasificarlos como atrasados.
- Categorías: suma de precios de ítems de los mismos pedidos entregados.
  Se usa la traducción disponible; si falta, se conserva el nombre
  original. Productos sin categoría se agrupan como `sin_categoria`.
- La moneda sigue pendiente de confirmación documental.

## Integración y conservación de importes

Las reseñas se agregan por pedido antes del merge. Las fechas se unen
con `validate="one_to_one"`. Productos y categorías se unen a ítems
con `validate="many_to_one"`. Se exige que el GMV por categorías
coincida con el total comercial con tolerancia inferior a un centavo.

Los pedidos únicos por categoría no son aditivos: un pedido puede
contener varias categorías. El GMV y los ítems sí se pueden sumar.

## Salidas y evidencia

| Tabla nueva | Filas |
|---|---:|
| pedidos_dashboard | 96478 |
| ventas_categorias | 74 |
| kpis_generales | 1 |

Se verificaron cinco tablas en total y `PRAGMA integrity_check = ok`.
Los identificadores de pedidos_dashboard son únicos.

| Métrica | Resultado |
|---|---:|
| GMV sin flete | 13221498,11 |
| Flete | 2198275,64 |
| Ticket promedio | 137,04 |
| Satisfacción promedio | 4,16 sobre 5 |
| Pedidos con reseña | 95832 |
| Pedidos sin reseña | 646 |
| Entregas evaluables | 96470 |
| Entregas no evaluables | 8 |
| Entregas a tiempo | 89936 |
| Entregas a tiempo sobre evaluables | 93,23 % |

El GMV de las 74 categorías coincide con 13221498,11 y sus ítems
suman 110197, igual que la base comercial.
`sin_categoria` conserva 170726,63 de GMV y 1537 ítems.

Las cinco categorías de mayor GMV son health_beauty, watches_gifts,
bed_bath_table, sports_leisure y computers_accessories.

## Límites y pendientes

- El 93,23 % usa días calendario; no equivale a comparar timestamps.
- Un pedido entregado no implica que haya sido entregado a tiempo.
- El ticket global no es el promedio simple de los tickets mensuales.
- La repetición del pipeline ampliado quedó comprobada posteriormente
  para las ocho tablas resultantes; consultar `05_contexto_nueve_tablas.md`.
- Las tablas se reemplazan individualmente; falta publicación atómica
  de la base completa y tratamiento final de errores.
- Las cuatro fuentes restantes se integraron en el siguiente paso.
  Siguen pendientes dashboard visual, configuración, logging, pruebas
  y materiales de entrega.
