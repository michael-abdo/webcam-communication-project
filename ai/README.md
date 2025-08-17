# Xenodex AI - Personality Detection System

AI-powered celebrity personality detection system focusing on F/T (Feeler/Thinker) and Di/De (Direct/Informative) classifications.

## Project Structure

This follows the Stage 2 MLOps structure with full production capabilities.

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: Copy `.env.example` to `.env`
3. Run training: `python -m src.cli.train --detector f_t`
4. Make predictions: `python -m src.cli.predict --input data.json`

## Training Phases

- **Phase 1**: F/T Detector (80%, 90%, 95% accuracy targets)
- **Phase 2**: Di/De Detector (similar targets)
- **Phase 3**: Ensemble Logic (90%+ system accuracy)