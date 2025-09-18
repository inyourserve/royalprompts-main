import { FALLBACK_IMAGE, IMAGE_URLS } from '../config/images';

// API base URL for constructing full image URLs
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Convert relative image URL to full URL
export const getFullImageUrl = (imageUrl: string | undefined | null): string => {
  if (!imageUrl || imageUrl.trim() === '') {
    return FALLBACK_IMAGE;
  }

  // If it's already a full URL (starts with http), return as is
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl;
  }

  // If it's a relative path, prepend the API base URL
  if (imageUrl.startsWith('/')) {
    return `${API_BASE_URL}${imageUrl}`;
  }

  // If it's a relative path without leading slash, add it
  return `${API_BASE_URL}/${imageUrl}`;
};

// Check if image URL returns 404 and return fallback if needed
export const getImageUrl = async (url: string): Promise<string> => {
  if (!url || url.trim() === '') {
    return FALLBACK_IMAGE;
  }

  try {
    const response = await fetch(url, { method: 'HEAD' });
    if (response.status === 404) {
      console.warn(`Image 404 error: ${url}, using fallback`);
      return FALLBACK_IMAGE;
    }
    return url;
  } catch (error) {
    console.warn(`Image fetch error: ${url}, using fallback`, error);
    return FALLBACK_IMAGE;
  }
};

// Preload image to check if it loads successfully
export const preloadImage = (url: string): Promise<boolean> => {
  return new Promise((resolve) => {
    if (!url || url.trim() === '') {
      resolve(false);
      return;
    }

    const img = new Image();
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = url;
  });
};

// Get working image URL with fallback
export const getWorkingImageUrl = async (url: string): Promise<string> => {
  const isWorking = await preloadImage(url);
  return isWorking ? url : FALLBACK_IMAGE;
};

// Get a random image from a specific category
export const getRandomImageFromCategory = (category: keyof typeof IMAGE_URLS): string => {
  return IMAGE_URLS[category] || FALLBACK_IMAGE;
};

// Get a random image from all available images
export const getRandomImage = (): string => {
  const imageKeys = Object.keys(IMAGE_URLS) as Array<keyof typeof IMAGE_URLS>;
  const randomKey = imageKeys[Math.floor(Math.random() * imageKeys.length)];
  return IMAGE_URLS[randomKey] || FALLBACK_IMAGE;
};

// Get images by category
export const getImagesByCategory = (category: 'modern' | 'trending' | 'cinematic' | 'portrait' | 'birthday') => {
  const categoryMap = {
    modern: ['modernMinimalist', 'abstractArt', 'techInnovation', 'urbanArchitecture', 'natureHarmony', 'creativeWorkshop', 'digitalArt', 'fashionForward', 'innovationLab', 'futureVision'],
    trending: ['viralStyle', 'instagramAesthetic', 'tiktokTrend', 'modernLifestyle', 'streetFashion', 'digitalNomad', 'wellnessTrend', 'ecoFriendly', 'minimalistTrend', 'boldColors'],
    cinematic: ['cinematicPortrait', 'actionSequence', 'filmNoir', 'sciFiScene', 'romanticDrama', 'thrillerMoment', 'epicBattle', 'mysteryScene', 'comedyMoment', 'horrorScene'],
    portrait: ['professionalHeadshot', 'creativePortrait', 'fashionPortrait', 'casualPortrait', 'artisticPortrait', 'corporatePortrait', 'lifestylePortrait', 'studioPortrait', 'environmentalPortrait', 'characterPortrait'],
    birthday: ['birthdayCelebration', 'partyDecorations', 'birthdayCake', 'giftGiving', 'birthdayWishes', 'partyGames', 'birthdayOutfit', 'birthdayMemories', 'birthdayTheme', 'birthdayJoy']
  };

  const keys = categoryMap[category] || [];
  return keys.map(key => IMAGE_URLS[key as keyof typeof IMAGE_URLS]).filter(Boolean);
};

// Get appropriate fallback image based on type
export const getFallbackImage = (type: 'avatar' | 'prompt' | 'category' | 'logo' = 'prompt'): string => {
  switch (type) {
    case 'avatar':
      return IMAGE_URLS.professionalHeadshot;
    case 'prompt':
      return IMAGE_URLS.creativeWorkshop;
    case 'category':
      return IMAGE_URLS.abstractArt;
    case 'logo':
      return '/images/logo/logo.svg';
    default:
      return FALLBACK_IMAGE;
  }
};

// Get image dimensions for a specific type
export const getImageDimensions = (type: 'avatar' | 'prompt' | 'category' | 'logo') => {
  switch (type) {
    case 'avatar':
      return { width: 40, height: 40 };
    case 'prompt':
      return { width: 48, height: 48 };
    case 'category':
      return { width: 40, height: 40 };
    case 'logo':
      return { width: 154, height: 32 };
    default:
      return { width: 48, height: 48 };
  }
};

// Validate image URL format
export const isValidImageUrl = (url: string): boolean => {
  if (!url || url.trim() === '') return false;
  
  try {
    new URL(url);
    return true;
  } catch {
    // Check if it's a relative path
    return url.startsWith('/') || url.startsWith('./') || url.startsWith('../');
  }
};

// Get image URL by key with fallback
export const getImageByKey = (key: keyof typeof IMAGE_URLS): string => {
  return IMAGE_URLS[key] || FALLBACK_IMAGE;
};

// Get multiple random images
export const getMultipleRandomImages = (count: number): string[] => {
  const imageKeys = Object.keys(IMAGE_URLS) as Array<keyof typeof IMAGE_URLS>;
  const shuffled = [...imageKeys].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count).map(key => IMAGE_URLS[key]);
};
