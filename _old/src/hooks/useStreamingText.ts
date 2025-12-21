import { useState, useEffect, useRef } from "react";

interface UseStreamingTextOptions {
  speed?: number;
  enabled?: boolean;
}

export function useStreamingText(
  text: string | null | undefined,
  options: UseStreamingTextOptions = {}
) {
  const { speed = 15, enabled = true } = options;
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const hasStreamedRef = useRef(false);
  const previousTextRef = useRef<string | null | undefined>(null);

  useEffect(() => {
    // Reset if text changes to a new value
    if (text !== previousTextRef.current) {
      previousTextRef.current = text;
      hasStreamedRef.current = false;
      setDisplayedText("");
      setIsComplete(false);
    }

    if (!enabled || !text || hasStreamedRef.current) {
      if (text && hasStreamedRef.current) {
        setDisplayedText(text);
        setIsComplete(true);
      }
      return;
    }

    let index = 0;
    hasStreamedRef.current = true;

    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayedText(text.slice(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
        setIsComplete(true);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed, enabled]);

  return {
    displayedText: displayedText || "",
    isStreaming: !isComplete && enabled && !!text,
    isComplete,
  };
}
