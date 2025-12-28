import { useState } from 'react';
import type { Participant, ExpenseItem, ItemAssignment } from '../types/expense';

export const useItemizedExpense = () => {
    const [itemizedItems, setItemizedItems] = useState<ExpenseItem[]>([]);
    const [taxAmount, setTaxAmount] = useState<string>('');
    const [tipAmount, setTipAmount] = useState<string>('');
    const [editingItemIndex, setEditingItemIndex] = useState<number | null>(null);
    const [showAddItemModal, setShowAddItemModal] = useState(false);

    // Calculate subtotal (before tax/tip) in cents
    const getSubtotalCents = () => {
        return itemizedItems.reduce((sum, item) => sum + item.price, 0);
    };

    // Set tip based on percentage of subtotal (before tax)
    const setTipFromPercentage = (percent: number) => {
        const subtotalCents = getSubtotalCents();
        const tipCents = Math.round(subtotalCents * (percent / 100));
        setTipAmount((tipCents / 100).toFixed(2));
    };

    const openAddItemModal = () => {
        setShowAddItemModal(true);
    };

    const closeAddItemModal = () => {
        setShowAddItemModal(false);
    };

    const addManualItem = (description: string, price: number) => {
        setItemizedItems(prev => [...prev, {
            description,
            price,
            is_tax_tip: false,
            assignments: []
        }]);
    };

    const removeItem = (idx: number) => {
        setItemizedItems(prev => prev.filter((_, i) => i !== idx));
    };

    const toggleItemAssignment = (itemIdx: number, participant: Participant) => {
        setItemizedItems(prev => {
            const updated = [...prev];
            const item = { ...updated[itemIdx] };

            const existingIdx = item.assignments.findIndex(
                a => a.user_id === participant.id && a.is_guest === participant.isGuest
            );

            if (existingIdx >= 0) {
                item.assignments = item.assignments.filter((_, i) => i !== existingIdx);
            } else {
                item.assignments = [...item.assignments, {
                    user_id: participant.id,
                    is_guest: participant.isGuest
                }];
            }

            updated[itemIdx] = item;
            return updated;
        });
    };

    const updateItemAssignments = (itemIdx: number, assignments: ItemAssignment[]) => {
        setItemizedItems(prev => {
            const updated = [...prev];
            updated[itemIdx] = { ...updated[itemIdx], assignments };
            return updated;
        });
    };

    const setItems = (items: ExpenseItem[]) => {
        setItemizedItems(items);
    };

    return {
        itemizedItems,
        taxAmount,
        tipAmount,
        editingItemIndex,
        showAddItemModal,
        setItemizedItems,
        setTaxAmount,
        setTipAmount,
        setTipFromPercentage,
        getSubtotalCents,
        setEditingItemIndex,
        openAddItemModal,
        closeAddItemModal,
        addManualItem,
        removeItem,
        toggleItemAssignment,
        updateItemAssignments,
        setItems
    };
};
