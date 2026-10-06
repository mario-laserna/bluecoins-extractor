# Bluecoins Extractor

Herramienta para leer y extraer transacciones de los archivos de copia de seguridad generados por la aplicación móvil **Bluecoins**.

---

## 🔍 ¿Cómo funcionan los archivos de Bluecoins?

Los archivos con extensión `.fydb` (como `bluecoins.fydb`) son en realidad **bases de datos estándar SQLite 3**.

### Estructura principal de la base de datos:
* **`TRANSACTIONSTABLE`**: Contiene el registro de todas las transacciones (ingresos, gastos, transferencias y balances iniciales).
  * Los montos (`amount`) se almacenan como enteros multiplicados por un factor de **1,000,000** (por ejemplo, `$1,000 COP` se almacena como `1000000000`).
  * El campo `deletedTransaction` indica si el registro está activo (`6`) o en la papelera/eliminado (`5`). El extractor filtra automáticamente solo los registros activos (`6`).
* **`ITEMTABLE`**: Nombres o conceptos de las transacciones (ej. *comida*, *pago colegio*).
* **`CHILDCATEGORYTABLE` & `PARENTCATEGORYTABLE`**: Jerarquía de categorías y subcategorías.
* **`ACCOUNTSTABLE` & `ACCOUNTTYPETABLE`**: Información sobre cuentas (bancos, tarjetas de crédito, efectivo, pasivos) y sus tipos.
* **`LABELSTABLE`**: Etiquetas asignadas a cada transacción.

---

## 🚀 Requisitos

* **Python 3** (viene preinstalado en macOS/Linux).
* **Sin dependencias externas**: Utiliza únicamente las librerías nativas `sqlite3`, `csv` y `argparse`.

---

## 💻 Uso del Script

### 1. Ejecución rápida por defecto
El script busca automáticamente el archivo `.fydb` en la carpeta `backups/` y genera `transacciones_bluecoins.csv`:

```bash
python3 extractor.py
```

### 2. Opciones avanzadas

* **Especificar archivo de entrada:**
  ```bash
  python3 extractor.py -i backups/bluecoins.fydb
  ```

* **Especificar nombre del archivo CSV de salida:**
  ```bash
  python3 extractor.py -o mis_gastos.csv
  ```

---

## 📊 Columnas del CSV generado

| Columna | Descripción |
|---|---|
| `id` | Identificador único de la transacción en Bluecoins |
| `date` | Fecha y hora de la transacción (`YYYY-MM-DD HH:MM:SS`) |
| `type` | Tipo (`Gastos`, `Ingresos`, `Transferir`, `Nueva cuenta`) |
| `title` | Concepto o título de la transacción |
| `amount` | Monto real en moneda original (dividido por 1,000,000) |
| `currency` | Código de moneda (ej. COP, USD) |
| `conversion_rate` | Tasa de conversión de divisa |
| `parent_category` | Categoría principal |
| `category` | Subcategoría |
| `account_type` | Tipo de cuenta (Tarjeta de Crédito, Banco, etc.) |
| `account` | Cuenta asociada |
| `transfer_pair_account` | Cuenta destino/origen (para transferencias) |
| `status` | Estado (`Reconciled`, `Cleared`, `Uncleared`) |
| `labels` | Etiquetas asociadas |
| `notes` | Notas de la transacción (máximo los primeros 15 caracteres) |
