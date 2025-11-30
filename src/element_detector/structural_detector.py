"""
StructuralDetector - Modul zur Erkennung von tragenden Elementen in Bauzeichnungen.

Dieses Modul erkennt Stützen, Unterzüge, Decken und Fundamente
basierend auf typischen Zeichnungssymbolen und Markierungen.
"""

import logging
from typing import List, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class StructuralDetector:
    """
    Detektor für tragende Elemente in Bauzeichnungen.
    
    Erkennt:
    - Stützen (quadratische/rechteckige ausgefüllte Elemente)
    - Unterzüge (gestrichelte Linien)
    - Decken (schraffierte Flächen)
    - Fundamente (spezielle Symbole)
    
    Attributes:
        min_column_size: Minimale Größe für Stützen in Pixel
        max_column_size: Maximale Größe für Stützen in Pixel
    """
    
    def __init__(
        self,
        min_column_size: int = 10,
        max_column_size: int = 100
    ) -> None:
        """
        Initialisiert den StructuralDetector.
        
        Args:
            min_column_size: Minimale Größe für Stützen in Pixel
            max_column_size: Maximale Größe für Stützen in Pixel
        """
        self.min_column_size = min_column_size
        self.max_column_size = max_column_size
        logger.info("StructuralDetector initialisiert")
    
    def detect(self, image: Image.Image, scale: str = "1:100") -> List:
        """
        Erkennt tragende Elemente in einem Bild.
        
        Args:
            image: Eingabebild (PIL-Image)
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter tragender Elemente als DetectedElement-Objekte
        """
        from .detector import DetectedElement, BoundingBox
        
        logger.info("Starte Erkennung tragender Elemente")
        
        detected_elements: List[DetectedElement] = []
        
        # Bild in Graustufen konvertieren
        if image.mode != "L":
            gray_image = image.convert("L")
        else:
            gray_image = image
        
        # Als NumPy-Array
        img_array = np.array(gray_image)
        
        # Binarisierung
        threshold = 128
        binary = np.where(img_array < threshold, 1, 0).astype(np.uint8)
        
        # Stützen erkennen
        columns = self._detect_columns(binary, scale)
        detected_elements.extend(columns)
        
        # Unterzüge erkennen
        beams = self._detect_beams(binary, scale)
        detected_elements.extend(beams)
        
        # Decken erkennen (schraffierte Bereiche)
        slabs = self._detect_slabs(binary, scale)
        detected_elements.extend(slabs)
        
        logger.info(
            f"{len(detected_elements)} tragende Elemente erkannt "
            f"({len(columns)} Stützen, {len(beams)} Unterzüge, {len(slabs)} Decken)"
        )
        
        return detected_elements
    
    def _detect_columns(
        self,
        binary: np.ndarray,
        scale: str
    ) -> List:
        """
        Erkennt Stützen (ausgefüllte rechteckige Elemente).
        
        Args:
            binary: Binärbild als NumPy-Array
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter Stützen
        """
        from .detector import DetectedElement, BoundingBox
        
        columns = []
        height, width = binary.shape
        
        # Suche nach kompakten, ausgefüllten Rechtecken
        filled_regions = self._find_filled_rectangles(binary)
        
        scale_factor = self._parse_scale(scale)
        
        for region in filled_regions:
            x, y, w, h, fill_ratio = region
            
            # Prüfe ob Größe zu Stütze passt
            if (self.min_column_size <= w <= self.max_column_size and
                self.min_column_size <= h <= self.max_column_size):
                
                # Stützen sind meist annähernd quadratisch
                aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 10
                
                if aspect_ratio < 3 and fill_ratio > 0.7:
                    column = DetectedElement(
                        element_type="column",
                        subtype="standard",
                        bbox=BoundingBox(x=x, y=y, width=w, height=h),
                        confidence=0.75,
                        dimensions={
                            "width_px": w,
                            "depth_px": h,
                            "width_m": w * scale_factor,
                            "depth_m": h * scale_factor,
                            "cross_section_m2": (w * scale_factor) * (h * scale_factor),
                        },
                        properties={
                            "column_type": "Rechteckstütze",
                            "fill_ratio": fill_ratio
                        }
                    )
                    columns.append(column)
        
        return columns
    
    def _detect_beams(
        self,
        binary: np.ndarray,
        scale: str
    ) -> List:
        """
        Erkennt Unterzüge (oft als gestrichelte Linien dargestellt).
        
        Args:
            binary: Binärbild als NumPy-Array
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter Unterzüge
        """
        from .detector import DetectedElement, BoundingBox
        
        beams = []
        
        # Suche nach gestrichelten Linien
        dashed_lines = self._find_dashed_lines(binary)
        
        scale_factor = self._parse_scale(scale)
        
        for line in dashed_lines:
            x, y, w, h = line
            
            beam = DetectedElement(
                element_type="beam",
                subtype="standard",
                bbox=BoundingBox(x=x, y=y, width=w, height=h),
                confidence=0.65,
                dimensions={
                    "length_px": max(w, h),
                    "length_m": max(w, h) * scale_factor,
                },
                properties={
                    "beam_type": "Unterzug",
                    "orientation": "horizontal" if w > h else "vertical"
                }
            )
            beams.append(beam)
        
        return beams
    
    def _detect_slabs(
        self,
        binary: np.ndarray,
        scale: str
    ) -> List:
        """
        Erkennt Decken (oft als schraffierte Flächen dargestellt).
        
        Args:
            binary: Binärbild als NumPy-Array
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter Decken
        """
        from .detector import DetectedElement, BoundingBox
        
        slabs = []
        
        # Suche nach schraffierten Bereichen
        hatched_regions = self._find_hatched_regions(binary)
        
        scale_factor = self._parse_scale(scale)
        
        for region in hatched_regions:
            x, y, w, h = region
            
            area_px = w * h
            area_m2 = (w * scale_factor) * (h * scale_factor)
            
            slab = DetectedElement(
                element_type="slab",
                subtype="floor",
                bbox=BoundingBox(x=x, y=y, width=w, height=h),
                confidence=0.6,
                dimensions={
                    "width_px": w,
                    "height_px": h,
                    "area_px": area_px,
                    "width_m": w * scale_factor,
                    "height_m": h * scale_factor,
                    "area_m2": area_m2,
                },
                properties={
                    "slab_type": "Geschossdecke"
                }
            )
            slabs.append(slab)
        
        return slabs
    
    def _find_filled_rectangles(
        self,
        binary: np.ndarray
    ) -> List[Tuple[int, int, int, int, float]]:
        """
        Findet ausgefüllte rechteckige Bereiche.
        
        Args:
            binary: Binärbild
            
        Returns:
            Liste von Tupeln (x, y, width, height, fill_ratio)
        """
        rectangles = []
        height, width = binary.shape
        
        # Einfache Implementierung: Zusammenhängende schwarze Bereiche finden
        visited = np.zeros_like(binary, dtype=bool)
        
        for y in range(height):
            for x in range(width):
                if binary[y, x] == 1 and not visited[y, x]:
                    # Finde zusammenhängenden Bereich
                    min_x, max_x = x, x
                    min_y, max_y = y, y
                    count = 0
                    
                    stack = [(x, y)]
                    while stack and count < 10000:
                        cx, cy = stack.pop()
                        
                        if (cx < 0 or cx >= width or cy < 0 or cy >= height or
                            visited[cy, cx] or binary[cy, cx] == 0):
                            continue
                        
                        visited[cy, cx] = True
                        count += 1
                        
                        min_x = min(min_x, cx)
                        max_x = max(max_x, cx)
                        min_y = min(min_y, cy)
                        max_y = max(max_y, cy)
                        
                        stack.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])
                    
                    if count > 0:
                        w = max_x - min_x + 1
                        h = max_y - min_y + 1
                        fill_ratio = count / (w * h) if w * h > 0 else 0
                        
                        if fill_ratio > 0.5:  # Mindestens 50% gefüllt
                            rectangles.append((min_x, min_y, w, h, fill_ratio))
        
        return rectangles
    
    def _find_dashed_lines(
        self,
        binary: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
        """
        Findet gestrichelte Linien.
        
        Args:
            binary: Binärbild
            
        Returns:
            Liste von Tupeln (x, y, width, height)
        """
        # TODO: Implementiere Mustererkennung für gestrichelte Linien
        # In einer vollständigen Implementierung würde hier:
        # 1. Linien mit regelmäßigen Unterbrechungen erkannt werden
        # 2. Das Strich-Lücken-Verhältnis analysiert werden
        # 3. Unterzüge anhand typischer Muster identifiziert werden
        logger.debug("Gestrichelte-Linien-Erkennung: Platzhalter-Implementierung")
        
        return []  # Platzhalter - keine gestrichelten Linien ohne vollständige Implementierung
    
    def _find_hatched_regions(
        self,
        binary: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
        """
        Findet schraffierte Bereiche.
        
        Args:
            binary: Binärbild
            
        Returns:
            Liste von Tupeln (x, y, width, height)
        """
        # TODO: Implementiere Mustererkennung für Schraffuren
        # In einer vollständigen Implementierung würde hier:
        # 1. Parallele Linien in regelmäßigen Abständen erkannt werden
        # 2. Verschiedene Schraffurwinkel (45°, 90°, etc.) analysiert werden
        # 3. Schraffierte Flächen als Decken oder andere Elemente klassifiziert werden
        logger.debug("Schraffur-Erkennung: Platzhalter-Implementierung")
        
        return []  # Platzhalter - keine Schraffuren ohne vollständige Implementierung
    
    def _parse_scale(self, scale: str) -> float:
        """
        Parst einen Maßstab-String.
        
        Args:
            scale: Maßstab als String (z.B. "1:100")
            
        Returns:
            Skalierungsfaktor
        """
        try:
            parts = scale.split(":")
            if len(parts) == 2:
                return float(parts[0]) / float(parts[1])
        except (ValueError, ZeroDivisionError):
            pass
        return 0.01  # Standard: 1:100
