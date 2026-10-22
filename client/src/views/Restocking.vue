<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Set your available budget to see recommended items based on demand forecasts.</p>
    </div>

    <div class="card budget-card">
      <div class="budget-header">
        <span class="budget-label">Available Budget</span>
        <span class="budget-amount">{{ formatCurrency(budget) }}</span>
      </div>
      <input
        type="range"
        class="budget-slider"
        min="1000"
        max="500000"
        step="1000"
        v-model.number="budget"
      />
      <div class="slider-labels">
        <span class="slider-min">$1,000</span>
        <span class="slider-max">$500,000</span>
      </div>
      <div class="budget-remaining">
        Budget remaining: {{ formatCurrency(budgetRemaining) }}
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Recommended Items</h3>
        <span class="card-meta">{{ recommendations.length }} items available &middot; {{ selectedItems.length }} selected &middot; {{ formatCurrency(totalCost) }} selected total</span>
      </div>

      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else>
        <div v-if="recommendations.length === 0" class="empty-state">
          No items fit within the current budget. Try increasing the budget.
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th class="col-select">
                  <input
                    type="checkbox"
                    ref="selectAllRef"
                    :checked="allSelected"
                    @change="toggleAll"
                  />
                </th>
                <th>Item Name</th>
                <th>SKU</th>
                <th>Trend</th>
                <th>Forecasted Demand</th>
                <th>Qty to Restock</th>
                <th>Unit Cost</th>
                <th>Subtotal</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations"
                :key="item.item_sku"
                :class="{ 'is-selected': selectedSkus.has(item.item_sku) }"
              >
                <td class="col-select">
                  <input
                    type="checkbox"
                    :checked="selectedSkus.has(item.item_sku)"
                    @change="toggleSku(item.item_sku)"
                  />
                </td>
                <td>{{ item.item_name }}</td>
                <td class="sku-cell">{{ item.item_sku }}</td>
                <td>
                  <span class="badge" :class="item.trend">{{ item.trend }}</span>
                </td>
                <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                <td>{{ item.qty.toLocaleString() }}</td>
                <td>{{ formatCurrency(item.unitCost) }}</td>
                <td><strong>{{ formatCurrency(item.subtotal) }}</strong></td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="totals-row">
                <td colspan="5" class="totals-label">{{ selectedItems.length }} of {{ recommendations.length }} selected</td>
                <td></td>
                <td></td>
                <td><strong>{{ formatCurrency(totalCost) }}</strong></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>

    <div class="order-actions">
      <div v-if="submittedOrder" class="success-banner">
        Order {{ submittedOrder.order_number }} submitted successfully.
        <router-link to="/orders" class="orders-link">View in Orders tab</router-link>
      </div>
      <button
        class="place-order-btn"
        :disabled="selectedItems.length === 0 || submitting || !!submittedOrder"
        @click="placeOrder"
      >
        {{ submitting ? 'Placing Order...' : 'Place Order' }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(50000)
    const allForecasts = ref([])
    const allInventory = ref([])
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submittedOrder = ref(null)

    const selectedSkus = ref(new Set())
    const selectAllRef = ref(null)

    onMounted(async () => {
      try {
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        allForecasts.value = forecasts
        allInventory.value = inventory
      } catch (err) {
        error.value = 'Failed to load data'
        console.error(err)
      } finally {
        loading.value = false
      }
    })

    const recommendations = computed(() => {
      const bysku = Object.fromEntries(allInventory.value.map(i => [i.sku, i]))
      const candidates = allForecasts.value
        .filter(f => bysku[f.item_sku])
        .map(f => {
          const inv = bysku[f.item_sku]
          const qty = Math.max(f.forecasted_demand, inv.reorder_point - inv.quantity_on_hand, 0)
          return { ...f, inv, qty, unitCost: inv.unit_cost, subtotal: qty * inv.unit_cost }
        })
        .filter(c => c.qty > 0)
        .sort((a, b) => b.forecasted_demand - a.forecasted_demand)

      let remaining = budget.value
      const result = []
      for (const c of candidates) {
        if (c.subtotal <= remaining) {
          result.push(c)
          remaining -= c.subtotal
        }
      }
      return result
    })

    // Reset selections whenever the recommendations list changes (e.g. budget slider moved)
    watch(recommendations, () => {
      selectedSkus.value = new Set()
    })

    const toggleSku = (sku) => {
      const next = new Set(selectedSkus.value)
      next.has(sku) ? next.delete(sku) : next.add(sku)
      selectedSkus.value = next
    }

    const toggleAll = () => {
      if (selectedSkus.value.size === recommendations.value.length) {
        selectedSkus.value = new Set()
      } else {
        selectedSkus.value = new Set(recommendations.value.map(r => r.item_sku))
      }
    }

    const allSelected = computed(() =>
      recommendations.value.length > 0 && selectedSkus.value.size === recommendations.value.length
    )

    const someSelected = computed(() =>
      selectedSkus.value.size > 0 && selectedSkus.value.size < recommendations.value.length
    )

    // Imperatively set the indeterminate state since it cannot be bound as an attribute
    watch(someSelected, (val) => {
      if (selectAllRef.value) selectAllRef.value.indeterminate = val
    })

    const selectedItems = computed(() =>
      recommendations.value.filter(r => selectedSkus.value.has(r.item_sku))
    )

    const totalCost = computed(() => selectedItems.value.reduce((s, r) => s + r.subtotal, 0))
    const budgetRemaining = computed(() => budget.value - totalCost.value)

    const placeOrder = async () => {
      submitting.value = true
      try {
        const items = selectedItems.value.map(r => ({
          sku: r.item_sku,
          name: r.item_name,
          quantity: r.qty,
          unit_price: r.unitCost
        }))
        submittedOrder.value = await api.createRestockingOrder({ items })
      } catch (err) {
        error.value = 'Failed to place order'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    const formatCurrency = (val) =>
      '$' + val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    return {
      budget,
      loading,
      error,
      recommendations,
      selectedSkus,
      selectedItems,
      allSelected,
      someSelected,
      toggleSku,
      toggleAll,
      selectAllRef,
      totalCost,
      budgetRemaining,
      submitting,
      submittedOrder,
      placeOrder,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

/* Budget card */
.budget-card {
  margin-bottom: 1.25rem;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.budget-label {
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
}

.budget-amount {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  height: 6px;
  cursor: pointer;
  margin-bottom: 0.375rem;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.625rem;
}

.slider-min,
.slider-max {
  font-size: 0.813rem;
  color: #64748b;
}

.budget-remaining {
  font-size: 0.875rem;
  color: #64748b;
  margin-top: 0.25rem;
}

/* Card meta */
.card-meta {
  font-size: 0.875rem;
  color: #64748b;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* SKU cell */
.sku-cell {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.813rem;
  color: #475569;
}

/* Table footer totals row */
.totals-row td {
  border-top: 2px solid #e2e8f0;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
  background: #f8fafc;
}

.totals-label {
  font-weight: 600;
  color: #0f172a;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

/* Order actions */
.order-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
  margin-bottom: 1.5rem;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* Success banner */
.success-banner {
  flex: 1;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  color: #065f46;
  font-size: 0.938rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.orders-link {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
}

.orders-link:hover {
  color: #047857;
}

/* Checkbox column */
.col-select {
  width: 40px;
  text-align: center;
}

.col-select input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #2563eb;
}

/* Highlight selected rows */
tbody tr.is-selected {
  background: #eff6ff;
}

tbody tr.is-selected:hover {
  background: #dbeafe;
}
</style>
