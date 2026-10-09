"""
QR Code generation and verification service using Python qrcode library.
Generates safe, tokenized QR codes with zero personal data leakage.
"""
import os
import secrets
import qrcode
from pathlib import Path
from flask import current_app, url_for


class QRService:
    """Service for generating and verifying pickup QR codes."""

    @staticmethod
    def generate_token():
        """Generate a cryptographically secure 32-byte hex token."""
        return secrets.token_hex(16)

    @classmethod
    def generate_order_qr(cls, order):
        """
        Generates a PNG QR code for the given order containing only a verification URL / token.
        Saves the file to app/static/qr_codes/<order_number>.png.
        """
        qr_dir = Path(current_app.config['STATIC_FOLDER']) / 'qr_codes'
        qr_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{order.order_number}.png"
        filepath = qr_dir / filename

        # Secure verification payload: only order number and verification token
        # Does NOT leak customer phone, student ID, or personal data
        verification_payload = f"FOODCOURT:VERIFY:{order.order_number}:{order.verification_token}"

        # High-quality QR code configuration
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=3,
        )
        qr.add_data(verification_payload)
        qr.make(fit=True)

        # Warm food-court themed or crisp contrast rendering (Navy/Dark slate on White)
        img = qr.make_image(fill_color="#1e293b", back_color="#ffffff")
        img.save(str(filepath))

        # Store relative path for static serving
        return f"qr_codes/{filename}"

    @staticmethod
    def parse_qr_payload(scanned_text):
        """
        Parse QR code text from scanner.
        Supports formatted string 'FOODCOURT:VERIFY:<order_number>:<token>'
        as well as raw order numbers entered manually.
        """
        scanned_text = scanned_text.strip()
        if scanned_text.startswith("FOODCOURT:VERIFY:"):
            parts = scanned_text.split(":")
            if len(parts) >= 4:
                return {
                    'order_number': parts[2],
                    'token': parts[3]
                }
        
        # Fallback: Scanned text might be just order number
        return {
            'order_number': scanned_text,
            'token': None
        }
