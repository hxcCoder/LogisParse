<div align="center">

# 📦 LogisParse

**Automatización Inteligente de Documentos Logísticos**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Desafío Crea](https://img.shields.io/badge/Desafío_Crea-INACAP_2026-red.svg)]()
[![codecov](https://codecov.io/gh/hxcCoder/LogisParse/branch/main/graph/badge.svg)](https://codecov.io/gh/hxcCoder/LogisParse)

> Transformando PDFs y fotografías en datos estructurados para la logística, con un sistema que aprende de cada corrección humana.

</div>

---

## Resumen

**LogisParse** es una plataforma SaaS que elimina el ingreso manual de datos en la logística. Extrae información clave desde guías de despacho, facturas y manifiestos mediante un motor híbrido (regex + IA), con validación semántica y un ciclo de aprendizaje continuo.

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
- **Valida** cada campo contra patrones (ciudades, patentes, fechas).
- Si la confianza < 80%, se deriva a **revisión humana** (`NEEDS_REVIEW`).
- **Cada corrección humana** se guarda y se usa como ejemplo (few-shot) en futuras extracciones.

---

## 📊 Comparativa Rápida

| | Tradicional | LogisParse |
|:---|:---|:---|
| Tiempo | Minutos | Segundos |
| Formatos | Fijos | Flexibles |
| Precisión | Baja | Alta + validación |
| Aprendizaje | No | Sí (continuo) |
| Integración | Manual | API REST JSON |

---

## Propuesta de Valor

- **Infraestructura ligera** (VPS, Railway, Render).
- **Costo-eficiente**: regex es gratis, IA solo cuando se necesita.
- **Foco en pymes logísticas**: resuelve un dolor específico sin complejidad innecesaria.
- **Mejora continua**: el sistema se vuelve más preciso con cada corrección humana.

---

## Innovación Técnica

1. **Arquitectura de adaptadores**: cada tipo de documento tiene su lógica de extracción (regex + reglas de negocio).
2. **AI Structured Outputs + Few‑Shot**: la IA responde en JSON estricto (Pydantic) y usa correcciones previas como contexto.
3. **Sistema de confianza y auditoría**: puntaje de confianza (0‑100) y estado `NEEDS_REVIEW` para revisión manual.
4. **Trazabilidad completa**: cada documento tiene un ID único, estado y registro de correcciones.
5. **Aprendizaje continuo**: tabla `data_corrections` que alimenta el modelo sin intervención de desarrolladores.

---
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
