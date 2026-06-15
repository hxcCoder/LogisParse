<div align="center">

# 📦 LogisParse

**Automatización Inteligente de Documentos Logísticos**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Desafío Crea](https://img.shields.io/badge/Desafío_Crea-INACAP_2026-red.svg)]()
[![CI](https://github.com/hxcCoder/LogisParse/actions/workflows/ci.yml/badge.svg)](https://github.com/hxcCoder/LogisParse/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/hxcCoder/LogisParse/branch/main/graph/badge.svg)](https://codecov.io/gh/hxcCoder/LogisParse)

> Transformando PDFs y fotografías en datos estructurados accionables para la industria del transporte y la logística mediante Inteligencia Artificial.

</div>

---

## 📑 Resumen Ejecutivo

**LogisParse** es una plataforma SaaS orientada al backend que elimina el ingreso manual de datos en las operaciones logísticas. Mediante el uso de modelos de lenguaje e IA estructurada (OpenAI Structured Outputs), la plataforma extrae, normaliza y valida información crítica desde guías de despacho, facturas y manifiestos de carga en segundos. 

El sistema está diseñado con una filosofía de bajo costo operativo y alta escalabilidad, apuntando a digitalizar a las pequeñas y medianas empresas (pymes) logísticas de Chile y Latinoamérica.

---

## ⚠️ El Problema: El Cuello de Botella Operativo

A pesar de los avances tecnológicos, gran parte de la industria logística sigue dependiendo de procesos manuales y análogos:

* **Ingreso Manual:** Los operadores dedican horas leyendo PDFs o fotos de documentos para transcribir datos (SKUs, patentes, fechas, destinos) a un Excel o ERP.
* **Errores Humanos:** La digitación manual genera discrepancias en inventarios, fechas de entrega y facturación.
* **Sistemas OCR Tradicionales:** Las tecnologías antiguas de reconocimiento óptico de caracteres son rígidas, fallan con formatos irregulares y requieren constante corrección humana.
* **Pérdida de Tiempo:** El flujo logístico se retrasa en la etapa de administración, restando agilidad a la cadena de suministro.

---

## 💡 La Solución: Extracción Semántica Estructurada

LogisParse no solo "lee" el texto, sino que **entiende el contexto** del documento. 

Las empresas solo deben cargar sus documentos (PDF o imagen) y el motor de LogisParse devuelve la información estructurada, limpia y lista para ser integrada en cualquier sistema mediante nuestra API.

### 📊 Comparativa de Modelos Operativos

| Característica | Proceso Tradicional / OCR Clásico | Plataforma LogisParse |
| :--- | :--- | :--- |
| **Tiempo de Procesamiento** | Minutos por documento | Segundos por lote |
| **Flexibilidad de Formatos** | Nula (requiere plantillas fijas) | Alta (la IA entiende la semántica sin plantillas) |
| **Precisión de Datos** | Susceptible a errores de tipeo | Validación estricta automatizada |
| **Integración** | Manual o compleja | API RESTful estructurada en JSON |

---

## 🚀 Propuesta de Valor y Viabilidad Comercial

El proyecto fue concebido para ser un modelo de negocio altamente viable, evitando la complejidad innecesaria de infraestructura que encarece los costos iniciales:

* **Infraestructura Ligera:** Arquitectura lista para desplegarse en entornos accesibles (VPS, Railway, Render).
* **Costo-Eficiencia:** Al utilizar APIs estructuradas, el costo por procesamiento de documento se mantiene en fracciones de centavo, asegurando un amplio margen de rentabilidad para un modelo SaaS.
* **Foco en el Nicho:** Diseñado no como un ERP gigante, sino como una herramienta especializada y confiable que resuelve un dolor específico que las pymes logísticas enfrentan a diario.

---

## 🛠️ Innovación Técnica Principal

> **Nota:** Para revisar la arquitectura en profundidad, dependencias, diagramas de flujo y endpoints, dirígete a nuestro [**README_TECH.md**](./README_TECH.md).

El núcleo innovador de LogisParse reside en:

1. **AI Structured Outputs:** En lugar de depender de IA generativa impredecible, LogisParse fuerza a los modelos a responder en esquemas JSON estrictos (usando *Pydantic*). Esto garantiza que, por ejemplo, un campo numérico como "cantidad" jamás contenga texto.
2. **Trazabilidad Absoluta:** Cada procesamiento cuenta con un ID de seguimiento único y control de estados en tiempo real (`PENDING`, `PROCESSING`, `EXTRACTED`, `FAILED`), brindando seguridad y auditoría a las empresas.

---

## 👥 Sobre el Autor

Proyecto desarrollado por **hxcCoder** para el **Desafío Crea INACAP 2026 (Categoría Estudiantes)**.

Nacido en Puerto Montt, Región de Los Lagos, LogisParse observa las necesidades de automatización en las cadenas de suministro de industrias clave del sur de Chile, proyectando una solución escalable y tecnológica de estándar internacional.
