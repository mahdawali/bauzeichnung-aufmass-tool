"""
TextExtractor - Modul zur OCR-basierten Texterkennung in Bauzeichnungen.

Dieses Modul verwendet Tesseract OCR zur Extraktion von Maßangaben,
Beschriftungen und anderen Textinformationen aus Bauzeichnungen.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class TextRegion:
    """
    Repräsentiert einen erkannten Textbereich.
    
    Attributes:
        text: Der erkannte Text
        x: X-Koordinate des Textbereichs
        y: Y-Koordinate des Textbereichs
        width: Breite des Textbereichs
        height: Höhe des Textbereichs
        confidence: Konfidenzwert der Erkennung (0-100)
    """
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass
class DimensionInfo:
    """
    Repräsentiert eine erkannte Maßangabe.
    
    Attributes:
        value: Numerischer Wert
        unit: Einheit (m, cm, mm)
        text: Originaltext
        region: Position des Textes im Bild
    """
    value: float
    unit: str
    text: str
    region: Optional[TextRegion] = None


class TextExtractor:
    """
    Klasse zur OCR-basierten Texterkennung.
    
    Verwendet Tesseract OCR zur Extraktion von:
    - Maßangaben (z.B. "3,50 m", "350 cm")
    - Raumbeschriftungen (z.B. "Wohnzimmer", "Bad")
    - Technische Beschriftungen
    
    Attributes:
        lang: Sprache für OCR (Standard: "deu" für Deutsch)
        config: Tesseract-Konfiguration
    """
    
    def __init__(self, lang: str = "deu") -> None:
        """
        Initialisiert den TextExtractor.
        
        Args:
            lang: Sprache für OCR (Standard: "deu")
        """
        self.lang = lang
        self.config = "--psm 6"  # Assume a single uniform block of text
        logger.info(f"TextExtractor initialisiert mit Sprache: {lang}")
        
        # Regex-Pattern für Maßangaben
        self.dimension_patterns = [
            # Meter (z.B. "3,50 m", "3.50m", "350m")
            r"(\d+[,.]?\d*)\s*m(?![m²³])",
            # Zentimeter (z.B. "350 cm")
            r"(\d+[,.]?\d*)\s*cm",
            # Millimeter (z.B. "3500 mm")
            r"(\d+[,.]?\d*)\s*mm",
            # Nur Zahlen (könnten Maße sein)
            r"(\d+[,.]?\d+)",
        ]
    
    def extract_text(self, image: Image.Image) -> List[TextRegion]:
        """
        Extrahiert alle Textbereiche aus einem Bild.
        
        Args:
            image: Eingabebild (PIL-Image)
            
        Returns:
            Liste erkannter Textbereiche
        """
        logger.info("Starte Texterkennung")
        
        try:
            import pytesseract
            
            # OCR mit detaillierten Informationen
            data = pytesseract.image_to_data(
                image,
                lang=self.lang,
                config=self.config,
                output_type=pytesseract.Output.DICT
            )
            
            regions = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                
                if text and conf > 0:
                    region = TextRegion(
                        text=text,
                        x=data['left'][i],
                        y=data['top'][i],
                        width=data['width'][i],
                        height=data['height'][i],
                        confidence=conf
                    )
                    regions.append(region)
            
            logger.info(f"{len(regions)} Textbereiche erkannt")
            return regions
            
        except ImportError:
            logger.warning(
                "pytesseract nicht installiert. "
                "Texterkennung nicht verfügbar."
            )
            return []
        except Exception as e:
            logger.error(f"Fehler bei der Texterkennung: {e}")
            return []
    
    def extract_dimensions(self, image: Image.Image) -> List[DimensionInfo]:
        """
        Extrahiert Maßangaben aus einem Bild.
        
        Args:
            image: Eingabebild (PIL-Image)
            
        Returns:
            Liste erkannter Maßangaben
        """
        logger.info("Extrahiere Maßangaben")
        
        text_regions = self.extract_text(image)
        dimensions = []
        
        for region in text_regions:
            dim = self._parse_dimension(region.text)
            if dim:
                dim.region = region
                dimensions.append(dim)
        
        logger.info(f"{len(dimensions)} Maßangaben extrahiert")
        return dimensions
    
    def extract_labels(self, image: Image.Image) -> List[TextRegion]:
        """
        Extrahiert Beschriftungen (nicht-numerische Texte) aus einem Bild.
        
        Args:
            image: Eingabebild (PIL-Image)
            
        Returns:
            Liste erkannter Beschriftungen
        """
        logger.info("Extrahiere Beschriftungen")
        
        text_regions = self.extract_text(image)
        
        # Filtere numerische Texte heraus
        labels = []
        for region in text_regions:
            # Prüfe ob Text hauptsächlich Buchstaben enthält
            alpha_ratio = sum(c.isalpha() for c in region.text) / len(region.text) if region.text else 0
            
            if alpha_ratio > 0.5 and len(region.text) >= 2:
                labels.append(region)
        
        logger.info(f"{len(labels)} Beschriftungen extrahiert")
        return labels
    
    def _parse_dimension(self, text: str) -> Optional[DimensionInfo]:
        """
        Parst eine Maßangabe aus einem Text.
        
        Args:
            text: Eingabetext
            
        Returns:
            DimensionInfo oder None
        """
        text = text.strip()
        
        # Versuche verschiedene Formate zu erkennen
        
        # Meter
        match = re.search(r"(\d+[,.]?\d*)\s*m(?![m²³])", text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", "."))
            return DimensionInfo(value=value, unit="m", text=text)
        
        # Zentimeter
        match = re.search(r"(\d+[,.]?\d*)\s*cm", text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", ".")) / 100
            return DimensionInfo(value=value, unit="cm", text=text)
        
        # Millimeter
        match = re.search(r"(\d+[,.]?\d*)\s*mm", text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", ".")) / 1000
            return DimensionInfo(value=value, unit="mm", text=text)
        
        return None
    
    def get_full_text(self, image: Image.Image) -> str:
        """
        Extrahiert den gesamten Text aus einem Bild als String.
        
        Args:
            image: Eingabebild (PIL-Image)
            
        Returns:
            Extrahierter Text
        """
        try:
            import pytesseract
            
            text = pytesseract.image_to_string(
                image,
                lang=self.lang,
                config=self.config
            )
            return text.strip()
            
        except ImportError:
            logger.warning(
                "pytesseract nicht installiert. "
                "Texterkennung nicht verfügbar."
            )
            return ""
        except Exception as e:
            logger.error(f"Fehler bei der Texterkennung: {e}")
            return ""
    
    def find_room_labels(self, image: Image.Image) -> List[TextRegion]:
        """
        Findet Raumbeschriftungen in einem Bild.
        
        Sucht nach typischen deutschen Raumbezeichnungen wie:
        - Wohnzimmer, Schlafzimmer, Kinderzimmer
        - Bad, WC, Flur, Küche
        - Büro, Lager, Technik
        
        Args:
            image: Eingabebild (PIL-Image)
            
        Returns:
            Liste erkannter Raumbeschriftungen
        """
        logger.info("Suche Raumbeschriftungen")
        
        room_keywords = [
            "wohnzimmer", "schlafzimmer", "kinderzimmer", "gästezimmer",
            "bad", "badezimmer", "wc", "gäste-wc", "toilette",
            "küche", "kochen", "essen", "esszimmer",
            "flur", "diele", "eingang", "windfang",
            "büro", "arbeitszimmer", "homeoffice",
            "lager", "abstellraum", "hauswirtschaft", "hwr",
            "technik", "heizung", "keller",
            "garage", "carport", "stellplatz",
            "balkon", "terrasse", "loggia",
            "zimmer", "raum"
        ]
        
        text_regions = self.extract_text(image)
        room_labels = []
        
        for region in text_regions:
            text_lower = region.text.lower()
            
            for keyword in room_keywords:
                if keyword in text_lower:
                    room_labels.append(region)
                    break
        
        logger.info(f"{len(room_labels)} Raumbeschriftungen gefunden")
        return room_labels
