<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" role="dialog" aria-modal="true" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'view' ? 'Purchase Order' : 'Create Purchase Order' }}</h3>
            <button class="close-button" aria-label="Close" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <div class="item-name">{{ translateProductName(backlogItem.item_name) }}</div>
              <div class="summary-grid">
                <div class="info-item">
                  <div class="info-label">SKU</div>
                  <div class="info-value mono">{{ backlogItem.item_sku }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Order ID</div>
                  <div class="info-value mono">{{ backlogItem.order_id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Shortfall</div>
                  <div class="info-value danger-text">{{ shortfall }} units</div>
                </div>
              </div>
            </div>

            <!-- Create mode -->
            <form v-if="mode === 'create'" id="po-form" class="po-form" novalidate @submit.prevent="submit">
              <div class="form-field">
                <label for="po-supplier">Supplier Name</label>
                <input id="po-supplier" v-model="form.supplier_name" type="text" :disabled="submitting" />
                <span v-if="errors.supplier_name" class="field-error">{{ errors.supplier_name }}</span>
              </div>

              <div class="form-row">
                <div class="form-field">
                  <label for="po-quantity">Quantity</label>
                  <input id="po-quantity" v-model="form.quantity" type="number" min="1" step="1" :disabled="submitting" />
                  <span v-if="errors.quantity" class="field-error">{{ errors.quantity }}</span>
                </div>
                <div class="form-field">
                  <label for="po-unit-cost">Unit Cost (USD)</label>
                  <input id="po-unit-cost" v-model="form.unit_cost" type="number" min="0" step="0.01" :disabled="submitting" />
                  <span v-if="errors.unit_cost" class="field-error">{{ errors.unit_cost }}</span>
                </div>
              </div>

              <div class="form-field">
                <label for="po-date">Expected Delivery Date</label>
                <input id="po-date" v-model="form.expected_delivery_date" type="date" :disabled="submitting" />
                <span v-if="errors.expected_delivery_date" class="field-error">{{ errors.expected_delivery_date }}</span>
              </div>

              <div class="form-field">
                <label for="po-notes">Notes (optional)</label>
                <textarea id="po-notes" v-model="form.notes" rows="3" :disabled="submitting"></textarea>
              </div>

              <div v-if="formTotal !== null" class="total-row">
                <span>Estimated Total</span>
                <strong>{{ formatMoney(formTotal, 2) }}</strong>
              </div>

              <div v-if="submitError" class="error-banner">{{ submitError }}</div>
            </form>

            <!-- View mode -->
            <div v-else>
              <div v-if="loading" class="state-message">Loading purchase order...</div>
              <div v-else-if="viewError" class="error-banner">{{ viewError }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">Supplier</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Status</div>
                  <div class="info-value">
                    <span class="badge" :class="statusClass">{{ purchaseOrder.status }}</span>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">Quantity</div>
                  <div class="info-value">{{ purchaseOrder.quantity }} units</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Unit Cost</div>
                  <div class="info-value">{{ formatMoney(purchaseOrder.unit_cost, 2) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Total</div>
                  <div class="info-value">{{ formatMoney(purchaseOrder.quantity * purchaseOrder.unit_cost, 2) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Expected Delivery</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Created</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div class="info-item full-width">
                  <div class="info-label">Notes</div>
                  <div class="info-value">{{ purchaseOrder.notes || 'None' }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" :disabled="submitting" @click="close">
              {{ mode === 'view' ? 'Close' : 'Cancel' }}
            </button>
            <button v-if="mode === 'create'" type="submit" form="po-form" class="btn-primary" :disabled="submitting">
              {{ submitting ? 'Submitting...' : 'Create Purchase Order' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const { translateProductName, currentCurrency } = useI18n()

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: {
    type: String,
    default: 'create',
    validator: (v) => ['create', 'view'].includes(v)
  }
})

const emit = defineEmits(['close', 'po-created'])

const form = reactive({
  supplier_name: '',
  quantity: 1,
  unit_cost: '',
  expected_delivery_date: '',
  notes: ''
})
const errors = reactive({})
const submitting = ref(false)
const submitError = ref(null)

const purchaseOrder = ref(null)
const loading = ref(false)
const viewError = ref(null)

const shortfall = computed(() => {
  if (!props.backlogItem) return 0
  return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
})

const formTotal = computed(() => {
  const q = Number(form.quantity)
  const c = Number(form.unit_cost)
  if (!form.unit_cost || !Number.isFinite(q) || !Number.isFinite(c) || q <= 0 || c <= 0) return null
  return q * c
})

const statusClass = computed(() => {
  // Map PO status to the project status colors (green/blue/yellow/red)
  const s = (purchaseOrder.value?.status || '').toLowerCase()
  if (['received', 'delivered', 'completed'].includes(s)) return 'success'
  if (['cancelled', 'canceled', 'rejected'].includes(s)) return 'danger'
  if (['shipped', 'confirmed', 'approved'].includes(s)) return 'info'
  return 'warning'
})

const formatMoney = (amount, decimals = 0) =>
  formatCurrencyWithDecimals(Number(amount) || 0, currentCurrency.value, decimals)

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const resetForm = () => {
  form.supplier_name = ''
  // Default to the shortfall, but never below the minimum of 1
  form.quantity = Math.max(1, shortfall.value)
  form.unit_cost = ''
  form.expected_delivery_date = ''
  form.notes = ''
  Object.keys(errors).forEach((k) => delete errors[k])
  submitError.value = null
  submitting.value = false
}

const loadPurchaseOrder = async () => {
  purchaseOrder.value = null
  viewError.value = null
  if (!props.backlogItem) return
  loading.value = true
  const requestedId = props.backlogItem.id
  try {
    const result = await api.getPurchaseOrderByBacklogItem(requestedId)
    // Ignore stale responses if the modal switched items meanwhile
    if (props.backlogItem?.id !== requestedId) return
    purchaseOrder.value = result
  } catch (err) {
    if (props.backlogItem?.id !== requestedId) return
    viewError.value = err?.response?.status === 404
      ? 'No purchase order found'
      : 'Failed to load purchase order'
    if (err?.response?.status !== 404) console.error('Failed to load purchase order:', err)
  } finally {
    if (props.backlogItem?.id === requestedId) loading.value = false
  }
}

// Reset/reload whenever the modal opens, the item changes, or the mode changes
watch(
  () => [props.isOpen, props.backlogItem, props.mode],
  () => {
    if (!props.isOpen || !props.backlogItem) return
    if (props.mode === 'view') {
      loadPurchaseOrder()
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

const validate = () => {
  Object.keys(errors).forEach((k) => delete errors[k])
  if (!form.supplier_name.trim()) errors.supplier_name = 'Supplier name is required'

  const q = Number(form.quantity)
  if (form.quantity === '' || form.quantity === null || !Number.isInteger(q) || q < 1) {
    errors.quantity = 'Quantity must be a whole number of at least 1'
  }

  const c = Number(form.unit_cost)
  if (form.unit_cost === '' || form.unit_cost === null || !Number.isFinite(c) || c <= 0) {
    errors.unit_cost = 'Unit cost must be greater than 0'
  }

  const d = new Date(form.expected_delivery_date)
  if (!form.expected_delivery_date || isNaN(d.getTime())) {
    errors.expected_delivery_date = 'Expected delivery date is required'
  }
  return Object.keys(errors).length === 0
}

const submit = async () => {
  if (submitting.value) return
  submitError.value = null
  if (!validate()) return

  submitting.value = true
  try {
    const po = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.supplier_name.trim(),
      quantity: Number(form.quantity),
      unit_cost: Number(form.unit_cost),
      expected_delivery_date: form.expected_delivery_date,
      notes: form.notes.trim()
    })
    emit('po-created', po)
  } catch (err) {
    console.error('Failed to create purchase order:', err)
    const detail = err?.response?.data?.detail
    submitError.value = typeof detail === 'string' ? detail : 'Failed to create purchase order'
  } finally {
    submitting.value = false
  }
}

const close = () => {
  if (submitting.value) return
  emit('close')
}

const onKeydown = (e) => {
  if (e.key === 'Escape' && props.isOpen) close()
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 640px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem;
}

.item-summary {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.item-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.75rem;
}

.summary-grid,
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
  overflow-wrap: anywhere;
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.danger-text {
  color: #dc2626;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
}

.badge.success { background: #dcfce7; color: #166534; }
.badge.info { background: #dbeafe; color: #1e40af; }
.badge.warning { background: #fef3c7; color: #92400e; }
.badge.danger { background: #fecaca; color: #991b1b; }

.po-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-field label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.form-field input,
.form-field textarea {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  font-family: inherit;
  color: #0f172a;
  background: white;
  resize: vertical;
}

.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-field input:disabled,
.form-field textarea:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
}

.field-error {
  font-size: 0.813rem;
  color: #dc2626;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #334155;
  font-size: 0.938rem;
}

.error-banner {
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  font-size: 0.875rem;
}

.state-message {
  padding: 1.5rem 0;
  text-align: center;
  color: #64748b;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary,
.btn-primary {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #334155;
}

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  background: #0f172a;
  border: 1px solid #0f172a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-secondary:disabled,
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
