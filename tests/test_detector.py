"""
Unit-Tests für das Bauzeichnung-Aufmaß-Tool.

Dieses Modul enthält Tests für die verschiedenen Detektoren und
Berechnungsfunktionen.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image


class TestElementDetector(unittest.TestCase):
    """Tests für den ElementDetector."""
    
    def setUp(self):
        """Test-Setup."""
        from src.element_detector.detector import ElementDetector
        self.detector = ElementDetector()
    
    def test_parse_scale_1_100(self):
        """Test: Maßstab 1:100 parsen."""
        scale_factor = self.detector.parse_scale("1:100")
        self.assertAlmostEqual(scale_factor, 0.01)
    
    def test_parse_scale_1_50(self):
        """Test: Maßstab 1:50 parsen."""
        scale_factor = self.detector.parse_scale("1:50")
        self.assertAlmostEqual(scale_factor, 0.02)
    
    def test_parse_scale_invalid(self):
        """Test: Ungültiger Maßstab gibt Standard zurück."""
        scale_factor = self.detector.parse_scale("invalid")
        self.assertAlmostEqual(scale_factor, 0.01)  # Standard: 1:100
    
    def test_detect_all_returns_list(self):
        """Test: detect_all gibt eine Liste zurück."""
        # Erstelle ein Test-Bild
        test_image = Image.new("RGB", (100, 100), color="white")
        
        result = self.detector.detect_all(test_image)
        
        self.assertIsInstance(result, list)
    
    def test_filter_by_type(self):
        """Test: Filter nach Elementtyp."""
        from src.element_detector.detector import DetectedElement
        
        elements = [
            DetectedElement(element_type="wall"),
            DetectedElement(element_type="window"),
            DetectedElement(element_type="wall"),
            DetectedElement(element_type="door"),
        ]
        
        walls = self.detector.filter_by_type(elements, "wall")
        
        self.assertEqual(len(walls), 2)
        self.assertTrue(all(e.element_type == "wall" for e in walls))
    
    def test_filter_by_confidence(self):
        """Test: Filter nach Konfidenz."""
        from src.element_detector.detector import DetectedElement
        
        elements = [
            DetectedElement(element_type="wall", confidence=0.9),
            DetectedElement(element_type="wall", confidence=0.3),
            DetectedElement(element_type="wall", confidence=0.7),
        ]
        
        filtered = self.detector.filter_by_confidence(elements, min_confidence=0.5)
        
        self.assertEqual(len(filtered), 2)
        self.assertTrue(all(e.confidence >= 0.5 for e in filtered))


class TestBoundingBox(unittest.TestCase):
    """Tests für BoundingBox."""
    
    def test_center(self):
        """Test: Mittelpunkt-Berechnung."""
        from src.element_detector.detector import BoundingBox
        
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        
        center = bbox.center
        
        self.assertEqual(center, (60, 45))
    
    def test_area(self):
        """Test: Flächen-Berechnung."""
        from src.element_detector.detector import BoundingBox
        
        bbox = BoundingBox(x=0, y=0, width=10, height=20)
        
        self.assertEqual(bbox.area, 200)


class TestWallDetector(unittest.TestCase):
    """Tests für den WallDetector."""
    
    def setUp(self):
        """Test-Setup."""
        from src.element_detector.wall_detector import WallDetector
        self.detector = WallDetector()
    
    def test_detect_returns_list(self):
        """Test: detect gibt eine Liste zurück."""
        test_image = Image.new("RGB", (100, 100), color="white")
        
        result = self.detector.detect(test_image)
        
        self.assertIsInstance(result, list)
    
    def test_parse_scale(self):
        """Test: Maßstab parsen."""
        self.assertAlmostEqual(self.detector._parse_scale("1:100"), 0.01)
        self.assertAlmostEqual(self.detector._parse_scale("1:50"), 0.02)


class TestQuantityCalculator(unittest.TestCase):
    """Tests für den QuantityCalculator."""
    
    def setUp(self):
        """Test-Setup."""
        from src.quantity_calculator.calculator import QuantityCalculator
        self.calculator = QuantityCalculator(
            default_wall_height=2.75,
            default_slab_thickness=0.20
        )
    
    def test_calculate_empty_list(self):
        """Test: Berechnung mit leerer Liste."""
        from src.quantity_calculator.calculator import QuantityResult
        
        result = self.calculator.calculate([])
        
        self.assertIsInstance(result, QuantityResult)
        self.assertEqual(len(result.items), 0)
    
    def test_calculate_wall(self):
        """Test: Wandberechnung."""
        from src.element_detector.detector import DetectedElement
        
        wall = DetectedElement(
            element_type="wall",
            subtype="exterior",
            dimensions={"length_m": 5.0, "thickness_m": 0.24},
            properties={"wall_type": "Außenwand"}
        )
        
        result = self.calculator.calculate([wall])
        
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].category, "Wände")
        # 5.0m * 2.75m = 13.75 m²
        self.assertAlmostEqual(result.items[0].quantity, 13.75, places=2)


class TestQuantityResult(unittest.TestCase):
    """Tests für QuantityResult."""
    
    def test_filter_by_category(self):
        """Test: Filter nach Kategorie."""
        from src.quantity_calculator.calculator import QuantityResult, QuantityItem
        
        result = QuantityResult()
        result.items = [
            QuantityItem(position=1, category="Wände", description="", quantity=1, unit="m²"),
            QuantityItem(position=2, category="Fenster", description="", quantity=2, unit="Stück"),
            QuantityItem(position=3, category="Wände", description="", quantity=3, unit="m²"),
        ]
        
        walls = result.filter_by_category("Wände")
        
        self.assertEqual(len(walls), 2)


class TestImagePreprocessor(unittest.TestCase):
    """Tests für den ImagePreprocessor."""
    
    def setUp(self):
        """Test-Setup."""
        from src.image_processor.preprocessor import ImagePreprocessor
        self.preprocessor = ImagePreprocessor()
    
    def test_to_grayscale(self):
        """Test: Graustufen-Konvertierung."""
        rgb_image = Image.new("RGB", (100, 100), color=(255, 0, 0))
        
        gray_image = self.preprocessor.to_grayscale(rgb_image)
        
        self.assertEqual(gray_image.mode, "L")
    
    def test_resize_with_scale_factor(self):
        """Test: Skalierung mit Faktor."""
        image = Image.new("RGB", (100, 100))
        
        resized = self.preprocessor.resize(image, scale_factor=0.5)
        
        self.assertEqual(resized.size, (50, 50))
    
    def test_resize_with_target_size(self):
        """Test: Skalierung auf Zielgröße."""
        image = Image.new("RGB", (100, 100))
        
        resized = self.preprocessor.resize(image, target_size=(200, 150))
        
        self.assertEqual(resized.size, (200, 150))
    
    def test_binarize(self):
        """Test: Binarisierung."""
        gray_image = Image.new("L", (10, 10), color=128)
        
        binary = self.preprocessor.binarize(gray_image, threshold=100)
        
        # Alle Pixel sollten weiß sein (>100)
        array = np.array(binary)
        self.assertTrue(np.all(array == 255))
    
    def test_pil_to_numpy_and_back(self):
        """Test: Konvertierung PIL <-> NumPy."""
        original = Image.new("RGB", (10, 10), color=(128, 64, 32))
        
        array = self.preprocessor.pil_to_numpy(original)
        restored = self.preprocessor.numpy_to_pil(array)
        
        self.assertEqual(original.size, restored.size)


class TestExporter(unittest.TestCase):
    """Tests für den Exporter."""
    
    def setUp(self):
        """Test-Setup."""
        from src.export.exporter import Exporter
        self.exporter = Exporter(project_name="Test-Projekt")
    
    def test_export_to_json(self):
        """Test: JSON-Export."""
        import json
        import tempfile
        from src.quantity_calculator.calculator import QuantityResult, QuantityItem
        
        result = QuantityResult()
        result.items = [
            QuantityItem(position=1, category="Wände", description="Test", quantity=10, unit="m²"),
        ]
        result.summary = {"Wände": {"m²": 10}}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            
            created_path = self.exporter.export_to_json(result, output_path)
            
            self.assertTrue(created_path.exists())
            
            with open(created_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.assertIn("items", data)
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["category"], "Wände")


class TestTextExtractor(unittest.TestCase):
    """Tests für den TextExtractor."""
    
    def setUp(self):
        """Test-Setup."""
        from src.ocr.text_extractor import TextExtractor
        self.extractor = TextExtractor(lang="deu")
    
    def test_parse_dimension_meters(self):
        """Test: Maßangabe in Metern parsen."""
        result = self.extractor._parse_dimension("3,50 m")
        
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.value, 3.5)
        self.assertEqual(result.unit, "m")
    
    def test_parse_dimension_centimeters(self):
        """Test: Maßangabe in Zentimetern parsen."""
        result = self.extractor._parse_dimension("350 cm")
        
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.value, 3.5)
        self.assertEqual(result.unit, "cm")
    
    def test_parse_dimension_millimeters(self):
        """Test: Maßangabe in Millimetern parsen."""
        result = self.extractor._parse_dimension("3500 mm")
        
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.value, 3.5)
        self.assertEqual(result.unit, "mm")
    
    def test_parse_dimension_no_match(self):
        """Test: Kein Maß erkannt."""
        result = self.extractor._parse_dimension("Wohnzimmer")
        
        self.assertIsNone(result)


class TestAnalysisResult(unittest.TestCase):
    """Tests für AnalysisResult."""
    
    def test_get_walls(self):
        """Test: Wände abrufen."""
        from src.main import AnalysisResult
        from src.element_detector.detector import DetectedElement
        
        result = AnalysisResult(
            source_file="test.pdf",
            scale="1:100",
            elements=[
                DetectedElement(element_type="wall", subtype="exterior"),
                DetectedElement(element_type="window"),
                DetectedElement(element_type="wall", subtype="interior"),
            ]
        )
        
        walls = result.get_walls()
        
        self.assertEqual(len(walls), 2)
    
    def test_get_exterior_walls(self):
        """Test: Außenwände abrufen."""
        from src.main import AnalysisResult
        from src.element_detector.detector import DetectedElement
        
        result = AnalysisResult(
            source_file="test.pdf",
            scale="1:100",
            elements=[
                DetectedElement(element_type="wall", subtype="exterior"),
                DetectedElement(element_type="wall", subtype="interior"),
                DetectedElement(element_type="wall", subtype="exterior"),
            ]
        )
        
        exterior_walls = result.get_exterior_walls()
        
        self.assertEqual(len(exterior_walls), 2)
    
    def test_get_summary(self):
        """Test: Zusammenfassung abrufen."""
        from src.main import AnalysisResult
        from src.element_detector.detector import DetectedElement
        
        result = AnalysisResult(
            source_file="test.pdf",
            scale="1:100",
            elements=[
                DetectedElement(element_type="wall", subtype="exterior", 
                              dimensions={"length_m": 5}, properties={"wall_type": "Außenwand"}),
                DetectedElement(element_type="window",
                              dimensions={"width_m": 1, "height_m": 1.2}, properties={"window_type": "Fenster"}),
            ]
        )
        
        summary = result.get_summary()
        
        self.assertIn("element_counts", summary)
        self.assertEqual(summary["element_counts"]["walls"], 1)
        self.assertEqual(summary["element_counts"]["windows"], 1)


class TestBauzeichnungAnalyzer(unittest.TestCase):
    """Tests für BauzeichnungAnalyzer."""
    
    def test_init(self):
        """Test: Initialisierung."""
        from src.main import BauzeichnungAnalyzer
        
        analyzer = BauzeichnungAnalyzer()
        
        self.assertIsNotNone(analyzer.pdf_reader)
        self.assertIsNotNone(analyzer.preprocessor)
        self.assertIsNotNone(analyzer.detector)
        self.assertIsNotNone(analyzer.text_extractor)
        self.assertIsNotNone(analyzer.calculator)
    
    def test_analyze_image(self):
        """Test: Bildanalyse."""
        from src.main import BauzeichnungAnalyzer, AnalysisResult
        
        analyzer = BauzeichnungAnalyzer()
        test_image = Image.new("RGB", (100, 100), color="white")
        
        result = analyzer.analyze_image(test_image, scale="1:100")
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.scale, "1:100")
    
    def test_analyze_file_not_found(self):
        """Test: Datei nicht gefunden."""
        from src.main import BauzeichnungAnalyzer
        
        analyzer = BauzeichnungAnalyzer()
        
        with self.assertRaises(FileNotFoundError):
            analyzer.analyze("nicht_existierende_datei.pdf")
    
    def test_analyze_unsupported_format(self):
        """Test: Nicht unterstütztes Format."""
        import tempfile
        from src.main import BauzeichnungAnalyzer
        
        analyzer = BauzeichnungAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        
        try:
            with self.assertRaises(ValueError):
                analyzer.analyze(temp_path)
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    unittest.main()
