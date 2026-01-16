## 2026-01-16 - Accessible Feedback in Embedded UI
**Learning:** Embedded single-file UIs often miss basic feedback loops. Adding immediate visual feedback (button state) + accessibility (hidden labels) provides a huge UX win with minimal code.
**Action:** Always check for `aria-label` or `<label>` on inputs and disabled states on submit buttons in raw HTML strings.
