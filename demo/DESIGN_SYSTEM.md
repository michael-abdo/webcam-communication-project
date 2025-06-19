# AI Behavioral Analytics Platform - Design System

## Brand Identity

### Logo and Branding
- **Platform Name**: BehaviorIQ Pro
- **Logo Placement**: Top-left corner of navigation bar
- **Tagline**: "Real-Time Meeting Intelligence"

### Color Palette
```css
:root {
  /* Primary Colors */
  --primary-color: #2563eb;        /* Deep Blue - Primary actions, headers */
  --primary-hover: #1d4ed8;        /* Darker blue for hover states */
  --primary-light: #dbeafe;        /* Light blue backgrounds */
  
  /* Secondary Colors */
  --secondary-color: #7c3aed;      /* Purple - Secondary actions, accents */
  --secondary-hover: #6d28d9;      /* Darker purple for hover */
  --secondary-light: #ede9fe;      /* Light purple backgrounds */
  
  /* Accent Colors */
  --accent-green: #10b981;         /* Success, positive metrics */
  --accent-orange: #f59e0b;        /* Warnings, alerts */
  --accent-red: #ef4444;           /* Errors, critical alerts */
  
  /* Neutral Colors */
  --gray-50: #f9fafb;              /* Page backgrounds */
  --gray-100: #f3f4f6;             /* Card backgrounds */
  --gray-200: #e5e7eb;             /* Borders, dividers */
  --gray-300: #d1d5db;             /* Input borders */
  --gray-600: #4b5563;             /* Secondary text */
  --gray-800: #1f2937;             /* Primary text */
  --gray-900: #111827;             /* Headings */
  
  /* Background Colors */
  --bg-primary: #ffffff;
  --bg-secondary: var(--gray-50);
  --bg-dark: var(--gray-900);
}
```

### Typography
```css
/* Font Families */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font Sizes */
--text-xs: 0.75rem;      /* 12px */
--text-sm: 0.875rem;     /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg: 1.125rem;     /* 18px */
--text-xl: 1.25rem;      /* 20px */
--text-2xl: 1.5rem;      /* 24px */
--text-3xl: 1.875rem;    /* 30px */
--text-4xl: 2.25rem;     /* 36px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

## Global Navigation Structure

### Main Navigation Menu
```html
<nav class="main-nav">
  <div class="nav-brand">
    <span class="logo">🧠 BehaviorIQ Pro</span>
  </div>
  <ul class="nav-menu">
    <li><a href="index.html" class="nav-link">Dashboard</a></li>
    <li><a href="analysis.html" class="nav-link">Live Analysis</a></li>
    <li><a href="reports.html" class="nav-link">Reports</a></li>
    <li><a href="settings.html" class="nav-link">Settings</a></li>
  </ul>
  <div class="nav-actions">
    <button class="btn btn-primary">Start Session</button>
  </div>
</nav>
```

### Navigation Behavior
- Fixed top navigation bar
- Active page highlighted with primary color
- Smooth hover transitions
- Responsive dropdown for actions on smaller screens

## Shared CSS Variables & Component Styles

### Spacing System
```css
--spacing-1: 0.25rem;    /* 4px */
--spacing-2: 0.5rem;     /* 8px */
--spacing-3: 0.75rem;    /* 12px */
--spacing-4: 1rem;       /* 16px */
--spacing-5: 1.25rem;    /* 20px */
--spacing-6: 1.5rem;     /* 24px */
--spacing-8: 2rem;       /* 32px */
--spacing-10: 2.5rem;    /* 40px */
--spacing-12: 3rem;      /* 48px */
--spacing-16: 4rem;      /* 64px */
```

### Border Radius
```css
--radius-sm: 0.25rem;    /* 4px */
--radius-md: 0.375rem;   /* 6px */
--radius-lg: 0.5rem;     /* 8px */
--radius-xl: 0.75rem;    /* 12px */
--radius-2xl: 1rem;      /* 16px */
```

### Shadows
```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
```

## Component Templates

### Button Styles
```html
<!-- Primary Button -->
<button class="btn btn-primary">Primary Action</button>

<!-- Secondary Button -->
<button class="btn btn-secondary">Secondary Action</button>

<!-- Danger Button -->
<button class="btn btn-danger">Delete</button>

<!-- Button Sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary">Default</button>
<button class="btn btn-primary btn-lg">Large</button>
```

### Card Component
```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Card Title</h3>
    <div class="card-actions">
      <button class="btn btn-sm btn-secondary">Action</button>
    </div>
  </div>
  <div class="card-body">
    <p class="card-text">Card content goes here</p>
  </div>
  <div class="card-footer">
    <small class="text-muted">Footer content</small>
  </div>
</div>
```

### Form Elements
```html
<div class="form-group">
  <label class="form-label" for="input-id">Label Text</label>
  <input type="text" class="form-input" id="input-id" placeholder="Placeholder">
  <span class="form-help">Help text for this field</span>
</div>

<div class="form-group">
  <label class="form-label">
    <input type="checkbox" class="form-checkbox">
    <span class="checkbox-label">Checkbox Label</span>
  </label>
</div>
```

### Alert Component
```html
<div class="alert alert-success">
  <div class="alert-icon">✓</div>
  <div class="alert-content">
    <h4 class="alert-title">Success!</h4>
    <p class="alert-message">Your action was completed successfully.</p>
  </div>
</div>
```

## Page Layout Standards

### Page Wrapper Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title - BehaviorIQ Pro</title>
</head>
<body>
  <!-- Navigation -->
  <nav class="main-nav">...</nav>
  
  <!-- Main Content -->
  <main class="main-content">
    <div class="container">
      <!-- Page content -->
    </div>
  </main>
  
  <!-- Footer (if needed) -->
  <footer class="main-footer">...</footer>
</body>
</html>
```

### Container Specifications
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-6);
}

.container-fluid {
  width: 100%;
  padding: 0 var(--spacing-6);
}
```

### Grid System
```css
.grid {
  display: grid;
  gap: var(--spacing-6);
}

.grid-cols-1 { grid-template-columns: repeat(1, 1fr); }
.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid-cols-4 { grid-template-columns: repeat(4, 1fr); }

.flex {
  display: flex;
}

.flex-col {
  flex-direction: column;
}

.items-center {
  align-items: center;
}

.justify-between {
  justify-content: space-between;
}
```

## Desktop-Specific Standards

### Viewport Specifications
- **Target Resolution**: 1280x720 minimum
- **Optimal Resolution**: 1920x1080
- **No mobile responsiveness required**
- **Fixed navigation bar**
- **Sidebar navigation where applicable**

### Layout Principles
1. **Fixed Navigation**: Top navigation bar always visible
2. **Sidebar Support**: Left sidebar for secondary navigation when needed
3. **Content Area**: Main content area with appropriate margins
4. **Action Areas**: Clear placement for primary/secondary actions
5. **Data Density**: Optimized for desktop viewing with rich data displays

## AI Platform Specific Components

### Real-Time Metrics Cards
```html
<div class="metric-card">
  <div class="metric-header">
    <h4 class="metric-title">Engagement Score</h4>
    <span class="metric-status status-good">Active</span>
  </div>
  <div class="metric-value">
    <span class="metric-number">87%</span>
    <span class="metric-trend trend-up">+5%</span>
  </div>
  <div class="metric-chart">
    <!-- Chart placeholder -->
  </div>
</div>
```

### Video Feed Container
```html
<div class="video-container">
  <div class="video-feed">
    <div class="video-placeholder">
      📹 Live Video Feed
    </div>
    <div class="video-controls">
      <button class="btn btn-sm btn-secondary">Pause</button>
      <button class="btn btn-sm btn-primary">Record</button>
    </div>
  </div>
  <div class="analysis-overlay">
    <div class="emotion-indicators">
      <span class="emotion-tag">😊 Happy: 65%</span>
      <span class="emotion-tag">🤔 Focused: 30%</span>
    </div>
  </div>
</div>
```

### Dashboard Widget
```html
<div class="dashboard-widget">
  <div class="widget-header">
    <h3 class="widget-title">Meeting Insights</h3>
    <div class="widget-actions">
      <button class="btn btn-xs btn-secondary">⚙️</button>
      <button class="btn btn-xs btn-secondary">📊</button>
    </div>
  </div>
  <div class="widget-content">
    <!-- Widget-specific content -->
  </div>
</div>
```

## Success Criteria Checklist

- ✅ Unified color palette and typography system
- ✅ Consistent navigation across all pages
- ✅ Reusable component templates
- ✅ Professional AI platform aesthetic
- ✅ Desktop-optimized layouts
- ✅ Clear hierarchy and information architecture
- ✅ Accessibility considerations in color contrast
- ✅ Interactive states defined for all components