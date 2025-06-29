#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 app.py --printer stampante01 &
google-chrome http://127.0.0.1:3000