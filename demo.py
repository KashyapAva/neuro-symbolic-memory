"""Main submission demo for the neuro-symbolic memory engine.

Run:
    python3 demo.py

This entrypoint intentionally delegates to demo_robust_system.main() so the
repo has one clear command while keeping the implementation readable.
"""

from demo_robust_system import main

if __name__ == "__main__":
    main()
