---
name: e2e-git-pr-workflow
description: Standardized Git commit, staging, branch management, and Pull Request (PR) template generation workflow for test automation projects. Use after completing, refactoring, or verifying any testcase or module change.
---

# E2E Git & Pull Request (PR) Workflow Skill

This skill defines the mandatory control flow for staging code changes, creating standardized Git commits under **Conventional Commits**, and generating clean, professional Pull Request (PR) documentation.

---

## 1. Conventional Commits Specification

All commit messages must strictly follow the format:

```text
<tipo>(<alcance>): <descripción corta en minúsculas y en español>
```

### Supported Types:
| Type | Purpose | Example |
| :--- | :--- | :--- |
| `feat` | New test cases or new action module features | `feat(pao_sistema_34): agregar test case 34 para validacion de BTN_SOMS` |
| `fix` | Bug fixes in locators, assertions, or test logic | `fix(locators): corregir selector de BTN_ACTIONS en home_locators` |
| `refactor` | Code restructuring without changing external behavior | `refactor(search_module): optimizar espera explicita en busqueda` |
| `docs` | Documentation updates (`README.md`, `expected_result.csv`, skills) | `docs(expected_result): actualizar resultado esperado de TC_032` |
| `style` | Formatting, linting, or whitespace adjustments | `style(test_pao_02): corregir espaciado e imports` |
| `test` | Adding unit tests or test framework configurations | `test(pytest): actualizar opciones en pytest.ini` |

---

## 2. Automated Git Execution Workflow

Immediately after generating or modifying any test case or module file and verifying syntax cleanliness:

1. **Inspect status**:
   ```bash
   git status --short
   ```
2. **Stage modified/created files**:
   ```bash
   git add .
   ```
3. **Commit with Conventional Commit message**:
   ```bash
   git commit -m "feat(SAP): implementar TC_032 para validacion de editar cliente y acciones"
   ```
4. **Push to remote branch (if required)**:
   ```bash
   git push origin <nombre_rama>
   ```

---

## 3. Pull Request (PR) Template Generator

After completing the commit, automatically generate and display a formatted PR template in GitHub Flavored Markdown:

```markdown
### **Título del PR**
`feat(<modulo>): <resumen corto en español>`

---

### **Descripción del PR**

## 📌 Descripción
<Breve explicación del objetivo del cambio y los casos de prueba impactados>

---

## 🛠️ Cambios Realizados

### 1. **Test Cases (`tests/<AppName>/`)**
- `<Archivo test_*.py>`: <Detalle de los pasos y validaciones agregadas o modificadas>

### 2. **Módulos de Acción & Localizadores (`apps/<AppName>/`)**
- `<Archivo module.py / locators.py>`: <Detalle de las funciones y selectores agregados>

### 3. **Datos & Documentación**
- `expected_result.csv`: <Actualización de resultados esperados>
- `README.md / SKILL.md`: <Actualización de documentación>

---

## 🧪 Verificación

Para ejecutar y probar únicamente los casos modificados:

```bash
pytest tests/<AppName>/test_<feature>.py -v
```
```
