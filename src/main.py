"""
BauzeichnungAnalyzer - Hauptmodul für das Bauzeichnung-Aufmaß-Tool.

Dieses Modul bietet die Hauptklasse zur Analyse von Bauzeichnungen
und zur automatischen Mengenermittlung.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from src.pdf_parser.pdf_reader import PDFReader
from src.image_processor.preprocessor import ImagePreprocessor
from src.element_detector.detector import ElementDetector, DetectedElement
from src.ocr.text_extractor import TextExtractor, DimensionInfo, TextRegion
from src.quantity_calculator.calculator import QuantityCalculator, QuantityResult
from src.export.exporter import Exporter

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """
    Ergebnis einer Bauzeichnungsanalyse.
    
    Attributes:
        source_file: Pfad zur Quelldatei
        scale: Verwendeter Maßstab
        elements: Alle erkannten Bauteile
        dimensions: Erkannte Maßangaben
        labels: Erkannte Beschriftungen
        quantities: Berechnete Mengen
    """
    source_file: str
    scale: str
    elements: List[DetectedElement] = field(default_factory=list)
    dimensions: List[DimensionInfo] = field(default_factory=list)
    labels: List[TextRegion] = field(default_factory=list)
    quantities: Optional[QuantityResult] = None
    _exporter: Optional[Exporter] = field(default=None, repr=False)
    
    def get_walls(self) -> List[DetectedElement]:
        """Gibt alle erkannten Wände zurück."""
        return [e for e in self.elements if e.element_type == "wall"]
    
    def get_exterior_walls(self) -> List[DetectedElement]:
        """Gibt alle Außenwände zurück."""
        return [e for e in self.elements if e.element_type == "wall" and e.subtype == "exterior"]
    
    def get_interior_walls(self) -> List[DetectedElement]:
        """Gibt alle Innenwände zurück."""
        return [e for e in self.elements if e.element_type == "wall" and e.subtype == "interior"]
    
    def get_windows(self) -> List[DetectedElement]:
        """Gibt alle erkannten Fenster zurück."""
        return [e for e in self.elements if e.element_type == "window"]
    
    def get_doors(self) -> List[DetectedElement]:
        """Gibt alle erkannten Türen zurück."""
        return [e for e in self.elements if e.element_type == "door"]
    
    def get_columns(self) -> List[DetectedElement]:
        """Gibt alle erkannten Stützen zurück."""
        return [e for e in self.elements if e.element_type == "column"]
    
    def get_beams(self) -> List[DetectedElement]:
        """Gibt alle erkannten Unterzüge zurück."""
        return [e for e in self.elements if e.element_type == "beam"]
    
    def get_slabs(self) -> List[DetectedElement]:
        """Gibt alle erkannten Decken zurück."""
        return [e for e in self.elements if e.element_type == "slab"]
    
    def calculate_quantities(self) -> QuantityResult:
        """
        Berechnet Mengen für alle erkannten Elemente.
        
        Returns:
            QuantityResult mit allen Mengenpositionen
        """
        if self.quantities is None:
            calculator = QuantityCalculator()
            self.quantities = calculator.calculate(self.elements)
        return self.quantities
    
    def export_to_excel(self, output_path: Union[str, Path]) -> Path:
        """
        Exportiert die Aufmaß-Liste als Excel-Datei.
        
        Args:
            output_path: Ausgabepfad
            
        Returns:
            Pfad zur erstellten Datei
        """
        if self._exporter is None:
            self._exporter = Exporter(project_name=Path(self.source_file).stem)
        
        quantities = self.calculate_quantities()
        return self._exporter.export_to_excel(quantities, output_path)
    
    def export_to_csv(self, output_path: Union[str, Path]) -> Path:
        """
        Exportiert die Aufmaß-Liste als CSV-Datei.
        
        Args:
            output_path: Ausgabepfad
            
        Returns:
            Pfad zur erstellten Datei
        """
        if self._exporter is None:
            self._exporter = Exporter(project_name=Path(self.source_file).stem)
        
        quantities = self.calculate_quantities()
        return self._exporter.export_to_csv(quantities, output_path)
    
    def export_to_json(self, output_path: Union[str, Path]) -> Path:
        """
        Exportiert die Aufmaß-Liste als JSON-Datei.
        
        Args:
            output_path: Ausgabepfad
            
        Returns:
            Pfad zur erstellten Datei
        """
        if self._exporter is None:
            self._exporter = Exporter(project_name=Path(self.source_file).stem)
        
        quantities = self.calculate_quantities()
        return self._exporter.export_to_json(quantities, output_path)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Gibt eine Zusammenfassung der Analyse zurück.
        
        Returns:
            Dictionary mit Analysezusammenfassung
        """
        quantities = self.calculate_quantities()
        
        return {
            "source_file": self.source_file,
            "scale": self.scale,
            "element_counts": {
                "walls": len(self.get_walls()),
                "exterior_walls": len(self.get_exterior_walls()),
                "interior_walls": len(self.get_interior_walls()),
                "windows": len(self.get_windows()),
                "doors": len(self.get_doors()),
                "columns": len(self.get_columns()),
                "beams": len(self.get_beams()),
                "slabs": len(self.get_slabs()),
            },
            "total_elements": len(self.elements),
            "dimensions_found": len(self.dimensions),
            "labels_found": len(self.labels),
            "quantity_summary": quantities.summary if quantities else {}
        }


class BauzeichnungAnalyzer:
    """
    Hauptklasse zur Analyse von Bauzeichnungen.
    
    Diese Klasse bietet eine einfache API zur:
    - Analyse von PDF- und Bilddateien
    - Erkennung von Bauteilen
    - Extraktion von Maßangaben
    - Mengenberechnung
    - Export in verschiedene Formate
    
    Beispiel:
        >>> analyzer = BauzeichnungAnalyzer()
        >>> result = analyzer.analyze("bauzeichnung.pdf", scale="1:100")
        >>> walls = result.get_walls()
        >>> result.export_to_excel("aufmass.xlsx")
    
    Attributes:
        pdf_reader: PDF-Leser für die Konvertierung
        preprocessor: Bildvorverarbeiter
        detector: Bauteil-Detektor
        text_extractor: OCR-Textextraktor
        calculator: Mengenberechner
    """
    
    def __init__(
        self,
        dpi: int = 300,
        ocr_lang: str = "deu",
        wall_height: float = 2.75,
        slab_thickness: float = 0.20
    ) -> None:
        """
        Initialisiert den BauzeichnungAnalyzer.
        
        Args:
            dpi: Auflösung für PDF-Konvertierung (Standard: 300)
            ocr_lang: Sprache für OCR (Standard: "deu")
            wall_height: Standard-Wandhöhe in Metern (Standard: 2.75)
            slab_thickness: Standard-Deckendicke in Metern (Standard: 0.20)
        """
        self.pdf_reader = PDFReader(dpi=dpi)
        self.preprocessor = ImagePreprocessor()
        self.detector = ElementDetector()
        self.text_extractor = TextExtractor(lang=ocr_lang)
        self.calculator = QuantityCalculator(
            default_wall_height=wall_height,
            default_slab_thickness=slab_thickness
        )
        
        logger.info(
            f"BauzeichnungAnalyzer initialisiert "
            f"(DPI: {dpi}, OCR: {ocr_lang})"
        )
    
    def analyze(
        self,
        file_path: Union[str, Path],
        scale: str = "1:100",
        pages: Optional[List[int]] = None
    ) -> AnalysisResult:
        """
        Analysiert eine Bauzeichnung.
        
        Args:
            file_path: Pfad zur PDF- oder Bilddatei
            scale: Maßstab der Zeichnung (z.B. "1:100")
            pages: Zu analysierende Seiten (nur für PDF, None = alle)
            
        Returns:
            AnalysisResult mit allen erkannten Elementen und Berechnungen
            
        Raises:
            FileNotFoundError: Wenn die Datei nicht gefunden wird
            ValueError: Wenn das Dateiformat nicht unterstützt wird
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")
        
        logger.info(f"Starte Analyse: {file_path} (Maßstab: {scale})")
        
        # Bilder laden
        images = self._load_images(file_path, pages)
        
        if not images:
            raise ValueError("Keine Bilder zum Analysieren gefunden")
        
        logger.info(f"{len(images)} Bild(er) geladen")
        
        # Analyse durchführen
        all_elements: List[DetectedElement] = []
        all_dimensions: List[DimensionInfo] = []
        all_labels: List[TextRegion] = []
        
        for i, image in enumerate(images, start=1):
            logger.info(f"Analysiere Bild {i}/{len(images)}")
            
            # Vorverarbeitung
            processed_image = self.preprocessor.preprocess_for_detection(image)
            
            # Bauteile erkennen
            elements = self.detector.detect_all(image, scale)
            all_elements.extend(elements)
            
            # Maßangaben extrahieren (OCR)
            try:
                ocr_image = self.preprocessor.preprocess_for_ocr(image)
                dimensions = self.text_extractor.extract_dimensions(ocr_image)
                all_dimensions.extend(dimensions)
                
                labels = self.text_extractor.extract_labels(ocr_image)
                all_labels.extend(labels)
            except Exception as e:
                logger.warning(f"OCR fehlgeschlagen: {e}")
        
        # Ergebnis erstellen
        result = AnalysisResult(
            source_file=str(file_path),
            scale=scale,
            elements=all_elements,
            dimensions=all_dimensions,
            labels=all_labels
        )
        
        # Mengen berechnen
        result.quantities = self.calculator.calculate(all_elements)
        
        logger.info(
            f"Analyse abgeschlossen: "
            f"{len(all_elements)} Elemente, "
            f"{len(all_dimensions)} Maße, "
            f"{len(all_labels)} Beschriftungen"
        )
        
        return result
    
    def analyze_image(
        self,
        image: Image.Image,
        scale: str = "1:100",
        source_name: str = "image"
    ) -> AnalysisResult:
        """
        Analysiert ein PIL-Bild direkt.
        
        Args:
            image: PIL-Image zur Analyse
            scale: Maßstab der Zeichnung
            source_name: Name für die Quelle
            
        Returns:
            AnalysisResult mit allen erkannten Elementen
        """
        logger.info(f"Starte Bildanalyse (Maßstab: {scale})")
        
        # Vorverarbeitung
        processed_image = self.preprocessor.preprocess_for_detection(image)
        
        # Bauteile erkennen
        elements = self.detector.detect_all(image, scale)
        
        # Maßangaben extrahieren (OCR)
        dimensions = []
        labels = []
        
        try:
            ocr_image = self.preprocessor.preprocess_for_ocr(image)
            dimensions = self.text_extractor.extract_dimensions(ocr_image)
            labels = self.text_extractor.extract_labels(ocr_image)
        except Exception as e:
            logger.warning(f"OCR fehlgeschlagen: {e}")
        
        # Ergebnis erstellen
        result = AnalysisResult(
            source_file=source_name,
            scale=scale,
            elements=elements,
            dimensions=dimensions,
            labels=labels
        )
        
        # Mengen berechnen
        result.quantities = self.calculator.calculate(elements)
        
        return result
    
    def _load_images(
        self,
        file_path: Path,
        pages: Optional[List[int]] = None
    ) -> List[Image.Image]:
        """
        Lädt Bilder aus einer Datei.
        
        Args:
            file_path: Pfad zur Datei
            pages: Zu ladende Seiten (nur für PDF)
            
        Returns:
            Liste von PIL-Bildern
        """
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            images = self.pdf_reader.read_pdf(file_path)
            
            if pages:
                # Nur angegebene Seiten verwenden
                images = [images[i-1] for i in pages if 0 < i <= len(images)]
            
            return images
        
        elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"]:
            return [self.pdf_reader.read_image(file_path)]
        
        else:
            raise ValueError(
                f"Nicht unterstütztes Dateiformat: {suffix}. "
                f"Unterstützt: PDF, PNG, JPG, JPEG, TIFF, BMP"
            )
    
    def detect_elements(
        self,
        image: Image.Image,
        scale: str = "1:100"
    ) -> List[DetectedElement]:
        """
        Erkennt nur Bauteile in einem Bild (ohne OCR und Mengenberechnung).
        
        Args:
            image: PIL-Image
            scale: Maßstab
            
        Returns:
            Liste erkannter Bauteile
        """
        return self.detector.detect_all(image, scale)
    
    def extract_text(self, image: Image.Image) -> str:
        """
        Extrahiert Text aus einem Bild.
        
        Args:
            image: PIL-Image
            
        Returns:
            Extrahierter Text
        """
        ocr_image = self.preprocessor.preprocess_for_ocr(image)
        return self.text_extractor.get_full_text(ocr_image)


def main() -> None:
    """Hauptfunktion für Kommandozeilenbetrieb."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Bauzeichnung-Analyse-Tool - Automatische Mengenermittlung"
    )
    parser.add_argument(
        "input",
        help="Eingabedatei (PDF oder Bild)"
    )
    parser.add_argument(
        "-s", "--scale",
        default="1:100",
        help="Maßstab der Zeichnung (Standard: 1:100)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Ausgabedatei (Excel, CSV oder JSON)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["excel", "csv", "json", "all"],
        default="excel",
        help="Ausgabeformat (Standard: excel)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Ausführliche Ausgabe"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Analyse durchführen
    analyzer = BauzeichnungAnalyzer()
    result = analyzer.analyze(args.input, scale=args.scale)
    
    # Zusammenfassung ausgeben
    summary = result.get_summary()
    print("\n=== Analyseergebnis ===")
    print(f"Datei: {summary['source_file']}")
    print(f"Maßstab: {summary['scale']}")
    print(f"\nErkannte Elemente:")
    for key, count in summary['element_counts'].items():
        if count > 0:
            print(f"  - {key}: {count}")
    
    # Export
    if args.output:
        output_path = Path(args.output)
        
        if args.format == "all":
            exporter = Exporter()
            results = exporter.export_all(
                result.calculate_quantities(),
                output_path.parent,
                output_path.stem
            )
            print(f"\nExportiert nach: {list(results.values())}")
        elif args.format == "excel":
            path = result.export_to_excel(output_path)
            print(f"\nExportiert nach: {path}")
        elif args.format == "csv":
            path = result.export_to_csv(output_path)
            print(f"\nExportiert nach: {path}")
        elif args.format == "json":
            path = result.export_to_json(output_path)
            print(f"\nExportiert nach: {path}")


if __name__ == "__main__":
    main()
