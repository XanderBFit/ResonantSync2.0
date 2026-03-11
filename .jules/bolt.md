## 2024-05-14 - Canvas Render Optimization
**Learning:** Frequent array creation, mapping, and string interpolation in a 60FPS animation frame loop (like `requestAnimationFrame`) can cause high CPU overhead and GC stuttering, even for simple canvas apps.
**Action:** Always pre-calculate and cache constants (like color arrays or standard size multipliers) outside of `requestAnimationFrame` loops when building React Canvas components.

## 2024-05-14 - Expensive Array Filtering
**Learning:** Unmemoized Array.filter operations containing multiple string matching functions (.toLowerCase(), .includes()) on every keystroke/render will cause noticeable UI input lag as list sizes grow.
**Action:** Always wrap computationally expensive UI state derivatives (like searching/filtering) in `useMemo` with correctly configured dependency arrays to guarantee fast input response.