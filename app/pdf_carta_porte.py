"""Genera el PDF de una carta porte con el formato tradicional impreso
(encabezado, origen/destino, mercancía, medio de transporte, figura de
transporte y recibí de conformidad).

Es un documento interno de FlotaTrack para respaldo/impresión — NO es el
CFDI de Carta Porte timbrado ante el SAT.
"""

import io

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _fmt_dt(dt) -> str:
    return dt.strftime("%d/%m/%Y %H:%M") if dt else "—"


def _address(record, prefix: str) -> str:
    calle = getattr(record, f"{prefix}_calle")
    num_ext = getattr(record, f"{prefix}_numero_exterior") or ""
    num_int = getattr(record, f"{prefix}_numero_interior") or ""
    colonia = getattr(record, f"{prefix}_colonia")
    localidad = getattr(record, f"{prefix}_localidad") or ""
    municipio = getattr(record, f"{prefix}_municipio")
    estado = getattr(record, f"{prefix}_estado")
    pais = getattr(record, f"{prefix}_pais")
    cp = getattr(record, f"{prefix}_codigo_postal")

    numero = f" {num_ext}".rstrip() + (f" int. {num_int}" if num_int else "")
    partes = [f"{calle}{numero}", colonia]
    if localidad:
        partes.append(localidad)
    partes += [municipio, estado, pais, f"CP {cp}"]
    return ", ".join(p for p in partes if p)


def generate_carta_porte_pdf(record, trip) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    left = 20 * mm
    right = width - 20 * mm

    def label_value(x, y, label, value, gap=4):
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y, label)
        c.setFont("Helvetica", 8)
        c.drawString(x + gap + c.stringWidth(label, "Helvetica-Bold", 8), y, str(value))

    # --- Encabezado ---
    top = height - 18 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, top, "CARTA DE PORTE")
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, top - 14, record.tipo_cfdi.upper())

    c.setFont("Helvetica", 8)
    c.drawRightString(right, top, f"Folio: {record.folio}")
    c.drawRightString(right, top - 12, f"ID de viaje: {trip.id}")

    y = top - 36
    label_value(left, y, "Autotransportista / operador: ", record.operador_nombre)
    y -= 13
    label_value(left, y, "RFC emisor: ", record.emisor_rfc)
    label_value(left + 220, y, "RFC receptor: ", record.receptor_rfc)
    y -= 13
    label_value(
        left, y, "Lugar y fecha de expedición: ",
        f"{record.origen_municipio}, {record.origen_estado} — "
        f"{_fmt_dt(record.origen_fecha_hora_salida)}",
    )

    # --- Origen / Destino ---
    y -= 20
    box_h = 100
    c.setLineWidth(0.8)
    c.rect(left, y - box_h, right - left, box_h)
    c.line(width / 2, y - box_h, width / 2, y)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(left + 4, y - 12, "ORIGEN")
    c.drawString(width / 2 + 4, y - 12, "DESTINO")

    c.setFont("Helvetica", 7.5)
    c.drawString(left + 4, y - 24, f"Clave: {record.origen_clave}")
    c.drawString(width / 2 + 4, y - 24, f"Clave: {record.destino_clave}")

    c.drawString(left + 4, y - 36, "Domicilio:")
    c.drawString(width / 2 + 4, y - 36, "Domicilio:")
    for i, chunk in enumerate(_wrap_text(_address(record, "origen"), 62)[:2]):
        c.drawString(left + 4, y - 46 - (i * 9), chunk)
    for i, chunk in enumerate(_wrap_text(_address(record, "destino"), 62)[:2]):
        c.drawString(width / 2 + 4, y - 46 - (i * 9), chunk)

    c.drawString(left + 4, y - 74, f"Salida: {_fmt_dt(record.origen_fecha_hora_salida)}")
    c.drawString(width / 2 + 4, y - 74, f"Llegada: {_fmt_dt(record.destino_fecha_hora_llegada)}")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(left + 4, y - 90, f"Distancia recorrida: {record.distancia_recorrida_km} km")

    # --- Mercancía ---
    y -= box_h + 18
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "MERCANCÍA")
    y -= 12
    box_h = 52
    c.rect(left, y - box_h, right - left, box_h)
    c.setFont("Helvetica", 8)
    c.drawString( left + 4, y - 12, 
        f"Clave prod./servicio (SAT): {record.mercancia_clave_prod_serv}"
    )
    c.drawString(left + 4, y - 24, f"Descripción: {record.merchandise_description}")
    c.drawString(
        left + 4, y - 36,
        f"Peso bruto: {record.mercancia_peso_bruto_kg} kg    "
        f"Peso neto: {record.mercancia_peso_neto_kg} kg    "
        f"Unidad: {record.mercancia_clave_unidad}",
    )
    peligroso = "SÍ" if record.material_peligroso else "NO"
    c.drawString(
        left + 4, y - 48,
        f"Material peligroso: {peligroso}    Embalaje: {record.mercancia_embalaje or '—'}",
    )

    # --- Medio de transporte ---
    y -= box_h + 18
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "MEDIO DE TRANSPORTE")
    y -= 12
    box_h = 52
    c.rect(left, y - box_h, right - left, box_h)
    c.setFont("Helvetica", 8)
    c.drawString( left + 4, y - 12, 
        f"Tipo: {record.tipo_transporte}    "
        f"Config. vehicular: {record.config_vehicular}"
    )
    c.drawString(
        left + 4, y - 24,
        f"Placa camión: {record.placa_camion}    Placa remolque: {record.placa_remolque or '—'}",
    )
    c.drawString(left + 4, y - 36, f"Permiso SICT: {record.numero_permiso_sict}")
    c.drawString( left + 4, y - 48, 
        f"Aseguradora: {record.aseguradora_nombre}    "
        f"Póliza: {record.poliza_numero}"
    )

    # --- Figura de transporte (operador) ---
    y -= box_h + 18
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "FIGURA DE TRANSPORTE (OPERADOR)")
    y -= 12
    box_h = 40
    c.rect(left, y - box_h, right - left, box_h)
    c.setFont("Helvetica", 8)
    c.drawString( left + 4, y - 12, 
        f"Nombre: {record.operador_nombre}    RFC: {record.operador_rfc}"
    )
    c.drawString(left + 4, y - 24, f"Licencia: {record.operador_licencia}")
    for i, chunk in enumerate(_wrap_text(f"Domicilio: {record.operador_domicilio}", 95)[:1]):
        c.drawString(left + 4, y - 36, chunk)

    # --- Recibí de conformidad ---
    y -= box_h + 40
    c.line(left, y, left + 220, y)
    c.setFont("Helvetica", 8)
    c.drawString( left, y - 10, 
        "Recibí de conformidad (nombre y firma del destinatario o persona autorizada)"
    )

    c.setFont("Helvetica-Oblique", 6.5)
    c.drawString(
        left, 15 * mm,
        "Documento generado — registro interno, no es el CFDI de Carta Porte timbrado ante el SAT.",
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def _wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines