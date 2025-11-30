"""
PDFReader - Modul zum Einlesen und Konvertieren von PDF-Dateien in Bilder.

Dieses Modul verwendet pdf2image zur Konvertierung von PDF-Seiten in PIL-Bilder,
die dann für die weitere Analyse verwendet werden können.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

from PIL import Image

logger = logging.getLogger(__name__)


class PDFReader:
    """
    Klasse zum Einlesen und Konvertieren von PDF-Dateien.
    
    Diese Klasse bietet Funktionen zum:
    - Einlesen von PDF-Dateien
    - Konvertieren von PDF-Seiten in Bilder
    - Speichern der konvertierten Bilder
    
    Attributes:
        dpi: Die Auflösung für die Bildkonvertierung (Standard: 300 DPI)
    """
    
    def __init__(self, dpi: int = 300) -> None:
        """
        Initialisiert den PDFReader.
        
        Args:
            dpi: Die Auflösung für die Bildkonvertierung (Standard: 300)
        """
        self.dpi = dpi
        logger.info(f"PDFReader initialisiert mit {dpi} DPI")
    
    def read_pdf(self, pdf_path: Union[str, Path]) -> List[Image.Image]:
        """
        Liest eine PDF-Datei ein und konvertiert sie in Bilder.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            Liste von PIL-Bildern, eines pro Seite
            
        Raises:
            FileNotFoundError: Wenn die PDF-Datei nicht gefunden wird
            ValueError: Wenn die Datei keine gültige PDF ist
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF-Datei nicht gefunden: {pdf_path}")
        
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Datei ist keine PDF: {pdf_path}")
        
        logger.info(f"Lese PDF: {pdf_path}")
        
        try:
            # pdf2image importieren (nur wenn benötigt)
            from pdf2image import convert_from_path
            
            images = convert_from_path(
                str(pdf_path),
                dpi=self.dpi,
                fmt="PNG"
            )
            
            logger.info(f"PDF erfolgreich konvertiert: {len(images)} Seite(n)")
            return images
            
        except ImportError:
            logger.warning(
                "pdf2image nicht installiert. "
                "Versuche alternative Methode mit PIL..."
            )
            # Fallback: Versuche direkt mit PIL zu öffnen (für Bilddateien)
            return [Image.open(pdf_path)]
        except Exception as e:
            logger.error(f"Fehler beim Lesen der PDF: {e}")
            raise
    
    def read_image(self, image_path: Union[str, Path]) -> Image.Image:
        """
        Liest eine Bilddatei ein.
        
        Args:
            image_path: Pfad zur Bilddatei
            
        Returns:
            PIL-Bild
            
        Raises:
            FileNotFoundError: Wenn die Bilddatei nicht gefunden wird
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Bilddatei nicht gefunden: {image_path}")
        
        logger.info(f"Lese Bild: {image_path}")
        
        return Image.open(image_path)
    
    def save_images(
        self,
        images: List[Image.Image],
        output_dir: Union[str, Path],
        prefix: str = "page"
    ) -> List[Path]:
        """
        Speichert eine Liste von Bildern als PNG-Dateien.
        
        Args:
            images: Liste von PIL-Bildern
            output_dir: Ausgabeverzeichnis
            prefix: Präfix für die Dateinamen (Standard: "page")
            
        Returns:
            Liste der gespeicherten Dateipfade
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        
        for i, image in enumerate(images, start=1):
            output_path = output_dir / f"{prefix}_{i:03d}.png"
            image.save(str(output_path), "PNG")
            saved_paths.append(output_path)
            logger.debug(f"Bild gespeichert: {output_path}")
        
        logger.info(f"{len(saved_paths)} Bild(er) gespeichert in: {output_dir}")
        return saved_paths
    
    def get_page_count(self, pdf_path: Union[str, Path]) -> int:
        """
        Ermittelt die Anzahl der Seiten in einer PDF-Datei.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            Anzahl der Seiten
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF-Datei nicht gefunden: {pdf_path}")
        
        try:
            from pdf2image import pdfinfo_from_path
            
            info = pdfinfo_from_path(str(pdf_path))
            return info.get("Pages", 0)
        except ImportError:
            logger.warning(
                "pdf2image nicht installiert. "
                "Seitenanzahl kann nicht ermittelt werden."
            )
            return 0
        except Exception as e:
            logger.error(f"Fehler beim Ermitteln der Seitenanzahl: {e}")
            return 0
