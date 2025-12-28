# ItemPreviewEditor Component

A production-ready React component for viewing and editing items extracted from receipt OCR with visual bounding box highlighting.

## Features

### Core Functionality
- ✅ Visual receipt display with bounding boxes (non-editable canvas)
- ✅ Interactive item list mapped to bounding boxes
- ✅ Two-way highlighting: click box → highlight item, click item → highlight box
- ✅ Inline editing of description and price
- ✅ Tax/tip checkbox per item
- ✅ Preview mode vs Edit mode toggle
- ✅ Automatic total calculation
- ✅ Full dark mode support

### Visual Connections
- Number labels on boxes matching item list (1, 2, 3...)
- Selected box: Teal border, teal highlight
- Hovered box: Blue border, blue highlight
- Unassigned boxes: Gray, muted appearance

### Edit Mode Features
- Inline contentEditable fields for description
- Price input with automatic $ formatting
- Tax/tip checkbox (enabled only in edit mode)
- Remove item button (X)
- Real-time validation and updates

### Responsive Design
- Desktop: Side-by-side layout (receipt | items)
- Mobile: Stacked layout (receipt on top)
- Sticky receipt image on scroll (desktop)

## Props

```typescript
interface ItemPreviewEditorProps {
    imageUrl: string;           // URL to receipt image
    regions: BoundingBox[];     // Bounding boxes from OCR
    items: ItemWithRegion[];    // Extracted items
    onItemsChange: (items: ItemWithRegion[]) => void; // Change handler
    currency?: string;          // Currency code (default: 'USD')
}

interface BoundingBox {
    id: string;                 // Unique identifier
    x: number;                  // X position in pixels
    y: number;                  // Y position in pixels
    width: number;              // Width in pixels
    height: number;             // Height in pixels
}

interface ItemWithRegion {
    region_id: string;          // Links to BoundingBox.id
    description: string;        // Item name
    price: number;              // Price in cents
    is_tax_tip: boolean;        // Tax/tip flag
}
```

## Usage

### Basic Usage

```tsx
import ItemPreviewEditor from './components/expense/ItemPreviewEditor';

function ReceiptEditor() {
    const [items, setItems] = useState<ItemWithRegion[]>([
        {
            region_id: "1",
            description: "Burger",
            price: 1299, // $12.99
            is_tax_tip: false
        },
        {
            region_id: "2",
            description: "Tax & Tip",
            price: 350, // $3.50
            is_tax_tip: true
        }
    ]);

    const regions: BoundingBox[] = [
        { id: "1", x: 100, y: 200, width: 400, height: 50 },
        { id: "2", x: 100, y: 300, width: 400, height: 50 }
    ];

    return (
        <ItemPreviewEditor
            imageUrl="/path/to/receipt.jpg"
            regions={regions}
            items={items}
            onItemsChange={setItems}
            currency="USD"
        />
    );
}
```

### With OCR Integration

See `ItemPreviewEditor.example.tsx` for a complete example with:
1. Receipt upload
2. OCR region detection (`POST /ocr/detect-regions`)
3. Text extraction (`POST /ocr/extract-regions`)
4. Item editing with ItemPreviewEditor
5. Expense creation with itemized splits

## API Integration

### Step 1: Detect Regions

```typescript
const formData = new FormData();
formData.append('file', receiptFile);

const response = await fetch('/api/ocr/detect-regions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
});

const data = await response.json();
// Returns: { regions: BoundingBox[], cache_key: string, image_size: {...} }
```

### Step 2: Extract Items

```typescript
const response = await fetch('/api/ocr/extract-regions', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        cache_key: data.cache_key,
        regions: selectedRegions
    })
});

const extractedData = await response.json();
// Returns: { items: Array<{ region_id, description, price, text }> }
```

### Step 3: Create Expense

```typescript
const total = items.reduce((sum, item) => sum + item.price, 0);

await fetch('/api/expenses', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        description: 'Restaurant',
        amount: total,
        currency: 'USD',
        date: '2025-12-27',
        group_id: 1,
        payer_id: 1,
        split_type: 'ITEMIZED',
        items: items.map(item => ({
            description: item.description,
            price: item.price,
            is_tax_tip: item.is_tax_tip,
            assignments: [] // Add participant assignments
        }))
    })
});
```

## Component Architecture

### Canvas Management
- Uses HTML Canvas API for drawing
- Image loaded via `Image()` constructor
- Redraws on state changes (selected, hovered)
- Touch-enabled for mobile devices

### State Management
- `selectedRegionId`: Currently selected box/item
- `hoveredRegionId`: Currently hovered box
- `editMode`: Toggle between preview and edit
- `imageLoaded`: Image loading state

### Event Handling
- Canvas click: Select box → highlight item
- Item click: Select item → highlight box
- Canvas hover: Show hover effect
- Input change: Update item data via `onItemsChange`

## Styling

### Colors
- Selected: Teal (`#0d9488`)
- Hovered: Blue (`#3b82f6`)
- Default: Gray (`#9ca3af`)
- Remove: Red (`#f87171`)

### Dark Mode
All colors have dark mode variants using Tailwind's `dark:` prefix:
- Backgrounds: `dark:bg-gray-800`
- Text: `dark:text-gray-100`
- Borders: `dark:border-gray-600`

### Responsive Breakpoints
- Mobile: Stacked layout (< 1024px)
- Desktop: Side-by-side (≥ 1024px)

## Accessibility

- Keyboard navigation support
- ARIA labels on interactive elements
- High contrast colors in dark mode
- Touch-friendly targets (min 44px)
- Screen reader friendly labels

## Performance

- Canvas redraws only on state change
- Image caching via `useRef`
- Efficient hover detection
- Debounced price input (automatic)

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires:
- Canvas API support
- ES6+ features
- CSS Grid/Flexbox

## Known Limitations

1. **Non-editable boxes**: Boxes cannot be moved or resized in this component. Use `BoundingBoxEditor` component for that functionality.

2. **Image size**: Large images (>5MB) may cause performance issues. Consider resizing before upload.

3. **Mobile touch**: Hover effects not available on touch devices (expected behavior).

4. **Currency**: Only supports single currency per receipt. Multi-currency receipts need manual handling.

## Testing

### Manual Testing Checklist
- [ ] Load receipt image successfully
- [ ] Click box highlights correct item
- [ ] Click item highlights correct box
- [ ] Edit mode enables inline editing
- [ ] Price input validates correctly
- [ ] Tax/tip checkbox toggles
- [ ] Remove button deletes item
- [ ] Total calculates correctly
- [ ] Dark mode renders properly
- [ ] Mobile layout stacks correctly

### Unit Testing
```typescript
// Example test structure
describe('ItemPreviewEditor', () => {
    it('renders receipt image', () => { ... });
    it('highlights item when box clicked', () => { ... });
    it('highlights box when item clicked', () => { ... });
    it('updates item on edit', () => { ... });
    it('calculates total correctly', () => { ... });
});
```

## Troubleshooting

### Image not loading
- Check CORS headers on image URL
- Verify image URL is accessible
- Check browser console for errors
- Ensure image format is supported (JPEG, PNG, WebP)

### Boxes not aligning
- Verify regions use pixel coordinates (not normalized)
- Check image dimensions match canvas dimensions
- Ensure regions array matches items array

### Items not updating
- Check `onItemsChange` callback is provided
- Verify state is immutable (use spread operator)
- Check price is in cents (not dollars)

### Dark mode not working
- Ensure ThemeProvider wraps component
- Check Tailwind CSS is properly configured
- Verify `dark` class on `<html>` element

## Future Enhancements

- [ ] Box editing (move, resize, delete)
- [ ] Multi-select items
- [ ] Undo/redo functionality
- [ ] Zoom in/out on receipt
- [ ] Auto-detect tax/tip items
- [ ] Item templates/categories
- [ ] Export to CSV
- [ ] Print receipt with highlights

## Related Components

- `BoundingBoxEditor`: Editable bounding boxes with drag/resize
- `ReceiptCanvas`: Low-level canvas rendering
- `ExpenseItemList`: Item list with participant assignments
- `ReceiptScanner`: Upload and OCR processing

## License

This component is part of the Splitwiser project.
