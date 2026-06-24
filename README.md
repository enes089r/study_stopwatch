# Study Stopwatch

A simple desktop app to track and optimize my daily study routine, built with Python and tkinter.

## About this project

I'm currently going through a busy exam period ("büt dönemi") and didn't want my GitHub activity to go quiet during it. Rather than skipping days, I treated this stretch as a different kind of learning exercise: working in short bursts, reviewing AI-assisted ("vibe coded") code, and practicing reading and understanding a codebase as a whole instead of writing every line from scratch.

This repo reflects that approach — it grew feature by feature, in small daily additions, rather than as one finished project.

## Current features

- Start / Stop / Reset stopwatch
- Automatically logs study time to a local JSON file (`study_log.json`) when stopped
- Manual time entry for study done away from the laptop (e.g. reading, offline practice)
- Last 7 days summary table
- 7-day total and daily average display
- Daily goal setting with a reached / not-reached status

## How to run

Requires Python 3 (tkinter is included by default on most installations).

```bash
python study_timer.py
```

## What's next

- Evolving this into a more general calendar / scheduling app, beyond a 7-day view
- More robust handling of day rollover and historical data

This isn't just a course exercise — the goal is to end up with something I actually use day to day to manage my own study schedule.

## Tech

- Python
- tkinter (GUI)
- JSON (local persistent storage)
