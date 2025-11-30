"""
ElementDetector - Haupt-Erkennungslogik für Bauteile in Bauzeichnungen.

Dieses Modul koordiniert die Erkennung verschiedener Bauteile wie
Wände, Fenster, Türen, Stützen, Unterzüge und Decken.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from .wall_detector import WallDetector
from .opening_detector import OpeningDetector
from .structural_detector import StructuralDetector

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Begrenzungsrahmen für ein erkanntes Element."""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> Tuple[int, int]:
        """Gibt die Mitte des Begrenzungsrahmens zurück."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        """Gibt die Fläche des Begrenzungsrahmens zurück."""
        return self.width * self.height


@dataclass
class DetectedElement:
    """
    Repräsentiert ein erkanntes Bauteil.
    
    Attributes:
        element_type: Typ des Bauteils (z.B. "wall", "window", "door")
        subtype: Untertyp (z.B. "exterior" für Außenwand)
        bbox: Begrenzungsrahmen des Elements
        confidence: Konfidenzwert der Erkennung (0.0 - 1.0)
        dimensions: Ermittelte Abmessungen (falls verfügbar)
        properties: Zusätzliche Eigenschaften
    """
    element_type: str
    subtype: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    confidence: float = 0.0
    dimensions: Dict[str, float] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)


class ElementDetector:
    """
    Haupt-Detektor-Klasse für die Erkennung von Bauteilen.
    
    Diese Klasse koordiniert die verschiedenen spezialisierten Detektoren
    und kombiniert deren Ergebnisse.
    
    Attributes:
        wall_detector: Detektor für Wände
        opening_detector: Detektor für Fenster und Türen
        structural_detector: Detektor für tragende Elemente
    """
    
    def __init__(self) -> None:
        """Initialisiert den ElementDetector mit allen Sub-Detektoren."""
        self.wall_detector = WallDetector()
        self.opening_detector = OpeningDetector()
        self.structural_detector = StructuralDetector()
        logger.info("ElementDetector initialisiert")
    
    def detect_all(
        self,
        image: Image.Image,
        scale: str = "1:100"
    ) -> List[DetectedElement]:
        """
        Erkennt alle Bauteile in einem Bild.
        
        Args:
            image: Eingabebild (PIL-Image)
            scale: Maßstab der Zeichnung (z.B. "1:100")
            
        Returns:
            Liste aller erkannten Bauteile
        """
        logger.info(f"Starte Bauteil-Erkennung mit Maßstab {scale}")
        
        detected_elements: List[DetectedElement] = []
        
        # Wände erkennen
        walls = self.wall_detector.detect(image, scale)
        detected_elements.extend(walls)
        logger.info(f"{len(walls)} Wände erkannt")
        
        # Öffnungen (Fenster/Türen) erkennen
        openings = self.opening_detector.detect(image, scale)
        detected_elements.extend(openings)
        logger.info(f"{len(openings)} Öffnungen erkannt")
        
        # Tragende Elemente erkennen
        structural = self.structural_detector.detect(image, scale)
        detected_elements.extend(structural)
        logger.info(f"{len(structural)} tragende Elemente erkannt")
        
        logger.info(f"Gesamt: {len(detected_elements)} Bauteile erkannt")
        return detected_elements
    
    def detect_walls(
        self,
        image: Image.Image,
        scale: str = "1:100"
    ) -> List[DetectedElement]:
        """
        Erkennt nur Wände in einem Bild.
        
        Args:
            image: Eingabebild
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter Wände
        """
        return self.wall_detector.detect(image, scale)
    
    def detect_openings(
        self,
        image: Image.Image,
        scale: str = "1:100"
    ) -> List[DetectedElement]:
        """
        Erkennt nur Öffnungen (Fenster/Türen) in einem Bild.
        
        Args:
            image: Eingabebild
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter Öffnungen
        """
        return self.opening_detector.detect(image, scale)
    
    def detect_structural(
        self,
        image: Image.Image,
        scale: str = "1:100"
    ) -> List[DetectedElement]:
        """
        Erkennt nur tragende Elemente in einem Bild.
        
        Args:
            image: Eingabebild
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter tragender Elemente
        """
        return self.structural_detector.detect(image, scale)
    
    def filter_by_type(
        self,
        elements: List[DetectedElement],
        element_type: str
    ) -> List[DetectedElement]:
        """
        Filtert erkannte Elemente nach Typ.
        
        Args:
            elements: Liste von erkannten Elementen
            element_type: Zu filternder Elementtyp
            
        Returns:
            Gefilterte Liste
        """
        return [e for e in elements if e.element_type == element_type]
    
    def filter_by_confidence(
        self,
        elements: List[DetectedElement],
        min_confidence: float = 0.5
    ) -> List[DetectedElement]:
        """
        Filtert erkannte Elemente nach Konfidenz.
        
        Args:
            elements: Liste von erkannten Elementen
            min_confidence: Minimale Konfidenz (0.0 - 1.0)
            
        Returns:
            Gefilterte Liste
        """
        return [e for e in elements if e.confidence >= min_confidence]
    
    @staticmethod
    def parse_scale(scale: str) -> float:
        """
        Parst einen Maßstab-String und gibt den Skalierungsfaktor zurück.
        
        Args:
            scale: Maßstab als String (z.B. "1:100")
            
        Returns:
            Skalierungsfaktor (z.B. 0.01 für 1:100)
        """
        try:
            parts = scale.split(":")
            if len(parts) == 2:
                numerator = float(parts[0])
                denominator = float(parts[1])
                return numerator / denominator
            else:
                logger.warning(f"Ungültiger Maßstab: {scale}, verwende 1:100")
                return 0.01
        except (ValueError, ZeroDivisionError):
            logger.warning(f"Fehler beim Parsen des Maßstabs: {scale}, verwende 1:100")
            return 0.01
