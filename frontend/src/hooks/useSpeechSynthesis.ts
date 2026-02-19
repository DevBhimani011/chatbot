import { useState, useEffect, useCallback, useRef } from 'react';

interface UseSpeechSynthesisReturn {
  speak: (text: string) => void;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  isSpeaking: boolean;
  isPaused: boolean;
  isSupported: boolean;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  setSelectedVoice: (voice: SpeechSynthesisVoice) => void;
  rate: number;
  setRate: (rate: number) => void;
  pitch: number;
  setPitch: (pitch: number) => void;
  currentWordIndex: number;
  currentText: string;
}

export const useSpeechSynthesis = (): UseSpeechSynthesisReturn => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [rate, setRate] = useState(1.0); // Speech rate: 0.1 to 10
  const [pitch, setPitch] = useState(1.0); // Speech pitch: 0 to 2
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [currentText, setCurrentText] = useState('');
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Check if speech synthesis is supported
  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  // Load available voices
  useEffect(() => {
    if (!isSupported) return;

    const loadVoices = () => {
      const availableVoices = speechSynthesis.getVoices();
      setVoices(availableVoices);

      // Default to first English voice, or first available voice
      if (!selectedVoice && availableVoices.length > 0) {
        const englishVoice = availableVoices.find(
          (v) => v.lang.startsWith('en-') || v.lang === 'en'
        );
        setSelectedVoice(englishVoice || availableVoices[0]);
      }
    };

    // Load voices immediately
    loadVoices();

    // Some browsers load voices asynchronously
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = loadVoices;
    }

    return () => {
      if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = null;
      }
    };
  }, [isSupported, selectedVoice]);

  // Monitor speaking state
  useEffect(() => {
    if (!isSupported) return;

    const checkSpeakingState = setInterval(() => {
      setIsSpeaking(speechSynthesis.speaking);
      setIsPaused(speechSynthesis.paused);
    }, 100);

    return () => clearInterval(checkSpeakingState);
  }, [isSupported]);

  // Speak text
  const speak = useCallback(
    (text: string) => {
      if (!isSupported) {
        console.error('Speech synthesis is not supported in this browser');
        return;
      }

      // Stop any ongoing speech
      speechSynthesis.cancel();

      // Set state immediately
      setCurrentText(text);
      setCurrentWordIndex(0);
      setIsSpeaking(true); // Set immediately, don't wait for onstart

      // Create new utterance
      const utterance = new SpeechSynthesisUtterance(text);
      utteranceRef.current = utterance;

      // Configure utterance
      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }
      utterance.rate = rate;
      utterance.pitch = pitch;
      utterance.volume = 1.0;

      // Event handlers
      utterance.onstart = () => {
        setIsSpeaking(true);
        setIsPaused(false);
        setCurrentWordIndex(0);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPaused(false);
        setCurrentWordIndex(0);
        setCurrentText('');
        utteranceRef.current = null;
      };

      utterance.onerror = (event: any) => {
        // Suppress "interrupted" error - it's expected when user clicks stop
        if (event.error !== 'interrupted' && event.error !== 'canceled') {
          console.error('Speech synthesis error:', event.error);
        }
        setIsSpeaking(false);
        setIsPaused(false);
        setCurrentWordIndex(0);
        setCurrentText('');
        utteranceRef.current = null;
      };

      // Track word boundaries for highlighting
      utterance.onboundary = (event: any) => {
        if (event.name === 'word') {
          // Calculate which word we're on based on character index
          const textUpToNow = text.substring(0, event.charIndex);
          const wordsSoFar = textUpToNow.trim().split(/\s+/).length;
          const newIndex = wordsSoFar - 1;
          setCurrentWordIndex(newIndex);
        }
      };

      utterance.onpause = () => {
        setIsPaused(true);
      };

      utterance.onresume = () => {
        setIsPaused(false);
      };

      // Start speaking
      speechSynthesis.speak(utterance);
    },
    [isSupported, selectedVoice, rate, pitch]
  );

  // Stop speaking
  const stop = useCallback(() => {
    if (!isSupported) return;
    speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
    setCurrentWordIndex(0);
    setCurrentText('');
    utteranceRef.current = null;
  }, [isSupported]);

  // Pause speaking
  const pause = useCallback(() => {
    if (!isSupported || !isSpeaking) return;
    speechSynthesis.pause();
    setIsPaused(true);
  }, [isSupported, isSpeaking]);

  // Resume speaking
  const resume = useCallback(() => {
    if (!isSupported || !isPaused) return;
    speechSynthesis.resume();
    setIsPaused(false);
  }, [isSupported, isPaused]);

  return {
    speak,
    stop,
    pause,
    resume,
    isSpeaking,
    isPaused,
    isSupported,
    voices,
    selectedVoice,
    setSelectedVoice,
    rate,
    setRate,
    currentWordIndex,
    currentText,
    pitch,
    setPitch,
  };
};
