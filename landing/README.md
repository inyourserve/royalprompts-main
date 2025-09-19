# RoyalPrompt Landing Page

A modern, responsive landing page for the RoyalPrompt mobile app built with Astro and Tailwind CSS.

## Features

- 🚀 **Fast & Modern**: Built with Astro for optimal performance
- 📱 **Responsive Design**: Looks great on all devices
- 🎨 **Beautiful UI**: Modern design with gradient accents
- 📄 **Complete Pages**: All essential pages for app store submission
- ⚡ **SEO Optimized**: Proper meta tags and structured content

## Pages Included

- **Home**: Hero section with app features and download links
- **About**: Detailed information about the app and team
- **Screenshots**: App interface gallery and feature highlights
- **Contact**: Support form and contact information
- **Privacy Policy**: Comprehensive privacy policy (required for app stores)
- **Terms of Service**: Complete terms and conditions

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Navigate to the landing directory:
   ```bash
   cd landing
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and visit `http://localhost:4321`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory, ready for deployment.

## Deployment

The landing page is designed to be deployed as a static site. You can deploy it to:

- **Vercel**: Connect your GitHub repository
- **Netlify**: Drag and drop the `dist/` folder
- **GitHub Pages**: Use GitHub Actions
- **Any static hosting service**

## Customization

### Colors

The app uses a custom color palette defined in `tailwind.config.mjs`:
- Primary: Blue gradient (`#0ea5e9` to `#0369a1`)
- Royal: Purple gradient (`#d946ef` to `#a21caf`)

### Content

Update the content in each page file:
- `src/pages/index.astro` - Homepage content
- `src/pages/about.astro` - About page content
- `src/pages/contact.astro` - Contact information
- `src/pages/privacy.astro` - Privacy policy
- `src/pages/terms.astro` - Terms of service

### App Store Links

Replace the placeholder download links in:
- Homepage hero section
- Screenshots page
- Footer

## App Store Requirements

This landing page includes all the essential pages required for app store submission:

✅ **Privacy Policy** - Required by both Google Play and Apple App Store  
✅ **Terms of Service** - Required for app store compliance  
✅ **Contact Information** - Required for support and legal purposes  
✅ **App Screenshots** - Showcases app features and interface  
✅ **About Page** - Provides app information and team details  

## License

This project is part of the RoyalPrompt application suite.
