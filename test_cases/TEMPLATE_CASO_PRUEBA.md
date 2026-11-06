# Especificación de Caso de Prueba SAP

## 1. Metadatos del Caso
- **ID del Caso (`test_id`)**: `<TCODE>_<NNN>` (ej. `FB50_001`)
- **Nombre de la Función Pytest**: `test_<TCODE>_<NNN>_<descripcion_corta>`
- **Transacciones SAP (`T-Codes`)**: `<TCODE_PRINCIPAL>` (y secundarias si aplica, ej. `FB03`)
- **Módulo SAP**: `FI / CO / MM / SD`
- **Objetivo**: Breve descripción funcional de lo que valida el caso de prueba.

---

## 2. Precondiciones
- Sesión activa en SAP GUI o credenciales configuradas en `.env` (`SAP_MODE=login` o `attach`).
- Datos maestros vigentes en el mandante de pruebas (sociedad, cuentas de mayor, centros de costo).

---

## 3. Insumos / Datos de Prueba
| Parámetro Funcional | Valor de Referencia | ¿Parametrizar en `.env`? | Variable Sugerida en `Config` |
| :--- | :--- | :---: | :--- |
| Sociedad | `110` | No / Sí | ` <TCODE>_SOCIEDAD` |
| Cuenta Mayor 1 | `51000271` | Sí | `<TCODE>_CUENTA_1` |
| Centro de Costo | `2100004004` | Sí | `<TCODE>_CENTRO_COSTO` |

---

## 4. Flujo Paso a Paso por Pantalla

### Pantalla 1: `<Nombre de la pantalla / T-Code>`
1. Ejecutar transacción `<TCODE>`.
2. Ingresar en el campo **<Etiqueta en SAP>**: `<Valor>`.
3. Presionar la tecla **`Enter`** (o hacer clic en el botón **<Nombre Botón>**).

### Pantalla 2: `<Detalle de posición / Resumen>`
1. Ingresar en el campo **<Etiqueta en SAP>**: `<Valor>`.
2. Presionar el botón **Guardar / Contabilizar** (`Ctrl+S` / `btn[11]`).

---

## 5. Validaciones y Resultado Esperado
- **Validación en Barra de Estado (`wnd[0]/sbar`)**:
  - Tipo de mensaje esperado: `S` (Success).
  - Texto esperado contiene: `"se contabilizó"`.
  - Buffer a extraer: `NumDocContable` (parámetro 1 de la barra de estado).
- **Resultado Esperado (para `data/expected_result.csv`)**:
  > "<Texto descriptivo que aparecerá en la cortinilla de inicio y en el reporte HTML Liverpool enviado a Nexus>"

