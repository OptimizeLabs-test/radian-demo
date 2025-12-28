import { useState, useEffect, useRef } from "react";

interface UseStreamingTextOptions {
  speed?: number;
  enabled?: boolean;
  mode?: "word" | "character"; // Stream word-by-word or character-by-character
}

export function useStreamingText(
  text: string | null | undefined,
  options: UseStreamingTextOptions = {}
) {
  const { speed = 25, enabled = true, mode = "character" } = options;
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const hasStreamedRef = useRef(false);
  const previousTextRef = useRef<string | null | undefined>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Reset if text changes to a new value
    if (text !== previousTextRef.current) {
      previousTextRef.current = text;
      hasStreamedRef.current = false;
      setDisplayedText("");
      setIsComplete(false);
      
      // Clear any existing interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    if (!enabled || !text || hasStreamedRef.current) {
      if (text && hasStreamedRef.current) {
        setDisplayedText(text);
        setIsComplete(true);
      }
      return;
    }

    hasStreamedRef.current = true;

    if (mode === "word") {
      // Word-by-word streaming for smoother experience
      const words = text.split(/(\s+)/); // Split preserving whitespace
      let wordIndex = 0;
      let currentText = "";

      const streamWords = () => {
        if (wordIndex < words.length) {
          currentText += words[wordIndex];
          setDisplayedText(currentText);
          wordIndex++;
        } else {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setIsComplete(true);
        }
      };

      // Start streaming immediately for first word
      streamWords();
      
      // Then continue with interval
      intervalRef.current = setInterval(streamWords, speed);
    } else {
      // Character-by-character streaming (fallback)
      let index = 0;

      const streamChars = () => {
        if (index < text.length) {
          setDisplayedText(text.slice(0, index + 1));
          index++;
        } else {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setIsComplete(true);
        }
      };

      streamChars();
      intervalRef.current = setInterval(streamChars, speed);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [text, speed, enabled, mode]);

  return {
    displayedText: displayedText || "",
    isStreaming: !isComplete && enabled && !!text,
    isComplete,
  };
}
