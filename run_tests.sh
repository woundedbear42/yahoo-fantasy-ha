#!/bin/bash
set -e
cd /home/woundedbear/projects/yahoo-fantasy-ha/.worktrees/t_e782f138
source .venv/bin/activate
python -m pytest tests/ -v 2>&1
