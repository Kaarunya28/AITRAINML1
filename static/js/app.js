/* SmartCart – No Auth Required. Everything works on open. */

const API = "";
let cart       = JSON.parse(localStorage.getItem("sc_cart") || "[]");
let customerId = parseInt(localStorage.getItem("sc_customer") || "1");
let customers  = [];

// ─── API helper ───────────────────────────────────────────────────────────────
async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const res  = await fetch(API + path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

// ─── UI helpers ───────────────────────────────────────────────────────────────
function showSection(id) {
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
  if (id === "products")        loadProducts();
  if (id === "recommendations") loadRecommendations();
  if (id === "dashboard")       loadDashboard();
  if (id === "cart")            renderCart();
  if (id === "admin")           loadAdmin("sales-summary");
}

function toast(msg, dur = 3500) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), dur);
}

function updateCartCount() {
  const count = cart.reduce((s, i) => s + i.quantity, 0);
  document.getElementById("cartCount").textContent = count;
}

function segClass(seg) {
  if (!seg) return "";
  const s = seg.toLowerCase();
  if (s.includes("premium"))    return "premium";
  if (s.includes("regular"))    return "regular";
  if (s.includes("occasional")) return "occasional";
  if (s.includes("risk"))       return "at-risk";
  return "";
}

// ─── Customer selector ────────────────────────────────────────────────────────
async function loadCustomers() {
  try {
    customers = await api("/customers?limit=150");
    const sel = document.getElementById("customerSelect");
    sel.innerHTML = customers.map(c =>
      `<option value="${c.customer_id}" ${c.customer_id === customerId ? "selected" : ""}>
        #${c.customer_id} – ${c.name} (${c.city || "?"})
      </option>`
    ).join("");
    updateCustomerBadge();
  } catch (e) { console.error("Could not load customers", e); }
}

function switchCustomer() {
  const sel = document.getElementById("customerSelect");
  customerId = parseInt(sel.value);
  localStorage.setItem("sc_customer", customerId);
  updateCustomerBadge();
  toast(`Switched to customer #${customerId}`);
}

function updateCustomerBadge() {
  const cust  = customers.find(c => c.customer_id === customerId);
  const badge = document.getElementById("currentCustomerBadge");
  if (cust) {
    badge.textContent = `${cust.name} · ${cust.segment || "New Customer"}`;
    badge.className   = `segment-badge ${segClass(cust.segment)}`;
    badge.style.display = "inline-block";
  }
}

// ─── PRODUCTS ─────────────────────────────────────────────────────────────────
async function loadProducts() {
  const search   = document.getElementById("searchInput")?.value.trim() || "";
  const category = document.getElementById("catFilter")?.value || "";
  let path = "/products?limit=60";
  if (search)   path += `&search=${encodeURIComponent(search)}`;
  if (category) path += `&category=${encodeURIComponent(category)}`;

  const grid = document.getElementById("productGrid");
  grid.innerHTML = `<div class="loading">⏳ Loading products…</div>`;
  try {
    const products = await api(path);
    renderProducts(products);
  } catch (e) { grid.innerHTML = `<p style="color:red">Error: ${e.message}</p>`; }
}

function clearSearch() {
  document.getElementById("searchInput").value = "";
  document.getElementById("catFilter").value   = "";
  loadProducts();
}

function renderProducts(products) {
  const grid = document.getElementById("productGrid");
  if (!products.length) { grid.innerHTML = "<p>No products found.</p>"; return; }
  grid.innerHTML = products.map(p => {
    const discountedPrice = p.discount > 0
      ? `<span style="text-decoration:line-through;color:var(--muted);font-size:.9rem">₹${p.price.toFixed(2)}</span>
         <span class="card-price"> ₹${(p.price * (1 - p.discount/100)).toFixed(2)}</span>`
      : `<span class="card-price">₹${p.price.toFixed(2)}</span>`;
    const stars = "★".repeat(Math.round(p.rating)) + "☆".repeat(5 - Math.round(p.rating));
    const stockClass = p.stock < 10 ? "stock-low" : "stock-ok";
    const stockText  = p.stock === 0 ? "Out of stock" : p.stock < 10 ? `⚠ Only ${p.stock} left` : `✓ In stock`;
    return `
      <div class="card">
        <div>
          <div class="card-cat">${p.category}</div>
          <div class="card-name">${p.product_name}</div>
          <div style="margin:.3rem 0">${discountedPrice}</div>
          ${p.discount > 0 ? `<div class="card-discount">${p.discount}% OFF</div>` : ""}
          <div class="card-rating">${stars} ${p.rating}</div>
          <div class="card-stock ${stockClass}">${stockText}</div>
        </div>
        <div class="card-actions">
          <button class="btn btn-primary btn-sm" onclick="addToCart(${p.product_id},'${p.product_name.replace(/'/g,"\\'")}',${p.price},${p.discount})"
            ${p.stock === 0 ? "disabled style='opacity:.5'" : ""}>
            🛒 Add to Cart
          </button>
          <button class="btn btn-outline btn-sm" onclick="predictForProduct(${p.product_id},'${p.product_name.replace(/'/g,"\\'")}')">
            🤖 Predict
          </button>
        </div>
      </div>`;
  }).join("");
}

// ─── CART ─────────────────────────────────────────────────────────────────────
function addToCart(id, name, price, discount = 0) {
  const finalPrice = discount > 0 ? price * (1 - discount / 100) : price;
  const existing   = cart.find(i => i.product_id === id);
  if (existing) { existing.quantity++; }
  else { cart.push({ product_id: id, product_name: name, price: finalPrice, quantity: 1 }); }
  localStorage.setItem("sc_cart", JSON.stringify(cart));
  updateCartCount();
  toast(`✅ ${name} added to cart`);
}

function changeQty(id, delta) {
  const item = cart.find(i => i.product_id === id);
  if (!item) return;
  item.quantity = Math.max(0, item.quantity + delta);
  if (item.quantity === 0) cart = cart.filter(i => i.product_id !== id);
  localStorage.setItem("sc_cart", JSON.stringify(cart));
  updateCartCount(); renderCart();
}

function removeFromCart(id) {
  cart = cart.filter(i => i.product_id !== id);
  localStorage.setItem("sc_cart", JSON.stringify(cart));
  updateCartCount(); renderCart();
}

function clearCart() {
  cart = []; localStorage.setItem("sc_cart", JSON.stringify(cart));
  updateCartCount(); renderCart();
}

function renderCart() {
  const el  = document.getElementById("cartItems");
  const btn = document.getElementById("checkoutBtn");
  const tot = document.getElementById("cartTotal");
  if (!cart.length) {
    el.innerHTML = `<div class="loading">🛒 Your cart is empty.<br><br>
      <button class="btn btn-primary" onclick="showSection('products')">Browse Products</button></div>`;
    btn.style.display = "none"; tot.textContent = ""; return;
  }
  el.innerHTML = cart.map(item => `
    <div class="cart-item">
      <div>
        <div class="cart-item-name">${item.product_name}</div>
        <div class="cart-item-price">₹${item.price.toFixed(2)} × ${item.quantity}
          = <strong>₹${(item.price * item.quantity).toFixed(2)}</strong></div>
      </div>
      <div style="display:flex;gap:.4rem;align-items:center">
        <button class="btn btn-sm btn-outline" onclick="changeQty(${item.product_id},-1)">−</button>
        <span style="font-weight:700;min-width:24px;text-align:center">${item.quantity}</span>
        <button class="btn btn-sm btn-outline" onclick="changeQty(${item.product_id}, 1)">+</button>
        <button class="btn btn-sm btn-danger"  onclick="removeFromCart(${item.product_id})">✕</button>
      </div>
    </div>`).join("");
  const total = cart.reduce((s, i) => s + i.price * i.quantity, 0);
  tot.textContent = `Total: ₹${total.toFixed(2)}`;
  btn.style.display = "inline-block";
}

async function checkout() {
  if (!cart.length) return toast("Cart is empty!");
  try {
    const items = cart.map(i => ({ product_id: i.product_id, quantity: i.quantity }));
    const order = await api("/orders", {
      method: "POST",
      body  : JSON.stringify({ customer_id: customerId, items, payment_method: "cash_on_delivery" }),
    });
    cart = []; localStorage.setItem("sc_cart", JSON.stringify(cart));
    updateCartCount(); renderCart();
    toast(`🎉 Order #${order.order_id} placed! Total: ₹${order.total_amount}`);
    setTimeout(() => showSection("dashboard"), 1500);
  } catch (e) { toast("❌ Order failed: " + e.message); }
}

// ─── ML: PURCHASE PREDICTION ──────────────────────────────────────────────────
async function predictForProduct(productId, productName) {
  toast("🤖 Running AI prediction…");
  try {
    const res = await api("/predict-purchase", {
      method: "POST",
      body  : JSON.stringify({ customer_id: customerId, product_id: productId }),
    });
    const pct   = (res.purchase_probability * 100).toFixed(0);
    const emoji = res.purchase_probability >= 0.5 ? "✅" : "❌";
    toast(`${emoji} ${productName}: ${res.prediction} (${pct}%)`, 5000);
  } catch (e) { toast("Prediction error: " + e.message); }
}

// ─── ML: RECOMMENDATIONS ──────────────────────────────────────────────────────
async function loadRecommendations() {
  const grid = document.getElementById("recGrid");
  const name = document.getElementById("recCustomerName");
  const cust = customers.find(c => c.customer_id === customerId);
  if (name && cust) name.textContent = `${cust.name} (#${customerId})`;

  grid.innerHTML = `<div class="loading">⏳ Fetching AI recommendations…</div>`;
  try {
    const data = await api(`/recommendations/${customerId}`);
    if (!data.recommendations.length) {
      grid.innerHTML = "<p>No recommendations available yet.</p>"; return;
    }
    grid.innerHTML = data.recommendations.map(r => `
      <div class="card">
        <div>
          <div class="card-cat">${r.category || ""}</div>
          <div class="card-name">${r.product_name}</div>
          <div class="card-price">₹${(r.price || 0).toFixed(2)}</div>
          <div class="card-rating">${"★".repeat(Math.round(r.rating||0))} ${r.rating || 0}</div>
          <div style="margin-top:.5rem">
            <span class="pred-chip pred-likely">🎯 Score: ${(r.score * 100).toFixed(0)}%</span>
          </div>
        </div>
        <button class="btn btn-primary btn-sm" style="margin-top:.9rem"
          onclick="addToCart(${r.product_id},'${r.product_name.replace(/'/g,"\\'")}',${r.price||0})">
          🛒 Add to Cart
        </button>
      </div>`).join("");
  } catch (e) { grid.innerHTML = `<p style="color:red">Error: ${e.message}</p>`; }
}

// ─── DASHBOARD ────────────────────────────────────────────────────────────────
async function loadDashboard() {
  const el   = document.getElementById("dashContent");
  const name = document.getElementById("dashCustomerName");
  const cust = customers.find(c => c.customer_id === customerId);
  if (name && cust) name.textContent = `${cust.name} (#${customerId})`;

  el.innerHTML = `<div class="loading">⏳ Loading dashboard…</div>`;
  try {
    const d = await api(`/customer-dashboard/${customerId}`);
    const segC = segClass(d.segment);
    el.innerHTML = `
      <!-- Stats -->
      <div class="dash-grid">
        <div class="stat-card"><div class="stat-val">${d.total_orders}</div><div class="stat-label">Total Orders</div></div>
        <div class="stat-card"><div class="stat-val">₹${Math.round(d.total_spending).toLocaleString()}</div><div class="stat-label">Total Spent</div></div>
        <div class="stat-card"><div class="stat-val">₹${Math.round(d.average_order_value).toLocaleString()}</div><div class="stat-label">Avg Order Value</div></div>
        <div class="stat-card"><div class="stat-val">${d.recommendations.length}</div><div class="stat-label">AI Picks for You</div></div>
      </div>

      <!-- Segment -->
      <div class="section-title">🏷 Customer Segment</div>
      <span class="segment-badge ${segC}">${d.segment}</span>

      <!-- Recommendations -->
      <div class="section-title">🎯 Recommended Products</div>
      <div class="grid" style="margin-bottom:1.5rem">
        ${d.recommendations.map(r => `
          <div class="card">
            <div>
              <div class="card-cat">${r.category||""}</div>
              <div class="card-name">${r.product_name}</div>
              <div class="card-price">₹${(r.price||0).toFixed(2)}</div>
              <span class="pred-chip pred-likely">Score ${(r.score*100).toFixed(0)}%</span>
            </div>
            <button class="btn btn-primary btn-sm" style="margin-top:.8rem"
              onclick="addToCart(${r.product_id},'${r.product_name.replace(/'/g,"\\'")}',${r.price||0})">
              🛒 Add to Cart
            </button>
          </div>`).join("") || "<p>No recommendations yet.</p>"}
      </div>

      <!-- Purchase Predictions -->
      <div class="section-title">🤖 AI Purchase Predictions</div>
      ${d.purchase_predictions.map(p => {
        const cls = p.probability >= 0.5 ? "pred-likely" : "pred-unlikely";
        const pct = (p.probability * 100).toFixed(0);
        return `<div class="order-row">
          <span>${p.product_name}</span>
          <span class="pred-chip ${cls}">${p.prediction} · ${pct}%</span>
        </div>`;
      }).join("") || "<p style='color:var(--muted)'>No predictions available.</p>"}

      <!-- Recent Orders -->
      <div class="section-title">📦 Recent Orders</div>
      ${d.previous_purchases.map(o => {
        const sc = `status-${(o.status||"pending").toLowerCase().replace(/ /g,"_")}`;
        return `<div class="order-row">
          <span>Order #${o.order_id} &nbsp;·&nbsp; ${String(o.order_date).split("T")[0]}</span>
          <span>₹${o.total_amount} &nbsp;<span class="status-badge ${sc}">${o.status}</span></span>
        </div>`;
      }).join("") || "<p style='color:var(--muted)'>No orders yet.</p>"}
    `;
  } catch (e) { el.innerHTML = `<p style="color:red">Error loading dashboard: ${e.message}</p>`; }
}

// ─── ADMIN ────────────────────────────────────────────────────────────────────
async function loadAdmin(endpoint) {
  const el = document.getElementById("adminContent");
  el.innerHTML = `<div class="loading">⏳ Loading…</div>`;
  try {
    const data = await api(`/admin/${endpoint}`);
    renderAdminData(endpoint, data);
  } catch (e) { el.innerHTML = `<p style="color:red">Error: ${e.message}</p>`; }
}

function renderAdminData(endpoint, data) {
  const el = document.getElementById("adminContent");
  if (endpoint === "sales-summary") {
    el.innerHTML = `
      <div class="dash-grid">
        <div class="stat-card"><div class="stat-val">₹${(data.total_revenue||0).toLocaleString()}</div><div class="stat-label">Total Revenue</div></div>
        <div class="stat-card"><div class="stat-val">${data.total_orders}</div><div class="stat-label">Total Orders</div></div>
        <div class="stat-card"><div class="stat-val">${data.total_customers}</div><div class="stat-label">Customers</div></div>
        <div class="stat-card"><div class="stat-val">₹${Math.round(data.avg_order_value).toLocaleString()}</div><div class="stat-label">Avg Order Value</div></div>
      </div>`;
    return;
  }
  if (!Array.isArray(data) || !data.length) { el.innerHTML = "<p>No data available.</p>"; return; }
  const keys = Object.keys(data[0]);
  el.innerHTML = `
    <table class="admin-table">
      <thead><tr>${keys.map(k => `<th>${k.replace(/_/g," ").toUpperCase()}</th>`).join("")}</tr></thead>
      <tbody>${data.map(row =>
        `<tr>${keys.map(k => {
          let v = row[k];
          if (typeof v === "number" && k.includes("revenue") || k.includes("spending") || k.includes("price"))
            v = `₹${parseFloat(v).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
          return `<td>${v ?? "–"}</td>`;
        }).join("")}</tr>`
      ).join("")}</tbody>
    </table>`;
}

// ─── INIT ─────────────────────────────────────────────────────────────────────
updateCartCount();
loadCustomers().then(() => loadProducts());
