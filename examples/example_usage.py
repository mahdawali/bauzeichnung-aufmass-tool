"""
Beispiel zur Verwendung des Bauzeichnung-Aufmaß-Tools.

Dieses Skript zeigt, wie das Tool zur Analyse von Bauzeichnungen
und zur Mengenermittlung verwendet werden kann.
"""

from pathlib import Path

# Import der Hauptklasse
from src.main import BauzeichnungAnalyzer

def beispiel_pdf_analyse():
    """
    Beispiel: Analyse einer PDF-Bauzeichnung.
    
    Zeigt die typische Verwendung des Tools für eine PDF-Datei.
    """
    print("=" * 60)
    print("Beispiel 1: PDF-Bauzeichnung analysieren")
    print("=" * 60)
    
    # Analyzer erstellen
    analyzer = BauzeichnungAnalyzer(
        dpi=300,           # Auflösung für PDF-Konvertierung
        ocr_lang="deu",    # Sprache für OCR (Deutsch)
        wall_height=2.75,  # Standard-Wandhöhe in Metern
        slab_thickness=0.20  # Standard-Deckendicke in Metern
    )
    
    # Beispiel-Pfad (muss durch echte Datei ersetzt werden)
    pdf_path = "bauzeichnung.pdf"
    
    # Prüfe ob Datei existiert
    if not Path(pdf_path).exists():
        print(f"Hinweis: Datei '{pdf_path}' nicht gefunden.")
        print("Erstelle Demo-Ergebnis mit Testbild...")
        
        # Demo mit Testbild
        from PIL import Image
        test_image = Image.new("RGB", (800, 600), color="white")
        result = analyzer.analyze_image(test_image, scale="1:100", source_name="Demo")
    else:
        # PDF analysieren
        result = analyzer.analyze(
            pdf_path,
            scale="1:100",  # Maßstab der Zeichnung
            pages=None      # Alle Seiten analysieren (oder z.B. [1, 2] für Seiten 1 und 2)
        )
    
    # Ergebnisse abrufen
    print("\n--- Erkannte Bauteile ---")
    print(f"Wände gesamt: {len(result.get_walls())}")
    print(f"  - Außenwände: {len(result.get_exterior_walls())}")
    print(f"  - Innenwände: {len(result.get_interior_walls())}")
    print(f"Fenster: {len(result.get_windows())}")
    print(f"Türen: {len(result.get_doors())}")
    print(f"Stützen: {len(result.get_columns())}")
    print(f"Unterzüge: {len(result.get_beams())}")
    print(f"Decken: {len(result.get_slabs())}")
    
    # Mengenermittlung
    print("\n--- Mengenermittlung ---")
    quantities = result.calculate_quantities()
    
    for item in quantities.items[:5]:  # Erste 5 Positionen zeigen
        print(f"Pos. {item.position}: {item.category} - {item.description}")
        print(f"       {item.quantity:.2f} {item.unit}")
    
    # Zusammenfassung
    print("\n--- Zusammenfassung ---")
    for category, totals in quantities.summary.items():
        for unit, total in totals.items():
            print(f"{category}: {total:.2f} {unit}")
    
    return result


def beispiel_export():
    """
    Beispiel: Export der Aufmaß-Liste.
    
    Zeigt, wie Ergebnisse in verschiedene Formate exportiert werden.
    """
    print("\n" + "=" * 60)
    print("Beispiel 2: Export der Aufmaß-Liste")
    print("=" * 60)
    
    from PIL import Image
    
    # Analyzer erstellen und Demo-Analyse durchführen
    analyzer = BauzeichnungAnalyzer()
    test_image = Image.new("RGB", (800, 600), color="white")
    result = analyzer.analyze_image(test_image, scale="1:100")
    
    # Export als Excel
    try:
        excel_path = result.export_to_excel("/tmp/aufmass.xlsx")
        print(f"Excel exportiert nach: {excel_path}")
    except ImportError:
        print("Hinweis: openpyxl nicht installiert, Excel-Export übersprungen")
    
    # Export als CSV
    try:
        csv_path = result.export_to_csv("/tmp/aufmass.csv")
        print(f"CSV exportiert nach: {csv_path}")
    except Exception as e:
        print(f"CSV-Export fehlgeschlagen: {e}")
    
    # Export als JSON
    json_path = result.export_to_json("/tmp/aufmass.json")
    print(f"JSON exportiert nach: {json_path}")
    
    # JSON-Inhalt anzeigen
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n--- JSON-Inhalt (Auszug) ---")
    print(f"Projekt: {data['meta']['project_name']}")
    print(f"Erstellt: {data['meta']['created_at']}")
    print(f"Positionen: {data['meta']['total_items']}")


def beispiel_einzelne_komponenten():
    """
    Beispiel: Verwendung einzelner Komponenten.
    
    Zeigt, wie einzelne Module des Tools direkt verwendet werden können.
    """
    print("\n" + "=" * 60)
    print("Beispiel 3: Einzelne Komponenten verwenden")
    print("=" * 60)
    
    from PIL import Image
    import numpy as np
    
    # 1. Bildvorverarbeitung
    from src.image_processor.preprocessor import ImagePreprocessor
    
    preprocessor = ImagePreprocessor()
    
    # Testbild erstellen
    test_image = Image.new("RGB", (200, 200), color="white")
    
    # Vorverarbeiten
    gray = preprocessor.to_grayscale(test_image)
    print(f"Graustufenbild: {gray.mode}, {gray.size}")
    
    enhanced = preprocessor.enhance_contrast(gray, factor=1.5)
    print(f"Kontrast erhöht: {enhanced.mode}, {enhanced.size}")
    
    # 2. Element-Erkennung
    from src.element_detector.detector import ElementDetector
    
    detector = ElementDetector()
    
    # Maßstab parsen
    scale_factor = detector.parse_scale("1:50")
    print(f"Maßstab 1:50 = Faktor {scale_factor}")
    
    # 3. Mengenberechnung
    from src.quantity_calculator.calculator import QuantityCalculator
    from src.element_detector.detector import DetectedElement
    
    calculator = QuantityCalculator(default_wall_height=3.0)
    
    # Test-Elemente
    test_elements = [
        DetectedElement(
            element_type="wall",
            subtype="exterior",
            dimensions={"length_m": 10.0, "thickness_m": 0.30},
            properties={"wall_type": "Außenwand"}
        ),
        DetectedElement(
            element_type="window",
            dimensions={"width_m": 1.5, "height_m": 1.2},
            properties={"window_type": "Standard-Fenster"}
        ),
    ]
    
    result = calculator.calculate(test_elements)
    
    print("\n--- Berechnete Mengen ---")
    for item in result.items:
        print(f"  {item.category}: {item.quantity:.2f} {item.unit}")


def beispiel_api_verwendung():
    """
    Beispiel: Einfache API-Verwendung.
    
    Zeigt die grundlegende Verwendung wie in der README beschrieben.
    """
    print("\n" + "=" * 60)
    print("Beispiel 4: Einfache API-Verwendung")
    print("=" * 60)
    
    from src.main import BauzeichnungAnalyzer
    from PIL import Image
    
    # Analyzer erstellen
    analyzer = BauzeichnungAnalyzer()
    
    # Demo mit Testbild
    test_image = Image.new("RGB", (800, 600), color="white")
    result = analyzer.analyze_image(test_image, scale="1:100")
    
    # Bauteile abrufen
    walls = result.get_walls()
    windows = result.get_windows()
    doors = result.get_doors()
    
    print(f"Erkannte Wände: {len(walls)}")
    print(f"Erkannte Fenster: {len(windows)}")
    print(f"Erkannte Türen: {len(doors)}")
    
    # Mengenermittlung
    quantities = result.calculate_quantities()
    print(f"Berechnete Positionen: {len(quantities.items)}")
    
    # Zusammenfassung
    summary = result.get_summary()
    print(f"\nZusammenfassung:")
    print(f"  Quelldatei: {summary['source_file']}")
    print(f"  Maßstab: {summary['scale']}")
    print(f"  Gesamt Elemente: {summary['total_elements']}")


def main():
    """Hauptfunktion - führt alle Beispiele aus."""
    print("\n" + "#" * 60)
    print("# Bauzeichnung-Aufmaß-Tool - Beispiele")
    print("#" * 60)
    
    # Beispiele ausführen
    beispiel_pdf_analyse()
    beispiel_export()
    beispiel_einzelne_komponenten()
    beispiel_api_verwendung()
    
    print("\n" + "#" * 60)
    print("# Alle Beispiele abgeschlossen!")
    print("#" * 60)


if __name__ == "__main__":
    main()
