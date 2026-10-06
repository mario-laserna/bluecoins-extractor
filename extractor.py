#!/usr/bin/env python3
"""
Bluecoins Backup Extractor
Lee los archivos de respaldo (.fydb) generados por Bluecoins y exporta las transacciones activas a CSV.
"""

import argparse
import csv
import os
import sqlite3
import sys
from pathlib import Path


def extract_bluecoins_data(db_path: str, output_csv: str):
    """Lee la base de datos de Bluecoins y exporta las transacciones activas a un archivo CSV."""
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"No se encontró el archivo de base de datos: {db_path}")

    # Conectar en modo solo lectura
    uri = f"file:{os.path.abspath(db_path)}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    cur = conn.cursor()

    # Excluir transacciones eliminadas (deletedTransaction = 5 son eliminadas, 6 son activas)
    query = """
    SELECT 
        t.transactionsTableID AS id,
        t.date AS date,
        COALESCE(tt.transactionTypeName, 'Otro') AS type,
        COALESCE(i.itemName, '') AS title,
        t.amount / 1000000.0 AS amount,
        COALESCE(t.transactionCurrency, '') AS currency,
        COALESCE(t.conversionRateNew, 1.0) AS conversion_rate,
        COALESCE(p.parentCategoryName, '') AS parent_category,
        COALESCE(c.childCategoryName, '') AS category,
        COALESCE(at.accountTypeName, '') AS account_type,
        COALESCE(a.accountName, '') AS account,
        CASE 
            WHEN t.transactionTypeID = 5 THEN COALESCE(ap.accountName, '') 
            ELSE '' 
        END AS transfer_pair_account,
        CASE t.status
            WHEN 2 THEN 'Reconciled'
            WHEN 1 THEN 'Cleared'
            ELSE 'Uncleared'
        END AS status,
        COALESCE(GROUP_CONCAT(DISTINCT l.labelName), '') AS labels,
        SUBSTR(COALESCE(t.notes, ''), 1, 15) AS notes
    FROM TRANSACTIONSTABLE t
    LEFT JOIN TRANSACTIONTYPETABLE tt ON t.transactionTypeID = tt.transactionTypeTableID
    LEFT JOIN ITEMTABLE i ON t.itemID = i.itemTableID
    LEFT JOIN CHILDCATEGORYTABLE c ON t.categoryID = c.categoryTableID
    LEFT JOIN PARENTCATEGORYTABLE p ON c.parentCategoryID = p.parentCategoryTableID
    LEFT JOIN ACCOUNTSTABLE a ON t.accountID = a.accountsTableID
    LEFT JOIN ACCOUNTTYPETABLE at ON a.accountTypeID = at.accountTypeTableID
    LEFT JOIN ACCOUNTSTABLE ap ON t.accountPairID = ap.accountsTableID
    LEFT JOIN LABELSTABLE l ON t.transactionsTableID = l.transactionIDLabels
    WHERE t.deletedTransaction = 6
    GROUP BY t.transactionsTableID
    ORDER BY t.date DESC
    """

    cur.execute(query)
    rows = cur.fetchall()
    headers = [
        "id",
        "date",
        "type",
        "title",
        "amount",
        "currency",
        "conversion_rate",
        "parent_category",
        "category",
        "account_type",
        "account",
        "transfer_pair_account",
        "status",
        "labels",
        "notes",
    ]

    # Escribir el CSV con codificación UTF-8 con BOM para compatibilidad con Excel
    with open(output_csv, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(rows)

    # Estadísticas resumidas
    print(f"==================================================")
    print(f" Resumen de extracción de Bluecoins")
    print(f"==================================================")
    print(f" Base de datos leída : {db_path}")
    print(f" Filas exportadas    : {len(rows):,}")
    print(f" Archivo CSV generado: {output_csv}")
    print(f" Transacciones elim. : Excluidas (deletedTransaction != 6)")

    # Mostrar desglose por tipo
    cur.execute(
        """
        SELECT COALESCE(tt.transactionTypeName, 'Otro'), COUNT(*), SUM(t.amount / 1000000.0)
        FROM TRANSACTIONSTABLE t
        LEFT JOIN TRANSACTIONTYPETABLE tt ON t.transactionTypeID = tt.transactionTypeTableID
        WHERE t.deletedTransaction = 6
        GROUP BY t.transactionTypeID
        """
    )
    summary_types = cur.fetchall()
    print("\n Desglose por tipo:")
    for type_name, count, total in summary_types:
        total_val = total if total is not None else 0.0
        print(f"  - {type_name:<15}: {count:>6} transacciones | Suma: {total_val:>14,.2f}")

    # Rango de fechas
    cur.execute(
        """
        SELECT MIN(date), MAX(date)
        FROM TRANSACTIONSTABLE t
        WHERE t.deletedTransaction = 6
        """
    )
    min_date, max_date = cur.fetchone()
    print(f"\n Rango de fechas     : {min_date}  -->  {max_date}")
    print(f"==================================================\n")

    conn.close()


def find_default_backup() -> str:
    """Busca automáticamente el archivo .fydb más reciente en la carpeta backups/."""
    candidates = list(Path("backups").glob("*.fydb"))
    if not candidates:
        # Buscar en el directorio actual
        candidates = list(Path(".").glob("*.fydb"))
    if candidates:
        # Retornar el más recientemente modificado
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return str(candidates[0])
    return "backups/bluecoins.fydb"


def main():
    parser = argparse.ArgumentParser(
        description="Extrae transacciones activas de respaldos Bluecoins (.fydb) a un archivo CSV."
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input_file",
        default=None,
        help="Ruta al archivo .fydb (por defecto busca en la carpeta backups/).",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        default="transacciones_bluecoins.csv",
        help="Nombre/ruta del archivo CSV de salida (por defecto: transacciones_bluecoins.csv).",
    )

    args = parser.parse_args()

    input_file = args.input_file or find_default_backup()

    try:
        extract_bluecoins_data(
            db_path=input_file,
            output_csv=args.output_file,
        )
    except Exception as e:
        print(f"Error al procesar el archivo: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
