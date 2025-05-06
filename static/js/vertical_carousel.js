/**
 * Professional Instagram-Style Carousel
 * Implements a professional and responsive 4:5 aspect ratio carousel
 * with smooth transitions, elegant hover effects, and automatic sliding
 */
document.addEventListener('DOMContentLoaded', function() {
  // Wait for page to fully load before initializing carousel
  if (document.readyState === 'complete') {
    initializeCarousel();
  } else {
    window.addEventListener('load', initializeCarousel);
  }
});

/**
 * Initializes the Instagram-style carousel with optimized settings
 * and ultra-smooth, lag-free transitions
 */
function initializeCarousel() {
  console.log('Initializing professional Instagram carousel...');
  
  // Performance optimization: Start preloading key images immediately
  preloadCriticalImages();
  
  // Check for carousel elements on the page
  const arabicCarousel = document.querySelector('.vertical-carousel');
  const englishCarousel = document.querySelector('.vertical-carousel-en');
  
  // Detect page language
  const isEnglishPage = window.location.pathname.includes('/en');
  console.log(`Page language: ${isEnglishPage ? 'English' : 'Arabic'}`);
  
  // Use a small timeout to ensure DOM is fully ready
  // This prevents layout shifts during initialization
  setTimeout(() => {
    // Initialize appropriate carousel based on page language
    if (arabicCarousel) {
      console.log('Initializing Arabic carousel');
      initializeSwiper('.vertical-carousel', {
        rtl: true, // Right-to-left for Arabic
        speed: 800, // Slightly slower for smoother transitions (important for lag reduction)
        observer: true, // Watch for DOM changes
        observeParents: true // Watch parent elements for changes
      });
    }
    
    if (englishCarousel) {
      console.log('Initializing English carousel');
      initializeSwiper('.vertical-carousel-en', {
        rtl: false, // Left-to-right for English
        speed: 800, // Slightly slower for smoother transitions (important for lag reduction)
        observer: true, // Watch for DOM changes
        observeParents: true // Watch parent elements for changes
      });
    }
    
    // Apply optimized image loading attributes
    optimizeImageLoading();
    
    // Verify images loaded correctly after a delay
    setTimeout(verifyCarouselImages, 800);
  }, 10);
  
  // Set up responsive behavior with debounce for better performance
  let resizeTimer;
  window.addEventListener('resize', function() {
    // Debounce resize events to prevent excessive calculations
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      console.log('Window resized - checking carousel responsiveness');
      updateCarouselResponsiveness();
    }, 150); // Wait for resize to finish
  });
  
  // Watch for visibility changes (tab switching, etc.)
  // This helps with smoother resumption when returning to tab
  if (document.visibilityState !== undefined) {
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        // Update all carousels when tab becomes visible again
        updateAllCarousels();
      }
    });
  }
}

/**
 * Immediately preload the first few carousel images
 * This improves initial page load perception
 */
function preloadCriticalImages() {
  try {
    // Find all carousel containers
    const carouselContainers = document.querySelectorAll('.vertical-carousel, .vertical-carousel-en');
    
    if (carouselContainers.length === 0) return;
    
    // For each carousel, preload its first 2 images
    carouselContainers.forEach(carousel => {
      const slideImages = carousel.querySelectorAll('.swiper-slide img');
      
      // Only preload first 2 images (active + next)
      const imagesToPreload = Array.from(slideImages).slice(0, 2);
      
      imagesToPreload.forEach(img => {
        if (img && img.src) {
          // Force immediate loading of critical images
          img.loading = 'eager';
          
          // Simply set the src to force browser preload without creating extra elements
          if (!img.complete) {
            // Create a fallback preload mechanism using the Image constructor instead of link
            try {
              const preloadImg = new Image();
              preloadImg.src = img.src;
            } catch (e) {
              console.log("خطأ في التحميل المسبق:", e);
            }
          }
        }
      });
    });
  } catch (error) {
    console.warn('Preload optimization error:', error);
  }
}

/**
 * Optimize image loading for better performance
 */
function optimizeImageLoading() {
  try {
    // Find all carousel containers
    const carouselContainers = document.querySelectorAll('.vertical-carousel, .vertical-carousel-en');
    
    carouselContainers.forEach(carousel => {
      const slideImages = carousel.querySelectorAll('.swiper-slide img');
      
      // Skip the first 2 images (these are preloaded eagerly)
      const nonCriticalImages = Array.from(slideImages).slice(2);
      
      nonCriticalImages.forEach(img => {
        // Apply lazy loading to non-critical images
        img.loading = 'lazy';
        
        // Improve render performance
        img.decoding = 'async';
      });
    });
  } catch (error) {
    console.warn('Image optimization error:', error);
  }
}

/**
 * Update all carousels on the page
 * Used when tab visibility changes for smoother experience
 */
function updateAllCarousels() {
  const carousels = document.querySelectorAll('.vertical-carousel, .vertical-carousel-en');
  
  carousels.forEach(carousel => {
    const swiperInstance = carousel.swiper;
    if (swiperInstance) {
      // Update the layout
      swiperInstance.update();
      
      // Resume autoplay if configured
      if (swiperInstance.params.autoplay && swiperInstance.params.autoplay.enabled) {
        swiperInstance.autoplay.start();
      }
    }
  });
}

/**
 * Initialize a Swiper carousel with professional settings
 * 
 * @param {string} selector - CSS selector for the carousel container
 * @param {Object} options - Additional configuration options
 * @returns {Swiper|null} - Initialized Swiper instance or null if failed
 */
function initializeSwiper(selector, options = {}) {
  const container = document.querySelector(selector);
  if (!container) {
    console.warn(`Carousel container not found: ${selector}`);
    return null;
  }
  
  // Professional settings for Instagram-style 4:5 aspect ratio carousel
  const carouselSettings = {
    slidesPerView: 1,
    spaceBetween: 30,
    centeredSlides: true,
    loop: true,
    grabCursor: true,
    updateOnWindowResize: true, // Ensures carousel stays responsive
    simulateTouch: true, // Better touch simulation
    threshold: 5, // Sensitivity, lower is more sensitive
    resistance: true, // Physical resistance feeling
    resistanceRatio: 0.85, // Higher makes it feel more elastic
    autoplay: {
      delay: 4500, // وقت أطول للتمتع بمشاهدة كل صورة (من 3.2 ثانية إلى 4.5 ثانية)
      disableOnInteraction: false, // Continue autoplay after user interaction
      pauseOnMouseEnter: true, // Pause on hover for better UX
      waitForTransition: true, // Wait for transition to complete
      stopOnLastSlide: false // Continue looping
    },
    effect: 'fade', // Smooth fade transition between slides
    fadeEffect: {
      crossFade: true // Enable professional cross-fade effect
    },
    speed: 900, // أبطأ وأكثر سلاسة وأناقة
    watchSlidesProgress: true, // For smoother animations
    preventInteractionOnTransition: true, // Prevent user interaction during transitions
    preloadImages: false, // Disable automatic preloading to avoid errors
    updateOnImagesReady: true, // Update layout after images are loaded
    observer: true, // Watch for DOM changes
    observeParents: true, // Watch parent elements for changes
    lazy: {
      enabled: true,
      loadPrevNext: true, // Load adjacent slides for smoother experience
      loadPrevNextAmount: 2,
      checkInView: true,
      loadOnTransitionStart: true // Start loading before transition
    },
    navigation: {
      nextEl: `${selector} .swiper-button-next`,
      prevEl: `${selector} .swiper-button-prev`
    },
    pagination: {
      el: `${selector} .swiper-pagination`,
      clickable: true,
      dynamicBullets: false, // Using custom styled bullets
      renderBullet: function (index, className) {
        return '<span class="' + className + '"><span class="dot-inner"></span></span>';
      }
    },
    keyboard: {
      enabled: true, // Allow keyboard navigation
      onlyInViewport: true
    },
    touchReleaseOnEdges: true, // Reduce edge friction
    uniqueNavElements: true, // Performance improvement
    // Optimized responsive breakpoints
    breakpoints: {
      320: { // Mobile devices
        spaceBetween: 15
      },
      768: { // Tablets
        spaceBetween: 20
      },
      1024: { // Desktop
        spaceBetween: 30
      }
    },
    // Event callbacks
    on: {
      init: function() {
        console.log(`Carousel ${selector} initialized successfully`);
        // Hide controls initially
        const container = this.$el[0].closest('.vertical-carousel-container');
        if (container) {
          const controls = container.querySelectorAll('.swiper-button-next, .swiper-button-prev');
          controls.forEach(control => {
            control.style.opacity = '0';
          });
        }
      },
      slideChange: function() {
        enhanceActiveSlide(this);
      },
      touchStart: function() {
        // Manual interaction detected
        if (this.autoplay.running) {
          this.autoplay.stop();
        }
      },
      touchEnd: function() {
        // Resume autoplay after user interaction
        if (!this.autoplay.running) {
          setTimeout(() => {
            this.autoplay.start();
          }, 2500); // تأخير أطول قبل استئناف التشغيل التلقائي
        }
      }
    }
  };
  
  // Merge default settings with custom options
  const swiperSettings = { ...carouselSettings, ...options };
  
  try {
    // Initialize Swiper with merged settings
    const swiper = new Swiper(selector, swiperSettings);
    
    // Add hover effects
    setupHoverEffects(container, swiper);
    
    // Apply initial slide enhancements
    enhanceActiveSlide(swiper);
    
    return swiper;
  } catch (error) {
    console.error(`Error initializing carousel: ${error.message}`);
    return null;
  }
}

/**
 * Sets up hover effects for the carousel
 * 
 * @param {HTMLElement} container - The carousel container
 * @param {Swiper} swiper - Swiper instance
 */
function setupHoverEffects(container, swiper) {
  // Get navigation controls
  const nextButton = container.querySelector('.swiper-button-next');
  const prevButton = container.querySelector('.swiper-button-prev');
  
  // Pause autoplay and show controls on hover
  container.addEventListener('mouseenter', () => {
    // Pause autoplay
    if (swiper.autoplay && swiper.autoplay.running) {
      swiper.autoplay.stop();
      console.log('Carousel autoplay paused on hover');
    }
    
    // Show navigation controls with fade-in effect
    if (nextButton) nextButton.style.opacity = '0.8';
    if (prevButton) prevButton.style.opacity = '0.8';
    
    // Add animation class for smooth entrance
    setTimeout(() => {
      if (nextButton) {
        nextButton.style.transform = 'translateY(-50%) scale(1)';
        nextButton.style.transition = 'all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1)';
      }
      if (prevButton) {
        prevButton.style.transform = 'translateY(-50%) scale(1)';
        prevButton.style.transition = 'all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1)';
      }
    }, 50);
  });
  
  // Resume autoplay and hide controls on leave
  container.addEventListener('mouseleave', () => {
    // Resume autoplay
    if (swiper.autoplay && !swiper.autoplay.running) {
      swiper.autoplay.start();
      console.log('Carousel autoplay resumed');
    }
    
    // Hide navigation controls with fade-out effect
    if (nextButton) {
      nextButton.style.opacity = '0';
      nextButton.style.transform = 'translateY(-50%) scale(0.9)';
    }
    if (prevButton) {
      prevButton.style.opacity = '0';  
      prevButton.style.transform = 'translateY(-50%) scale(0.9)';
    }
  });
  
  // Add Instagram-style hover effects to slides
  const slides = container.querySelectorAll('.vertical-slide');
  slides.forEach(slide => {
    // Enhanced hover transition - slower for more elegant effects
    slide.addEventListener('mouseenter', () => {
      slide.style.transition = 'all 0.5s cubic-bezier(0.25, 0.1, 0.25, 1)';
      
      // Find caption elements and enhance them
      const caption = slide.querySelector('.slide-caption');
      if (caption) {
        caption.style.opacity = '1';
        caption.style.transform = 'translateY(0)';
        caption.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
      }
    });
    
    // Smooth exit transition
    slide.addEventListener('mouseleave', () => {
      slide.style.transition = 'all 0.6s cubic-bezier(0.25, 0.1, 0.25, 1)';
      
      // Smooth caption exit animation
      const caption = slide.querySelector('.slide-caption');
      if (caption) {
        caption.style.opacity = '0';
        caption.style.transform = 'translateY(8px)';
        caption.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
      }
    });
  });
}

/**
 * Enhances the active slide with professional effects using requestAnimationFrame
 * for smoother transitions and better performance
 * 
 * @param {Swiper} swiper - Swiper instance
 */
function enhanceActiveSlide(swiper) {
  if (!swiper || !swiper.slides) return;
  
  // Use requestAnimationFrame for smoother animations
  window.requestAnimationFrame(() => {
    const slides = swiper.slides;
    const totalSlides = slides.length;
    
    // Process all slides with optimized properties
    for (let i = 0; i < totalSlides; i++) {
      const slide = slides[i];
      const isActive = slide.classList.contains('swiper-slide-active');
      const slideElement = slide.querySelector('.vertical-slide');
      
      if (!slideElement) continue;
      
      // Apply hardware-accelerated transforms
      if (isActive) {
        // Optimize active slide with transform and opacity
        // Note: Using transform and opacity only for best GPU acceleration - now with slower transition
        slideElement.style.transition = 'transform 0.8s cubic-bezier(0.25, 0.1, 0.25, 1), opacity 0.8s cubic-bezier(0.25, 0.1, 0.25, 1)';
        slideElement.style.opacity = '1';
        slideElement.style.transform = 'translateZ(0) scale(1)';
        slideElement.style.zIndex = '1';
        
        // Preload high-quality version if needed
        const slideImage = slideElement.querySelector('img');
        if (slideImage && !slideImage.dataset.highresLoaded) {
          const dataSrc = slideImage.dataset.highresSrc;
          if (dataSrc) {
            // Preload higher quality version in background
            const img = new Image();
            img.src = dataSrc;
            img.onload = () => {
              slideImage.src = dataSrc;
              slideImage.dataset.highresLoaded = 'true';
            };
          }
        }
      } else {
        // De-emphasize inactive slides
        const distance = Math.abs(swiper.activeIndex - i);
        // Gradually decrease opacity and scale based on distance from active slide
        const opacityValue = Math.max(0.5, 1 - (distance * 0.15));
        const scaleValue = Math.max(0.8, 1 - (distance * 0.05));
        
        slideElement.style.transition = 'transform 0.8s cubic-bezier(0.25, 0.1, 0.25, 1), opacity 0.8s cubic-bezier(0.25, 0.1, 0.25, 1)';
        slideElement.style.opacity = opacityValue.toString();
        slideElement.style.transform = `translateZ(0) scale(${scaleValue})`;
        slideElement.style.zIndex = '0';
      }
    }
  });
}

/**
 * Verifies carousel images are loaded correctly
 */
function verifyCarouselImages() {
  // Find all carousel images
  const carouselImages = document.querySelectorAll('.vertical-carousel img, .vertical-carousel-en img');
  console.log(`Verifying ${carouselImages.length} carousel images`);
  
  if (carouselImages.length === 0) {
    console.warn('No carousel images found - check database or HTML structure');
    return;
  }
  
  let loadedCount = 0;
  carouselImages.forEach((img, index) => {
    // Check if image is loaded correctly
    if (img.complete && img.naturalWidth > 0) {
      loadedCount++;
    } else {
      console.warn(`Image #${index + 1} not fully loaded:`, img.src);
      
      // Add load/error listeners for delayed images
      img.addEventListener('load', () => {
        console.log(`Image loaded successfully:`, img.src);
      });
      
      img.addEventListener('error', () => {
        console.error(`Failed to load image:`, img.src);
        // Attempt to fix the image path if it failed to load
        attemptImagePathFix(img);
      });
    }
  });
  
  console.log(`${loadedCount} of ${carouselImages.length} carousel images verified`);
}

/**
 * Update carousel responsiveness for different screen sizes
 */
function updateCarouselResponsiveness() {
  const windowWidth = window.innerWidth;
  const carousels = document.querySelectorAll('.vertical-carousel, .vertical-carousel-en');
  
  carousels.forEach(carousel => {
    // Get the Swiper instance associated with this element
    const swiperInstance = carousel.swiper;
    if (swiperInstance) {
      // Update the Swiper instance to reflect new dimensions
      swiperInstance.update();
    }
  });
}

/**
 * Attempts to fix a broken image path
 * 
 * @param {HTMLImageElement} img - The image element to fix
 */
function attemptImagePathFix(img) {
  const originalSrc = img.src;
  const fixedSrc = originalSrc.replace(/^https?:\/\/[^\/]+/, ''); // Remove domain if present
  
  if (fixedSrc !== originalSrc) {
    console.log(`Attempting to fix image path: ${originalSrc} -> ${fixedSrc}`);
    img.src = fixedSrc;
  }
}