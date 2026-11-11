"""Detector de PII (src/datagen.detect_pii / explicar_pii)."""
import pytest

from src.datagen import detect_pii, explicar_pii, _luhn_ok, _clabe_ok


@pytest.mark.parametrize("nombre,esperado", [
    # nombre de persona
    ("nombre_cliente", "name"), ("NombreCliente", "name"), ("apellido_paterno", "name"),
    ("nombrecompleto", "name"), ("first_name", "name"), ("razon_social", "name"), ("nombre", "name"),
    # cuentas / tarjetas (con identificador)
    ("num_cuenta", "account"), ("NumCta", "account"), ("no_cuenta_cliente", "account"),
    ("clabe", "account"), ("iban", "account"), ("numerocuenta", "account"),
    ("num_tarjeta", "card"), ("tdc", "card"), ("card_number", "card"), ("pan", "card"),
    # identificaciones oficiales
    ("rfc", "ssn"), ("CURP", "ssn"), ("nss_empleado", "ssn"), ("ine_cliente", "ssn"),
    # contacto
    ("email", "email"), ("correo_electronico", "email"), ("tel_cel", "phone"),
    ("TelefonoCelular", "phone"), ("telefono", "phone"),
    # nacimiento
    ("fecha_nacimiento", "dob"), ("fec_nac", "dob"), ("dob", "dob"), ("FechaNacimiento", "dob"),
    ("edad_cliente", "dob"),
    # direccion
    ("direccion", "address"), ("codigo_postal", "address"), ("cp_cliente", "address"),
    ("colonia", "address"), ("calle", "address"),
    # identificador de persona
    ("id_cliente", "id"), ("customer_id", "id"), ("cve_cte", "id"), ("no_cliente", "id"),
    ("cliente", "id"), ("user_id", "id"),
    # secretos
    ("password", "secret"), ("cvv", "secret"), ("nip_tarjeta", "secret"),
])
def test_detecta(nombre, esperado):
    assert detect_pii(nombre) == esperado, explicar_pii(nombre)


@pytest.mark.parametrize("nombre", [
    # falsos positivos del detector anterior (sin limites de palabra)
    "cpu_usage", "hotel", "company", "mailbox", "pandas_version", "catalogo",
    # describen la cuenta/tarjeta, no la identifican
    "tipo_cuenta", "saldo_cuenta", "fecha_apertura_cuenta", "estatus_tarjeta",
    "num_cuentas", "total_tarjetas", "limite_tarjeta", "tasa_interes_cuenta",
    # nombres de objetos, no de personas
    "nombre_archivo", "file_name", "table_name", "hostname", "nombre_producto",
    "nombre_sucursal", "name_column",
    # ids que no son de persona
    "id_producto", "id_transaccion", "id", "folio",
    # negocio comun
    "monto", "saldo", "fecha_corte", "importe_total", "edad_cuenta", "plazo",
])
def test_no_es_pii(nombre):
    assert detect_pii(nombre) is None, explicar_pii(nombre)


def test_explicar_trae_confianza_y_motivo():
    e = explicar_pii("num_cuenta")
    assert e["categoria"] == "account" and e["confianza"] >= 0.9 and e["motivo"]
    e = explicar_pii("tipo_cuenta")
    assert e["categoria"] is None and "describe" in e["motivo"]


def test_validadores():
    assert _luhn_ok("4111111111111111") and not _luhn_ok("4111111111111112")
    assert _clabe_ok("002010077777777771") and not _clabe_ok("002010077777777772")


def test_por_valores_gana_sobre_nombre_generico():
    # columna con nombre opaco pero con CURPs reales -> ssn
    curps = ["GOMC850101HDFRRL09", "PEMJ900215MDFRRN05", "LOAA750630HJCPRL01"]
    assert detect_pii("col_7", sample_values=curps) == "ssn"
    assert detect_pii("campo_x", sample_values=["a@b.com", "c@d.mx", "e@f.org", None]) == "email"
    assert detect_pii("dato", sample_values=["4111111111111111", "5500005555555559", "340000000000009"]) == "card"
    assert detect_pii("ref", sample_values=["002010077777777771"] * 3) == "account"


def test_valores_que_no_son_pii():
    assert detect_pii("col_7", sample_values=["100.5", "200", "0", "17"]) is None
    assert detect_pii("col_7", sample_values=["A", "B"]) is None        # pocas muestras
    # telefono por valores no contradice un nombre que dice otra cosa
    assert detect_pii("monto", sample_values=["5512345678"] * 5) is None


def test_compatible_firma_y_categorias_de_siempre():
    # misma firma (solo nombre) y categorias que ya usan _redact_pii / mask_real_value
    for n, c in [("email", "email"), ("rfc", "ssn"), ("direccion", "address"), ("dob", "dob")]:
        assert detect_pii(n) == c
    from src.datagen import PII_PATTERNS
    assert "name" in PII_PATTERNS
