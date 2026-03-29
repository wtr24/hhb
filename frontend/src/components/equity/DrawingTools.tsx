/**
 * DrawingTools — state machine for Fibonacci and Elliott Wave drawing modes.
 * Exported as a custom hook: useDrawingTools().
 */
import { useState, useCallback } from "react";
import { fetchFibonacciLevels, validateElliottWave } from "../../lib/ta-api";

export type DrawingMode = "none" | "fib_waiting_first" | "fib_waiting_second" | "ew_labelling";

export interface FibDrawing {
  id: string;
  swingHigh: number;
  swingLow: number;
  levels: Array<{ ratio: number; price: number; label: string; is_key_level: boolean }>;
}

export interface EWLabel {
  barIdx: number;
  price: number;
  label: string;  // "1" | "2" | "3" | "4" | "5" | "A" | "B" | "C"
}

export interface EWValidation {
  valid: boolean;
  rule: string;
  message: string;
}

const EW_SEQUENCE = ["1", "2", "3", "4", "5", "A", "B", "C"] as const;

export function useDrawingTools(onClearAll: () => void) {
  const [drawingMode, setDrawingMode] = useState<DrawingMode>("none");
  const [fibFirstClick, setFibFirstClick] = useState<number | null>(null);  // price
  const [fibDrawings, setFibDrawings] = useState<FibDrawing[]>([]);
  const [ewLabels, setEwLabels] = useState<EWLabel[]>([]);
  const [ewValidations, setEwValidations] = useState<EWValidation[]>([]);

  /** Activate / deactivate Fibonacci drawing mode */
  const toggleFib = useCallback(() => {
    setDrawingMode(prev =>
      prev === "none" ? "fib_waiting_first" : "none"
    );
    setFibFirstClick(null);
  }, []);

  /** Activate / deactivate Elliott Wave labelling mode */
  const toggleEW = useCallback(() => {
    setDrawingMode(prev =>
      prev === "none" ? "ew_labelling" : "none"
    );
    setEwLabels([]);
    setEwValidations([]);
  }, []);

  /**
   * Called by chart click handler with the price at the clicked bar.
   * Handles state transitions for both Fib and EW modes.
   */
  const handleChartClick = useCallback(async (barIdx: number, price: number) => {
    if (drawingMode === "fib_waiting_first") {
      setFibFirstClick(price);
      setDrawingMode("fib_waiting_second");
      return;
    }

    if (drawingMode === "fib_waiting_second" && fibFirstClick !== null) {
      const high = Math.max(fibFirstClick, price);
      const low = Math.min(fibFirstClick, price);
      try {
        const result = await fetchFibonacciLevels(high, low);
        const drawing: FibDrawing = {
          id: `fib_${Date.now()}`,
          swingHigh: high,
          swingLow: low,
          levels: result.levels,
        };
        setFibDrawings(prev => [...prev, drawing]);
      } catch (e) {
        console.error("Fibonacci fetch failed", e);
      }
      // After drawing, return to waiting_first (allow multiple drawings per TA-11 spec)
      setFibFirstClick(null);
      setDrawingMode("fib_waiting_first");
      return;
    }

    if (drawingMode === "ew_labelling") {
      const nextLabelIdx = ewLabels.length;
      if (nextLabelIdx >= EW_SEQUENCE.length) {
        // Sequence complete — exit mode
        setDrawingMode("none");
        return;
      }
      const newLabel: EWLabel = {
        barIdx,
        price,
        label: EW_SEQUENCE[nextLabelIdx],
      };
      const updatedLabels = [...ewLabels, newLabel];
      setEwLabels(updatedLabels);

      // Trigger validation after Wave 3 end (4 points) and Wave 4 end (5 points)
      if (updatedLabels.length === 4 || updatedLabels.length === 5 || updatedLabels.length === 6) {
        try {
          const wavePoints = updatedLabels.map(l => ({ bar_idx: l.barIdx, price: l.price }));
          const result = await validateElliottWave(wavePoints);
          setEwValidations(result.validations);
        } catch (e) {
          console.error("EW validation failed", e);
        }
      }

      // If "C" placed (index 7 = last), exit mode
      if (nextLabelIdx === EW_SEQUENCE.length - 1) {
        setDrawingMode("none");
      }
      return;
    }
  }, [drawingMode, fibFirstClick, ewLabels]);

  /** Cancel current drawing mode and clear in-progress state */
  const cancelDrawing = useCallback(() => {
    setDrawingMode("none");
    setFibFirstClick(null);
  }, []);

  /** Clear all drawings on ticker/timeframe change (D-14, D-15) */
  const clearAllDrawings = useCallback(() => {
    setFibDrawings([]);
    setEwLabels([]);
    setEwValidations([]);
    setDrawingMode("none");
    setFibFirstClick(null);
    onClearAll();
  }, [onClearAll]);

  return {
    drawingMode,
    fibActive: drawingMode === "fib_waiting_first" || drawingMode === "fib_waiting_second",
    ewActive: drawingMode === "ew_labelling",
    fibDrawings,
    ewLabels,
    ewValidations,
    toggleFib,
    toggleEW,
    handleChartClick,
    cancelDrawing,
    clearAllDrawings,
  };
}
