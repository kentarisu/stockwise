<script>
const formatCurrency = (value) => {
  const num = Number(value || 0);
  return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// CSRF helper
function getCookie(name){let v=null;if(document.cookie&&document.cookie!==''){const cs=document.cookie.split(';');for(let i=0;i<cs.length;i++){const c=cs[i].trim();if(c.substring(0,name.length+1)===(name+'=')){v=decodeURIComponent(c.substring(name.length+1));break;}}}return v;}
const csrftoken=getCookie('csrftoken');
$.ajaxSetup({headers:{'X-CSRFToken':csrftoken}});

// Template variables - get from data attribute to avoid linter errors
const configEl = document.getElementById('page-config');
var preselectedProductId = configEl && configEl.dataset.preselectedProductId ? parseInt(configEl.dataset.preselectedProductId, 10) : null;
var productLocked = configEl ? (configEl.dataset.productLocked === 'true') : false;

let products=[]; let currentStep=1; window.saleItems=[]; let transactionNumber=''; let orNumber='';

function loadActiveProducts(){
  console.log('loadActiveProducts called');
  const url = "{% url 'get_active_products' %}";
  console.log('Fetching from:', url);
  
  return fetch(url, {
    method: 'GET',
    headers: {
      'X-CSRFToken': csrftoken
    }
  })
    .then(r=>{
      console.log('Response status:', r.status, r.statusText);
      if (!r.ok) {
        console.error('Failed to load products:', r.status, r.statusText);
        return {success: false, data: []};
      }
      return r.json();
    })
    .then(resp=>{ 
      console.log('Products response:', resp);
      if(!resp.success) {
        console.error('Products API returned error:', resp.error || 'Unknown error');
        products = [];
        updateProductSelects(); 
        return [];
      }
      if (!resp.data || !Array.isArray(resp.data)) {
        console.error('Invalid products data format:', resp);
        products = [];
        updateProductSelects();
        return [];
      }
      products=resp.data.map(p=>{p.price=parseFloat(p.price)||0; return p;}); 
      console.log('Products processed:', products.length);
      updateProductSelects(); 
      return products; 
    })
    .catch(err=>{
      console.error('Error loading products:', err);
      products = [];
      updateProductSelects();
      return [];
    });
}
function updateProductSelects(){
  console.log('updateProductSelects called with', products.length, 'products');
  
  // If no products, show empty dropdown
  if (!products || products.length === 0) {
    console.warn('No products available to populate dropdowns');
    $('.product-select').each(function(){
      $(this).html('<option value="">No products available</option>');
    });
    return;
  }
  
  // Group products by fruit base name (e.g., "Apple (Fuji)" -> "Apple")
  const groupedProducts = {};
  products.forEach(p => {
    // Extract base fruit name (remove variant in parentheses)
    const baseName = p.name ? (p.name.split('(')[0].trim() || p.name.trim()) : 'Other';
    if (!groupedProducts[baseName]) {
      groupedProducts[baseName] = [];
    }
    groupedProducts[baseName].push(p);
  });
  
  // Sort fruit names alphabetically
  const sortedFruits = Object.keys(groupedProducts).sort();
  
  $('.product-select').each(function(){
    const $this=$(this);
    const currentValue = $this.val(); // Store current selection
    let options='<option value="">Select a fruit</option>';
    
    // Create optgroups for each fruit category
    sortedFruits.forEach(fruitName => {
      options += `<optgroup label="${fruitName}">`;
      groupedProducts[fruitName].forEach(p => {
        const stock = p.stock || 0;
        const stockText = stock > 0 ? `[Stock: ${stock}]` : '[Out of Stock]';
        
        // Extract variant if name already contains it in parentheses, otherwise use p.variant
        // e.g., "Apple (Fuji)" -> name already has variant, don't add again
        let displayName = p.name || '';
        
        // Only add quantity if it exists
        const size = p.size ? ` (Qty: ${p.size})` : '';
        
        // Format: "Product Name (Qty) - Price [Stock: X]"
        displayName = `${displayName}${size} - ₱${formatCurrency(p.price)} ${stockText}`;
        
        options += `<option value="${p.product_id}" data-price="${p.price}" data-name="${p.name}" data-variant="${p.variant||''}" data-size="${p.size||''}" data-stock="${stock}">${displayName}</option>`;
      });
      options += '</optgroup>';
    });
    
    $this.html(options);
    if(currentValue) {
      $this.val(currentValue); // Restore previous selection
    }
    if(!$this.hasClass('select2-hidden-accessible')){
      $this.select2({placeholder:'Search and select a fruit...',allowClear:true,width:'100%',dropdownParent:$this.closest('.card-modern')});
    } else { $this.trigger('change.select2'); }
  });
}
function updateTotal(){ let total=0; $('.item-row').each(function(){ const $sel=$(this).find('.product-select option:selected'); const $qty=$(this).find('.quantity-input'); if($sel.val()&&$qty.val()){ const price=parseFloat($sel.data('price'))||0; const q=parseInt($qty.val())||0; total+=price*q; }}); $('#liveSaleTotalWithVATText').text(formatCurrency(total)); }

async function updateBatchesToSell(itemRow) {
  const $row = $(itemRow);
  const productId = $row.find('.product-select').val();
  const quantity = parseInt($row.find('.quantity-input').val()) || 0;
  const $batchDisplay = $row.find('.batches-display');
  
  if (!productId || quantity <= 0) {
    $batchDisplay.text('Select fruit and enter quantity to see which batches will be sold');
    $batchDisplay.removeClass('text-success fw-bold').addClass('text-muted');
    return;
  }
  
  try {
    // Get available batches for this product
    const response = await fetch(`/api/products/${productId}/stock_details/`, {
      method: 'GET',
      headers: {
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
      }
    });
    const data = await response.json();
    
    if (data.success && data.data.length > 0) {
      const availableBatches = data.data.map(batch => batch.batch_id);
      const totalAvailable = availableBatches.length;
      
      if (quantity > totalAvailable) {
        $batchDisplay.text(`Only ${totalAvailable} boxes available`);
        $batchDisplay.removeClass('text-muted text-success').addClass('text-warning fw-bold');
      } else if (quantity === 1) {
        // Single batch
        $batchDisplay.text(availableBatches[0]);
        $batchDisplay.removeClass('text-muted text-warning').addClass('text-success fw-bold');
      } else {
        // Multiple batches - show range
        const firstBatch = availableBatches[0];
        const lastBatch = availableBatches[quantity - 1];
        $batchDisplay.text(firstBatch + ' to ' + lastBatch);
        $batchDisplay.removeClass('text-muted text-warning').addClass('text-success fw-bold');
      }
    } else {
      $batchDisplay.text('No stock available');
      $batchDisplay.removeClass('text-success fw-bold').addClass('text-warning');
    }
  } catch (error) {
    console.error('Error fetching batch info:', error);
    $batchDisplay.text('Error loading batch info');
    $batchDisplay.removeClass('text-success fw-bold').addClass('text-danger');
  }
}
function showStep(step){ $('#saleStep1,#saleStep2,#saleStep3').hide(); $('#stepIndicator1,#stepIndicator2,#stepIndicator3').removeClass('active'); if(step===1){ $('#saleStep1').show(); $('#nextToStep2').show(); $('#confirmPaymentStep,#recordSaleBtn,#printReceiptBtn,#printReceiptAfterBtn,#doneBtn').hide(); $('#backToStep1').hide(); $('#stepIndicator1').addClass('active'); } else if(step===2){ $('#saleStep2').show(); $('#nextToStep2').hide(); $('#confirmPaymentStep').show(); $('#recordSaleBtn,#printReceiptBtn,#printReceiptAfterBtn,#doneBtn').hide(); $('#backToStep1').show(); $('#stepIndicator2').addClass('active'); } else { $('#saleStep3').show(); $('#nextToStep2,#confirmPaymentStep').hide(); $('#recordSaleBtn,#printReceiptBtn').show(); $('#backToStep1').show(); $('#stepIndicator3').addClass('active'); } currentStep=step; }
function generateReceipt(){ const items=window.saleItems||[]; const subtotal=parseFloat($('#paymentSubtotal').text().replace(/,/g,''))||0; const vat=parseFloat($('#paymentVAT').text().replace(/,/g,''))||0; const totalAmount=parseFloat($('#paymentTotalWithVAT').text().replace(/,/g,''))||0; const amountPaid=parseFloat($('#paymentTendered').val())||0; const change=parseFloat($('#paymentChange').text().replace(/,/g,''))||0; const customerName=$('#customerName').val()||'Walk-in Customer'; const customerContact=$('#customerContact').val()||''; const customerAddress=$('#customerAddress').val()||''; let html=''; items.forEach(it=>{ const baseName=(it.name||'').split('(')[0].trim(); let d=baseName||it.name||''; if(it.variant) d+=` (${it.variant})`; if(it.size) d+=` (${it.size})`; html+=`<tr><td>${d}</td><td class="text-end">${it.quantity}</td><td class="text-end">₱${formatCurrency(it.price)}</td><td class="text-end">₱${formatCurrency(it.amount)}</td></tr>`; }); $('#receiptTableItems').html(html); $('#receiptSubtotal').text('₱'+formatCurrency(subtotal)); $('#receiptVAT').text('₱'+formatCurrency(vat)); $('#receiptTotalAmount').text('₱'+formatCurrency(totalAmount)); $('#receiptAmountPaid').text('₱'+formatCurrency(amountPaid)); $('#receiptChange').text('₱'+formatCurrency(change)); $('#transactionNumber').text(transactionNumber||''); $('#orNumber').text(orNumber||''); $('#receiptDate').text(new Date().toLocaleString()); $('#receiptCustomerName').text(customerName); $('#receiptCustomerContact').text(customerContact||'N/A'); $('#receiptCustomerAddress').text(customerAddress||'N/A'); }
function recordSale(){ const items=window.saleItems||[]; const amountPaid=parseFloat($('#paymentTendered').val())||0; const customerName=$('#customerName').val()||''; const customerContact=$('#customerContact').val()||''; const customerAddress=$('#customerAddress').val()||''; const saleData={ action:'buy', items: JSON.stringify(items), amount_paid: amountPaid, customer_name: customerName, customer_contact: customerContact, customer_address: customerAddress, transaction_number: transactionNumber, or_number: orNumber, purchase_date: new Date().toISOString().split('T')[0], csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val() }; $.ajax({ url: "{% url 'handle_product_post' %}", method:'POST', data:saleData, success:function(resp){ if(resp.success){ try{ if(resp.sale_ids && resp.sale_ids.length){ transactionNumber = String(resp.sale_ids[0]); window.lastRecordedSaleId = resp.sale_ids[0]; // Store the actual sale_id $('#transactionNumber').text(transactionNumber); } $('#orNumber').text(orNumber||''); }catch(e){} $('#saleSuccessMessage').show(); $('#printReceiptBtn').hide(); $('#printReceiptAfterBtn,#doneBtn').show(); } else { $('#buyFormAlert').html(`<div class=\"alert alert-danger alert-dismissible fade show\" role=\"alert\">${resp.message}<button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\"></button></div>`); }}, error:function(){ $('#buyFormAlert').html('<div class=\"alert alert-danger alert-dismissible fade show\" role=\"alert\">Error recording sale. Please try again.<button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\"></button></div>'); }}); }
function printReceipt(){ 
    // Get the sale ID - use lastRecordedSaleId first (actual DB ID), then transactionNumber
    const saleId = window.lastRecordedSaleId || transactionNumber;
    
    if (!saleId) {
        alert('No sale ID found. Please record the sale first.');
        return;
    }
    
    // Ensure saleId is a number (sale_id from database)
    const numericSaleId = parseInt(saleId);
    if (isNaN(numericSaleId)) {
        alert('Invalid sale ID. Please record the sale first.');
        return;
    }
    
    // Use thermal printer
    printThermalReceipt(numericSaleId);
}

function printThermalReceipt(saleId) {
    const formData = new FormData();
    
    // Get printer settings from localStorage or use defaults
    const connectionType = localStorage.getItem('thermalPrinterConnectionType') || 'windows';
    const printerName = localStorage.getItem('thermalPrinterName') || 'POS58 Printer';
    
    formData.append('connection_type', connectionType);
    
    if (connectionType === 'windows') {
        formData.append('printer_name', printerName);
    } else if (connectionType === 'serial' || connectionType === 'bluetooth') {
        formData.append('port', localStorage.getItem('thermalPrinterPort') || 'COM3');
        formData.append('baudrate', localStorage.getItem('thermalPrinterBaudrate') || '9600');
    }
    
    // Get CSRF token (use the global getCookie function defined earlier)
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/api/printer/receipt/${saleId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        },
        body: formData
    })
    .then(response => {
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // Response is HTML (likely an error page)
            return response.text().then(html => {
                throw new Error('Server returned HTML instead of JSON. Check server logs for errors.');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Receipt printed successfully to thermal printer!');
        } else {
            alert('Print failed: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(err => {
        console.error('Thermal print error', err);
        alert('Error printing to thermal printer: ' + err.message);
    });
}

$(document).ready(function(){
  $('#purchaseDate').val(new Date().toLocaleDateString('en-US',{year:'numeric',month:'long',day:'numeric'}));
  
  // Load products with error handling
  console.log('Loading active products...');
  loadActiveProducts()
    .then(products => {
      console.log('Products loaded:', products.length);
      if (products.length === 0) {
        console.warn('No products found. Check if products exist and are active.');
      }
    })
    .catch(err => {
      console.error('Failed to load products:', err);
    });
  $(document).on('change','.product-select',function(){ const $this=$(this); const pid=$this.val(); const $row=$this.closest('.item-row'); const $qty=$row.find('.quantity-input'); const $info=$row.find('.stock-info'); if(pid){ const p=products.find(pp=>pp.product_id==pid); if(p){ $this.data('price',p.price); $this.data('name',p.name); $this.data('variant',p.variant); $this.data('size',p.size); $info.text(`Stock: ${p.stock||0} boxes`); $qty.attr('max',p.stock||999); } } else { $info.text(''); $qty.removeAttr('max'); } updateTotal(); updateBatchesToSell($row); });
  $(document).on('input','.quantity-input',function(){
    updateTotal();
    updateBatchesToSell($(this).closest('.item-row'));
  });
  $('#addItemBtn').on('click',function(){ 
    const row=`<div class="item-row"><div class="row g-3 align-items-end"><div class="col-md-6 col-lg-5"><label class="form-label">Fruit</label><select class="form-select product-select" required><option value="">Select a fruit</option></select><div class="stock-info text-muted"></div></div><div class="col-md-5 col-lg-4"><label class="form-label">Boxes</label><input type="number" class="form-control quantity-input stock-quantity" min="1" required></div><div class="col-md-1 col-lg-3 text-end"><button type="button" class="btn btn-outline-danger btn-sm remove-item"><i class="bi bi-trash"></i></button></div></div><div class="row mt-2"><div class="col-12"><label class="form-label small fw-semibold">Batches to Sell (FIFO)</label><div class="batches-to-sell"><span class="batches-display text-muted">Select fruit and enter quantity to see which batches will be sold</span></div></div></div></div>`; 
    $('#itemsContainer').append(row); 
    // Show remove buttons for all rows
    $('.remove-item').show();
    // Update all dropdowns with categorized options (using the same function)
    updateProductSelects();
  });
  $(document).on('click','.remove-item',function(){ 
    $(this).closest('.item-row').remove(); 
    updateTotal();
    // Hide remove buttons if only one row remains
    if($('.item-row').length <= 1) {
      $('.remove-item').hide();
    }
  });

  $('#nextToStep2').on('click',function(){ const form=$('#buyForm')[0]; if(!form.checkValidity()){ form.reportValidity(); return; } const items=[]; let total=0; $('.item-row').each(function(){ const $sel=$(this).find('.product-select option:selected'); const $qty=$(this).find('.quantity-input'); if($sel.val()&&$qty.val()){ const price=parseFloat($sel.data('price')); const q=parseInt($qty.val()); const amt=q*price; total+=amt; items.push({ product_id:$sel.val(), name:$sel.data('name')||'', variant:$sel.data('variant')||'', size:$sel.data['size']||'', quantity:q, price:price, amount:amt }); }}); if(items.length===0){ $('#buyFormAlert').html('<div class=\"alert alert-warning alert-dismissible fade show\" role=\"alert\">Please add at least one item to proceed.<button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\"></button></div>'); return; } const subtotal=total/1.12; const vat=total-subtotal; $('#paymentSubtotal').text(formatCurrency(subtotal)); $('#paymentVAT').text(formatCurrency(vat)); $('#paymentTotalWithVAT').text(formatCurrency(total)); let html=''; items.forEach(it=>{ let d=`#${it.product_id} ${it.name}`; if(it.variant) d+=` (${it.variant})`; if(it.size) d+=` (${it.size})`; html+=`<tr><td>${d}</td><td class=\"text-end\">${it.quantity}</td><td class=\"text-end\">₱${formatCurrency(it.price)}</td><td class=\"text-end\">₱${formatCurrency(it.amount)}</td></tr>`; }); $('#paymentTableItems').html(html); window.saleItems=items; const base=Date.now(); const txnSuffix=(base%1000000).toString().padStart(6,'0'); let orSuffix=((base + Math.floor(Math.random()*900+100))%1000000); if(orSuffix===Number(txnSuffix)){ orSuffix=(orSuffix+1)%1000000; } transactionNumber=`TXN${txnSuffix}`; orNumber=`OR${orSuffix.toString().padStart(6,'0')}`; showStep(2); });
  $('#backToStep1').on('click',function(){ if(currentStep===2){ showStep(1); } else if(currentStep===3){ showStep(2); }});
  $('#confirmPaymentStep').on('click',function(){ const tendered=parseFloat($('#paymentTendered').val())||0; const total=parseFloat($('#paymentTotalWithVAT').text().replace(/,/g,''))||0; if(tendered<total){ $('#buyFormAlert').html('<div class="alert alert-danger alert-dismissible fade show" role="alert">Amount tendered is less than total amount.<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'); return; } const change=tendered-total; $('#paymentChange').text(formatCurrency(change)); generateReceipt(); showStep(3); });
  $('#paymentTendered').on('input',function(){ const t=parseFloat($(this).val())||0; const total=parseFloat($('#paymentTotalWithVAT').text().replace(/,/g,''))||0; const change=t-total; $('#paymentChange').text(formatCurrency(change)); $('#confirmPaymentStep').prop('disabled', t<total); });
  $('#recordSaleBtn').on('click',recordSale);
  $('#printReceiptBtn,#printReceiptAfterBtn').on('click',printReceipt);
  
  // Auto-select product if preselected_product_id is provided (from QR code scan)
  if (preselectedProductId) {
    setTimeout(function() {
      const preselectedId = preselectedProductId;
      if (preselectedId && products.length > 0) {
        // Find the first product select dropdown and set the value
        const $firstSelect = $('.product-select').first();
        if ($firstSelect.length > 0) {
          $firstSelect.val(preselectedId).trigger('change');
          
          // Lock the product selection if accessed via QR scan
          if (productLocked) {
            $firstSelect.prop('disabled', true);
            $firstSelect.addClass('bg-light');
          }
        
          // Show a success message
          var lockMessage = productLocked ? ' Product is locked and cannot be changed.' : '';
          $('#buyFormAlert').html('<div class="alert alert-success alert-dismissible fade show" role="alert"><i class="bi bi-qr-code me-2"></i>Product automatically selected from QR code scan!' + lockMessage + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>');
        }
      }
    }, 1000); // Delay to ensure products are loaded
  }
});

// Input sanitizers for Record Sale
document.addEventListener('input', function(e){
  if(e.target && e.target.id === 'customerName'){
    const cleaned = e.target.value.replace(/[^A-Za-z\s\-.,&]/g,'');
    if (cleaned !== e.target.value) e.target.value = cleaned;
  }
  if(e.target && e.target.id === 'customerContact'){
    const cleaned = e.target.value.replace(/[^0-9+]/g,'');
    if (cleaned !== e.target.value) e.target.value = cleaned;
  }
  if(e.target && e.target.id === 'customerAddress'){
    const cleaned = e.target.value.replace(/[^A-Za-z0-9\s\-.,#]/g,'');
    if (cleaned !== e.target.value) e.target.value = cleaned;
  }
});
document.addEventListener('blur', function(e){
  if(e.target && e.target.id === 'customerName'){
    const val = e.target.value;
    if(!val) return;
    const title = val.toLowerCase().replace(/\s+/g,' ').replace(/\b[a-z]/g, ch=>ch.toUpperCase()).trim();
    e.target.value = title;
  }
}, true);
</script>