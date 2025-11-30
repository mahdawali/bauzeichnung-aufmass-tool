"""
QuantityCalculator - Modul zur Mengenberechnung für Bauteile.

Dieses Modul berechnet Mengen wie Längen, Flächen und Volumen
basierend auf den erkannten Bauteilen und deren Abmessungen.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class QuantityItem:
    """
    Repräsentiert eine einzelne Mengenposition.
    
    Attributes:
        position: Positionsnummer
        category: Kategorie (z.B. "Wände", "Fenster")
        description: Beschreibung des Elements
        quantity: Menge
        unit: Einheit (m, m², m³, Stück)
        dimensions: Detaillierte Abmessungen
        notes: Anmerkungen
    """
    position: int
    category: str
    description: str
    quantity: float
    unit: str
    dimensions: Dict[str, float] = field(default_factory=dict)
    notes: str = ""


@dataclass
class QuantityResult:
    """
    Ergebnis einer Mengenberechnung.
    
    Attributes:
        items: Liste der Mengenpositionen
        summary: Zusammenfassung nach Kategorien
    """
    items: List[QuantityItem] = field(default_factory=list)
    summary: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def get_total_by_category(self, category: str) -> Dict[str, float]:
        """
        Gibt die Summen für eine Kategorie zurück.
        
        Args:
            category: Kategoriename
            
        Returns:
            Dictionary mit Summen pro Einheit
        """
        return self.summary.get(category, {})
    
    def get_all_items(self) -> List[QuantityItem]:
        """Gibt alle Mengenpositionen zurück."""
        return self.items
    
    def filter_by_category(self, category: str) -> List[QuantityItem]:
        """
        Filtert Mengenpositionen nach Kategorie.
        
        Args:
            category: Kategoriename
            
        Returns:
            Gefilterte Liste
        """
        return [item for item in self.items if item.category == category]


class QuantityCalculator:
    """
    Klasse zur Mengenberechnung für Bauteile.
    
    Berechnet:
    - Längen (m) für Wände, Unterzüge
    - Flächen (m²) für Wände, Decken, Fenster, Türen
    - Volumen (m³) für Beton, Mauerwerk
    - Stückzahlen für Fenster, Türen, Stützen
    
    Attributes:
        default_wall_height: Standard-Wandhöhe in Metern
        default_slab_thickness: Standard-Deckendicke in Metern
    """
    
    def __init__(
        self,
        default_wall_height: float = 2.75,
        default_slab_thickness: float = 0.20
    ) -> None:
        """
        Initialisiert den QuantityCalculator.
        
        Args:
            default_wall_height: Standard-Wandhöhe in Metern
            default_slab_thickness: Standard-Deckendicke in Metern
        """
        self.default_wall_height = default_wall_height
        self.default_slab_thickness = default_slab_thickness
        logger.info(
            f"QuantityCalculator initialisiert "
            f"(Wandhöhe: {default_wall_height}m, Deckendicke: {default_slab_thickness}m)"
        )
    
    def calculate(self, elements: List[Any]) -> QuantityResult:
        """
        Berechnet Mengen für alle erkannten Elemente.
        
        Args:
            elements: Liste von DetectedElement-Objekten
            
        Returns:
            QuantityResult mit allen Mengenpositionen
        """
        logger.info(f"Berechne Mengen für {len(elements)} Elemente")
        
        result = QuantityResult()
        position = 1
        
        # Gruppiere Elemente nach Typ
        walls = [e for e in elements if e.element_type == "wall"]
        windows = [e for e in elements if e.element_type == "window"]
        doors = [e for e in elements if e.element_type == "door"]
        columns = [e for e in elements if e.element_type == "column"]
        beams = [e for e in elements if e.element_type == "beam"]
        slabs = [e for e in elements if e.element_type == "slab"]
        
        # Wände berechnen
        for wall in walls:
            item = self._calculate_wall(wall, position)
            result.items.append(item)
            position += 1
        
        # Fenster berechnen
        for window in windows:
            item = self._calculate_window(window, position)
            result.items.append(item)
            position += 1
        
        # Türen berechnen
        for door in doors:
            item = self._calculate_door(door, position)
            result.items.append(item)
            position += 1
        
        # Stützen berechnen
        for column in columns:
            item = self._calculate_column(column, position)
            result.items.append(item)
            position += 1
        
        # Unterzüge berechnen
        for beam in beams:
            item = self._calculate_beam(beam, position)
            result.items.append(item)
            position += 1
        
        # Decken berechnen
        for slab in slabs:
            item = self._calculate_slab(slab, position)
            result.items.append(item)
            position += 1
        
        # Zusammenfassung erstellen
        result.summary = self._create_summary(result.items)
        
        logger.info(f"{len(result.items)} Mengenpositionen berechnet")
        return result
    
    def _calculate_wall(self, wall: Any, position: int) -> QuantityItem:
        """
        Berechnet Mengen für eine Wand.
        
        Args:
            wall: DetectedElement für Wand
            position: Positionsnummer
            
        Returns:
            QuantityItem
        """
        dims = wall.dimensions
        props = wall.properties
        
        length_m = dims.get("length_m", 0)
        thickness_m = dims.get("thickness_m", 0.24)  # Standard: 24cm
        height_m = self.default_wall_height
        
        # Wandfläche berechnen
        area_m2 = length_m * height_m
        
        # Volumen berechnen
        volume_m3 = area_m2 * thickness_m
        
        wall_type = props.get("wall_type", "Wand")
        
        return QuantityItem(
            position=position,
            category="Wände",
            description=f"{wall_type} ({wall.subtype})",
            quantity=area_m2,
            unit="m²",
            dimensions={
                "length_m": round(length_m, 2),
                "height_m": round(height_m, 2),
                "thickness_m": round(thickness_m, 3),
                "area_m2": round(area_m2, 2),
                "volume_m3": round(volume_m3, 3),
            },
            notes=f"Länge: {length_m:.2f}m, Höhe: {height_m:.2f}m"
        )
    
    def _calculate_window(self, window: Any, position: int) -> QuantityItem:
        """
        Berechnet Mengen für ein Fenster.
        
        Args:
            window: DetectedElement für Fenster
            position: Positionsnummer
            
        Returns:
            QuantityItem
        """
        dims = window.dimensions
        props = window.properties
        
        width_m = dims.get("width_m", 1.0)
        height_m = dims.get("height_m", 1.2)
        
        # Fensterfläche
        area_m2 = width_m * height_m
        
        window_type = props.get("window_type", "Fenster")
        
        return QuantityItem(
            position=position,
            category="Fenster",
            description=window_type,
            quantity=1,
            unit="Stück",
            dimensions={
                "width_m": round(width_m, 2),
                "height_m": round(height_m, 2),
                "area_m2": round(area_m2, 2),
            },
            notes=f"Größe: {width_m:.2f}m x {height_m:.2f}m"
        )
    
    def _calculate_door(self, door: Any, position: int) -> QuantityItem:
        """
        Berechnet Mengen für eine Tür.
        
        Args:
            door: DetectedElement für Tür
            position: Positionsnummer
            
        Returns:
            QuantityItem
        """
        dims = door.dimensions
        props = door.properties
        
        width_m = dims.get("width_m", 0.88)  # Standard: 88cm
        height_m = dims.get("height_m", 2.01)  # Standard: 201cm
        
        # Türfläche
        area_m2 = width_m * height_m
        
        door_type = props.get("door_type", "Tür")
        
        return QuantityItem(
            position=position,
            category="Türen",
            description=door_type,
            quantity=1,
            unit="Stück",
            dimensions={
                "width_m": round(width_m, 2),
                "height_m": round(height_m, 2),
                "area_m2": round(area_m2, 2),
            },
            notes=f"Größe: {width_m:.2f}m x {height_m:.2f}m"
        )
    
    def _calculate_column(self, column: Any, position: int) -> QuantityItem:
        """
        Berechnet Mengen für eine Stütze.
        
        Args:
            column: DetectedElement für Stütze
            position: Positionsnummer
            
        Returns:
            QuantityItem
        """
        dims = column.dimensions
        props = column.properties
        
        width_m = dims.get("width_m", 0.3)
        depth_m = dims.get("depth_m", 0.3)
        height_m = self.default_wall_height  # Geschosshöhe
        
        # Querschnittsfläche
        cross_section_m2 = width_m * depth_m
        
        # Volumen
        volume_m3 = cross_section_m2 * height_m
        
        column_type = props.get("column_type", "Stütze")
        
        return QuantityItem(
            position=position,
            category="Stützen",
            description=column_type,
            quantity=volume_m3,
            unit="m³",
            dimensions={
                "width_m": round(width_m, 2),
                "depth_m": round(depth_m, 2),
                "height_m": round(height_m, 2),
                "cross_section_m2": round(cross_section_m2, 4),
                "volume_m3": round(volume_m3, 3),
            },
            notes=f"Querschnitt: {width_m:.2f}m x {depth_m:.2f}m, Höhe: {height_m:.2f}m"
        )
    
    def _calculate_beam(self, beam: Any, position: int) -> QuantityItem:
        """
        Berechnet Mengen für einen Unterzug.
        
        Args:
            beam: DetectedElement für Unterzug
            position: Positionsnummer
            
        Returns:
            QuantityItem
        """
        dims = beam.dimensions
        props = beam.properties
        
        length_m = dims.get("length_m", 1.0)
        width_m = 0.30  # Standard: 30cm
        height_m = 0.50  # Standard: 50cm
        
        # Querschnittsfläche
        cross_section_m2 = width_m * height_m
        
        # Volumen
        volume_m3 = cross_section_m2 * length_m
        
        beam_type = props.get("beam_type", "Unterzug")
        
        return QuantityItem(
            position=position,
            category="Unterzüge",
            description=beam_type,
            quantity=volume_m3,
            unit="m³",
            dimensions={
                "length_m": round(length_m, 2),
                "width_m": round(width_m, 2),
                "height_m": round(height_m, 2),
                "cross_section_m2": round(cross_section_m2, 4),
                "volume_m3": round(volume_m3, 3),
            },
            notes=f"Länge: {length_m:.2f}m, Querschnitt: {width_m:.2f}m x {height_m:.2f}m"
        )
    
    def _calculate_slab(self, slab: Any, position: int) -> QuantityItem:
        """
        Berechnet Mengen für eine Decke.
        
        Args:
            slab: DetectedElement für Decke
            position: Positionsnummer
            
        Returns:
            QuantityItem
        """
        dims = slab.dimensions
        props = slab.properties
        
        area_m2 = dims.get("area_m2", 0)
        thickness_m = self.default_slab_thickness
        
        # Volumen
        volume_m3 = area_m2 * thickness_m
        
        slab_type = props.get("slab_type", "Decke")
        
        return QuantityItem(
            position=position,
            category="Decken",
            description=slab_type,
            quantity=area_m2,
            unit="m²",
            dimensions={
                "area_m2": round(area_m2, 2),
                "thickness_m": round(thickness_m, 3),
                "volume_m3": round(volume_m3, 3),
            },
            notes=f"Fläche: {area_m2:.2f}m², Dicke: {thickness_m*100:.0f}cm"
        )
    
    def _create_summary(self, items: List[QuantityItem]) -> Dict[str, Dict[str, float]]:
        """
        Erstellt eine Zusammenfassung der Mengen nach Kategorien.
        
        Args:
            items: Liste von QuantityItems
            
        Returns:
            Dictionary mit Summen pro Kategorie und Einheit
        """
        summary: Dict[str, Dict[str, float]] = {}
        
        for item in items:
            if item.category not in summary:
                summary[item.category] = {}
            
            unit = item.unit
            if unit not in summary[item.category]:
                summary[item.category][unit] = 0
            
            summary[item.category][unit] += item.quantity
        
        # Runde alle Werte
        for category in summary:
            for unit in summary[category]:
                summary[category][unit] = round(summary[category][unit], 2)
        
        return summary
    
    def calculate_wall_area(
        self,
        walls: List[Any],
        deduct_openings: bool = True,
        openings: Optional[List[Any]] = None
    ) -> float:
        """
        Berechnet die Gesamtwandfläche.
        
        Args:
            walls: Liste von Wand-Elementen
            deduct_openings: Ob Öffnungen abgezogen werden sollen
            openings: Liste von Öffnungen (Fenster/Türen)
            
        Returns:
            Gesamtwandfläche in m²
        """
        total_area = 0
        
        for wall in walls:
            length_m = wall.dimensions.get("length_m", 0)
            area_m2 = length_m * self.default_wall_height
            total_area += area_m2
        
        if deduct_openings and openings:
            for opening in openings:
                width_m = opening.dimensions.get("width_m", 0)
                height_m = opening.dimensions.get("height_m", 0)
                total_area -= width_m * height_m
        
        return round(max(0, total_area), 2)
    
    def calculate_concrete_volume(self, elements: List[Any]) -> float:
        """
        Berechnet das Gesamtbetonvolumen.
        
        Args:
            elements: Liste von Beton-Elementen (Stützen, Unterzüge, Decken)
            
        Returns:
            Gesamtbetonvolumen in m³
        """
        total_volume = 0
        
        for element in elements:
            if element.element_type in ["column", "beam", "slab"]:
                if "volume_m3" in element.dimensions:
                    total_volume += element.dimensions["volume_m3"]
        
        return round(total_volume, 3)
