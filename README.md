<div align="center">

# 📦 LogisParse

**Automatización Inteligente de Documentos Logísticos**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Desafío Crea](https://img.shields.io/badge/Desafío_Crea-INACAP_2026-red.svg)]()
[![codecov](https://codecov.io/gh/hxcCoder/LogisParse/branch/main/graph/badge.svg)](https://codecov.io/gh/hxcCoder/LogisParse)

> Transformando PDFs y fotografías en datos estructurados para la logística, con un sistema que aprende de cada corrección humana.

</div>

---

## Resumen

**LogisParse** es una plataforma SaaS que elimina el ingreso manual de datos en la logística. Extrae información clave desde guías de despacho, facturas y manifiestos mediante un motor híbrido (regex + IA), con validación semántica y un ciclo de aprendizaje continuo.

**Nuevo:** Integración opcional con **AWS Textract** para escaneo de alta precisión, mapeo automático de campos tributarios chilenos (RUT, folio SII, monto total), exportación directa a **Excel** y archivo automático en bandeja de procesados.

**Estado actual:** MVP funcional con adaptador para guías de despacho chilenas (formato SII), extracción de campos clave (origen, destino, patente, chofer, fecha, número de guía), sistema de confianza y corrección humana.

---

## El Problema

- **Ingreso manual** de datos desde PDFs y fotos → horas perdidas.
- **Errores de digitación** que afectan inventarios y facturación.
- **OCR tradicional** rígido, sin adaptabilidad a nuevos formatos.
- **No aprenden** de los errores; cada corrección se repite.

---

## 💡 La Solución

**Extracción semántica estructurada + aprendizaje continuo.**

- **Clasifica** el documento y usa un adaptador específico (ej. Starken) con regex afinados.
- Si la confianza es baja, **fallback a IA** (OpenAI) para inferir datos faltantes.
- **Valida** cada campo contra patrones (ciudades, patentes, fechas, RUT).
- Si la confianza < 80%, se deriva a **revisión humana** (`NEEDS_REVIEW`).
- **Cada corrección humana** se guarda y se usa como ejemplo (few-shot) en futuras extracciones.
- **Escaneo avanzado** con AWS Textract (opcional) para extraer tablas y formularios con precisión.
- **Exportación instantánea** a Excel (.xlsx) y archivo automático del documento original en `/procesados`.

---

## 📊 Comparativa Rápida

| Característica | Tradicional | LogisParse |
| :--- | :--- | :--- |
| **Tiempo** | Minutos | Segundos |
| **Formatos** | Fijos | Flexibles (adaptadores + IA) |
| **Precisión** | Baja | Alta + validación semántica + Textract |
| **Aprendizaje** | No | Sí (continuo con correcciones) |
| **Integración** | Manual | API REST JSON + Frontend Next.js |
| **Salida de datos** | PDF/Imagen | JSON + Excel automático |

---

## Propuesta de Valor

- **Infraestructura ligera** (VPS, Railway, Render).
- **Costo-eficiente**: regex es gratis, IA solo cuando se necesita.
- **Foco en pymes logísticas**: resuelve un dolor específico sin complejidad innecesaria.
- **Mejora continua**: el sistema se vuelve más preciso con cada corrección humana.
- **Frontend moderno**: construido con Next.js 14, TailwindCSS, diseño limpio (inspirado en Stripe/Linear).
- **Listo para cumplimiento tributario**: captura automática de RUT emisor/receptor, folio electrónico SII y monto total.

---

## Innovación Técnica

1.  **Arquitectura de adaptadores**: cada tipo de documento tiene su propia lógica de extracción (regex + reglas de negocio). Actualmente soporta:
    *   `StarkenAdapter` (documentos de Starken/Turbus)
    *   `ChileanGuiaAdapter` (guías de despacho chilenas formato SII)
    *   `GenericLLMAdapter` (fallback con IA para formatos desconocidos)
2.  **AI Structured Outputs + Few‑Shot**: la IA responde en JSON estricto (Pydantic) y usa correcciones previas como contexto en el prompt.
3.  **Sistema de confianza y auditoría**: puntaje de confianza (0‑100) calculado según campos extraídos. Si `< 80`, el documento pasa a `NEEDS_REVIEW` para revisión manual.
4.  **Trazabilidad completa**: cada documento tiene un ID único, estado, registro de errores y campo `extracted_data` con el JSON extraído.
5.  **Aprendizaje continuo**: tabla `data_corrections` que registra cada corrección humana (campo, valor original, valor corregido, adaptador usado).
    *   Esta tabla se consulta para mejorar el prompt de la IA (few‑shot) y puede usarse en el futuro para reentrenar modelos o afinar regex.
6.  **Integración con AWS Textract** *(nuevo)*: escaneo de alta precisión con extracción de tablas y formularios. Si no está configurado, el sistema usa OCR local automáticamente.
7.  **Mapeo de datos SII** *(nuevo)*: extrae RUT emisor/receptor, folio electrónico SII, fecha de emisión y monto total desde el texto o desde las estructuras devueltas por Textract.
8.  **Exportación a Excel** *(nuevo)*: genera un archivo `.xlsx` profesional con todos los campos extraídos, listo para compartir o integrar con otros sistemas.
9.  **Bandeja limpia** *(nuevo)*: los archivos procesados se mueven automáticamente a `/procesados` organizados por fecha, conservando los originales para auditoría.
10. **Frontend funcional** (Next.js 14 + TypeScript):
    *   Registro/Login con JWT
    *   Dashboard con tarjetas de documentos y paginación
    *   Subida con drag & drop y pipeline visual (Recibido → OCR → IA → Validado)
    *   Detalle del documento con campos extraídos (incluyendo datos fiscales) y formulario de corrección
    *   Responsive y diseño moderno (TailwindCSS)

---

## 🔄 Flujo Completo (Backend + Frontend)

```mermaid
flowchart TD
    A[Usuario sube PDF/Imagen] --> B[Validación de archivo]
    B --> C{AWS Textract configurado?}
    C -->|Sí| D[Extracción con Textract: texto + tablas/forms]
    C -->|No| E[OCR local: pdfplumber / pytesseract]
    D --> F[Mapeo de campos SII: RUT, folio, monto, etc.]
    E --> F
    F --> G[Limpieza de texto + Clasificador: DocumentClassifier]
    G --> H{Adaptador Específico?}
    H -->|Sí| I[Adaptador Regex]
    H -->|No| J[IA Genérica]
    I --> K[Validación Semántica + fusión de datos SII]
    J --> K
    K --> L[Cálculo de Confianza]
    L --> M{Confianza ≥ 80?}
    M -->|Sí| N[Estado EXTRACTED]
    M -->|No| O[Estado NEEDS_REVIEW]
    O --> P[Usuario corrige desde frontend]
    P --> Q[Guardar corrección en data_corrections]
    Q --> R[Reintentar extracción con contexto]
    N --> S[Generar Excel (.xlsx)]
    S --> T[Mover archivo original a /procesados]
    T --> U[Respuesta JSON + Excel disponible]
```
## 📁 Estructura del Proyecto
```plaintext
logisparse/
├── app/                         # Backend FastAPI
│   ├── api/                     # Endpoints REST
│   │   ├── deps.py              # Inyección de dependencias
│   │   └── v1/                  # Versión 1 de la API
│   ├── core/                    # Configuración, seguridad, logging
│   ├── crud/                    # Operaciones DB asíncronas
│   ├── models/                  # Modelos SQLAlchemy (User, Document, DataCorrection)
│   ├── schemas/                 # Schemas Pydantic
│   └── services/                # Lógica de negocio
│       ├── document_extractor.py # Orquestador principal
│       ├── aws_textract_service.py  # Integración AWS Textract (nuevo)
│       ├── sii_mapper.py        # Mapeo de campos SII chilenos (nuevo)
│       ├── excel_service.py     # Generación de Excel (nuevo)
│       ├── file_manager.py      # Manejo de bandeja limpia (nuevo)
│       └── extractors/           # Adaptadores de extracción
│           ├── adapter_factory.py
│           ├── base_adapter.py
│           ├── generic_llm_adapter.py
│           └── specific/
│               ├── starken_adapter.py
│               └── chilean_guia_adapter.py
├── frontend/                    # Frontend Next.js 14
│   └── src/
│       ├── app/                 # App Router (login, dashboard, upload, detail)
│       ├── components/          # Componentes reutilizables
│       ├── context/             # AuthContext
│       ├── lib/                 # API client (Axios)
│       └── types/               # Tipos TypeScript
├── migrations/                  # Migraciones Alembic
├── tests/                       # Pruebas unitarias e integración
├── .env.example                 # Variables de entorno (incluye AWS)
├── requirements.txt
└── README.md
```

# 🛠️ Desarrollo y Calidad

Para garantizar la estabilidad del motor de extracción, el proyecto cuenta con un entorno de pruebas automatizadas con cobertura total del código.

### Ejecutar Pruebas Locales
Si deseas replicar el entorno de pruebas y verificar la integridad de los validadores semánticos y adaptadores:

```bash
# Activar el entorno virtual e instalar dependencias de desarrollo
source .venv/bin/activate  # En Linux/macOS
.venv\Scripts\activate     # En Windows

# Ejecutar la suite de pruebas con reporte de cobertura
pytest --cov=app
```
---

## 👥 Autor

Proyecto desarrollado por **hxcCoder** para el **Desafío Crea INACAP 2026 (Categoría Estudiantes)**.

Nacido en Puerto Montt, Región de Los Lagos, LogisParse nace observando las necesidades de automatización en la cadena de suministro del sur de Chile, con visión de escalar a estándares internacionales.
