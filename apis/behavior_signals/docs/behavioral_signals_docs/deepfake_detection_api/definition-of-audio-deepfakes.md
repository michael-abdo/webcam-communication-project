# Definition of Audio Deepfakes

## Overview
Audio deepfakes are "synthetic speech samples generated using AI models to mimic human voices" with significant challenges in detection and prevention.

## Types of Deepfake Generators

### Voice Cloning Generators
- Replicate a specific person's voice using a short audio sample
- Used by commercial and open-source tools to mimic real individuals

### Text-to-Speech (TTS) Generators
- Convert written text into synthetic speech
- Can use generic or prebuilt voices

## Open-Source Generators
- F5-TTS: Multilingual zero-shot voice cloning
- xTTS-v2: Coqui's multilingual zero-shot voice cloning

## Commercial API Services
- ElevenLabs: High-quality commercial voice cloning
- PlayHT: Enterprise-grade TTS services

## Attack Sophistication Levels
1. High-Quality Deepfakes: Nearly indistinguishable from authentic speech
2. Medium-Quality Spoofs: Detectable with advanced algorithms
3. Low-Quality Fakes: Poor quality, easy to create

## Detection Technology
The deepfake audio detector uses behavioral AI that:
- Analyzes speech dynamics
- Examines intonation, emotional tone, hesitation patterns
- Trained on authentic and synthetic speech data
- Segments audio into utterances
- Extracts key speech features
- Evaluates audio authenticity

## Key Challenges
- High realism of modern AI models
- Cross-lingual threats
- Need for speaker-independent detection