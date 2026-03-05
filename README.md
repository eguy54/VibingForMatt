# Maze Builder (Streamlit)

This app generates playable mazes and can solve them on demand.

## User inputs
- Difficulty: Easy, Medium, Hard
- Width and height
- Seed (set 0 for random)

## Toggle options
- Allow loops
- Add room areas
- Vertical symmetry
- Multiple exits
- Allow diagonal solve moves

## Actions
- Generate Maze: builds a new maze from the selected settings
- Solve: overlays the shortest path in blue

## Run locally
1. Activate the virtual environment:
   .\\.venv\\Scripts\\Activate.ps1
2. Install dependencies (if needed):
   pip install -r requirements.txt
3. Run:
   streamlit run app.py
