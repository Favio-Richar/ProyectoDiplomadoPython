from pathlib import Path

import pandas as pd


def main():
    """Lee pedidos e ítems y genera un inventario básico."""
    raiz = Path(__file__).resolve().parents[1]
    carpeta_datos = raiz / "data" / "raw"
    carpeta_reportes = raiz / "reports"

    archivos = {
        "orders": "olist_orders_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
    }

    claves ={
        "orders": ["order_id"],
        "order_items": ["order_id", "order_item_id"],
     }
    
    resumen = []
    detalle_columnas = []
    tablas = {}

    for tabla, nombre_archivo in archivos.items():
        datos = pd.read_csv(carpeta_datos / nombre_archivo)
        tablas[tabla] = datos

        columnas_clave =claves[tabla]
        columnas_faltantes = [
            columna for columna in columnas_clave 
            if columna not in datos.columns
        ]

        if columnas_faltantes:
            raise ValueError(
                f"{tabla}: faltan columnas clave: {columnas_faltantes}"
            )

        resumen.append({
            "tabla": tabla,
            "filas": len(datos),
            "columnas": len(datos.columns),
            "celdas_nulas": int(datos.isna().sum().sum()),
            "filas_duplicadas": int(datos.duplicated().sum()),
            "clave": " + ".join(columnas_clave),
            "filas_clave_nula":int(
                datos[columnas_clave].isna().any(axis=1).sum()
            ),
            "duplicados_clave": int(
                datos.duplicated(subset=columnas_clave).sum()
            ),     
        })

        print(f"\nTabla: {tabla}")
        print(f"Columnas: {', '.join(datos.columns)}")

        for columna in datos.columns:
            detalle_columnas.append({
                "tabla": tabla,
                "columna": columna,
                "tipo_detectado": str(datos[columna].dtype),
                "celdas_nulas": int(datos[columna].isna().sum()),
                "porcentaje_nulos": round(
                    datos[columna].isna().mean() * 100, 2
                ),
            })

    reporte = pd.DataFrame(resumen)

    carpeta_reportes.mkdir(parents=True, exist_ok=True)
    salida = carpeta_reportes / "inventario_inicial.csv"
    reporte.to_csv(salida, index=False)
    detalle = pd.DataFrame(detalle_columnas)
    salida_detalle = carpeta_reportes / "calidad_por_columna.csv"
    detalle.to_csv(salida_detalle, index=False)

    print("\nCalidad por columna:")
    print(detalle.to_string(index=False))
    print(f"\nDetalle guardado en: {salida_detalle}")

    print("\nInventario:")
    print(reporte.to_string(index=False))
    print(f"\nReporte guardado en: {salida}")


    pedidos = tablas["orders"]
    items = tablas["order_items"]

    pedidos_sin_items = int(
        (~pedidos["order_id"].isin(items["order_id"])).sum()
    )

    items_sin_pedido = int(
        (~items["order_id"].isin(pedidos["order_id"])).sum()
    )

    relacion = pd.DataFrame([{
        "pedidos_totales": len(pedidos),
        "pedidos_sin_items": pedidos_sin_items,
        "items_totales": len(items),
        "items_sin_pedido": items_sin_pedido,
    }])

    salida_relacion = carpeta_reportes / "relacion_pedidos_items.csv"
    relacion.to_csv(salida_relacion, index=False)

    print("\nRelacion entre pedidos e items:")
    print(relacion.to_string(index=False))
    print(f"\nRelacion guardada en: {salida_relacion}")

    resumen_estados = (
    pedidos["order_status"]
    .value_counts(dropna=False)
    .rename_axis("estado")
    .reset_index(name="cantidad_pedidos")
    )

    resumen_estados["porcentaje"] = (
        resumen_estados["cantidad_pedidos"] / len(pedidos) * 100
    ).round(2)

    salida_estados = carpeta_reportes / "resumen_pedidos_estado.csv"
    resumen_estados.to_csv(salida_estados, index=False)
    print("\nResumen de pedidos por estado:")
    print(resumen_estados.to_string(index=False))
    print(f"\nResumen guardado en: {salida_estados}")
    


if __name__ == "__main__":
    main()