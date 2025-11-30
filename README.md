# Bauzeichnung-Aufmaß-Tool

Ein Python-Tool zur automatischen Analyse von Bauzeichnungen und Mengenermittlung.

## Funktionen

- **PDF-Import**: PDF-Dateien einlesen und in Bilder konvertieren
- **Bauteil-Erkennung**: Automatische Erkennung von:
  - Wänden (Außen- und Innenwände)
  - Fenstern und Türen
  - Stützen und Unterzügen
  - Decken und Fundamenten
- **OCR**: Maßangaben und Beschriftungen aus Zeichnungen extrahieren
- **Mengenberechnung**: Längen (m), Flächen (m²), Volumen (m³), Stückzahlen berechnen
- **Export**: Aufmaß-Listen als Excel (.xlsx), CSV und JSON exportieren

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- Poppler (für PDF-Konvertierung)
- Tesseract OCR (für Texterkennung)

### System-Abhängigkeiten installieren

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-deu
```

**macOS:**
```bash
brew install poppler tesseract tesseract-lang
```

**Windows:**
- Poppler: https://github.com/oschwartz10612/poppler-windows/releases
- Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

### Python-Pakete installieren

```bash
# Repository klonen
git clone https://github.com/mahdawali/bauzeichnung-aufmass-tool.git
cd bauzeichnung-aufmass-tool

# Virtuelle Umgebung erstellen (empfohlen)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Paket installieren (optional)
pip install -e .
```

## Verwendung

### Einfaches Beispiel

```python
from src.main import BauzeichnungAnalyzer

# Analyzer erstellen
analyzer = BauzeichnungAnalyzer()

# PDF analysieren
result = analyzer.analyze("bauzeichnung.pdf", scale="1:100")

# Bauteile abrufen
walls = result.get_walls()
windows = result.get_windows()
doors = result.get_doors()

# Mengenermittlung
quantities = result.calculate_quantities()

# Export als Excel
result.export_to_excel("aufmass.xlsx")
```

### Kommandozeile

```bash
# Einfache Analyse mit Excel-Export
python -m src.main bauzeichnung.pdf -o aufmass.xlsx

# Mit spezifischem Maßstab
python -m src.main bauzeichnung.pdf -s 1:50 -o aufmass.xlsx

# Export in alle Formate
python -m src.main bauzeichnung.pdf -f all -o aufmass

# Mit ausführlicher Ausgabe
python -m src.main bauzeichnung.pdf -v -o aufmass.xlsx
```

### Erweiterte Verwendung

```python
from src.main import BauzeichnungAnalyzer

# Analyzer mit benutzerdefinierten Einstellungen
analyzer = BauzeichnungAnalyzer(
    dpi=300,              # PDF-Auflösung
    ocr_lang="deu",       # OCR-Sprache
    wall_height=2.75,     # Standard-Wandhöhe
    slab_thickness=0.20   # Standard-Deckendicke
)

# Analyse durchführen
result = analyzer.analyze(
    "bauzeichnung.pdf",
    scale="1:100",
    pages=[1, 2]  # Nur Seiten 1 und 2
)

# Detaillierte Ergebnisse
summary = result.get_summary()
print(f"Erkannte Elemente: {summary['total_elements']}")

# Mengen nach Kategorie
quantities = result.calculate_quantities()
for category, totals in quantities.summary.items():
    for unit, total in totals.items():
        print(f"{category}: {total:.2f} {unit}")

# Export in verschiedene Formate
result.export_to_excel("aufmass.xlsx")
result.export_to_csv("aufmass.csv")
result.export_to_json("aufmass.json")
```

## Projektstruktur

```
bauzeichnung-aufmass-tool/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Haupteinstiegspunkt (BauzeichnungAnalyzer)
│   ├── pdf_parser/
│   │   ├── __init__.py
│   │   └── pdf_reader.py          # PDF einlesen und konvertieren
│   ├── image_processor/
│   │   ├── __init__.py
│   │   └── preprocessor.py        # Bildvorverarbeitung
│   ├── element_detector/
│   │   ├── __init__.py
│   │   ├── detector.py            # Haupt-Erkennungslogik
│   │   ├── wall_detector.py       # Wand-Erkennung
│   │   ├── opening_detector.py    # Fenster/Türen-Erkennung
│   │   └── structural_detector.py # Stützen/Unterzüge/Decken
│   ├── ocr/
│   │   ├── __init__.py
│   │   └── text_extractor.py      # OCR für Maßangaben
│   ├── quantity_calculator/
│   │   ├── __init__.py
│   │   └── calculator.py          # Mengenberechnung
│   └── export/
│       ├── __init__.py
│       └── exporter.py            # Export (Excel, CSV, JSON)
├── tests/
│   ├── __init__.py
│   └── test_detector.py           # Unit-Tests
├── examples/
│   └── example_usage.py           # Verwendungsbeispiele
├── requirements.txt
├── setup.py
└── .gitignore
```

## Abhängigkeiten

| Paket | Version | Beschreibung |
|-------|---------|--------------|
| pdf2image | ≥1.16.0 | PDF zu Bild Konvertierung |
| opencv-python | ≥4.8.0 | Bildverarbeitung |
| pytesseract | ≥0.3.10 | OCR-Texterkennung |
| numpy | ≥1.24.0 | Numerische Berechnungen |
| pandas | ≥2.0.0 | Datenverarbeitung |
| openpyxl | ≥3.1.0 | Excel-Export |
| Pillow | ≥10.0.0 | Bildverarbeitung |

## Tests

```bash
# Alle Tests ausführen
python -m pytest tests/

# Mit Testabdeckung
python -m pytest tests/ --cov=src --cov-report=html

# Einzelne Tests
python -m pytest tests/test_detector.py -v
```

## Beispiele

Weitere Beispiele finden Sie im `examples/` Verzeichnis:

```bash
python examples/example_usage.py
```

## Lizenz

MIT License

## Mitwirken

Beiträge sind willkommen! Bitte erstellen Sie einen Pull Request oder öffnen Sie ein Issue.
