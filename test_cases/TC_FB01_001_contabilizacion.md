# Especificación de Caso de Prueba: Contabilización en FB01 y Visualización en FB03

## 1. Metadatos del Caso
- **ID del Caso (`test_id`)**: `FB01_001`
- **Nombre de la Función Pytest**: `test_FB01_001_contabilizacion_y_visualizacion`
- **Transacciones SAP (`T-Codes`)**: `FB01`, `FB03`
- **Módulo SAP**: `FI (Finanzas)`
- **Objetivo**: Contabilizar un documento financiero de cuentas de mayor en la transacción `FB01` (con posición Debe 40 con centro de costo y posición Haber 50) y verificar la generación del número de documento contable en la barra de estado y su consulta en `FB03`.

---

## 2. Precondiciones
- Sesión disponible en SAP GUI (`SAP_MODE=login` o `attach`).
- Periodo contable abierto para la sociedad `110`.

---

## 3. Insumos / Datos de Prueba
| Parámetro Funcional | Valor de Referencia | ¿Parametrizar en `.env`? | Variable en `Config` |
| :--- | :--- | :---: | :--- |
| Fecha de documento | `14.10.2026` | No | - |
| Clase de documento | `SA` | No | - |
| Sociedad | `110` | No | - |
| Fecha de contabilización | `14.10.2026` | No | - |
| Moneda | `MXP` | No | - |
| Clave contab. 1 (Debe) | `40` | No | - |
| Cuenta mayor 1 (Debe) | `51000271` | Sí | `FB01_CUENTA_1` |
| Importe Debe | `100` | No | - |
| Indicador de impuestos | `E0` | No | - |
| Centro de coste | `2100004004` | Sí | `FB01_CENTRO_COSTO` |
| Clave contab. 2 (Haber) | `50` | No | - |
| Cuenta mayor 2 (Haber) | `22570009` | Sí | `FB01_SIG_CUENTA` |
| Importe Haber | `100` | No | - |

---

## 4. Flujo Paso a Paso por Pantalla

### Pantalla 1: Cabecera de Documento y Primera Posición (`FB01`)
1. Abrir la transacción `FB01`.
2. Completar los datos de cabecera (`BKPF`):
   - **Fecha de documento** (`BKPF-BLDAT`): `14.10.2026`
   - **Clase de documento** (`BKPF-BLART`): `SA`
   - **Sociedad** (`BKPF-BUKRS`): `110`
   - **Fecha de contabilización** (`BKPF-BUDAT`): `14.10.2026`
   - **Moneda/Tasa** (`BKPF-WAERS`): `MXP`
3. En el pie de página (Primera posición `RF05A`):
   - **ClvCT** (`RF05A-NEWBS`): `40`
   - **Cuenta** (`RF05A-NEWKO`): Valor de `Config.FB01_CUENTA_1` (`51000271`)
4. Presionar **`Enter`** para avanzar al detalle de la primera posición.

### Pantalla 2: Detalle Posición 1 (Debe 40) y preparación de Posición 2 (`FB01`)
1. Completar el detalle del cargo (`BSEG` / `COBL`):
   - **Importe** (`BSEG-WRBTR`): `100`
   - **Indicador de impuestos** (`BSEG-MWSKZ`): `E0`
   - **Centro de coste** (`COBL-KOSTL`, ubicado en subscreen dinámico `SAPLKACB`): Valor de `Config.FB01_CENTRO_COSTO` (`2100004004`)
2. En la sección de siguiente posición (`RF05A`):
   - **ClvCT** (`RF05A-NEWBS`): `50`
   - **Cuenta** (`RF05A-NEWKO`): Valor de `Config.FB01_SIG_CUENTA` (`22570009`)
3. Presionar **`Enter`** para avanzar al detalle de la segunda posición.

### Pantalla 3: Detalle Posición 2 (Haber 50) y Resumen (`FB01`)
1. Ingresar el **Importe** (`BSEG-WRBTR`): `100`.
2. Hacer clic en el botón **Resumen de documento** (`wnd[0]/tbar[1]/btn[14]` o comando `=AB`).
3. Hacer clic en **Guardar / Contabilizar** (`wnd[0]/tbar[0]/btn[11]`).

---

## 5. Validaciones y Resultado Esperado
- **Validación en Barra de Estado (`wnd[0]/sbar`)**:
  - El mensaje en la barra de estado debe contener `"se contabilizó"`.
  - Extraer el número de documento generado hacia el buffer `NumDocContable` y validar con `assert num_doc`.
- **Resultado Esperado (para `data/expected_result.csv`)**:
  > "El documento se contabiliza en la sociedad 110 (mensaje 'Doc.XXXXXXXXX se contabilizó en sociedad 110') y en FB03 se muestran los documentos en Finanzas: Documento contable, Doc.ctro.beneficios, Documento CO y Consolidación."

