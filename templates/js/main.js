/**
 * CAP Services - Main JavaScript File
 * Inspired by Foxin.in Design Aesthetic
 */

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

/**
 * Main initialization function
 */
function initializeApp() {
    hideLoader();
    initializeNavigation();
    initializeHeroSlider();
    initializeProductFilters();
    initializeCart();
    initializeWishlist();
    initializeSearch();
    initializeNewsletter();
    initializeBackToTop();
    initializeCountdown();
    initializeTestimonials();
    initializeScrollAnimations();
    loadSampleData();
}

/**
 * Hide loader after page load
 */
function hideLoader() {
    setTimeout(() => {
        document.querySelector('.loader-wrapper').classList.add('hidden');
    }, 1000);
}

/**
 * Navigation functionality
 */
function initializeNavigation() {
    // Mobile menu toggle
    const menuToggle = document.createElement('button');
    menuToggle.className = 'mobile-menu-toggle';
    menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
    
    const navbar = document.querySelector('.navbar .container');
    const categoryMenu = document.querySelector('.category-menu');
    
    if (window.innerWidth <= 768 && !document.querySelector('.mobile-menu-toggle')) {
        navbar.insertBefore(menuToggle, navbar.firstChild);
        
        menuToggle.addEventListener('click', () => {
            categoryMenu.classList.toggle('show');
            menuToggle.innerHTML = categoryMenu.classList.contains('show') 
                ? '<i class="fas fa-times"></i>' 
                : '<i class="fas fa-bars"></i>';
        });
    }
    
    // Dropdown hover for mobile
    const dropdowns = document.querySelectorAll('.has-dropdown');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                dropdown.querySelector('.dropdown').classList.toggle('show');
            }
        });
    });
    
    // Resize handler
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            categoryMenu.classList.remove('show');
            if (document.querySelector('.mobile-menu-toggle')) {
                document.querySelector('.mobile-menu-toggle').remove();
            }
        }
    });
}

/**
 * Hero Slider
 */
function initializeHeroSlider() {
    const slides = [
        {
            title: 'Professional Computer <span class="highlight">Sales & Service</span>',
            description: 'Get the best deals on computers, laptops, and accessories with expert service support',
            image: 'https://via.placeholder.com/600x400',
            btn1: 'Shop Now',
            btn2: 'Book Service'
        },
        {
            title: 'Expert <span class="highlight">Repair Services</span>',
            description: 'Fast and reliable computer repair services at your doorstep',
            image: 'https://via.placeholder.com/600x400',
            btn1: 'Book Now',
            btn2: 'Learn More'
        },
        {
            title: 'Summer <span class="highlight">Sale 2026</span>',
            description: 'Up to 40% off on selected laptops and accessories',
            image: 'https://via.placeholder.com/600x400',
            btn1: 'Shop Sale',
            btn2: 'View Offers'
        }
    ];
    
    const slider = document.querySelector('.hero-slider');
    const dotsContainer = document.querySelector('.slider-dots');
    let currentSlide = 0;
    let slideInterval;
    
    // Create slides
    slides.forEach((slide, index) => {
        const slideElement = document.createElement('div');
        slideElement.className = `slide ${index === 0 ? 'active' : ''}`;
        slideElement.innerHTML = `
            <div class="slide-content">
                <h1>${slide.title}</h1>
                <p>${slide.description}</p>
                <div class="slide-buttons">
                    <a href="#" class="btn btn-primary">${slide.btn1}</a>
                    <a href="#" class="btn btn-outline">${slide.btn2}</a>
                </div>
            </div>
            <div class="slide-image">
                <img src="${slide.image}" alt="Slide ${index + 1}">
            </div>
        `;
        slider.appendChild(slideElement);
        
        // Create dot
        const dot = document.createElement('span');
        dot.className = `dot ${index === 0 ? 'active' : ''}`;
        dot.addEventListener('click', () => goToSlide(index));
        dotsContainer.appendChild(dot);
    });
    
    // Slider controls
    document.querySelector('.slider-prev').addEventListener('click', () => {
        goToSlide(currentSlide - 1);
    });
    
    document.querySelector('.slider-next').addEventListener('click', () => {
        goToSlide(currentSlide + 1);
    });
    
    function goToSlide(index) {
        if (index < 0) index = slides.length - 1;
        if (index >= slides.length) index = 0;
        
        document.querySelectorAll('.slide').forEach(slide => slide.classList.remove('active'));
        document.querySelectorAll('.dot').forEach(dot => dot.classList.remove('active'));
        
        document.querySelectorAll('.slide')[index].classList.add('active');
        document.querySelectorAll('.dot')[index].classList.add('active');
        
        currentSlide = index;
    }
    
    // Auto slide
    function startAutoSlide() {
        slideInterval = setInterval(() => {
            goToSlide(currentSlide + 1);
        }, 5000);
    }
    
    function stopAutoSlide() {
        clearInterval(slideInterval);
    }
    
    slider.addEventListener('mouseenter', stopAutoSlide);
    slider.addEventListener('mouseleave', startAutoSlide);
    
    startAutoSlide();
}

/**
 * Product Filters
 */
function initializeProductFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const products = document.querySelectorAll('.product-card');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Filter products
            const filter = button.dataset.filter;
            products.forEach(product => {
                if (filter === 'all' || product.dataset.category === filter) {
                    product.style.display = 'block';
                    setTimeout(() => {
                        product.style.opacity = '1';
                        product.style.transform = 'scale(1)';
                    }, 50);
                } else {
                    product.style.opacity = '0';
                    product.style.transform = 'scale(0.8)';
                    setTimeout(() => {
                        product.style.display = 'none';
                    }, 300);
                }
            });
        });
    });
}

/**
 * Cart Functionality
 */
function initializeCart() {
    const cartIcon = document.getElementById('cartIcon');
    const cartSidebar = document.getElementById('cartSidebar');
    const closeCart = document.getElementById('closeCart');
    const overlay = document.getElementById('overlay');
    const cartItems = document.getElementById('cartItems');
    const cartTotal = document.getElementById('cartTotal');
    const cartBadge = document.querySelector('.cart-badge');
    
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    // Open cart
    cartIcon.addEventListener('click', () => {
        cartSidebar.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    });
    
    // Close cart
    function closeCartSidebar() {
        cartSidebar.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    closeCart.addEventListener('click', closeCartSidebar);
    overlay.addEventListener('click', closeCartSidebar);
    
    // Add to cart
    document.querySelectorAll('.btn-primary, .btn-outline').forEach(button => {
        if (button.textContent.includes('Add to Cart')) {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const productCard = button.closest('.product-card');
                if (productCard) {
                    addToCart(productCard);
                }
            });
        }
    });
    
    function addToCart(productCard) {
        const product = {
            id: Date.now() + Math.random(),
            title: productCard.querySelector('.product-title').textContent,
            price: productCard.querySelector('.current-price').textContent,
            image: productCard.querySelector('img').src,
            quantity: 1
        };
        
        cart.push(product);
        updateCart();
        showNotification('Product added to cart!', 'success');
    }
    
    function updateCart() {
        // Update cart items display
        if (cart.length === 0) {
            cartItems.innerHTML = '<div class="empty-cart">Your cart is empty</div>';
        } else {
            cartItems.innerHTML = cart.map(item => `
                <div class="cart-item" data-id="${item.id}">
                    <div class="cart-item-image">
                        <img src="${item.image}" alt="${item.title}">
                    </div>
                    <div class="cart-item-info">
                        <h4 class="cart-item-title">${item.title}</h4>
                        <div class="cart-item-price">${item.price}</div>
                        <div class="cart-item-quantity">
                            <button class="quantity-btn minus">-</button>
                            <span class="quantity-value">${item.quantity}</span>
                            <button class="quantity-btn plus">+</button>
                        </div>
                        <button class="remove-item">Remove</button>
                    </div>
                </div>
            `).join('');
        }
        
        // Update total
        const total = cart.reduce((sum, item) => {
            const price = parseFloat(item.price.replace('₹', '').replace(',', ''));
            return sum + (price * item.quantity);
        }, 0);
        cartTotal.textContent = `₹${total.toLocaleString()}`;
        
        // Update badge
        const itemCount = cart.reduce((sum, item) => sum + item.quantity, 0);
        cartBadge.textContent = itemCount;
        
        // Save to localStorage
        localStorage.setItem('cart', JSON.stringify(cart));
        
        // Add event listeners to cart items
        attachCartItemListeners();
    }
    
    function attachCartItemListeners() {
        document.querySelectorAll('.quantity-btn.minus').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cartItem = e.target.closest('.cart-item');
                const id = cartItem.dataset.id;
                const item = cart.find(i => i.id == id);
                if (item.quantity > 1) {
                    item.quantity--;
                } else {
                    cart = cart.filter(i => i.id != id);
                }
                updateCart();
            });
        });
        
        document.querySelectorAll('.quantity-btn.plus').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cartItem = e.target.closest('.cart-item');
                const id = cartItem.dataset.id;
                const item = cart.find(i => i.id == id);
                item.quantity++;
                updateCart();
            });
        });
        
        document.querySelectorAll('.remove-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cartItem = e.target.closest('.cart-item');
                const id = cartItem.dataset.id;
                cart = cart.filter(i => i.id != id);
                updateCart();
                showNotification('Item removed from cart', 'info');
            });
        });
    }
    
    // Initial cart update
    updateCart();
}

/**
 * Wishlist Functionality
 */
function initializeWishlist() {
    const wishlistButtons = document.querySelectorAll('.wishlist-btn');
    const wishlistBadge = document.querySelector('.wishlist-badge');
    let wishlistCount = 0;
    
    wishlistButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            btn.classList.toggle('active');
            
            if (btn.classList.contains('active')) {
                wishlistCount++;
                showNotification('Added to wishlist!', 'success');
            } else {
                wishlistCount--;
                showNotification('Removed from wishlist', 'info');
            }
            
            wishlistBadge.textContent = wishlistCount;
        });
    });
}

/**
 * Search Functionality
 */
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const suggestions = document.getElementById('searchSuggestions');
    
    // Sample search suggestions
    const products = [
        { name: 'Gaming Laptop', price: '₹65,999', image: 'https://via.placeholder.com/40' },
        { name: 'Wireless Mouse', price: '₹999', image: 'https://via.placeholder.com/40' },
        { name: 'Printer', price: '₹8,499', image: 'https://via.placeholder.com/40' },
        { name: 'RAM 16GB', price: '₹4,999', image: 'https://via.placeholder.com/40' },
        { name: 'SSD 512GB', price: '₹5,499', image: 'https://via.placeholder.com/40' }
    ];
    
    searchInput.addEventListener('input', (e) => {
        const value = e.target.value.toLowerCase();
        if (value.length < 2) {
            suggestions.classList.remove('active');
            return;
        }
        
        const filtered = products.filter(p => 
            p.name.toLowerCase().includes(value)
        );
        
        if (filtered.length > 0) {
            suggestions.innerHTML = filtered.map(p => `
                <div class="suggestion-item">
                    <img src="${p.image}" alt="${p.name}">
                    <div class="suggestion-info">
                        <h4>${p.name}</h4>
                        <p>${p.price}</p>
                    </div>
                </div>
            `).join('');
            suggestions.classList.add('active');
        } else {
            suggestions.innerHTML = '<div class="suggestion-item">No products found</div>';
            suggestions.classList.add('active');
        }
    });
    
    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !suggestions.contains(e.target)) {
            suggestions.classList.remove('active');
        }
    });
    
    // Search button click
    searchBtn.addEventListener('click', () => {
        if (searchInput.value.trim()) {
            showNotification(`Searching for "${searchInput.value}"...`, 'info');
        }
    });
    
    // Enter key
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && searchInput.value.trim()) {
            searchBtn.click();
        }
    });
}

/**
 * Newsletter Form
 */
function initializeNewsletter() {
    const form = document.getElementById('newsletterForm');
    const message = document.getElementById('newsletterMessage');
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = form.querySelector('input[type="email"]').value;
        
        if (validateEmail(email)) {
            message.textContent = 'Thank you for subscribing!';
            message.className = 'form-message success';
            form.reset();
        } else {
            message.textContent = 'Please enter a valid email address';
            message.className = 'form-message error';
        }
    });
}

/**
 * Email validation
 */
function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Back to Top Button
 */
function initializeBackToTop() {
    const backToTop = document.getElementById('backToTop');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTop.classList.add('show');
        } else {
            backToTop.classList.remove('show');
        }
    });
    
    backToTop.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/**
 * Countdown Timer
 */
function initializeCountdown() {
    const countdown = document.getElementById('countdown');
    if (!countdown) return;
    
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + 7); // 7 days from now
    
    function updateCountdown() {
        const now = new Date().getTime();
        const distance = targetDate - now;
        
        if (distance < 0) {
            document.querySelector('.days').textContent = '00';
            document.querySelector('.hours').textContent = '00';
            document.querySelector('.minutes').textContent = '00';
            document.querySelector('.seconds').textContent = '00';
            return;
        }
        
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        document.querySelector('.days').textContent = days.toString().padStart(2, '0');
        document.querySelector('.hours').textContent = hours.toString().padStart(2, '0');
        document.querySelector('.minutes').textContent = minutes.toString().padStart(2, '0');
        document.querySelector('.seconds').textContent = seconds.toString().padStart(2, '0');
    }
    
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

/**
 * Testimonials Slider
 */
function initializeTestimonials() {
    const testimonials = [
        {
            name: 'Rajesh Kumar',
            role: 'Business Owner',
            content: 'Excellent service! They repaired my laptop within 24 hours. Highly recommended!',
            image: 'https://via.placeholder.com/100',
            rating: 5
        },
        {
            name: 'Priya Sharma',
            role: 'Software Engineer',
            content: 'Great products and even better service. The staff is very knowledgeable and helpful.',
            image: 'https://via.placeholder.com/100',
            rating: 5
        },
        {
            name: 'Amit Patel',
            role: 'Student',
            content: 'Bought a gaming laptop from them. Best prices in town and genuine products.',
            image: 'https://via.placeholder.com/100',
            rating: 4
        }
    ];
    
    const wrapper = document.querySelector('.testimonials-wrapper');
    const prevBtn = document.querySelector('.testimonial-prev');
    const nextBtn = document.querySelector('.testimonial-next');
    let currentIndex = 0;
    
    // Create testimonials
    testimonials.forEach((testimonial, index) => {
        const card = document.createElement('div');
        card.className = 'testimonial-card';
        card.innerHTML = `
            <div class="testimonial-image">
                <img src="${testimonial.image}" alt="${testimonial.name}">
            </div>
            <div class="testimonial-content">
                <p>"${testimonial.content}"</p>
                <div class="stars">
                    ${'★'.repeat(testimonial.rating)}${'☆'.repeat(5 - testimonial.rating)}
                </div>
            </div>
            <div class="testimonial-author">
                <h4>${testimonial.name}</h4>
                <p>${testimonial.role}</p>
            </div>
        `;
        wrapper.appendChild(card);
    });
    
    function slideTestimonials(direction) {
        const cards = document.querySelectorAll('.testimonial-card');
        const cardWidth = cards[0].offsetWidth + 32; // Including gap
        
        if (direction === 'next') {
            currentIndex = (currentIndex + 1) % cards.length;
        } else {
            currentIndex = (currentIndex - 1 + cards.length) % cards.length;
        }
        
        wrapper.style.transform = `translateX(-${currentIndex * cardWidth}px)`;
    }
    
    prevBtn.addEventListener('click', () => slideTestimonials('prev'));
    nextBtn.addEventListener('click', () => slideTestimonials('next'));
    
    // Auto slide
    setInterval(() => slideTestimonials('next'), 5000);
}

/**
 * Scroll Animations
 */
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.feature-card, .category-card, .product-card, .service-card').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Load Sample Product Data
 */
function loadSampleData() {
    const productsGrid = document.getElementById('productsGrid');
    const categoriesGrid = document.getElementById('categoriesGrid');
    
    // Sample categories
    const categories = [
        { name: 'Computers', count: 45, image: 'https://via.placeholder.com/300' },
        { name: 'Laptops', count: 32, image: 'https://via.placeholder.com/300' },
        { name: 'Printers', count: 18, image: 'https://via.placeholder.com/300' },
        { name: 'Accessories', count: 67, image: 'https://via.placeholder.com/300' }
    ];
    
    // Sample products
    const products = [
        {
            category: 'Laptops',
            name: 'ASUS ROG Gaming Laptop',
            price: '₹65,999',
            originalPrice: '₹79,999',
            rating: 4.5,
            reviews: 128,
            image: 'https://via.placeholder.com/300',
            attributes: ['16GB RAM', '512GB SSD', 'RTX 3050'],
            badge: 'SALE'
        },
        {
            category: 'Accessories',
            name: 'Logitech Wireless Mouse',
            price: '₹999',
            originalPrice: '₹1,499',
            rating: 4.3,
            reviews: 89,
            image: 'https://via.placeholder.com/300',
            attributes: ['Wireless', '2.4GHz', 'USB'],
            badge: '-33%'
        },
        {
            category: 'Printers',
            name: 'HP LaserJet Printer',
            price: '₹8,499',
            originalPrice: '₹9,999',
            rating: 4.2,
            reviews: 56,
            image: 'https://via.placeholder.com/300',
            attributes: ['Laser', 'WiFi', 'Duplex'],
            badge: 'NEW'
        },
        {
            category: 'Computers',
            name: 'Dell Desktop Computer',
            price: '₹32,999',
            originalPrice: '₹36,999',
            rating: 4.4,
            reviews: 42,
            image: 'https://via.placeholder.com/300',
            attributes: ['i5', '8GB RAM', '1TB HDD'],
            badge: 'SALE'
        },
        {
            category: 'Accessories',
            name: 'Samsung 27" Monitor',
            price: '₹15,999',
            originalPrice: '₹18,999',
            rating: 4.6,
            reviews: 73,
            image: 'https://via.placeholder.com/300',
            attributes: ['27 inch', '4K', 'HDMI'],
            badge: '-15%'
        },
        {
            category: 'Laptops',
            name: 'Apple MacBook Air',
            price: '₹89,999',
            originalPrice: '₹99,999',
            rating: 4.8,
            reviews: 156,
            image: 'https://via.placeholder.com/300',
            attributes: ['M2', '8GB RAM', '256GB'],
            badge: 'TOP'
        },
        {
            category: 'Accessories',
            name: 'HP Wireless Keyboard',
            price: '₹1,299',
            originalPrice: '₹1,799',
            rating: 4.1,
            reviews: 34,
            image: 'https://via.placeholder.com/300',
            attributes: ['Wireless', 'Full-size', 'USB'],
            badge: '-28%'
        },
        {
            category: 'Printers',
            name: 'Canon Inkjet Printer',
            price: '₹5,499',
            originalPrice: '₹6,499',
            rating: 4.0,
            reviews: 28,
            image: 'https://via.placeholder.com/300',
            attributes: ['Inkjet', 'Color', 'WiFi'],
            badge: 'SALE'
        }
    ];
    
    // Load categories
    if (categoriesGrid) {
        categoriesGrid.innerHTML = categories.map(cat => `
            <div class="category-card">
                <img src="${cat.image}" alt="${cat.name}">
                <div class="category-overlay">
                    <h3>${cat.name}</h3>
                    <p>${cat.count} Products</p>
                </div>
            </div>
        `).join('');
    }
    
    // Load products
    if (productsGrid) {
        productsGrid.innerHTML = products.map(product => `
            <div class="product-card" data-category="${product.category.toLowerCase()}">
                <div class="product-badge">${product.badge}</div>
                <button class="wishlist-btn"><i class="far fa-heart"></i></button>
                <div class="product-image">
                    <img src="${product.image}" alt="${product.name}">
                    <div class="image-overlay">
                        <button class="quick-view">Quick View</button>
                    </div>
                </div>
                <div class="product-info">
                    <div class="product-category">${product.category}</div>
                    <h3 class="product-title">${product.name}</h3>
                    <div class="product-rating">
                        <div class="stars">
                            ${'★'.repeat(Math.floor(product.rating))}${product.rating % 1 ? '½' : ''}${'☆'.repeat(5 - Math.ceil(product.rating))}
                        </div>
                        <span class="rating-count">(${product.reviews})</span>
                    </div>
                    <div class="product-price">
                        <span class="current-price">${product.price}</span>
                        <span class="original-price">${product.originalPrice}</span>
                    </div>
                    <div class="product-attributes">
                        ${product.attributes.map(attr => `<span class="attribute">${attr}</span>`).join('')}
                    </div>
                    <div class="product-actions">
                        <button class="btn-primary">Add to Cart</button>
                        <button class="btn-outline">Buy Now</button>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Reinitialize wishlist and cart for new products
        initializeWishlist();
        initializeCart();
    }
}

/**
 * Show Notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Add styles dynamically
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            z-index: 1000;
            animation: slideIn 0.3s ease;
            border-left: 4px solid;
        }
        
        .notification.success {
            border-left-color: #4CAF50;
        }
        
        .notification.error {
            border-left-color: #F44336;
        }
        
        .notification.info {
            border-left-color: #2196F3;
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .notification.success i {
            color: #4CAF50;
        }
        
        .notification.error i {
            color: #F44336;
        }
        
        .notification.info i {
            color: #2196F3;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    
    document.head.appendChild(style);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Export functions for use in other files
window.capServices = {
    showNotification,
    addToCart: (product) => {
        // Function to add product programmatically
        console.log('Add to cart:', product);
    }
};