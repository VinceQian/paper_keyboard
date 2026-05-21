# Prototype Recorder V1

This is the first modular prototype for the paper keyboard project.

It is designed to:

1. Run a paper keyboard vision demo
2. Detect candidate keys from finger positions
3. Record intermediate demo data
4. Export data that can be reused in course lessons

## Required Python Version

Use Python 3.11.

## Setup

Create a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python --version
```

## Install dependencies:
```
python -m pip install -r requirements.txt
```

## Main App
```
python app/demo_record.py
```

## Folder Structure
```
app/       runnable demo scripts
core/      core logic such as layout, candidate detection, and recording
vision/    camera, hand tracking, ArUco, and coordinate mapping
audio/     tap detection
output/    keyboard or text output
data/      layouts, recorded data, and example data
docs/      documentation
```