import re
import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from threading import Lock


@dataclass
class BoundingBox:
    """Normalized bounding box coordinates (0-1 range)."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float:
        """Calculate width of bounding box."""
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        """Calculate height of bounding box."""
        return self.y_max - self.y_min

    @property
    def center_y(self) -> float:
        """Calculate vertical center of bounding box."""
        return (self.y_min + self.y_max) / 2

    @property
    def area(self) -> float:
        """Calculate area of bounding box."""
        return self.width * self.height


@dataclass
class TextRegion:
    """Represents a detected text region with metadata."""
    text: str
    bounding_box: BoundingBox
    confidence: float = 1.0

    def has_price_pattern(self) -> bool:
        """Check if region contains price-like text."""
        price_patterns = [
            r'\$\s?\d+\.\d{2}',           # $12.99
            r'\d+\.\d{2}\s?(?:USD|usd)',  # 12.99 USD
            r'(?<!\d)\d+\.\d{2}(?!\d)',   # 12.99
        ]
        for pattern in price_patterns:
            if re.search(pattern, self.text):
                return True
        return False


# In-memory cache with TTL
_cache: Dict[str, Tuple[Any, float]] = {}
_cache_lock = Lock()


def detect_regions(vision_response) -> List[TextRegion]:
    """
    Extract paragraph/block boundaries from Vision API response.

    Converts Vision API's text annotations into structured regions with
    normalized bounding boxes. Uses smart detection to identify item regions.

    Args:
        vision_response: Google Cloud Vision AnnotateImageResponse with
                        text_annotations or full_text_annotation.pages

    Returns:
        List of TextRegion objects with normalized coordinates

    Raises:
        ValueError: If vision_response is invalid or missing required data
    """
    if not vision_response:
        raise ValueError("vision_response cannot be None")

    # Try smart detection first (best quality)
    try:
        regions = detect_smart_regions(vision_response)
        if regions:
            return regions
    except Exception as e:
        print(f"Warning: Smart region detection failed: {e}")

    regions = []

    # Fallback: Try full_text_annotation (provides block/paragraph structure)
    if hasattr(vision_response, 'full_text_annotation') and vision_response.full_text_annotation:
        try:
            regions = _extract_regions_from_full_annotation(vision_response.full_text_annotation)
        except Exception as e:
            print(f"Warning: Failed to extract regions from full_text_annotation: {e}")

    # Fallback to text_annotations (simpler structure)
    if not regions and hasattr(vision_response, 'text_annotations') and vision_response.text_annotations:
        try:
            regions = _extract_regions_from_text_annotations(vision_response.text_annotations)
        except Exception as e:
            print(f"Warning: Failed to extract regions from text_annotations: {e}")

    if not regions:
        raise ValueError("No text regions found in vision_response")

    # Apply filtering heuristics
    filtered_regions = filter_item_regions(regions)

    return filtered_regions


def detect_smart_regions(vision_response) -> List[TextRegion]:
    """
    Smart region detection using Vision API's structural data and price patterns.

    Uses paragraph boundaries, price alignment, and content analysis to:
    - Identify item lines with prices
    - Group multi-line items together
    - Filter out headers (store name, address, phone)
    - Filter out footers (totals, thank you messages)
    - Separate tax/tip into dedicated boxes

    Args:
        vision_response: Google Cloud Vision AnnotateImageResponse with
                        full_text_annotation.pages structure

    Returns:
        List of TextRegion objects representing likely items

    Raises:
        ValueError: If vision_response is missing required structure
    """
    if not hasattr(vision_response, 'full_text_annotation') or not vision_response.full_text_annotation:
        raise ValueError("vision_response missing full_text_annotation")

    full_text = vision_response.full_text_annotation
    if not hasattr(full_text, 'pages') or not full_text.pages:
        raise ValueError("full_text_annotation missing pages")

    page = full_text.pages[0]
    image_width = page.width if hasattr(page, 'width') else 1
    image_height = page.height if hasattr(page, 'height') else 1
    image_size = (image_width, image_height)

    # Extract all paragraphs with metadata
    all_paragraphs = []
    for block in page.blocks:
        for paragraph in block.paragraphs:
            # Reconstruct text from words
            words = []
            for word in paragraph.words:
                word_text = ''.join([symbol.text for symbol in word.symbols])
                words.append(word_text)

            text = ' '.join(words).strip()
            if not text:
                continue

            bbox = normalize_bounding_box(paragraph.bounding_box.vertices, image_size)
            confidence = paragraph.confidence if hasattr(paragraph, 'confidence') else 1.0

            region = TextRegion(text=text, bounding_box=bbox, confidence=confidence)
            all_paragraphs.append(region)

    # Sort by vertical position
    all_paragraphs.sort(key=lambda r: r.bounding_box.center_y)

    # Identify regions: header, items, footer
    header_end_y = _detect_header_boundary(all_paragraphs)
    footer_start_y = _detect_footer_boundary(all_paragraphs)

    # Filter and categorize regions
    item_regions = []
    tax_tip_regions = []

    for region in all_paragraphs:
        center_y = region.bounding_box.center_y

        # Skip header region
        if center_y < header_end_y:
            continue

        # Skip footer region
        if center_y > footer_start_y:
            continue

        # Skip if too small or too large
        if region.bounding_box.area < 0.003 or region.bounding_box.area > 0.5:
            continue

        # Skip single characters
        if len(region.text.strip()) <= 1:
            continue

        # Check if tax/tip line
        if _is_tax_tip_line(region.text):
            tax_tip_regions.append(region)
            continue

        # Check if likely an item (has price or matches item patterns)
        if region.has_price_pattern() or _is_likely_item_line(region.text):
            item_regions.append(region)

    # Group multi-line items together
    grouped_regions = _group_multiline_items(item_regions, image_size)

    # Return items + tax/tip regions
    return grouped_regions + tax_tip_regions


def _detect_header_boundary(paragraphs: List[TextRegion]) -> float:
    """
    Detect where the header ends (store name, address, phone, etc.).

    Headers typically:
    - Appear in the top of the receipt
    - Contain no prices
    - Have business info (phone numbers, addresses, URLs)

    Args:
        paragraphs: List of all paragraphs sorted by vertical position

    Returns:
        Y coordinate (normalized 0-1) where items likely begin
    """
    # Default: top 15% is header
    header_boundary = 0.15

    # Look for the first paragraph with a price pattern
    for i, region in enumerate(paragraphs):
        if region.has_price_pattern():
            # Header ends just before first price
            if i > 0:
                header_boundary = paragraphs[i - 1].bounding_box.y_max
            else:
                header_boundary = region.bounding_box.y_min
            break

    # Cap at 25% to avoid over-filtering
    return min(header_boundary, 0.25)


def _detect_footer_boundary(paragraphs: List[TextRegion]) -> float:
    """
    Detect where the footer begins (totals, thank you, etc.).

    Footers typically:
    - Appear at the bottom of receipt
    - Contain "total", "subtotal", "thank you"
    - May have payment method info

    Args:
        paragraphs: List of all paragraphs sorted by vertical position

    Returns:
        Y coordinate (normalized 0-1) where footer begins
    """
    footer_keywords = [
        r'\btotal\b',
        r'\bsubtotal\b',
        r'\bgrand\s+total\b',
        r'\bthank\s+you\b',
        r'\bhave\s+a\s+.*\s+day\b',
        r'\bvisit\s+us\b',
        r'\bcard\s*#',
        r'\btender\b',
        r'\bchange\b',
        r'\bbalance\b',
    ]

    # Default: bottom 15% is footer
    footer_boundary = 0.85

    # Look for footer keyword from bottom up
    for region in reversed(paragraphs):
        for pattern in footer_keywords:
            if re.search(pattern, region.text, re.I):
                # Footer starts at this line
                footer_boundary = region.bounding_box.y_min
                return max(footer_boundary, 0.75)  # Cap at 75% to avoid over-filtering

    return footer_boundary


def _is_tax_tip_line(text: str) -> bool:
    """
    Check if line represents tax or tip.

    Args:
        text: Line text to check

    Returns:
        True if line contains tax/tip keywords
    """
    tax_tip_patterns = [
        r'\btax\b',
        r'\btip\b',
        r'\bgratuity\b',
        r'\bservice\s+charge\b',
        r'\bdelivery\s+fee\b',
    ]

    for pattern in tax_tip_patterns:
        if re.search(pattern, text, re.I):
            return True

    return False


def _is_likely_item_line(text: str) -> bool:
    """
    Check if line looks like an item (even without price visible).

    Heuristics:
    - Contains quantity patterns (e.g., "2x", "@ $5")
    - Has reasonable length (3-40 chars)
    - Not just numbers or special characters
    - Doesn't match noise patterns

    Args:
        text: Line text to check

    Returns:
        True if likely an item description
    """
    # Check for quantity patterns
    quantity_patterns = [
        r'\d+\s?x\b',            # "2x Burger"
        r'^\d+\s+[A-Za-z]',      # "2 Diet Coke"
        r'@\s?\$?\d+\.\d{2}',    # "@ $5.99"
    ]

    for pattern in quantity_patterns:
        if re.search(pattern, text, re.I):
            return True

    # Check length
    if len(text.strip()) < 3 or len(text.strip()) > 50:
        return False

    # Check if mostly letters (likely a description)
    letter_count = sum(1 for c in text if c.isalpha())
    total_count = len(text.replace(' ', ''))

    if total_count > 0 and letter_count / total_count > 0.4:
        # At least 40% letters = likely description
        return True

    return False


def _group_multiline_items(regions: List[TextRegion], image_size: Tuple[int, int]) -> List[TextRegion]:
    """
    Group multi-line items together (e.g., description on one line, price on next).

    Looks for:
    - Adjacent regions (vertically close)
    - Description without price + price without description
    - Similar horizontal alignment

    Args:
        regions: List of item regions to potentially group
        image_size: Tuple of (width, height) for coordinate calculations

    Returns:
        List of regions with multi-line items merged
    """
    if len(regions) < 2:
        return regions

    grouped = []
    skip_next = False

    for i in range(len(regions)):
        if skip_next:
            skip_next = False
            continue

        current = regions[i]

        # Check if we should merge with next region
        if i < len(regions) - 1:
            next_region = regions[i + 1]

            # Vertical proximity check (within 5% of image height)
            vertical_distance = next_region.bounding_box.y_min - current.bounding_box.y_max
            if vertical_distance < 0.05:
                # Check if one has price and other doesn't
                current_has_price = current.has_price_pattern()
                next_has_price = next_region.has_price_pattern()

                if current_has_price != next_has_price:
                    # Merge: description + price
                    merged_text = f"{current.text} {next_region.text}"

                    # Calculate combined bounding box
                    merged_bbox = BoundingBox(
                        x_min=min(current.bounding_box.x_min, next_region.bounding_box.x_min),
                        y_min=current.bounding_box.y_min,
                        x_max=max(current.bounding_box.x_max, next_region.bounding_box.x_max),
                        y_max=next_region.bounding_box.y_max,
                    )

                    merged_confidence = (current.confidence + next_region.confidence) / 2
                    merged_region = TextRegion(text=merged_text, bounding_box=merged_bbox, confidence=merged_confidence)

                    grouped.append(merged_region)
                    skip_next = True
                    continue

        # No merge, add as-is
        grouped.append(current)

    return grouped


def _extract_regions_from_full_annotation(full_text_annotation) -> List[TextRegion]:
    """
    Extract regions from full_text_annotation structure.

    Uses paragraph-level boundaries for more accurate region detection.

    Args:
        full_text_annotation: Vision API full_text_annotation object

    Returns:
        List of TextRegion objects
    """
    regions = []

    if not hasattr(full_text_annotation, 'pages') or not full_text_annotation.pages:
        return regions

    # Get image dimensions from first page
    page = full_text_annotation.pages[0]
    image_width = page.width if hasattr(page, 'width') else 1
    image_height = page.height if hasattr(page, 'height') else 1
    image_size = (image_width, image_height)

    # Extract paragraphs from blocks
    for block in page.blocks:
        for paragraph in block.paragraphs:
            # Concatenate words in paragraph
            text_parts = []
            for word in paragraph.words:
                word_text = ''.join([symbol.text for symbol in word.symbols])
                text_parts.append(word_text)

            text = ' '.join(text_parts).strip()

            if text and hasattr(paragraph, 'bounding_box'):
                bbox = normalize_bounding_box(paragraph.bounding_box.vertices, image_size)
                confidence = paragraph.confidence if hasattr(paragraph, 'confidence') else 1.0
                regions.append(TextRegion(text=text, bounding_box=bbox, confidence=confidence))

    return regions


def _extract_regions_from_text_annotations(text_annotations) -> List[TextRegion]:
    """
    Extract regions from text_annotations structure (fallback method).

    Groups individual text annotations into line-based regions.

    Args:
        text_annotations: List of Vision API text annotations

    Returns:
        List of TextRegion objects
    """
    regions = []

    if len(text_annotations) < 2:
        return regions

    # Skip first annotation (full text), process individual words
    # Determine image size from first annotation's bounding box
    first_bbox = text_annotations[0].bounding_poly.vertices
    image_width = max(v.x for v in first_bbox if hasattr(v, 'x'))
    image_height = max(v.y for v in first_bbox if hasattr(v, 'y'))
    image_size = (image_width, image_height)

    # Group annotations by vertical position (approximate lines)
    lines: Dict[int, List[Tuple[str, Any]]] = {}

    for annotation in text_annotations[1:]:  # Skip first (full text)
        if not hasattr(annotation, 'bounding_poly') or not annotation.bounding_poly.vertices:
            continue

        text = annotation.description
        vertices = annotation.bounding_poly.vertices

        # Calculate center Y position
        y_coords = [v.y for v in vertices if hasattr(v, 'y')]
        if not y_coords:
            continue

        center_y = sum(y_coords) / len(y_coords)

        # Group into lines (within 10 pixels vertical tolerance)
        line_key = int(center_y / 10) * 10

        if line_key not in lines:
            lines[line_key] = []

        lines[line_key].append((text, vertices))

    # Convert lines to regions
    for line_key in sorted(lines.keys()):
        line_items = lines[line_key]

        # Sort items by x position
        line_items.sort(key=lambda item: min(v.x for v in item[1] if hasattr(v, 'x')))

        # Combine text
        text = ' '.join([item[0] for item in line_items])

        # Calculate combined bounding box
        all_vertices = [v for item in line_items for v in item[1]]
        bbox = normalize_bounding_box(all_vertices, image_size)

        regions.append(TextRegion(text=text, bounding_box=bbox))

    return regions


def normalize_bounding_box(vertices, image_size: Tuple[int, int]) -> BoundingBox:
    """
    Convert pixel coordinates to normalized 0-1 values.

    Args:
        vertices: List of vertex objects with x, y attributes
        image_size: Tuple of (width, height) in pixels

    Returns:
        BoundingBox with normalized coordinates (0-1 range)

    Raises:
        ValueError: If vertices or image_size are invalid
    """
    if not vertices:
        raise ValueError("vertices cannot be empty")

    if not image_size or image_size[0] <= 0 or image_size[1] <= 0:
        raise ValueError(f"Invalid image_size: {image_size}")

    image_width, image_height = image_size

    # Extract x and y coordinates
    x_coords = [v.x for v in vertices if hasattr(v, 'x')]
    y_coords = [v.y for v in vertices if hasattr(v, 'y')]

    if not x_coords or not y_coords:
        raise ValueError("No valid x/y coordinates found in vertices")

    # Calculate bounds
    x_min = min(x_coords) / image_width
    x_max = max(x_coords) / image_width
    y_min = min(y_coords) / image_height
    y_max = max(y_coords) / image_height

    # Clamp to [0, 1] range
    x_min = max(0.0, min(1.0, x_min))
    x_max = max(0.0, min(1.0, x_max))
    y_min = max(0.0, min(1.0, y_min))
    y_max = max(0.0, min(1.0, y_max))

    return BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)


def filter_item_regions(regions: List[TextRegion]) -> List[TextRegion]:
    """
    Apply smart heuristics to filter out headers, footers, and noise.

    Filtering rules (enhanced):
    - Detect header boundary using price alignment
    - Detect footer boundary using keyword search
    - Ignore very small regions (< 0.3% of image area)
    - Ignore very large regions (> 50% of image area)
    - Prefer regions with price patterns
    - Filter out single-character regions
    - Filter out regions with only numbers (except prices)
    - Filter out common header patterns (phone, URL, address)
    - Filter out common footer patterns (thank you, totals)
    - Detect quantity patterns to identify items

    Args:
        regions: List of TextRegion objects to filter

    Returns:
        Filtered list of TextRegion objects
    """
    if not regions:
        return []

    # Sort by vertical position first
    sorted_regions = sorted(regions, key=lambda r: r.bounding_box.center_y)

    # Detect header/footer boundaries using price alignment
    header_end_y = 0.1  # Default
    footer_start_y = 0.9  # Default

    # Find first region with price (header ends here)
    for region in sorted_regions:
        if region.has_price_pattern():
            header_end_y = max(0.05, region.bounding_box.y_min - 0.02)
            break

    # Find footer keywords
    footer_keywords = [
        r'\btotal\b', r'\bsubtotal\b', r'\bgrand\s+total\b',
        r'\bthank\s+you\b', r'\bhave\s+a\s+.*\s+day\b',
        r'\bcard\s*#', r'\btender\b', r'\bbalance\b',
    ]

    for region in reversed(sorted_regions):
        for keyword in footer_keywords:
            if re.search(keyword, region.text, re.I):
                footer_start_y = min(0.95, region.bounding_box.y_min)
                break
        if footer_start_y < 0.9:
            break

    # Header/footer filtering patterns
    header_patterns = [
        r'\d{3}[-.:]\d{3}[-.:]\d{4}',  # Phone numbers
        r'www\.|\.com|\.net',           # URLs
        r'^\d+\s+[A-Z][a-z]+\s+St',     # Addresses (e.g., "123 Main St")
    ]

    footer_patterns = [
        r'thank\s+you',
        r'please\s+come\s+again',
        r'visit\s+us',
    ]

    filtered = []

    for region in sorted_regions:
        center_y = region.bounding_box.center_y

        # Skip header region
        if center_y < header_end_y:
            continue

        # Skip footer region
        if center_y > footer_start_y:
            continue

        # Skip very small regions (noise, dots, etc.)
        if region.bounding_box.area < 0.003:
            continue

        # Skip very large regions (full document text)
        if region.bounding_box.area > 0.5:
            continue

        # Skip single characters
        if len(region.text.strip()) <= 1:
            continue

        # Skip regions that are too thin (horizontal lines, separators)
        if region.bounding_box.height < 0.008:
            continue

        # Check for header patterns
        is_header = False
        for pattern in header_patterns:
            if re.search(pattern, region.text, re.I):
                is_header = True
                break
        if is_header:
            continue

        # Check for footer patterns
        is_footer = False
        for pattern in footer_patterns:
            if re.search(pattern, region.text, re.I):
                is_footer = True
                break
        if is_footer:
            continue

        # Skip regions with only numbers (unless they contain price pattern)
        text_stripped = region.text.replace(' ', '').replace('.', '').replace(',', '').replace('$', '')
        if text_stripped.isdigit() and not region.has_price_pattern():
            continue

        # Skip if text is too short (unless has price)
        if len(region.text.strip()) < 3 and not region.has_price_pattern():
            continue

        filtered.append(region)

    return filtered


def cache_ocr_response(key: str, response: Any, ttl: int = 900) -> None:
    """
    Cache OCR response in memory with TTL.

    Thread-safe caching with automatic expiration.

    Args:
        key: Cache key (e.g., hash of image bytes)
        response: OCR response object to cache
        ttl: Time-to-live in seconds (default: 900 = 15 minutes)

    Raises:
        ValueError: If key is empty or ttl is negative
    """
    if not key:
        raise ValueError("Cache key cannot be empty")

    if ttl < 0:
        raise ValueError("TTL cannot be negative")

    expiry_time = time.time() + ttl

    with _cache_lock:
        _cache[key] = (response, expiry_time)

        # Clean up expired entries (garbage collection)
        _cleanup_expired_cache()


def get_cached_response(key: str) -> Optional[Any]:
    """
    Retrieve cached OCR response.

    Returns None if key not found or entry expired.

    Args:
        key: Cache key to lookup

    Returns:
        Cached response object or None if not found/expired
    """
    if not key:
        return None

    with _cache_lock:
        if key not in _cache:
            return None

        response, expiry_time = _cache[key]

        # Check expiration
        if time.time() > expiry_time:
            # Remove expired entry
            del _cache[key]
            return None

        return response


def _cleanup_expired_cache() -> None:
    """
    Remove expired entries from cache.

    Should be called while holding _cache_lock.
    """
    current_time = time.time()
    expired_keys = [
        key for key, (_, expiry_time) in _cache.items()
        if current_time > expiry_time
    ]

    for key in expired_keys:
        del _cache[key]


def clear_cache() -> None:
    """
    Clear all cached entries.

    Useful for testing or manual cache invalidation.
    """
    with _cache_lock:
        _cache.clear()


def get_cache_stats() -> Dict[str, int]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache metrics:
        - total_entries: Total number of cached items
        - expired_entries: Number of expired items
    """
    with _cache_lock:
        current_time = time.time()
        total = len(_cache)
        expired = sum(1 for _, expiry_time in _cache.values() if current_time > expiry_time)

        return {
            'total_entries': total,
            'expired_entries': expired,
        }
