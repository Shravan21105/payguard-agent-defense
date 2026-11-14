# PAYGUARD — Phase 8 Design System Specification
## Futuristic Cybersecurity SaaS Design Language & Tokens

### 1. Design Vision & Visual Identity
PAYGUARD's visual architecture is engineered to project the highest tier of enterprise cybersecurity, cryptographic integrity, and autonomous agent financial defense. Combining **Linear-level minimalism and polish** with a **futuristic Security Operations Center (SOC)** aesthetic, the design language communicates:
- **Autonomous Agent Financial Protection:** Clean technical metrics and real-time transaction telemetry.
- **Deterministic Supremacy with AI Advisory:** Clear visual distinction between advisory intelligence and hard deterministic barriers.
- **Cryptographic Trust:** Domain-separated Ed25519 signatures, RFC-8785 evidence digests, and NEAR blockchain verifications.

---

### 2. Design Tokens

#### A. Color Palette

```
Canvas / Deep Midnight Navy:
  navy-950: #070B18 (Primary canvas)
  navy-900: #0B1020 (Layer 1 sub-base)
  navy-850: #10172B (Layer 2 card base)
  navy-800: #111A30 (Surface Primary)
  navy-750: #17213A (Surface Secondary)
  navy-700: #1C2945 (Surface Raised)

Text & Contrast:
  navy-100: #E2E9F6 (High-contrast headings)
  navy-200: #C7D4EC (Emphasized body text)
  navy-300: #94A7CE (Primary body text)
  navy-400: #627CB0 (Secondary labels / captions)
  navy-500: #3D5285 (Muted placeholder text)

Gradients:
  Primary Electric:   linear-gradient(135deg, #2563EB 0%, #6366F1 50%, #8B5CF6 100%)
  Secondary Cyber:    linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)
  Cyber Gradient:     linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #22D3EE 100%)
  Security Emerald:   linear-gradient(135deg, #059669 0%, #10B981 100%)
  Warning Amber:      linear-gradient(135deg, #D97706 0%, #F59E0B 100%)
  Critical Threat:    linear-gradient(135deg, #DC2626 0%, #EF4444 100%)
```

#### B. Status Tokens
| State | Hex | Background Token | Glow Effect |
| :--- | :---: | :--- | :--- |
| **`ALLOW` / `CONFIRMED`** | `#10B981` | `rgba(16, 185, 129, 0.1)` | `shadow-success-glow` (`0 0 25px -4px rgba(16, 185, 129, 0.35)`) |
| **`WARN` / `ESCROW_CREATED`** | `#F59E0B` | `rgba(245, 158, 11, 0.1)` | `shadow-warning-glow` (`0 0 25px -4px rgba(245, 158, 11, 0.35)`) |
| **`BLOCK` / `FAILED` / `CRITICAL`** | `#EF4444` | `rgba(239, 68, 68, 0.1)` | `shadow-danger-glow` (`0 0 25px -4px rgba(239, 68, 68, 0.35)`) |
| **`INFO` / `ANALYZING` / `RECEIVED`**| `#22D3EE` | `rgba(34, 211, 238, 0.1)` | `shadow-cyan-glow` (`0 0 25px -5px rgba(34, 211, 238, 0.3)`) |

#### C. Typography
- **Primary Font:** `'Inter'`, system-ui, -apple-system, sans-serif
- **Technical Monospace Font:** `'JetBrains Mono'`, `'Fira Code'`, Menlo, monospace
- Monospace styling is applied strictly to cryptographic hashes, account identifiers, numerical quantities, transaction IDs, block heights, and policy check names.

---

### 3. Reusable UI Components Architecture

All components reside in [`frontend/src/components/ui/`](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/frontend/src/components/ui):

1. **`GlassCard`**:
   - Translucent glassmorphism using `backdrop-blur-md` or `backdrop-blur-lg`.
   - Subtle 1px borders (`border-white/[0.08]`) with inner edge reflection (`shadow-glass-panel`).
   - Variants: `default`, `elevated`, `subtle`, `interactive`.
   - Glow accents: `primary`, `cyan`, `emerald`, `amber`, `rose`.

2. **`GradientCard`**:
   - Directional gradient card with subtle ambient lighting.
   - Accents: `primary`, `cyan`, `violet`, `emerald`, `danger`.

3. **`GradientButton`**:
   - Highly interactive button with micro-interactions, active press scale (`active:scale-[0.98]`), disabled state, and built-in loading spinner.
   - Variants: `primary`, `secondary`, `glass`, `danger`, `success`, `ghost`, `outline`.

4. **`StatusBadge`**:
   - Pill badge featuring a pulsing radar dot, status-keyed color, and font-mono uppercase text.

5. **`MetricCard`**:
   - KPI card displaying real backend metrics, accent borders (`border-l-4`), themed icon container, large bold monospace numbers, and authentic trend labels.

6. **`RiskIndicator`**:
   - Visual risk score meter with color-coded gradients, risk tier badge (`LOW`, `MEDIUM`, `HIGH`), and percentage bar.

7. **`LiveIndicator`**:
   - Real-time WebSocket connection state indicator with animated ping radar ring (`live`, `syncing`, `offline`).

8. **`EmptyState`**:
   - Cyber empty state container with icon badges, title, description, and action CTA.

9. **`ConfirmationDialog`**:
   - High-contrast modal dialog preventing accidental execution of irreversible or financial actions (such as authorizing escrow releases or refunds).

10. **`PageTransition`**:
    - Smooth entry container applying performant CSS `animate-fade-in-up` with `transform: translateY(8px)`.

---

### 4. Responsiveness & Accessibility
- **Breakpoints:**
  - `sm`: 640px (Mobile landscape & small tablets)
  - `md`: 768px (Tablets & standard laptops)
  - `lg`: 1024px (Desktops)
  - `xl`: 1280px (Wide enterprise monitors)
- **Zero Horizontal Overflow:** Tables are wrapped in responsive horizontal scrolling containers with custom slim scrollbars.
- **Mobile Navigation Drawer:** Responsive slide-over menu with backdrop blur on screens `< 1024px`.
- **Keyboard Navigation:** Modals and confirmation dialogs listen for `Escape` keys and trap background scrolling.

