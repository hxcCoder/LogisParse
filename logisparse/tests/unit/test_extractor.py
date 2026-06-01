from app.services.document_extractor import missing_fields, run_regex, to_schema


def test_run_regex_full_document():
    text = """
    Origen: Puerto Montt
    Destino: Santiago
    Chofer: Juan Perez
    Patente: AB1234
    Guía: 123456
    10 kg Salmon Atlantico
    5 cajas hielo
    """

    r = run_regex(text)

    assert r.origen == "Puerto Montt"
    assert r.destino == "Santiago"
    assert r.chofer == "Juan Perez"
    assert r.patente == "AB1234"
    assert r.guia == "123456"

    assert r.items is not None
    assert len(r.items) >= 1


def test_run_regex_partial_document():
    text = "Origen: Puerto Montt"

    r = run_regex(text)
    missing = missing_fields(r)

    assert "destino" in missing
    assert "chofer" in missing
    assert "patente" in missing


def test_to_schema_mapping():
    text = """
    Origen: A
    Destino: B
    Chofer: C
    Patente: ZZ9999
    Guía: 7777
    2 kg pescado
    """

    r = run_regex(text)
    schema = to_schema(r)

    assert schema.origen == "A"
    assert schema.destino == "B"
    assert schema.patente_camion == "ZZ9999"
    assert schema.numero_guia == "7777"
    assert len(schema.items) >= 1
