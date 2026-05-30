# AI Extraction Pipeline

Documents flow through a 5-stage extraction pipeline that validates input, calls OpenAI, and persists results.

## Pipeline Flow

1. **Validate**: Check file type, size, and magic bytes
2. **Create**: Insert document row in DB (status = `PENDING`)
3. **Mark Processing**: Update status to `PROCESSING`
4. **OpenAI Call**: Send file to OpenAI API with Structured Outputs (gpt-4o-mini)
5. **Persist**: Store extracted JSON or error logs; update status to `EXTRACTED` or `FAILED`

## Why Structured Outputs?

The Pydantic schema `ExtractedLogisticsData` is passed directly to OpenAI as the response format. This ensures type-safe extraction without manual JSON parsing.

```python
class ExtractedLogisticsData(BaseModel):
    origen: str
    destino: str
    patente_camion: Optional[str]
    fecha_despacho: str
    items: list[dict]  # [{"sku": "001", "cantidad": 100}, ...]
```

## Failure Handling

- **Bad file**: 400/413 error, document not created
- **Missing API key**: Document stays `PENDING` with error note  
- **Extraction error**: Document becomes `FAILED`
- **Success**: Document becomes `EXTRACTED`, JSON stored
