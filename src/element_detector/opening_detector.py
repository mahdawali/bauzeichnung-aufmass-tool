"""
OpeningDetector - Modul zur Erkennung von Fenstern und Türen in Bauzeichnungen.

Dieses Modul erkennt Fenster und Türen basierend auf typischen
Zeichnungssymbolen und Öffnungen in Wänden.
"""

import logging
from typing import List, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class OpeningDetector:
    """
    Detektor für Öffnungen (Fenster und Türen) in Bauzeichnungen.
    
    Erkennt Fenster und Türen basierend auf:
    - Unterbrechungen in Wandlinien
    - Typische Zeichnungssymbole (Türbogen, Fensterkreuz)
    
    Attributes:
        min_opening_width: Minimale Öffnungsbreite in Pixel
        max_opening_width: Maximale Öffnungsbreite in Pixel
    """
    
    def __init__(
        self,
        min_opening_width: int = 20,
        max_opening_width: int = 200
    ) -> None:
        """
        Initialisiert den OpeningDetector.
        
        Args:
            min_opening_width: Minimale Öffnungsbreite in Pixel
            max_opening_width: Maximale Öffnungsbreite in Pixel
        """
        self.min_opening_width = min_opening_width
        self.max_opening_width = max_opening_width
        logger.info("OpeningDetector initialisiert")
    
    def detect(self, image: Image.Image, scale: str = "1:100") -> List:
        """
        Erkennt Fenster und Türen in einem Bild.
        
        Args:
            image: Eingabebild (PIL-Image)
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter Öffnungen als DetectedElement-Objekte
        """
        from src.element_detector.detector import DetectedElement, BoundingBox
        
        logger.info("Starte Öffnungs-Erkennung")
        
        detected_openings: List[DetectedElement] = []
        
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
        
        # Fenster erkennen
        windows = self._detect_windows(binary, scale)
        detected_openings.extend(windows)
        
        # Türen erkennen
        doors = self._detect_doors(binary, scale)
        detected_openings.extend(doors)
        
        logger.info(
            f"{len(detected_openings)} Öffnungen erkannt "
            f"({len(windows)} Fenster, {len(doors)} Türen)"
        )
        
        return detected_openings
    
    def _detect_windows(
        self,
        binary: np.ndarray,
        scale: str
    ) -> List:
        """
        Erkennt Fenster in einem binären Bild.
        
        Fenster werden typischerweise als:
        - Unterbrechung in Wandlinie mit parallelen Linien
        - Kreuz-Symbol
        
        Args:
            binary: Binärbild als NumPy-Array
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter Fenster
        """
        from .detector import DetectedElement, BoundingBox
        
        windows = []
        height, width = binary.shape
        
        # Suche nach typischen Fenstermustern
        # (Vereinfachte Implementierung)
        
        # Suche horizontale Unterbrechungen
        window_regions = self._find_wall_gaps(binary)
        
        scale_factor = self._parse_scale(scale)
        
        for region in window_regions:
            x, y, w, h = region
            
            # Prüfe ob Größe zu Fenster passt
            if self.min_opening_width <= w <= self.max_opening_width:
                # Als Fenster klassifizieren wenn nicht zu hoch
                if h < w * 2:  # Fenster sind typischerweise breiter als hoch
                    window = DetectedElement(
                        element_type="window",
                        subtype="standard",
                        bbox=BoundingBox(x=x, y=y, width=w, height=h),
                        confidence=0.7,
                        dimensions={
                            "width_px": w,
                            "height_px": h,
                            "width_m": w * scale_factor,
                            "height_m": h * scale_factor,
                        },
                        properties={
                            "window_type": "Standard-Fenster"
                        }
                    )
                    windows.append(window)
        
        return windows
    
    def _detect_doors(
        self,
        binary: np.ndarray,
        scale: str
    ) -> List:
        """
        Erkennt Türen in einem binären Bild.
        
        Türen werden typischerweise als:
        - Unterbrechung in Wandlinie mit Viertelkreis (Türschwung)
        - Rechteckige Öffnung
        
        Args:
            binary: Binärbild als NumPy-Array
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter Türen
        """
        from .detector import DetectedElement, BoundingBox
        
        doors = []
        height, width = binary.shape
        
        # Suche nach typischen Türmustern
        door_regions = self._find_door_swings(binary)
        
        scale_factor = self._parse_scale(scale)
        
        for region in door_regions:
            x, y, w, h = region
            
            # Prüfe ob Größe zu Tür passt
            if self.min_opening_width <= w <= self.max_opening_width:
                door = DetectedElement(
                    element_type="door",
                    subtype="standard",
                    bbox=BoundingBox(x=x, y=y, width=w, height=h),
                    confidence=0.7,
                    dimensions={
                        "width_px": w,
                        "height_px": h,
                        "width_m": w * scale_factor,
                        "height_m": h * scale_factor,
                    },
                    properties={
                        "door_type": "Standard-Tür"
                    }
                )
                doors.append(door)
        
        return doors
    
    def _find_wall_gaps(
        self,
        binary: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
        """
        Findet Unterbrechungen in Wandlinien.
        
        Args:
            binary: Binärbild
            
        Returns:
            Liste von Regionen (x, y, width, height)
        """
        gaps = []
        height, width = binary.shape
        
        # Vereinfachte Implementierung:
        # Suche nach zusammenhängenden weißen Bereichen
        # die von schwarzen Linien umgeben sind
        
        visited = np.zeros_like(binary, dtype=bool)
        
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if binary[y, x] == 0 and not visited[y, x]:
                    # Weißer Bereich gefunden
                    region = self._flood_fill_region(binary, visited, x, y)
                    if region:
                        rx, ry, rw, rh = region
                        # Prüfe ob es wie eine Öffnung aussieht
                        if (self.min_opening_width <= rw <= self.max_opening_width and
                            self.min_opening_width // 2 <= rh <= self.max_opening_width):
                            gaps.append(region)
        
        return gaps
    
    def _find_door_swings(
        self,
        binary: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
        """
        Findet Türschwung-Symbole (Viertelkreise).
        
        Args:
            binary: Binärbild
            
        Returns:
            Liste von Regionen (x, y, width, height)
        """
        # TODO: Implementiere Mustererkennung für Viertelkreise (Türschwung-Symbole)
        # In einer vollständigen Implementierung würde hier:
        # 1. Kreisförmige Konturen erkannt werden
        # 2. Viertelkreise als Türschwung-Symbol identifiziert werden
        # 3. Position und Größe der Türöffnung aus dem Symbol abgeleitet werden
        logger.debug("Türschwung-Erkennung: Platzhalter-Implementierung")
        
        return []  # Platzhalter - keine Türschwünge ohne vollständige Implementierung
    
    def _flood_fill_region(
        self,
        binary: np.ndarray,
        visited: np.ndarray,
        start_x: int,
        start_y: int,
        max_size: int = 10000
    ) -> Tuple[int, int, int, int]:
        """
        Füllt eine zusammenhängende Region und gibt deren Begrenzung zurück.
        
        Args:
            binary: Binärbild
            visited: Array mit bereits besuchten Pixeln
            start_x: Start-X-Koordinate
            start_y: Start-Y-Koordinate
            max_size: Maximale Regionsgröße
            
        Returns:
            Begrenzung der Region (x, y, width, height) oder None
        """
        height, width = binary.shape
        
        stack = [(start_x, start_y)]
        min_x, max_x = start_x, start_x
        min_y, max_y = start_y, start_y
        count = 0
        
        while stack and count < max_size:
            x, y = stack.pop()
            
            if (x < 0 or x >= width or y < 0 or y >= height or
                visited[y, x] or binary[y, x] == 1):
                continue
            
            visited[y, x] = True
            count += 1
            
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            
            # Nachbarn hinzufügen
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
        
        if count > 0 and count < max_size:
            return (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        
        return None
    
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
