import { useState, useEffect, useRef, useCallback } from 'react';

interface UseSpeechRecognitionReturn {
  transcript: string;
  isListening: boolean;
  isSupported: boolean;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
}

export const useSpeechRecognition = (): UseSpeechRecognitionReturn => {
  const [transcript, setTranscript] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  // Check if speech recognition is supported
  const isSupported = typeof window !== 'undefined' && 
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  useEffect(() => {
    if (!isSupported) {
      setError('Speech recognition is not supported in this browser');
      return;
    }

    // Initialize speech recognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    // Configuration
    recognition.continuous = true; // Keep listening until manually stopped
    recognition.interimResults = true; // Show real-time results
    recognition.lang = 'en-US'; // Default language

    // Handle results
    recognition.onresult = (event: any) => {
      let finalTranscript = '';

      // Process all results - only accumulate FINAL results
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPiece = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcriptPiece + ' ';
        }
        // Ignore interim results to prevent duplication
      }

      // Only update transcript with FINAL confirmed speech
      if (finalTranscript) {
        setTranscript((prev) => prev + finalTranscript);
      }
    };

    // Handle errors
    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      
      switch (event.error) {
        case 'no-speech':
          setError('No speech detected. Please try again.');
          break;
        case 'audio-capture':
          setError('Microphone not found or not accessible.');
          break;
        case 'not-allowed':
          setError('Microphone permission denied.');
          break;
        case 'network':
          setError('Network error occurred.');
          break;
        default:
          setError(`Error: ${event.error}`);
      }
      
      setIsListening(false);
    };

    // Handle end of recognition
    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isSupported]);

  // Start listening
  const startListening = useCallback(() => {
    if (!isSupported || !recognitionRef.current) {
      setError('Speech recognition is not supported');
      return;
    }

    try {
      setError(null);
      setTranscript(''); // Clear previous transcript
      recognitionRef.current.start();
      setIsListening(true);
    } catch (err: any) {
      // If already started, this will throw an error
      if (err.message && err.message.includes('already started')) {
        console.log('Recognition already running');
      } else {
        setError('Failed to start speech recognition');
        console.error(err);
      }
    }
  }, [isSupported]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, [isListening]);

  // Reset transcript
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setError(null);
  }, []);

  return {
    transcript,
    isListening,
    isSupported,
    error,
    startListening,
    stopListening,
    resetTranscript,
  };
};
