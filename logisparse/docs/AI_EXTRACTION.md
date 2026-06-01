# AI Extraction Pipeline

The extractor is hybrid: deterministic parsing first, AI only when useful. This keeps common documents fast and makes OpenAI a fallback instead of the only path.

```mermaid
flowchart TD
    A["Validated file bytes"] --> B{"Content type"}
    B -- "application/pdf" --> C["pdfplumber text extraction"]
    B -- "image/png or image/jpeg" --> D["Tesseract OCR"]
    C --> E["Plain text"]
    D --> E
    E --> F["Regex extraction"]
    F --> G["origen, destino, patente, chofer, fecha, guia, items"]
    G --> H{"Missing fields<br/>or confidence < 0.7?"}
    H -- "No" --> I["Build Pydantic schema"]
    H -- "Yes" --> J["OpenAI Structured Outputs"]
    J --> K["Merge results<br/>regex wins over AI"]
    I --> L["ExtractedLogisticsData"]
    K --> L
```

## Output Contract

The service returns `ExtractedLogisticsData`:

| Field | Meaning |
| --- | --- |
| `origen` | Dispatch origin |
| `destino` | Dispatch destination |
| `patente_camion` | Truck plate |
| `chofer` | Driver name |
| `fecha_despacho` | Dispatch date in `YYYY-MM-DD` |
| `numero_guia` | Dispatch guide number |
| `items` | Cargo line items |
| `observaciones` | Extra notes when detected |

## Failure Shape

- Upload validation errors return HTTP `400` or `413` before creating a document.
- Extraction `ValueError` marks the document as `FAILED` with the controlled error.
- Unexpected extraction exceptions are logged and stored as a generic `FAILED` result.
- Successful extraction stores JSON in `documents.extracted_data`.
