# 🎨 White Agent Theme Guide

## Overview

The White Agent chat interface uses a modern, professional design system inspired by Vercel AI SDK, adapted for React + Vite + Tailwind CSS.

## 🎨 Color Palette

### Primary Colors

| Color | Value | Usage |
|-------|-------|-------|
| **Primary** | `hsl(262 83% 58%)` | Purple - Main brand color |
| **Background** | `hsl(0 0% 100%)` | White - Main background |
| **Foreground** | `hsl(240 10% 3.9%)` | Dark gray - Main text |

### Agent-Specific Colors

| Agent | Background | Text | Border |
|-------|-----------|------|--------|
| **User** | `hsl(217 91% 95%)` | `hsl(217 91% 60%)` | Blue theme |
| **White Agent** | `hsl(262 83% 95%)` | `hsl(262 83% 58%)` | Purple theme |
| **Supervisor** | `hsl(142 76% 95%)` | `hsl(142 76% 36%)` | Green theme |
| **Tool** | `hsl(25 95% 95%)` | `hsl(25 95% 53%)` | Orange theme |

### Semantic Colors

- **Destructive**: Red for errors
- **Muted**: Gray for secondary content
- **Accent**: Subtle highlights
- **Border**: Consistent borders throughout

## 🔤 Typography

### Fonts

**Sans Serif** - Inter (Google Fonts)
- Weights: 300, 400, 500, 600, 700
- Usage: Body text, headings, UI elements

**Monospace** - JetBrains Mono (Google Fonts)
- Weights: 400, 500, 600
- Usage: Code blocks, technical data

### Font Classes

```tsx
<div className="font-sans">Regular text</div>
<code className="font-mono">Code text</code>
```

## ✨ Components

### Message Bubbles

**User Messages:**
```tsx
<div className="bg-user-light border border-user/20 text-foreground">
  {/* User message */}
</div>
```

**White Agent Messages:**
```tsx
<div className="bg-card border border-border text-card-foreground">
  {/* Agent message */}
</div>
```

### Agent Badges

Each message has a badge showing the agent type:

```tsx
// User
<span className="bg-user-light text-user border border-user/20">
  👤 You
</span>

// White Agent  
<span className="bg-white-agent-light text-white-agent border border-white-agent/20">
  ⚪ White Agent
</span>

// Supervisor
<span className="bg-supervisor-light text-supervisor border border-supervisor/20">
  ✓ Supervisor
</span>

// Tool
<span className="bg-tool-light text-tool border border-tool/20">
  ⚙️ Tool
</span>
```

## 🎬 Animations

### Slide Up

Messages slide up with a subtle animation when they appear:

```tsx
<div className="animate-slide-up">
  {/* Message content */}
</div>
```

### Fade In

Loading states and empty states fade in smoothly:

```tsx
<div className="animate-fade-in">
  {/* Loading content */}
</div>
```

### Hover Effects

Interactive elements have smooth transitions:

```tsx
<div className="transition-all hover:shadow-md">
  {/* Hoverable content */}
</div>
```

## 📐 Spacing & Layout

### Container Widths

- **Chat Container**: `max-w-4xl` (wider for flight data tables)
- **Message Bubbles**: `max-w-[85%]` (allows for comfortable reading)
- **Empty State**: `max-w-lg` (centered welcome message)

### Padding

- **Messages**: `px-5 py-4` (comfortable spacing)
- **Input**: `px-4 py-3` (balanced input area)
- **Header**: `px-6 py-4` (consistent header spacing)

### Border Radius

- **Large**: `rounded-2xl` (modern, friendly)
- **Medium**: `rounded-xl` (inputs, buttons)
- **Small**: `rounded-full` (badges)

## 🌓 Dark Mode Ready

All colors are defined as CSS variables and support dark mode:

```css
.dark {
  --background: 240 10% 3.9%;
  --foreground: 0 0% 98%;
  /* ... inverted colors ... */
}
```

To enable dark mode:
```tsx
<html className="dark">
```

## 🎯 Design Principles

1. **Clarity** - Clear visual hierarchy with badges and colors
2. **Consistency** - Unified spacing and styling throughout
3. **Accessibility** - Proper contrast ratios for all text
4. **Responsiveness** - Works on all screen sizes
5. **Performance** - Smooth animations without jank

## 📦 Key Features

### Visual Enhancements

✅ **Gradient Backgrounds** - Subtle gradients for depth
✅ **Shadow System** - Layered shadows for elevation
✅ **Smooth Transitions** - All interactions feel responsive
✅ **Custom Fonts** - Professional typography
✅ **Color-Coded Agents** - Instantly identify who's talking
✅ **Emoji Icons** - Friendly, approachable interface

### Interactions

✅ **Hover States** - All clickable elements respond to hover
✅ **Focus States** - Clear focus rings for accessibility
✅ **Loading States** - Animated feedback during processing
✅ **Error States** - Distinct error styling

## 🔧 Customization

### Change Primary Color

Edit `index.css`:
```css
--primary: 262 83% 58%;  /* Purple */
/* Change to: */
--primary: 142 76% 36%;  /* Green */
--primary: 217 91% 60%;  /* Blue */
```

### Change Fonts

Edit `tailwind.config.js`:
```js
fontFamily: {
  sans: ['Your Font', 'system-ui', 'sans-serif'],
  mono: ['Your Mono Font', 'monospace'],
}
```

Update Google Fonts import in `index.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=YourFont:wght@...&display=swap');
```

### Adjust Border Radius

Edit `index.css`:
```css
--radius: 0.5rem;  /* Current: medium rounded */
/* Change to: */
--radius: 0rem;    /* Sharp corners */
--radius: 1rem;    /* Extra rounded */
```

## 📱 Responsive Design

The interface automatically adapts to different screen sizes:

- **Desktop**: Full width with max-w-4xl constraint
- **Tablet**: Adjusted spacing and sizing
- **Mobile**: Stack elements vertically, touch-friendly buttons

## 🎁 Bonus Features

### Gradient Headers

The header uses a gradient orb for the White Agent logo:
```tsx
<div className="bg-gradient-to-br from-white-agent to-primary">
  ⚪
</div>
```

### Animated Gradient Border

Active navigation tabs have a multi-color gradient border:
```tsx
<div className="bg-gradient-to-r from-primary via-white-agent to-primary" />
```

### Enhanced Input

The input field has smooth focus transitions and a styled send button with an arrow icon.

---

**Theme Version:** 1.0.0  
**Last Updated:** October 25, 2025  
**Framework:** React + Tailwind CSS + Vite







