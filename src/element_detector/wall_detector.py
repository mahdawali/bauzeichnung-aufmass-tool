"""
WallDetector - Modul zur Erkennung von Wänden in Bauzeichnungen.

Dieses Modul erkennt Außenwände und Innenwände in Grundrisszeichnungen
basierend auf Liniendicke und Linienmuster.
"""

import logging
from typing import List, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class WallDetector:
    """
    Detektor für Wände in Bauzeichnungen.
    
    Erkennt Außenwände (dickere Linien) und Innenwände (dünnere Linien)
    basierend auf der Linienbreite in der Zeichnung.
    
    Attributes:
        exterior_wall_min_thickness: Minimale Dicke für Außenwände in Pixel
        interior_wall_min_thickness: Minimale Dicke für Innenwände in Pixel
    """
    
    def __init__(
        self,
        exterior_wall_min_thickness: int = 10,
        interior_wall_min_thickness: int = 5
    ) -> None:
        """
        Initialisiert den WallDetector.
        
        Args:
            exterior_wall_min_thickness: Minimale Dicke für Außenwände
            interior_wall_min_thickness: Minimale Dicke für Innenwände
        """
        self.exterior_wall_min_thickness = exterior_wall_min_thickness
        self.interior_wall_min_thickness = interior_wall_min_thickness
        logger.info("WallDetector initialisiert")
    
    def detect(self, image: Image.Image, scale: str = "1:100") -> List:
        """
        Erkennt Wände in einem Bild.
        
        Args:
            image: Eingabebild (PIL-Image)
            scale: Maßstab der Zeichnung
            
        Returns:
            Liste erkannter Wände als DetectedElement-Objekte
        """
        from src.element_detector.detector import DetectedElement, BoundingBox
        
        logger.info("Starte Wand-Erkennung")
        
        detected_walls: List[DetectedElement] = []
        
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
        
        # Horizontale und vertikale Linien suchen
        h_lines = self._detect_horizontal_lines(binary)
        v_lines = self._detect_vertical_lines(binary)
        
        # Linien als Wände klassifizieren
        for line in h_lines + v_lines:
            x, y, w, h, thickness = line
            
            # Bestimme Wandtyp basierend auf Dicke
            if thickness >= self.exterior_wall_min_thickness:
                subtype = "exterior"
                wall_type = "Außenwand"
            elif thickness >= self.interior_wall_min_thickness:
                subtype = "interior"
                wall_type = "Innenwand"
            else:
                continue  # Zu dünn für Wand
            
            # Berechne reale Abmessungen basierend auf Maßstab
            scale_factor = self._parse_scale(scale)
            
            wall = DetectedElement(
                element_type="wall",
                subtype=subtype,
                bbox=BoundingBox(x=x, y=y, width=w, height=h),
                confidence=0.8,
                dimensions={
                    "length_px": max(w, h),
                    "thickness_px": thickness,
                    "length_m": max(w, h) * scale_factor,
                    "thickness_m": thickness * scale_factor,
                },
                properties={
                    "wall_type": wall_type,
                    "orientation": "horizontal" if w > h else "vertical"
                }
            )
            detected_walls.append(wall)
        
        logger.info(f"{len(detected_walls)} Wände erkannt")
        return detected_walls
    
    def _detect_horizontal_lines(
        self,
        binary: np.ndarray,
        min_length: int = 50
    ) -> List[Tuple[int, int, int, int, int]]:
        """
        Erkennt horizontale Linien in einem binären Bild.
        
        Args:
            binary: Binärbild als NumPy-Array
            min_length: Minimale Linienlänge in Pixel
            
        Returns:
            Liste von Tupeln (x, y, width, height, thickness)
        """
        lines = []
        height, width = binary.shape
        
        # Zeilenweise nach zusammenhängenden Pixeln suchen
        visited = np.zeros_like(binary, dtype=bool)
        
        for y in range(height):
            x = 0
            while x < width:
                if binary[y, x] == 1 and not visited[y, x]:
                    # Finde Ende der horizontalen Linie
                    end_x = x
                    while end_x < width and binary[y, end_x] == 1:
                        end_x += 1
                    
                    line_length = end_x - x
                    
                    if line_length >= min_length:
                        # Dicke der Linie bestimmen
                        thickness = self._measure_line_thickness(
                            binary, x, y, "horizontal", line_length
                        )
                        
                        if thickness >= self.interior_wall_min_thickness:
                            lines.append((x, y, line_length, thickness, thickness))
                        
                        # Markiere als besucht
                        for dy in range(thickness):
                            if y + dy < height:
                                visited[y + dy, x:end_x] = True
                    
                    x = end_x
                else:
                    x += 1
        
        return lines
    
    def _detect_vertical_lines(
        self,
        binary: np.ndarray,
        min_length: int = 50
    ) -> List[Tuple[int, int, int, int, int]]:
        """
        Erkennt vertikale Linien in einem binären Bild.
        
        Args:
            binary: Binärbild als NumPy-Array
            min_length: Minimale Linienlänge in Pixel
            
        Returns:
            Liste von Tupeln (x, y, width, height, thickness)
        """
        lines = []
        height, width = binary.shape
        
        # Spaltenweise nach zusammenhängenden Pixeln suchen
        visited = np.zeros_like(binary, dtype=bool)
        
        for x in range(width):
            y = 0
            while y < height:
                if binary[y, x] == 1 and not visited[y, x]:
                    # Finde Ende der vertikalen Linie
                    end_y = y
                    while end_y < height and binary[end_y, x] == 1:
                        end_y += 1
                    
                    line_length = end_y - y
                    
                    if line_length >= min_length:
                        # Dicke der Linie bestimmen
                        thickness = self._measure_line_thickness(
                            binary, x, y, "vertical", line_length
                        )
                        
                        if thickness >= self.interior_wall_min_thickness:
                            lines.append((x, y, thickness, line_length, thickness))
                        
                        # Markiere als besucht
                        for dx in range(thickness):
                            if x + dx < width:
                                visited[y:end_y, x + dx] = True
                    
                    y = end_y
                else:
                    y += 1
        
        return lines
    
    def _measure_line_thickness(
        self,
        binary: np.ndarray,
        x: int,
        y: int,
        orientation: str,
        length: int
    ) -> int:
        """
        Misst die Dicke einer Linie.
        
        Args:
            binary: Binärbild
            x: X-Koordinate des Startpunkts
            y: Y-Koordinate des Startpunkts
            orientation: "horizontal" oder "vertical"
            length: Länge der Linie
            
        Returns:
            Durchschnittliche Dicke in Pixel
        """
        height, width = binary.shape
        thicknesses = []
        
        if orientation == "horizontal":
            # Messe an mehreren Punkten entlang der Linie
            sample_points = min(10, length)
            for i in range(sample_points):
                sample_x = x + (i * length) // sample_points
                if sample_x < width:
                    thickness = 0
                    check_y = y
                    while check_y < height and binary[check_y, sample_x] == 1:
                        thickness += 1
                        check_y += 1
                    thicknesses.append(thickness)
        else:
            # Vertikale Linie
            sample_points = min(10, length)
            for i in range(sample_points):
                sample_y = y + (i * length) // sample_points
                if sample_y < height:
                    thickness = 0
                    check_x = x
                    while check_x < width and binary[sample_y, check_x] == 1:
                        thickness += 1
                        check_x += 1
                    thicknesses.append(thickness)
        
        if thicknesses:
            return int(np.median(thicknesses))
        return 0
    
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
