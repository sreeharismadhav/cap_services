/* ============================================================
   CAP Services – Ecommerce JS
   Features: Cart, Filters, Search, Sort, View Toggle, Toast
   ============================================================ */

// ── PRODUCT DATA ─────────────────────────────────────────────
const PRODUCTS = [
  // COMPUTERS
  { id:1, name:'HP 15s Intel Core i5 Laptop', cat:'computer', price:42999, mrp:47999, disc:11, emoji:'💻', badge:'sale', inStock:true },
  { id:2, name:'Dell Inspiron 14 AMD Ryzen 5', cat:'computer', price:38499, mrp:43000, disc:10, emoji:'💻', badge:'hot', inStock:true },
  { id:3, name:'Assembled Desktop PC (i3, 8GB)', cat:'computer', price:18999, mrp:21000, disc:10, emoji:'🖥', badge:'new', inStock:true },
  { id:4, name:'Lenovo IdeaPad Slim 3 Laptop', cat:'computer', price:34990, mrp:38000, disc:8, emoji:'💻', badge:null, inStock:true },
  { id:5, name:'Workstation PC (i5, 16GB, SSD)', cat:'computer', price:32999, mrp:36000, disc:8, emoji:'🖥', badge:'new', inStock:true },
  { id:6, name:'Used HP Laptop Refurbished i3', cat:'computer', price:14999, mrp:18000, disc:17, emoji:'💻', badge:'sale', inStock:true },

  // PRINTERS
  { id:7, name:'HP DeskJet 2331 All-in-One', cat:'printer', price:3499, mrp:3999, disc:13, emoji:'🖨', badge:'sale', inStock:true },
  { id:8, name:'Canon PIXMA G3010 Ink Tank', cat:'printer', price:12499, mrp:13999, disc:11, emoji:'🖨', badge:'hot', inStock:true },
  { id:9, name:'Epson L3250 Wi-Fi All-in-One', cat:'printer', price:11499, mrp:12999, disc:12, emoji:'🖨', badge:'new', inStock:true },
  { id:10, name:'HP LaserJet MFP M140w', cat:'printer', price:15999, mrp:18000, disc:11, emoji:'🖨', badge:null, inStock:true },
  { id:11, name:'Canon LBP6030 Monochrome Laser', cat:'printer', price:9499, mrp:10999, disc:14, emoji:'🖨', badge:'sale', inStock:false },

  // CARTRIDGES
  { id:12, name:'HP 803 Black Ink Cartridge', cat:'cartridge', price:349, mrp:399, disc:13, emoji:'🖊', badge:'hot', inStock:true },
  { id:13, name:'HP 803 Tri-Color Cartridge', cat:'cartridge', price:399, mrp:449, disc:11, emoji:'🖊', badge:null, inStock:true },
  { id:14, name:'Canon PG-745 Black Ink', cat:'cartridge', price:329, mrp:379, disc:13, emoji:'🖊', badge:'sale', inStock:true },
  { id:15, name:'Epson T664 Black Ink Bottle', cat:'cartridge', price:399, mrp:449, disc:11, emoji:'🖊', badge:null, inStock:true },
  { id:16, name:'HP CF217A Laser Toner', cat:'cartridge', price:999, mrp:1199, disc:17, emoji:'📦', badge:'sale', inStock:true },
  { id:17, name:'Canon 047 Black Toner', cat:'cartridge', price:1099, mrp:1299, disc:15, emoji:'📦', badge:null, inStock:true },
  { id:18, name:'Epson T6641 Ink Bottle Set', cat:'cartridge', price:1399, mrp:1599, disc:13, emoji:'🖊', badge:'new', inStock:true },
  { id:19, name:'Samsung D111S Toner', cat:'cartridge', price:799, mrp:999, disc:20, emoji:'📦', badge:'sale', inStock:false },

  // CCTV
  { id:20, name:'CP Plus 2MP Full HD CCTV Kit 4Ch', cat:'cctv', price:4499, mrp:5499, disc:18, emoji:'📷', badge:'hot', inStock:true },
  { id:21, name:'Hikvision 2MP Dome Camera', cat:'cctv', price:1899, mrp:2299, disc:17, emoji:'📷', badge:'new', inStock:true },
  { id:22, name:'CP Plus 4MP IP Camera', cat:'cctv', price:2999, mrp:3499, disc:14, emoji:'📷', badge:null, inStock:true },
  { id:23, name:'Dahua 8Ch DVR 1080P', cat:'cctv', price:6499, mrp:7499, disc:13, emoji:'📹', badge:'sale', inStock:true },
  { id:24, name:'Complete CCTV Package 8 Cam', cat:'cctv', price:12999, mrp:15999, disc:19, emoji:'📹', badge:'hot', inStock:true },

  // SUPPLIES
  { id:25, name:'A4 Paper 75GSM (500 Sheets)', cat:'supplies', price:299, mrp:349, disc:14, emoji:'📄', badge:null, inStock:true },
  { id:26, name:'A4 Paper Premium 80GSM 1 Ream', cat:'supplies', price:349, mrp:399, disc:13, emoji:'📄', badge:'new', inStock:true },
  { id:27, name:'A4 Paper Box (5 Reams, 2500 Sheets)', cat:'supplies', price:1399, mrp:1699, disc:18, emoji:'📦', badge:'hot', inStock:true },
  { id:28, name:'Photo Paper A4 Glossy 20 Sheets', cat:'supplies', price:199, mrp:249, disc:20, emoji:'🗒', badge:'sale', inStock:true },
  { id:29, name:'USB Flash Drive 32GB', cat:'supplies', price:249, mrp:299, disc:17, emoji:'💾', badge:null, inStock:true },
  { id:30, name:'HDMI Cable 1.5m', cat:'supplies', price:149, mrp:199, disc:25, emoji:'🔌', badge:'sale', inStock:true },

  // NETWORKING
  { id:31, name:'TP-Link TL-WR845N Wi-Fi Router', cat:'networking', price:999, mrp:1199, disc:17, emoji:'📡', badge:'hot', inStock:true },
  { id:32, name:'D-Link 8-Port Ethernet Switch', cat:'networking', price:699, mrp:849, disc:18, emoji:'🔀', badge:null, inStock:true },
  { id:33, name:'Cat6 LAN Cable 10m', cat:'networking', price:199, mrp:249, disc:20, emoji:'🔌', badge:'sale', inStock:true },
  { id:34, name:'TP-Link Powerline Adapter Kit', cat:'networking', price:1799, mrp:2099, disc:14, emoji:'⚡', badge:'new', inStock:true },
];

// ── CART STATE ────────────────────────────────────────────────
let cart = JSON.parse(localStorage.getItem('cap-cart') || '[]');
let currentFilter = 'all';
let currentView   = 'grid';
let searchQuery   = '';

// ── INIT ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  renderProducts(PRODUCTS);
  updateCartUI();
  initHeader();
  initCart();
  initContactForm();
  initSearch();
});

// ── HEADER ────────────────────────────────────────────────────
function initHeader() {
  const header    = document.getElementById('header');
  const hamburger = document.getElementById('hamburger');
  const mainNav   = document.getElementById('mainNav');

  window.addEventListener('scroll', () => {
    header.style.boxShadow = window.scrollY > 10 ? '0 4px 20px rgba(0,0,0,.1)' : '';
  }, { passive: true });

  hamburger.addEventListener('click', () => {
    mainNav.classList.toggle('open');
    hamburger.classList.toggle('active');
  });

  mainNav.querySelectorAll('.nav-link').forEach(l => {
    l.addEventListener('click', () => {
      mainNav.classList.remove('open');
      hamburger.classList.remove('active');
    });
  });

  // Active nav on scroll
  const sections = document.querySelectorAll('section[id]');
  window.addEventListener('scroll', () => {
    const y = window.scrollY + 120;
    sections.forEach(s => {
      if (y >= s.offsetTop && y < s.offsetTop + s.offsetHeight) {
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        const a = document.querySelector(`.nav-link[href="#${s.id}"]`);
        if (a) a.classList.add('active');
      }
    });
  }, { passive: true });
}

// ── SEARCH ────────────────────────────────────────────────────
function initSearch() {
  const input = document.getElementById('searchInput');
  if (!input) return;
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') applyFilters();
  });
}
function liveSearch(val) {
  searchQuery = val.trim().toLowerCase();
  applyFilters();
}

// ── PRODUCT RENDERING ─────────────────────────────────────────
function renderProducts(products) {
  const grid    = document.getElementById('productGrid');
  const noRes   = document.getElementById('noResults');
  const counter = document.getElementById('productCount');

  if (!grid) return;

  if (products.length === 0) {
    grid.innerHTML = '';
    noRes.style.display = 'block';
    counter.textContent = 'No products found';
    return;
  }

  noRes.style.display = 'none';
  counter.textContent = `Showing ${products.length} product${products.length !== 1 ? 's' : ''}`;

  grid.innerHTML = products.map(p => {
    const inCartItem = cart.find(c => c.id === p.id);
    const added      = !!inCartItem;
    const badgeHtml  = p.badge ? `<span class="pc-badge badge-${p.badge}">${p.badge.toUpperCase()}</span>` : '';
    const stockBadge = !p.inStock ? `<span class="pc-badge badge-stock">Out of Stock</span>` : '';

    return `
    <div class="product-card" data-id="${p.id}" data-cat="${p.cat}" data-price="${p.price}" data-name="${p.name.toLowerCase()}">
      <div class="pc-image">
        <div class="pc-badges">${badgeHtml}${stockBadge}</div>
        ${p.emoji}
        <button class="pc-wish" onclick="wishlist(${p.id})" title="Wishlist">♡</button>
      </div>
      <div class="pc-body">
        <div class="pc-cat">${catLabel(p.cat)}</div>
        <div class="pc-name">${p.name}</div>
        <div class="pc-price-row">
          <span class="pc-price">₹${p.price.toLocaleString('en-IN')}</span>
          ${p.mrp ? `<span class="pc-mrp">₹${p.mrp.toLocaleString('en-IN')}</span>` : ''}
          ${p.disc ? `<span class="pc-disc">${p.disc}% off</span>` : ''}
        </div>
        <div class="pc-actions">
          <button class="pc-add-btn ${added ? 'added' : ''}" onclick="addToCart(${p.id})" ${!p.inStock ? 'disabled style="opacity:.5;cursor:not-allowed"' : ''}>
            ${!p.inStock ? 'Out of Stock' : added ? '✓ Added' : '+ Add to Cart'}
          </button>
          <a href="https://wa.me/919XXXXXXXXX?text=Hi, I want to order: ${encodeURIComponent(p.name)} (₹${p.price.toLocaleString('en-IN')})" target="_blank" class="pc-wa-btn" title="Order on WhatsApp">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
          </a>
        </div>
      </div>
    </div>`;
  }).join('');
}

function catLabel(cat) {
  const map = { computer:'Computers & Laptops', printer:'Printers', cartridge:'Ink & Toner', cctv:'CCTV & Security', supplies:'Office Supplies', networking:'Networking' };
  return map[cat] || cat;
}

// ── FILTERS ───────────────────────────────────────────────────
function filterProducts(cat) {
  currentFilter = cat;
  // sync radio
  const r = document.querySelector(`input[name="cat"][value="${cat}"]`);
  if (r) r.checked = true;
  applyFilters();
}

function filterAndScroll(cat) {
  filterProducts(cat);
  document.getElementById('shop')?.scrollIntoView({ behavior: 'smooth' });
}

function applyFilters() {
  let list = [...PRODUCTS];

  // Category
  if (currentFilter && currentFilter !== 'all')
    list = list.filter(p => p.cat === currentFilter);

  // Search
  if (searchQuery)
    list = list.filter(p => p.name.toLowerCase().includes(searchQuery) || p.cat.includes(searchQuery));

  // Price
  const mn = parseFloat(document.getElementById('priceMin')?.value) || 0;
  const mx = parseFloat(document.getElementById('priceMax')?.value) || Infinity;
  if (mn || mx < Infinity) list = list.filter(p => p.price >= mn && p.price <= mx);

  // Sort
  const sort = document.getElementById('sortSel')?.value || 'default';
  if (sort === 'price-asc')  list.sort((a, b) => a.price - b.price);
  if (sort === 'price-desc') list.sort((a, b) => b.price - a.price);
  if (sort === 'name')       list.sort((a, b) => a.name.localeCompare(b.name));

  renderProducts(list);
}

function resetFilters() {
  currentFilter = 'all';
  searchQuery   = '';
  const allRadio = document.querySelector('input[name="cat"][value="all"]');
  if (allRadio) allRadio.checked = true;
  const pMin = document.getElementById('priceMin');
  const pMax = document.getElementById('priceMax');
  const sSel = document.getElementById('sortSel');
  if (pMin) pMin.value = '';
  if (pMax) pMax.value = '';
  if (sSel) sSel.value = 'default';
  const sInput = document.getElementById('searchInput');
  if (sInput) sInput.value = '';
  renderProducts(PRODUCTS);
}

// ── VIEW TOGGLE ───────────────────────────────────────────────
function setView(view) {
  currentView = view;
  const grid = document.getElementById('productGrid');
  const gridBtn = document.getElementById('gridBtn');
  const listBtn = document.getElementById('listBtn');
  if (!grid) return;
  if (view === 'list') {
    grid.classList.add('list-view');
    listBtn?.classList.add('active');
    gridBtn?.classList.remove('active');
  } else {
    grid.classList.remove('list-view');
    gridBtn?.classList.add('active');
    listBtn?.classList.remove('active');
  }
}

// ── CART ──────────────────────────────────────────────────────
function initCart() {
  const trigger  = document.getElementById('cartTrigger');
  const overlay  = document.getElementById('cartOverlay');
  const drawer   = document.getElementById('cartDrawer');
  const closeBtn = document.getElementById('cartClose');

  trigger?.addEventListener('click', openCart);
  overlay?.addEventListener('click', closeCart);
  closeBtn?.addEventListener('click', closeCart);
}

function openCart() {
  document.getElementById('cartOverlay')?.classList.add('open');
  document.getElementById('cartDrawer')?.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeCart() {
  document.getElementById('cartOverlay')?.classList.remove('open');
  document.getElementById('cartDrawer')?.classList.remove('open');
  document.body.style.overflow = '';
}

function addToCart(id) {
  const product = PRODUCTS.find(p => p.id === id);
  if (!product || !product.inStock) return;

  const existing = cart.find(c => c.id === id);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ ...product, qty: 1 });
  }
  saveCart();
  updateCartUI();
  renderProducts(applyCurrentFiltersGet());
  showToast(`✓ ${product.name.split(' ').slice(0,4).join(' ')} added to cart`);
}

function applyCurrentFiltersGet() {
  let list = [...PRODUCTS];
  if (currentFilter !== 'all') list = list.filter(p => p.cat === currentFilter);
  if (searchQuery) list = list.filter(p => p.name.toLowerCase().includes(searchQuery));
  return list;
}

function removeFromCart(id) {
  cart = cart.filter(c => c.id !== id);
  saveCart();
  updateCartUI();
}

function changeQty(id, delta) {
  const item = cart.find(c => c.id === id);
  if (!item) return;
  item.qty += delta;
  if (item.qty <= 0) removeFromCart(id);
  else { saveCart(); updateCartUI(); }
}

function saveCart() {
  localStorage.setItem('cap-cart', JSON.stringify(cart));
}

function updateCartUI() {
  const total  = cart.reduce((sum, i) => sum + i.price * i.qty, 0);
  const count  = cart.reduce((sum, i) => sum + i.qty, 0);
  const countEl    = document.getElementById('cartCount');
  const countInl   = document.getElementById('cartCountInline');
  const totalEl    = document.getElementById('cartTotal');
  const emptyEl    = document.getElementById('cartEmpty');
  const itemsEl    = document.getElementById('cartItems');
  const footerEl   = document.getElementById('cartFooter');

  if (countEl)  { countEl.textContent = count; countEl.style.display = count > 0 ? 'flex' : 'none'; }
  if (countInl) countInl.textContent = `${count} item${count !== 1 ? 's' : ''}`;
  if (totalEl)  totalEl.textContent  = `₹${total.toLocaleString('en-IN')}`;

  if (emptyEl)  emptyEl.style.display  = cart.length ? 'none' : 'flex';
  if (footerEl) footerEl.style.display = cart.length ? 'flex' : 'none';
  if (footerEl) footerEl.style.flexDirection = 'column';

  if (itemsEl) {
    itemsEl.innerHTML = cart.map(item => `
      <div class="cart-item">
        <div class="ci-emoji">${item.emoji}</div>
        <div class="ci-info">
          <div class="ci-name">${item.name}</div>
          <div class="ci-price">₹${(item.price * item.qty).toLocaleString('en-IN')}</div>
          <div class="ci-qty-row">
            <button class="qty-btn" onclick="changeQty(${item.id},-1)">−</button>
            <span class="qty-val">${item.qty}</span>
            <button class="qty-btn" onclick="changeQty(${item.id},1)">+</button>
            <button class="ci-remove" onclick="removeFromCart(${item.id})">Remove</button>
          </div>
        </div>
      </div>`).join('');
  }
}

function checkout() {
  if (cart.length === 0) return;
  showToast('🎉 Redirecting to checkout…');
  setTimeout(() => {
    alert('Checkout integration coming soon!\n\nFor now, use WhatsApp to confirm your order — we\'ll process it personally.');
  }, 800);
}

function whatsappOrder() {
  if (cart.length === 0) return;
  const lines = cart.map(i => `• ${i.name} x${i.qty} — ₹${(i.price * i.qty).toLocaleString('en-IN')}`).join('\n');
  const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
  const msg   = `Hi CAP Services! I'd like to place an order:\n\n${lines}\n\nTotal: ₹${total.toLocaleString('en-IN')}\n\nPlease confirm availability and delivery.`;
  window.open(`https://wa.me/919XXXXXXXXX?text=${encodeURIComponent(msg)}`, '_blank');
}

function wishlist(id) {
  const p = PRODUCTS.find(x => x.id === id);
  showToast(`♡ ${p?.name.split(' ').slice(0,3).join(' ')} added to wishlist`);
}

// ── TOAST ─────────────────────────────────────────────────────
function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => toast.classList.remove('show'), 2800);
}

// ── CONTACT FORM ──────────────────────────────────────────────
function initContactForm() {
  const form = document.getElementById('contactForm');
  if (!form) return;
  form.addEventListener('submit', e => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    btn.textContent = '✓ Request Sent!';
    btn.style.background = '#16a34a';
    setTimeout(() => {
      btn.textContent = 'Submit Request →';
      btn.style.background = '';
      form.reset();
    }, 3000);
  });
}

// ── SMOOTH SCROLL ─────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', function(e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
  });
});