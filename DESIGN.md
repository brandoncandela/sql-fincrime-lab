# SQL Financial Crime Lab design system

## Direction

A dark financial-crime investigation workbench. The interface must make the SQL, thresholds, alert evidence and reviewer judgment feel inspectable rather than magical.

## Foundations

- **Typography:** Public Sans for product UI; the existing system monospace stack for SQL and transaction evidence.
- **Canvas:** deep navy (`#08131f`) with layered work surfaces (`#102233`).
- **Signals:** mint (`#5bd4bd`) for primary action and analytical selection; evidence gold (`#e5b966`) for focus and review attention.
- **Geometry:** crisp one-pixel dividers and small control radii. No decorative glyphs, glow or gradient treatments.
- **Spacing:** compact in alert queues and controls, wider around analytical sections and conclusions.

## Components and interaction

- Rule cards are tunable monitoring scenarios, not marketing cards.
- Metrics stay attached to the selected thresholds and retain exact values.
- The alert queue, case panel and raw SQL form one evidence chain.
- Controls and disclosure targets are at least 44px high, keyboard visible and reduced-motion safe.
- Status colors never substitute for labels or written conclusions.

## Responsive behavior

The workbench collapses to one column while preserving the queue before the detail panel. Dense evidence tables remain horizontally scrollable instead of becoming illegible.
