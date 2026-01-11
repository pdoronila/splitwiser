import { useState, useCallback } from 'react';

export interface BoundingBox {
  id: string;
  x: number;      // 0-1 normalized
  y: number;      // 0-1 normalized
  width: number;  // 0-1 normalized
  height: number; // 0-1 normalized
  isSelected?: boolean;
}

export type Corner = 'nw' | 'ne' | 'sw' | 'se';

interface DragState {
  isDragging: boolean;
  isResizing: boolean;
  corner: Corner | null;
  boxId: string | null;
}

interface UseBoundingBoxesReturn {
  boxes: BoundingBox[];
  selectedBoxId: string | null;
  dragState: DragState;
  addBox: (x: number, y: number, width: number, height: number) => string;
  removeBox: (id: string) => void;
  updateBox: (id: string, updates: Partial<Omit<BoundingBox, 'id'>>) => void;
  selectBox: (id: string | null) => void;
  moveBox: (id: string, deltaX: number, deltaY: number) => void;
  resizeBox: (id: string, corner: Corner, deltaX: number, deltaY: number) => void;
  clearSelection: () => void;
  setDragState: (state: Partial<DragState>) => void;
}

export const useBoundingBoxes = (): UseBoundingBoxesReturn => {
  const [boxes, setBoxes] = useState<BoundingBox[]>([]);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [dragState, setDragStateInternal] = useState<DragState>({
    isDragging: false,
    isResizing: false,
    corner: null,
    boxId: null,
  });

  const addBox = useCallback((x: number, y: number, width: number, height: number): string => {
    const id = `box-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newBox: BoundingBox = {
      id,
      x: Math.max(0, Math.min(1, x)),
      y: Math.max(0, Math.min(1, y)),
      width: Math.max(0, Math.min(1 - x, width)),
      height: Math.max(0, Math.min(1 - y, height)),
      isSelected: false,
    };
    setBoxes(prev => [...prev, newBox]);
    return id;
  }, []);

  const removeBox = useCallback((id: string) => {
    setBoxes(prev => prev.filter(box => box.id !== id));
    if (selectedBoxId === id) {
      setSelectedBoxId(null);
    }
  }, [selectedBoxId]);

  const updateBox = useCallback((id: string, updates: Partial<Omit<BoundingBox, 'id'>>) => {
    setBoxes(prev => prev.map(box => {
      if (box.id !== id) return box;

      const updated = { ...box, ...updates };

      // Clamp values to valid range [0, 1]
      updated.x = Math.max(0, Math.min(1, updated.x));
      updated.y = Math.max(0, Math.min(1, updated.y));
      updated.width = Math.max(0, Math.min(1 - updated.x, updated.width));
      updated.height = Math.max(0, Math.min(1 - updated.y, updated.height));

      return updated;
    }));
  }, []);

  const selectBox = useCallback((id: string | null) => {
    setSelectedBoxId(id);
    setBoxes(prev => prev.map(box => ({
      ...box,
      isSelected: box.id === id,
    })));
  }, []);

  const moveBox = useCallback((id: string, deltaX: number, deltaY: number) => {
    setBoxes(prev => prev.map(box => {
      if (box.id !== id) return box;

      const newX = Math.max(0, Math.min(1 - box.width, box.x + deltaX));
      const newY = Math.max(0, Math.min(1 - box.height, box.y + deltaY));

      return {
        ...box,
        x: newX,
        y: newY,
      };
    }));
  }, []);

  const resizeBox = useCallback((id: string, corner: Corner, deltaX: number, deltaY: number) => {
    setBoxes(prev => prev.map(box => {
      if (box.id !== id) return box;

      let newX = box.x;
      let newY = box.y;
      let newWidth = box.width;
      let newHeight = box.height;

      // Handle horizontal resize
      if (corner.includes('w')) {
        // West side: adjust x and width
        const maxDelta = box.width - 0.01; // Minimum width of 1%
        const clampedDeltaX = Math.min(maxDelta, Math.max(-box.x, deltaX));
        newX = box.x + clampedDeltaX;
        newWidth = box.width - clampedDeltaX;
      } else if (corner.includes('e')) {
        // East side: adjust width only
        const maxWidth = 1 - box.x;
        newWidth = Math.max(0.01, Math.min(maxWidth, box.width + deltaX));
      }

      // Handle vertical resize
      if (corner.includes('n')) {
        // North side: adjust y and height
        const maxDelta = box.height - 0.01; // Minimum height of 1%
        const clampedDeltaY = Math.min(maxDelta, Math.max(-box.y, deltaY));
        newY = box.y + clampedDeltaY;
        newHeight = box.height - clampedDeltaY;
      } else if (corner.includes('s')) {
        // South side: adjust height only
        const maxHeight = 1 - box.y;
        newHeight = Math.max(0.01, Math.min(maxHeight, box.height + deltaY));
      }

      return {
        ...box,
        x: newX,
        y: newY,
        width: newWidth,
        height: newHeight,
      };
    }));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedBoxId(null);
    setBoxes(prev => prev.map(box => ({
      ...box,
      isSelected: false,
    })));
  }, []);

  const setDragState = useCallback((state: Partial<DragState>) => {
    setDragStateInternal(prev => ({ ...prev, ...state }));
  }, []);

  return {
    boxes,
    selectedBoxId,
    dragState,
    addBox,
    removeBox,
    updateBox,
    selectBox,
    moveBox,
    resizeBox,
    clearSelection,
    setDragState,
  };
};
