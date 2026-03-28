# Modern UI Redesign - Template Migration Guide

## Overview

This guide explains how to activate the new Tailwind-based UI templates that replace the Bootstrap Material Design with a modern, shadcn/ui-inspired aesthetic using Tailwind CSS CDN.

## New Templates Created

All new templates use:
- **Tailwind CSS CDN** (no build tools required)
- **Modern Fonts**: Space Grotesk (headings), Inter (body)
- **shadcn/ui-inspired Design**: Clean, minimal, professional
- **Full Responsiveness**: Mobile-first approach
- **Material Icons**: For consistent iconography

### Frontend Templates

| Original | New | Purpose |
|----------|-----|---------|
| `login.html` | `login_new.html` | Authentication page |
| `index.html` | `index_new.html` | Dashboard with balance & transactions |
| `signup.html` | `signup_new.html` | Registration page |
| `consent.html` | `consent_new.html` | OAuth authorization consent |
| `shared/navigation.html` | `shared/navigation_new.html` | Top navigation bar |
| `shared/footer.html` | `shared/footer_new.html` | Page footer |

### Failure-Injector Dashboard

| Original | New | Purpose |
|----------|-----|---------|
| `templates/dashboard.html` | `templates/dashboard_new.html` | Chaos testing control panel |

## Activation Steps

### Option 1: Quick Test (Keep Both)

Test new templates without removing old ones:

```bash
# Frontend - Access via different routes
# Edit src/frontend/app.py to add routes to _new templates:

@app.route('/test/login')
def test_login():
    return render_template('login_new.html', bank_name='The Bank of Catz')

@app.route('/test/dashboard')
def test_dashboard():
    # Pass required variables
    return render_template('index_new.html', ...)

@app.route('/test/failure')
def test_failure():
    return render_template('failure-injector/templates/dashboard_new.html')
```

Then visit:
- http://localhost:8080/test/login
- http://localhost:8080/test/dashboard
- http://localhost:8090/test/failure

### Option 2: Full Migration (Replace Originals)

Backup and replace the original templates:

```bash
cd /workspaces/bank-of-anthos/src/frontend/templates

# Backup originals
mkdir -p backups
cp login.html backups/
cp index.html backups/
cp signup.html backups/
cp consent.html backups/
cp shared/navigation.html backups/
cp shared/footer.html backups/

# Replace with new versions
mv login_new.html login.html
mv index_new.html index.html
mv signup_new.html signup.html
mv consent_new.html consent.html
mv shared/navigation_new.html shared/navigation.html
mv shared/footer_new.html shared/footer.html

# Failure-injector
cd /workspaces/bank-of-anthos/src/failure-injector/templates
mkdir -p backups
cp dashboard.html backups/
mv dashboard_new.html dashboard.html
```

## Design System

### Color Palette

```
Primary (Blue):
  - Base: #2563eb (blue-600)
  - Hover: #1d4ed8 (blue-700)
  - Active: #1e40af (blue-800)

Success (Green):
  - Base: #16a34a (green-600)
  - Light: #dcfce7 (green-50)
  - Dark: #15803d (green-700)

Danger (Red):
  - Base: #dc2626 (red-600)
  - Light: #fee2e2 (red-50)
  - Dark: #b91c1c (red-700)

Neutral (Slate):
  - 50, 100, 200, 300, 400, 500, 600, 700, 800, 900
```

### Typography

```
Headings: Space Grotesk
  - 3xl: 30px / 36px (balance display)
  - 2xl: 24px / 32px (page titles)
  - xl: 20px / 28px (card headers)
  - lg: 18px / 28px (section headers)

Body: Inter
  - sm: 14px / 20px (labels, hints)
  - base: 16px / 24px (body text)
```

### Spacing Rhythm (8px base)

```
xs: 4px
sm: 8px
md: 12px
lg: 16px
xl: 24px
2xl: 32px
```

### Components

#### Buttons
```html
<!-- Primary -->
<button class="px-4 py-2.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-all">
  Action
</button>

<!-- Secondary -->
<button class="px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 font-medium hover:bg-slate-50 transition-all">
  Secondary
</button>

<!-- Danger -->
<button class="px-4 py-2.5 rounded-lg bg-red-600 text-white font-medium hover:bg-red-700 transition-all">
  Delete
</button>
```

#### Input Fields
```html
<input 
  type="text"
  class="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all"
  placeholder="Enter text"
>
```

#### Cards
```html
<div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
  <div class="px-6 py-4 border-b border-slate-200">
    <h3 class="font-display font-bold text-slate-900">Title</h3>
  </div>
  <div class="px-6 py-4">
    <!-- Content -->
  </div>
</div>
```

#### Modals
```html
<div id="modal" class="hidden fixed inset-0 z-50 overflow-y-auto">
  <!-- Background overlay -->
  <div class="fixed inset-0 bg-black/30 backdrop-blur-sm" onclick="closeModal()"></div>
  
  <!-- Modal content -->
  <div class="flex items-center justify-center min-h-screen p-4 pointer-events-none">
    <div class="bg-white rounded-2xl shadow-xl max-w-md w-full p-8 pointer-events-auto">
      <!-- Content -->
    </div>
  </div>
</div>
```

#### Alerts
```html
<!-- Success -->
<div class="p-4 rounded-lg bg-green-50 border border-green-200 flex items-start gap-3">
  <span class="material-icons text-green-600">check_circle</span>
  <div>
    <h3 class="font-medium text-green-900">Success</h3>
    <p class="text-sm text-green-700">Message</p>
  </div>
</div>

<!-- Error -->
<div class="p-4 rounded-lg bg-red-50 border border-red-200">
  <p class="text-sm text-red-700 font-medium">Error message</p>
</div>

<!-- Info -->
<div class="p-4 rounded-lg bg-blue-50 border border-blue-200">
  <p class="text-sm text-blue-700">Information message</p>
</div>
```

## Important Jinja2 Variables

### Login Page
- `bank_name`: Display name of bank
- `message`: Optional status message
- `default_user`: Pre-filled username
- `default_password`: Pre-filled password

### Dashboard (index.html)
- `bank_name`: Display name of bank
- `account_number`: Account ID to display
- `current_balance`: Current account balance
- `account_holder`: User's full name (for avatar initial)
- `results`: List of transaction objects with:
  - `readable_name`: Transaction description
  - `timestamp`: Formatted date/time
  - `amount`: Transaction amount
  - `type`: 'DEPOSIT', 'SEND', or other

### Signup Page
- `bank_name`: Display name of bank
- `message`: Optional status message
- `response_type`, `state`, `redirect_uri`, `app_name`: OAuth parameters

### Consent Page
- `app_name`: Third-party app name requesting access
- `state`: OAuth state parameter
- `redirect_uri`: OAuth redirect URL

### Failure-Injector Dashboard
- No Jinja2 variables (pure static HTML + JavaScript)
- Uses fetch API to call `/api/*` endpoints

## Flask Backend Integration

### Key Points

1. **All templates work with existing Flask routes** - No backend changes required
2. **Pass variables exactly as before** - e.g., `render_template('login.html', bank_name=...)`
3. **Form submissions work unchanged** - Button clicks and form posts work as-is
4. **Material Icons is CDN-loaded** - No icon library installation needed

### Example Flask Route

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... existing login logic ...
    return render_template('login.html', 
                         bank_name='The Bank of Catz',
                         default_user='alice',
                         default_password='password123')

@app.route('/dashboard')
def dashboard():
    # ... fetch user data ...
    return render_template('index.html',
                         bank_name='The Bank of Catz',
                         account_number='1234567890',
                         current_balance='1234.56',
                         account_holder='Alice Johnson',
                         results=transactions)
```

## Responsive Breakpoints

All templates are fully responsive:
- **Mobile**: 320px+ (default)
- **Tablet**: 768px+ (`md:` prefix)
- **Desktop**: 1024px+ (`lg:` prefix)

Example responsive grid:
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- Cards stack on mobile, 2 columns on tablet, 3 on desktop -->
</div>
```

## Browser Support

All templates support:
- Chrome/Edge 88+
- Firefox 87+
- Safari 15+
- Mobile browsers (iOS Safari, Chrome Mobile)

Requires JavaScript enabled for:
- Modal interactions
- Form validation
- Fetch API calls (failure-injector)

## Troubleshooting

### Styles aren't loading
- Ensure Tailwind CDN script loads: `<script src="https://cdn.tailwindcss.com"></script>`
- Check browser console for 404 errors
- Verify internet connection (CDN required)

### Material Icons not showing
- Ensure icon link loads: `<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">`
- Use correct icon names: `<span class="material-icons">icon_name</span>`

### Modal not closing
- Verify JavaScript is enabled
- Check browser console for errors
- Ensure modal ID matches function references

### Forms not submitting
- Check that `<form>` tags have correct `action` and `method` attributes
- Verify input `name` attributes match Flask form parameter names
- Check browser console for validation errors

## Build & Deploy

### No build step required!

All templates work with static Flask rendering:

```bash
# Just run Flask as normal
cd src/frontend
python app.py

# Access at http://localhost:8080
```

### Docker

Add to Dockerfile if needed:

```dockerfile
# No additional dependencies needed
# Tailwind, fonts, icons all load from CDN
```

### Kubernetes

Templates work unchanged in cluster:

```bash
kubectl apply -f kubernetes-manifests/frontend.yaml
# UI automatically loads Tailwind from CDN
```

## Customization

### Change Primary Color

Edit the Tailwind config in `<script>` tag and change `blue-600` to desired color:

```javascript
tailwind.config = {
  theme: {
    extend: {
      // Custom colors here
    }
  }
}
```

### Change Fonts

Update the Google Fonts link:

```html
<link href="https://fonts.googleapis.com/css2?family=Your+Font:wght@400;600&display=swap" rel="stylesheet">
```

Then update fontFamily in Tailwind config.

### Add New Components

All components use standard Tailwind classes. Add CSS classes as needed:

```html
<!-- Custom component -->
<div class="custom-class">
  <!-- With Tailwind utilities -->
  <p class="text-lg font-semibold text-slate-900">Custom</p>
</div>

<!-- Add CSS in head or external stylesheet -->
<style>
  .custom-class { /* Custom styles */ }
</style>
```

## Summary

✅ **Completed:**
- 6 frontend templates (login, dashboard, signup, consent, nav, footer)
- 1 failure-injector dashboard
- Complete Tailwind-based design system
- Responsive mobile-first layout
- shadcn/ui-inspired aesthetic
- Zero build tools required

**Next Steps:**
1. Choose activation option (test or migrate)
2. Build and deploy with new templates
3. Test responsive behavior on all devices
4. Customize colors/fonts as needed
5. Monitor browser compatibility
