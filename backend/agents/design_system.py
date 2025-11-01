"""
AICOE Advanced Design System
Apple-inspired design guidelines for all HTML-generating agents
"""

# AICOE Color Palette
AICOE_COLORS = {
    "primary_navy": "#1a1a2e",
    "midnight_blue": "#2a2a3e",
    "deep_purple": "#3a2a4e",
    "accent_pink": "#ff69b4",
    "accent_cyan": "#00ffcc",
    "accent_turquoise": "#00e5b3",
    "text_primary": "#1a1a1a",
    "text_secondary": "#6e6e73",
    "bg_white": "#ffffff",
    "bg_gray": "#f5f5f7",
    "bg_dark": "#1d1d1f",
    "success": "#34c759",
    "warning": "#ff9500",
    "error": "#ff3b30",
    "info": "#007aff"
}

# Typography Scale
TYPOGRAPHY = {
    "font_family": "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif",
    "hero": "clamp(2.5rem, 5vw, 4rem)",
    "h1": "clamp(2rem, 4vw, 3rem)",
    "h2": "clamp(1.5rem, 3vw, 2.25rem)",
    "h3": "clamp(1.25rem, 2.5vw, 1.75rem)",
    "h4": "1.125rem",
    "body": "1rem",
    "small": "0.875rem",
    "tiny": "0.75rem"
}

# Spacing System (8px grid)
SPACING = {
    "xs": "0.5rem",   # 8px
    "sm": "1rem",     # 16px
    "md": "1.5rem",   # 24px
    "lg": "2rem",     # 32px
    "xl": "2.5rem",   # 40px
    "2xl": "3rem",    # 48px
    "3xl": "4rem",    # 64px
    "4xl": "5rem"     # 80px
}

# Shadow System
SHADOWS = {
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
    "inner": "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)"
}

# Border Radius
RADIUS = {
    "sm": "0.375rem",   # 6px
    "md": "0.5rem",     # 8px
    "lg": "0.75rem",    # 12px
    "xl": "1rem",       # 16px
    "2xl": "1.5rem",    # 24px
    "full": "9999px"
}

# Transitions
TRANSITIONS = {
    "fast": "150ms cubic-bezier(0.4, 0, 0.2, 1)",
    "base": "300ms cubic-bezier(0.4, 0, 0.2, 1)",
    "slow": "500ms cubic-bezier(0.4, 0, 0.2, 1)"
}

# Advanced Design System Prompt Template
DESIGN_SYSTEM_PROMPT = """
## 🎨 AICOE ADVANCED DESIGN SYSTEM

### **CORE PRINCIPLES (Apple-Inspired)**
1. **Clarity**: Typography is clear, icons are precise, adornments are subtle
2. **Deference**: Fluid motion and crisp interface help people understand content
3. **Depth**: Layers and realistic motion convey hierarchy and vitality

### **COLOR PALETTE**
```css
:root {
    /* Primary Colors */
    --aicoe-primary-navy: #1a1a2e;
    --aicoe-midnight-blue: #2a2a3e;
    --aicoe-deep-purple: #3a2a4e;
    
    /* Accent Colors */
    --aicoe-accent-pink: #ff69b4;
    --aicoe-accent-cyan: #00ffcc;
    --aicoe-accent-turquoise: #00e5b3;
    
    /* Text Colors */
    --aicoe-text-primary: #1a1a1a;
    --aicoe-text-secondary: #6e6e73;
    
    /* Background Colors */
    --aicoe-bg-white: #ffffff;
    --aicoe-bg-gray: #f5f5f7;
    --aicoe-bg-dark: #1d1d1f;
    
    /* Semantic Colors */
    --aicoe-success: #34c759;
    --aicoe-warning: #ff9500;
    --aicoe-error: #ff3b30;
    --aicoe-info: #007aff;
    
    /* Gradients */
    --aicoe-gradient-primary: linear-gradient(135deg, var(--aicoe-accent-pink), var(--aicoe-accent-cyan));
    --aicoe-gradient-secondary: linear-gradient(135deg, var(--aicoe-primary-navy), var(--aicoe-deep-purple));
}
```

### **TYPOGRAPHY SYSTEM**
```css
/* Font Family */
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;

/* Type Scale (Fluid Typography) */
--font-hero: clamp(2.5rem, 5vw, 4rem);      /* 40-64px */
--font-h1: clamp(2rem, 4vw, 3rem);          /* 32-48px */
--font-h2: clamp(1.5rem, 3vw, 2.25rem);     /* 24-36px */
--font-h3: clamp(1.25rem, 2.5vw, 1.75rem);  /* 20-28px */
--font-h4: 1.125rem;                         /* 18px */
--font-body: 1rem;                           /* 16px */
--font-small: 0.875rem;                      /* 14px */
--font-tiny: 0.75rem;                        /* 12px */

/* Font Weights */
--font-light: 300;
--font-regular: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line Heights */
--line-tight: 1.2;
--line-normal: 1.5;
--line-relaxed: 1.75;
```

### **SPACING SYSTEM (8px Grid)**
```css
--space-xs: 0.5rem;   /* 8px */
--space-sm: 1rem;     /* 16px */
--space-md: 1.5rem;   /* 24px */
--space-lg: 2rem;     /* 32px */
--space-xl: 2.5rem;   /* 40px */
--space-2xl: 3rem;    /* 48px */
--space-3xl: 4rem;    /* 64px */
--space-4xl: 5rem;    /* 80px */
```

### **SHADOW SYSTEM (Elevation)**
```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
--shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
```

### **BORDER RADIUS**
```css
--radius-sm: 0.375rem;   /* 6px */
--radius-md: 0.5rem;     /* 8px */
--radius-lg: 0.75rem;    /* 12px */
--radius-xl: 1rem;       /* 16px */
--radius-2xl: 1.5rem;    /* 24px */
--radius-full: 9999px;   /* Fully rounded */
```

### **TRANSITIONS & ANIMATIONS**
```css
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-base: 300ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 500ms cubic-bezier(0.4, 0, 0.2, 1);

/* Smooth Scroll */
html { scroll-behavior: smooth; }

/* Fade In Animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Slide In Animation */
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

/* Scale In Animation */
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}
```

### **COMPONENT LIBRARY**

#### **Buttons**
```css
.btn {
    display: inline-flex;
    align-items: center;
    gap: var(--space-xs);
    padding: var(--space-sm) var(--space-lg);
    border-radius: var(--radius-lg);
    font-weight: var(--font-medium);
    font-size: var(--font-body);
    transition: all var(--transition-base);
    cursor: pointer;
    border: none;
    text-decoration: none;
}

.btn-primary {
    background: var(--aicoe-gradient-primary);
    color: white;
    box-shadow: var(--shadow-md);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.btn-secondary {
    background: var(--aicoe-bg-white);
    color: var(--aicoe-primary-navy);
    border: 2px solid var(--aicoe-primary-navy);
}

.btn-secondary:hover {
    background: var(--aicoe-primary-navy);
    color: white;
}
```

#### **Cards**
```css
.card {
    background: var(--aicoe-bg-white);
    border-radius: var(--radius-2xl);
    padding: var(--space-xl);
    box-shadow: var(--shadow-md);
    transition: all var(--transition-base);
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
}

.card-glass {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
}
```

### **LAYOUT PATTERNS**

#### **Container**
```css
.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--space-lg);
}
```

#### **Grid System**
```css
.grid {
    display: grid;
    gap: var(--space-lg);
}

.grid-2 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
.grid-3 { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
.grid-4 { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
```

### **RESPONSIVE BREAKPOINTS**
```css
/* Mobile First Approach */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

### **ACCESSIBILITY**
- Use semantic HTML (header, nav, main, section, article, footer)
- Include ARIA labels for interactive elements
- Ensure color contrast ratio ≥ 4.5:1 for text
- Support keyboard navigation (Tab, Enter, Escape)
- Include focus states for all interactive elements

### **ICONS**
- Use Lucide Icons: `<script src="https://unpkg.com/lucide@latest"></script>`
- Initialize: `<script>lucide.createIcons();</script>`
- Usage: `<i data-lucide="icon-name"></i>`

### **REQUIRED LIBRARIES**
```html
<!-- Lucide Icons -->
<script src="https://unpkg.com/lucide@latest"></script>

<!-- Optional: Chart.js for data visualization -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- Optional: Mermaid for diagrams -->
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
```
"""

def get_design_system_prompt():
    """Returns the complete design system prompt for HTML generation"""
    return DESIGN_SYSTEM_PROMPT

