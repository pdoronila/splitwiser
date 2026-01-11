/**
 * Example usage of ItemPreviewEditor component
 *
 * This example demonstrates how to integrate the ItemPreviewEditor component
 * into your expense creation flow with OCR receipt scanning.
 */

import React, { useState } from 'react';
import ItemPreviewEditor, { type BoundingBox, type ItemWithRegion } from './ItemPreviewEditor';
import { getApiUrl } from '../../api';

const ItemPreviewEditorExample: React.FC = () => {
    const [imageUrl, setImageUrl] = useState<string>('');
    const [regions, setRegions] = useState<BoundingBox[]>([]);
    const [items, setItems] = useState<ItemWithRegion[]>([]);
    const [cacheKey, setCacheKey] = useState<string>('');

    // Step 1: User uploads receipt image
    const handleImageUpload = async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);

        const token = localStorage.getItem('token');

        try {
            // Call OCR API to detect regions
            const response = await fetch(getApiUrl('ocr/detect-regions'), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to detect regions');
            }

            const data = await response.json();

            // Set image URL (create local URL from file)
            const localImageUrl = URL.createObjectURL(file);
            setImageUrl(localImageUrl);

            // Set regions (bounding boxes)
            setRegions(data.regions || []);

            // Store cache key for later extraction
            setCacheKey(data.cache_key);

            console.log('Detected regions:', data.regions);
        } catch (error) {
            console.error('OCR detection error:', error);
            alert('Failed to detect regions in receipt');
        }
    };

    // Step 2: User draws/selects boxes, then extracts text
    const handleExtractItems = async (selectedRegions: BoundingBox[]) => {
        if (!cacheKey || selectedRegions.length === 0) {
            alert('Please select regions to extract');
            return;
        }

        const token = localStorage.getItem('token');

        try {
            // Call OCR API to extract text from selected regions
            const response = await fetch(getApiUrl('ocr/extract-regions'), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    cache_key: cacheKey,
                    regions: selectedRegions.map(r => ({
                        x: r.x,
                        y: r.y,
                        width: r.width,
                        height: r.height
                    }))
                })
            });

            if (!response.ok) {
                throw new Error('Failed to extract items');
            }

            const data = await response.json() as { items: Array<{ region_id: string; description: string; price: number; text: string }> };

            // Convert extracted items to ItemWithRegion format
            const extractedItems: ItemWithRegion[] = data.items.map((item) => ({
                region_id: item.region_id,
                description: item.description,
                price: item.price,
                is_tax_tip: false, // User can toggle this later
                split_type: 'EQUAL' as const // Default to equal split
            }));

            setItems(extractedItems);
            console.log('Extracted items:', extractedItems);
        } catch (error) {
            console.error('Item extraction error:', error);
            alert('Failed to extract items from receipt');
        }
    };

    // Step 3: User edits items in the preview editor
    const handleItemsChange = (updatedItems: ItemWithRegion[]) => {
        setItems(updatedItems);
        console.log('Items updated:', updatedItems);
    };

    // Step 4: User submits expense with items
    const handleSubmitExpense = async () => {
        if (items.length === 0) {
            alert('Please add at least one item');
            return;
        }

        const token = localStorage.getItem('token');

        // Calculate total from items
        const total = items.reduce((sum, item) => sum + item.price, 0);

        try {
            // Create expense with itemized split type
            const response = await fetch(getApiUrl('expenses'), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description: 'Restaurant bill',
                    amount: total,
                    currency: 'USD',
                    date: new Date().toISOString().split('T')[0],
                    group_id: 1, // Replace with actual group ID
                    payer_id: 1, // Replace with actual user ID
                    split_type: 'ITEMIZED',
                    items: items.map(item => ({
                        description: item.description,
                        price: item.price,
                        is_tax_tip: item.is_tax_tip,
                        assignments: [] // Add assignments here
                    }))
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create expense');
            }

            const expense = await response.json();
            console.log('Expense created:', expense);
            alert('Expense created successfully!');
        } catch (error) {
            console.error('Expense creation error:', error);
            alert('Failed to create expense');
        }
    };

    return (
        <div className="container mx-auto p-6">
            <h1 className="text-2xl font-bold mb-6">Receipt Scanner Example</h1>

            {/* Step 1: Upload */}
            {!imageUrl && (
                <div className="mb-6">
                    <label className="block mb-2 font-semibold">Step 1: Upload Receipt</label>
                    <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handleImageUpload(file);
                        }}
                        className="block w-full text-sm text-gray-500
                            file:mr-4 file:py-2 file:px-4
                            file:rounded-full file:border-0
                            file:text-sm file:font-semibold
                            file:bg-teal-50 file:text-teal-700
                            hover:file:bg-teal-100
                            cursor-pointer file:cursor-pointer"
                    />
                </div>
            )}

            {/* Step 2: Extract Items */}
            {imageUrl && regions.length > 0 && items.length === 0 && (
                <div className="mb-6">
                    <button
                        onClick={() => handleExtractItems(regions)}
                        className="px-4 py-2 bg-teal-500 text-white rounded hover:bg-teal-600"
                    >
                        Extract Items from Regions
                    </button>
                </div>
            )}

            {/* Step 3: Preview and Edit */}
            {imageUrl && items.length > 0 && (
                <>
                    <ItemPreviewEditor
                        imageUrl={imageUrl}
                        regions={regions}
                        items={items}
                        onItemsChange={handleItemsChange}
                        currency="USD"
                    />

                    {/* Step 4: Submit */}
                    <div className="mt-6 flex justify-end gap-3">
                        <button
                            onClick={() => {
                                setImageUrl('');
                                setRegions([]);
                                setItems([]);
                                setCacheKey('');
                            }}
                            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSubmitExpense}
                            className="px-4 py-2 bg-teal-500 text-white rounded hover:bg-teal-600"
                        >
                            Create Expense
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default ItemPreviewEditorExample;

/**
 * Integration Notes:
 *
 * 1. The component expects regions in this format:
 *    { id: string, x: number, y: number, width: number, height: number }
 *    Coordinates should be in pixels matching the image dimensions.
 *
 * 2. Items should be in this format:
 *    { region_id: string, description: string, price: number, is_tax_tip: boolean }
 *    Price is in cents (e.g., 1299 = $12.99).
 *
 * 3. The component provides two modes:
 *    - Preview mode: Read-only view of items
 *    - Edit mode: Inline editing of descriptions, prices, and tax/tip flags
 *
 * 4. Visual connections:
 *    - Click on a box in the receipt image to highlight the corresponding item
 *    - Click on an item in the list to highlight the corresponding box
 *    - Hover over boxes shows highlighting effect
 *
 * 5. The component is fully responsive:
 *    - Desktop: Side-by-side layout (image | items)
 *    - Mobile: Stacked layout (image on top, items below)
 *
 * 6. Dark mode is fully supported through Tailwind's dark: variants
 *
 * 7. The total is automatically calculated from all items
 *
 * 8. Tax/tip items are marked with a checkbox and show a help message
 */
