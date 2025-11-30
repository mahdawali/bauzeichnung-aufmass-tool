"""
ImagePreprocessor - Modul zur Bildvorverarbeitung für die Analyse von Bauzeichnungen.

Dieses Modul enthält Funktionen zur Vorbereitung von Bildern für die
Bauteil-Erkennung und OCR-Verarbeitung.
"""

import logging
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Klasse zur Bildvorverarbeitung für die Bauzeichnungsanalyse.
    
    Diese Klasse bietet Funktionen zur:
    - Graustufen-Konvertierung
    - Rauschreduzierung
    - Kontrastverbesserung
    - Kantenerkennung
    - Binarisierung
    """
    
    def __init__(self) -> None:
        """Initialisiert den ImagePreprocessor."""
        logger.info("ImagePreprocessor initialisiert")
    
    def pil_to_numpy(self, image: Image.Image) -> np.ndarray:
        """
        Konvertiert ein PIL-Bild in ein NumPy-Array.
        
        Args:
            image: PIL-Bild
            
        Returns:
            NumPy-Array des Bildes
        """
        return np.array(image)
    
    def numpy_to_pil(self, array: np.ndarray) -> Image.Image:
        """
        Konvertiert ein NumPy-Array in ein PIL-Bild.
        
        Args:
            array: NumPy-Array
            
        Returns:
            PIL-Bild
        """
        return Image.fromarray(array)
    
    def to_grayscale(self, image: Image.Image) -> Image.Image:
        """
        Konvertiert ein Bild in Graustufen.
        
        Args:
            image: Eingabebild
            
        Returns:
            Graustufenbild
        """
        logger.debug("Konvertiere zu Graustufen")
        return image.convert("L")
    
    def resize(
        self,
        image: Image.Image,
        target_size: Optional[Tuple[int, int]] = None,
        scale_factor: Optional[float] = None
    ) -> Image.Image:
        """
        Skaliert ein Bild auf eine bestimmte Größe oder um einen Faktor.
        
        Args:
            image: Eingabebild
            target_size: Zielgröße als (Breite, Höhe)
            scale_factor: Skalierungsfaktor (z.B. 0.5 für halbe Größe)
            
        Returns:
            Skaliertes Bild
        """
        if target_size:
            logger.debug(f"Skaliere auf {target_size}")
            return image.resize(target_size, Image.Resampling.LANCZOS)
        elif scale_factor:
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            logger.debug(f"Skaliere um Faktor {scale_factor} auf {new_width}x{new_height}")
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return image
    
    def enhance_contrast(self, image: Image.Image, factor: float = 1.5) -> Image.Image:
        """
        Verbessert den Kontrast eines Bildes.
        
        Args:
            image: Eingabebild
            factor: Kontrastfaktor (>1 erhöht Kontrast, <1 verringert)
            
        Returns:
            Kontrastverbessertes Bild
        """
        from PIL import ImageEnhance
        
        logger.debug(f"Erhöhe Kontrast um Faktor {factor}")
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)
    
    def enhance_sharpness(self, image: Image.Image, factor: float = 2.0) -> Image.Image:
        """
        Verbessert die Schärfe eines Bildes.
        
        Args:
            image: Eingabebild
            factor: Schärfefaktor (>1 erhöht Schärfe)
            
        Returns:
            Geschärftes Bild
        """
        from PIL import ImageEnhance
        
        logger.debug(f"Erhöhe Schärfe um Faktor {factor}")
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)
    
    def binarize(self, image: Image.Image, threshold: int = 128) -> Image.Image:
        """
        Binarisiert ein Graustufenbild.
        
        Args:
            image: Graustufenbild
            threshold: Schwellenwert für die Binarisierung (0-255)
            
        Returns:
            Binärbild
        """
        logger.debug(f"Binarisiere mit Schwellenwert {threshold}")
        
        # In Graustufen konvertieren falls noch nicht geschehen
        if image.mode != "L":
            image = image.convert("L")
        
        # Binarisierung mittels NumPy
        array = np.array(image)
        binary = np.where(array > threshold, 255, 0).astype(np.uint8)
        
        return Image.fromarray(binary)
    
    def detect_edges(self, image: Image.Image) -> Image.Image:
        """
        Erkennt Kanten in einem Bild mittels Sobel-Filter.
        
        Args:
            image: Eingabebild
            
        Returns:
            Kantenbild
        """
        logger.debug("Erkenne Kanten")
        
        # In Graustufen konvertieren
        if image.mode != "L":
            image = image.convert("L")
        
        array = np.array(image, dtype=np.float64)
        
        # Sobel-Kernel für x- und y-Richtung
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
        sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
        
        # Einfache Faltung (ohne scipy)
        def convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
            """Einfache 2D-Faltung."""
            h, w = image.shape
            kh, kw = kernel.shape
            pad_h, pad_w = kh // 2, kw // 2
            
            # Padding
            padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='edge')
            
            output = np.zeros_like(image)
            for i in range(h):
                for j in range(w):
                    output[i, j] = np.sum(
                        padded[i:i+kh, j:j+kw] * kernel
                    )
            
            return output
        
        # Kanten in x- und y-Richtung
        edges_x = convolve2d(array, sobel_x)
        edges_y = convolve2d(array, sobel_y)
        
        # Kantenstärke
        edges = np.sqrt(edges_x**2 + edges_y**2)
        edges = np.clip(edges, 0, 255).astype(np.uint8)
        
        return Image.fromarray(edges)
    
    def denoise(self, image: Image.Image) -> Image.Image:
        """
        Reduziert Rauschen in einem Bild mittels Median-Filter.
        
        Args:
            image: Eingabebild
            
        Returns:
            Entrauschtes Bild
        """
        from PIL import ImageFilter
        
        logger.debug("Reduziere Rauschen")
        return image.filter(ImageFilter.MedianFilter(size=3))
    
    def preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Bereitet ein Bild für die OCR-Verarbeitung vor.
        
        Führt folgende Schritte durch:
        1. Graustufen-Konvertierung
        2. Rauschreduzierung
        3. Kontrastverbesserung
        4. Binarisierung
        
        Args:
            image: Eingabebild
            
        Returns:
            Vorverarbeitetes Bild
        """
        logger.info("Bereite Bild für OCR vor")
        
        # Graustufen
        processed = self.to_grayscale(image)
        
        # Entrauschen
        processed = self.denoise(processed)
        
        # Kontrast verbessern
        processed = self.enhance_contrast(processed, factor=1.5)
        
        # Binarisieren
        processed = self.binarize(processed, threshold=128)
        
        return processed
    
    def preprocess_for_detection(self, image: Image.Image) -> Image.Image:
        """
        Bereitet ein Bild für die Bauteil-Erkennung vor.
        
        Führt folgende Schritte durch:
        1. Graustufen-Konvertierung
        2. Kontrastverbesserung
        3. Schärfeverbesserung
        
        Args:
            image: Eingabebild
            
        Returns:
            Vorverarbeitetes Bild
        """
        logger.info("Bereite Bild für Bauteil-Erkennung vor")
        
        # Graustufen
        processed = self.to_grayscale(image)
        
        # Kontrast verbessern
        processed = self.enhance_contrast(processed, factor=1.3)
        
        # Schärfe verbessern
        processed = self.enhance_sharpness(processed, factor=1.5)
        
        return processed
