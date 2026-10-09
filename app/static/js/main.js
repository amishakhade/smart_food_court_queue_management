/**
 * Smart Food Court & Queue Management System
 * Client-Side Cart Engine, Real-Time Poller, and UI Interactions
 */

const FoodCourtCart = {
    STORAGE_KEY: 'campus_foodcourt_cart',

    getItems() {
        try {
            return JSON.parse(localStorage.getItem(this.STORAGE_KEY)) || [];
        } catch (e) {
            return [];
        }
    },

    saveItems(items) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(items));
        this.updateBadge();
    },

    addItem(item) {
        const items = this.getItems();
        const existing = items.find(i => i.id === item.id);
        if (existing) {
            existing.quantity += (item.quantity || 1);
        } else {
            items.push({
                id: item.id,
                name: item.name,
                price: parseFloat(item.price),
                quantity: item.quantity || 1,
                image_url: item.image_url || '',
                is_veg: item.is_veg
            });
        }
        this.saveItems(items);
        this.showToast(`Added ${item.name} to cart!`);
    },

    updateQuantity(id, delta) {
        let items = this.getItems();
        const item = items.find(i => i.id === id);
        if (item) {
            item.quantity += delta;
            if (item.quantity <= 0) {
                items = items.filter(i => i.id !== id);
            }
        }
        this.saveItems(items);
        this.renderCartPage();
    },

    removeItem(id) {
        let items = this.getItems();
        items = items.filter(i => i.id !== id);
        this.saveItems(items);
        this.renderCartPage();
        this.showToast("Item removed from cart", "info");
    },

    clearCart() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.updateBadge();
    },

    getCount() {
        return this.getItems().reduce((sum, item) => sum + item.quantity, 0);
    },

    getTotal() {
        return this.getItems().reduce((sum, item) => sum + (item.price * item.quantity), 0);
    },

    updateBadge() {
        const badge = document.getElementById('navbar-cart-count');
        if (badge) {
            const count = this.getCount();
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    },

    showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type === 'info' ? 'primary' : 'success'} border-0 show mb-2`;
        toastEl.setAttribute('role', 'alert');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body fw-medium">
                    <i class="bi bi-${type === 'info' ? 'info-circle' : 'check-circle-fill'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        toastContainer.appendChild(toastEl);
        setTimeout(() => toastEl.remove(), 3200);
    },

    renderCartPage() {
        const cartItemsList = document.getElementById('cart-items-container');
        const cartSummary = document.getElementById('cart-summary-container');
        const emptyState = document.getElementById('cart-empty-state');
        if (!cartItemsList) return;

        const items = this.getItems();

        if (items.length === 0) {
            cartItemsList.innerHTML = '';
            if (cartSummary) cartSummary.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';
        if (cartSummary) cartSummary.style.display = 'block';

        let html = '';
        items.forEach(item => {
            const itemSubtotal = (item.price * item.quantity).toFixed(2);
            html += `
                <div class="card mb-3 border shadow-sm">
                    <div class="card-body p-3">
                        <div class="row align-items-center">
                            <div class="col-3 col-md-2">
                                <img src="${item.image_url || '/static/images/food-placeholder.png'}" 
                                     alt="${item.name}" 
                                     class="img-fluid rounded" 
                                     style="height: 70px; width: 100%; object-fit: cover;">
                            </div>
                            <div class="col-5 col-md-4">
                                <div class="d-flex align-items-center gap-1">
                                    <span class="dietary-badge ${item.is_veg ? 'veg' : 'non-veg'} position-static p-1">
                                        <i class="bi bi-circle-fill" style="font-size: 8px;"></i>
                                    </span>
                                    <h6 class="mb-0 fw-bold">${item.name}</h6>
                                </div>
                                <span class="text-muted small">₹${item.price.toFixed(2)} each</span>
                            </div>
                            <div class="col-4 col-md-3 text-center">
                                <div class="d-inline-flex align-items-center">
                                    <button class="qty-btn" onclick="FoodCourtCart.updateQuantity(${item.id}, -1)">-</button>
                                    <span class="qty-input px-2">${item.quantity}</span>
                                    <button class="qty-btn" onclick="FoodCourtCart.updateQuantity(${item.id}, 1)">+</button>
                                </div>
                            </div>
                            <div class="col-12 col-md-3 d-flex justify-content-between justify-content-md-end align-items-center mt-2 mt-md-0">
                                <span class="fw-bold fs-5 text-success me-3">₹${itemSubtotal}</span>
                                <button class="btn btn-outline-danger btn-sm" onclick="FoodCourtCart.removeItem(${item.id})">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        cartItemsList.innerHTML = html;

        // Update totals
        const total = this.getTotal();
        const totalEl = document.getElementById('cart-grand-total');
        const subtotalEl = document.getElementById('cart-subtotal');
        if (totalEl) totalEl.textContent = `₹${total.toFixed(2)}`;
        if (subtotalEl) subtotalEl.textContent = `₹${total.toFixed(2)}`;
    },

    setupCheckoutPage() {
        const checkoutForm = document.getElementById('checkout-form');
        const cartInput = document.getElementById('cart_data_input');
        const checkoutItemsList = document.getElementById('checkout-items-list');
        const checkoutTotalEl = document.getElementById('checkout-total-val');

        if (!checkoutForm || !cartInput) return;

        const items = this.getItems();
        if (items.length === 0) {
            window.location.href = '/menu';
            return;
        }

        cartInput.value = JSON.stringify(items);

        if (checkoutItemsList) {
            let listHtml = '';
            items.forEach(i => {
                listHtml += `
                    <li class="list-group-item d-flex justify-content-between lh-sm">
                        <div>
                            <h6 class="my-0">${i.name}</h6>
                            <small class="text-muted">Qty: ${i.quantity} × ₹${i.price.toFixed(2)}</small>
                        </div>
                        <span class="text-muted fw-bold">₹${(i.price * i.quantity).toFixed(2)}</span>
                    </li>
                `;
            });
            checkoutItemsList.innerHTML = listHtml;
        }

        if (checkoutTotalEl) {
            checkoutTotalEl.textContent = `₹${this.getTotal().toFixed(2)}`;
        }

        // On successful form submit, clear local cart
        checkoutForm.addEventListener('submit', () => {
            // Cart will be cleared on confirmation page
        });
    }
};

// Periodic polling for Live Order Tracker
function initOrderTracking(orderNumber) {
    if (!orderNumber) return;

    function pollStatus() {
        fetch(`/api/orders/${orderNumber}/status`)
            .then(res => res.json())
            .then(data => {
                if (!data.success) return;

                const statusBadge = document.getElementById('live-status-badge');
                const queuePosEl = document.getElementById('live-queue-position');
                const waitTimeEl = document.getElementById('live-wait-time');
                const cancelBtn = document.getElementById('cancel-order-container');

                if (statusBadge) {
                    statusBadge.textContent = data.status;
                    statusBadge.className = `badge-status ${data.status.replace(/ /g, '-')}`;
                }

                if (queuePosEl) {
                    if (data.is_ready) {
                        queuePosEl.innerHTML = '<span class="text-success"><i class="bi bi-bell-fill"></i> READY FOR PICKUP!</span>';
                    } else if (data.is_completed) {
                        queuePosEl.innerHTML = '<span class="text-muted"><i class="bi bi-check-circle-fill"></i> Order Picked Up</span>';
                    } else if (data.is_cancelled) {
                        queuePosEl.innerHTML = '<span class="text-danger"><i class="bi bi-x-circle-fill"></i> Order Cancelled</span>';
                    } else {
                        queuePosEl.textContent = data.queue_position ? `#${data.queue_position}` : 'Processing';
                    }
                }

                if (waitTimeEl) {
                    if (data.is_ready) {
                        waitTimeEl.textContent = 'Ready now! Please collect at food counter.';
                    } else if (data.is_completed || data.is_cancelled) {
                        waitTimeEl.textContent = '0 mins';
                    } else {
                        waitTimeEl.textContent = `~${data.estimated_wait_mins} mins`;
                    }
                }

                // Stepper update
                updateTrackerSteps(data.status);

                // Cancel button visibility
                if (cancelBtn) {
                    cancelBtn.style.display = data.is_cancellable ? 'block' : 'none';
                }

                // If completed or cancelled, stop continuous aggressive polling
                if (data.is_completed || data.is_cancelled) {
                    clearInterval(trackingInterval);
                }
            })
            .catch(err => console.error("Error polling order status:", err));
    }

    function updateTrackerSteps(currentStatus) {
        const steps = ['Pending', 'Accepted', 'Preparing', 'Ready for Pickup', 'Completed'];
        const currentIdx = steps.indexOf(currentStatus);

        steps.forEach((step, idx) => {
            const stepEl = document.getElementById(`step-${idx + 1}`);
            if (!stepEl) return;

            stepEl.classList.remove('active', 'completed');
            if (idx < currentIdx) {
                stepEl.classList.add('completed');
            } else if (idx === currentIdx) {
                stepEl.classList.add('active');
            }
        });
    }

    // Initial poll and recurring every 5 seconds
    pollStatus();
    const trackingInterval = setInterval(pollStatus, 5000);
}

// Auto-run on DOM load
document.addEventListener('DOMContentLoaded', () => {
    FoodCourtCart.updateBadge();
    FoodCourtCart.renderCartPage();
    FoodCourtCart.setupCheckoutPage();

    // Check if on confirmation page to clear client cart
    if (document.body.dataset.page === 'order-confirmation') {
        FoodCourtCart.clearCart();
    }
});
